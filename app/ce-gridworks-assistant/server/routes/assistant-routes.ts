import type { Application, Request, Response } from 'express';
import { z } from 'zod';
import { type Db, SCHEMA } from '../lib/db';
import {
  type Chunk,
  FORMATS,
  type Format,
  REGIONS,
  type Filters,
  buildEvidence,
  citedIds,
  exclusionReason,
  governedFilters,
  systemPrompt,
} from '../lib/context';
import { MODEL, chat } from '../lib/llm';

interface SearchApi {
  query(
    alias: string,
    req: { queryText: string; numResults?: number; filters?: Filters }
  ): Promise<{ results: { score: number; data: Record<string, unknown> }[] }>;
}

const GOVERNED_K = 3; // Lab 6: the smallest context that met every threshold
const UNGOVERNED_K = 6;

function identity(req: Request): { email: string; viaProxy: boolean } {
  const email = req.header('x-forwarded-email');
  return email ? { email, viaProxy: true } : { email: process.env.LOCAL_DEV_USER ?? 'local-dev', viaProxy: false };
}

function toChunk(r: { score: number; data: Record<string, unknown> }): Chunk {
  const d = r.data;
  return {
    chunk_id: String(d.chunk_id),
    document_id: String(d.document_id),
    title: String(d.title),
    text: String(d.text),
    region_code: String(d.region_code),
    status: String(d.status),
    effective_date: String(d.effective_date),
    score: Number(r.score),
  };
}

const chatBody = z.object({
  question: z.string().trim().min(3).max(500),
  region: z.enum(REGIONS),
  governed: z.boolean(),
  // Explicit instruction for this session: nearest valid memory source beats long-term preference.
  sessionFormat: z.enum(FORMATS).optional(),
});

const prefBody = z.object({ key: z.literal('response_format'), value: z.enum(FORMATS) });
const requestBody = z.object({ asset_id: z.string().regex(/^A-\d{4}$/), summary: z.string().trim().min(5).max(200) });
const decisionBody = z.object({ approve: z.boolean() });

export function registerAssistantRoutes(app: Application, db: Db, search: SearchApi): void {
  const handler = (fn: (req: Request, res: Response) => Promise<void> | void) => (req: Request, res: Response) => {
    Promise.resolve()
      .then(() => fn(req, res))
      .catch((e: unknown) => {
        console.error('[route error]', e instanceof Error ? e.message : e);
        if (!res.headersSent) res.status(500).json({ error: 'Internal error. See app logs.' });
      });
  };

  app.get(
    '/api/whoami',
    handler((req, res) => {
      const who = identity(req);
      res.json({
        ...who,
        model: MODEL,
        executesAs: 'app service principal (data and model calls are not on-behalf-of-user)',
      });
    })
  );

  // ---- long-term memory (structured, exact) -----------------------------------------------
  app.get(
    '/api/prefs',
    handler(async (req, res) => {
      const { rows } = await db.query(`SELECT key, value FROM ${SCHEMA}.prefs WHERE user_id = $1`, [
        identity(req).email,
      ]);
      res.json(Object.fromEntries(rows.map((r) => [String(r.key), String(r.value)])));
    })
  );

  app.put(
    '/api/prefs',
    handler(async (req, res) => {
      const p = prefBody.safeParse(req.body);
      if (!p.success) {
        res.status(400).json({ error: 'Invalid preference' });
        return;
      }
      await db.query(
        `INSERT INTO ${SCHEMA}.prefs (user_id, key, value) VALUES ($1, $2, $3)
       ON CONFLICT (user_id, key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()`,
        [identity(req).email, p.data.key, p.data.value]
      );
      res.json({ ok: true });
    })
  );

  // ---- chat: governed vs ungoverned context -------------------------------------------------
  app.post(
    '/api/chat',
    handler(async (req, res) => {
      const p = chatBody.safeParse(req.body);
      if (!p.success) {
        res.status(400).json({ error: 'Invalid request', details: p.error.issues.map((i) => i.path.join('.')) });
        return;
      }
      const { question, region, governed, sessionFormat } = p.data;
      const who = identity(req);
      const t0 = Date.now();

      // Long-term memory only if the session did not state a format (nearest valid source wins).
      let format: Format = sessionFormat ?? 'concise bullet points';
      let formatSource = sessionFormat ? 'this session' : 'default';
      if (!sessionFormat) {
        const { rows } = await db.query(
          `SELECT value FROM ${SCHEMA}.prefs WHERE user_id = $1 AND key = 'response_format'`,
          [who.email]
        );
        const stored = rows[0]?.value;
        if (typeof stored === 'string' && (FORMATS as readonly string[]).includes(stored)) {
          format = stored as Format;
          formatSource = 'saved preference';
        }
      }

      // Retrieval. The ungoverned pass is always run so the UI can show what governance removed.
      const raw = (await search.query('default', { queryText: question, numResults: UNGOVERNED_K })).results.map(
        toChunk
      );
      const removed = raw.map((c) => ({ c, reason: exclusionReason(c, region) })).filter((x) => x.reason !== null);

      let candidates: Chunk[];
      if (governed) {
        candidates = (
          await search.query('default', {
            queryText: question,
            numResults: GOVERNED_K,
            filters: governedFilters(region),
          })
        ).results.map(toChunk);
      } else {
        candidates = raw;
      }
      const { used, chars } = buildEvidence(candidates);
      const contaminated = used.filter((c) => exclusionReason(c, region) !== null);

      const evidence = used
        .map((c) => `[${c.chunk_id}] (${c.status}, ${c.region_code}, effective ${c.effective_date}) ${c.text}`)
        .join('\n\n');
      const answer = await chat([
        { role: 'system', content: systemPrompt(format) },
        {
          role: 'user',
          content: `Region: ${region}\nQuestion: ${question}\n\nEvidence:\n${evidence || '(none retrieved)'}`,
        },
      ]);
      const cited = citedIds(answer);
      const latencyMs = Date.now() - t0;

      const sources = used.map((c) => ({
        chunk_id: c.chunk_id,
        document_id: c.document_id,
        title: c.title,
        status: c.status,
        region_code: c.region_code,
        effective_date: c.effective_date,
        score: c.score,
        cited: cited.has(c.chunk_id),
        problem: exclusionReason(c, region),
      }));

      await db.query(
        `INSERT INTO ${SCHEMA}.turns (user_id, question, answer, region, governed, retrieved, removed_count, contaminated_count, context_chars, latency_ms, model)
       VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7,$8,$9,$10,$11)`,
        [
          who.email,
          question,
          answer,
          region,
          governed,
          JSON.stringify(sources.map((s) => s.chunk_id)),
          removed.length,
          contaminated.length,
          chars,
          latencyMs,
          MODEL,
        ]
      );

      res.json({
        answer,
        sources,
        latencyMs,
        model: MODEL,
        context: {
          governed,
          region,
          k: governed ? GOVERNED_K : UNGOVERNED_K,
          chars,
          format,
          formatSource,
          filters: governed ? governedFilters(region) : null,
          // What governance would have kept out, and (if ungoverned) what actually reached the model.
          removedByGovernance: removed.map((x) => ({ chunk_id: x.c.chunk_id, reason: x.reason })),
          contaminatedInContext: contaminated.map((c) => ({
            chunk_id: c.chunk_id,
            reason: exclusionReason(c, region),
          })),
        },
      });
    })
  );

  // ---- approval gate ------------------------------------------------------------------------
  app.get(
    '/api/requests',
    handler(async (_req, res) => {
      const { rows } = await db.query(`SELECT * FROM ${SCHEMA}.requests ORDER BY created_at DESC LIMIT 20`);
      res.json(rows);
    })
  );

  app.post(
    '/api/requests',
    handler(async (req, res) => {
      const p = requestBody.safeParse(req.body);
      if (!p.success) {
        res.status(400).json({ error: 'Invalid request' });
        return;
      }
      const ins = await db.query(
        `INSERT INTO ${SCHEMA}.requests (asset_id, summary, requested_by) VALUES ($1, $2, $3)
       ON CONFLICT (asset_id) WHERE status = 'pending' DO NOTHING RETURNING *`,
        [p.data.asset_id, p.data.summary, identity(req).email]
      );
      if (ins.rows[0]) {
        res.status(201).json({ created: true, request: ins.rows[0] });
        return;
      }
      const existing = await db.query(`SELECT * FROM ${SCHEMA}.requests WHERE asset_id = $1 AND status = 'pending'`, [
        p.data.asset_id,
      ]);
      res.status(200).json({ created: false, request: existing.rows[0] }); // idempotent: same asset, no duplicate
    })
  );

  app.post(
    '/api/requests/:id/decision',
    handler(async (req, res) => {
      const id = Number.parseInt(String(req.params.id), 10);
      const p = decisionBody.safeParse(req.body);
      if (Number.isNaN(id) || !p.success) {
        res.status(400).json({ error: 'Invalid request' });
        return;
      }
      const upd = await db.query(
        `UPDATE ${SCHEMA}.requests SET status = $1, decided_by = $2, decided_at = NOW()
       WHERE id = $3 AND status = 'pending' RETURNING *`,
        [p.data.approve ? 'approved' : 'rejected', identity(req).email, id]
      );
      if (!upd.rows[0]) {
        res.status(409).json({ error: 'Request is not pending (already decided or not found)' });
        return;
      }
      res.json(upd.rows[0]);
    })
  );
}
