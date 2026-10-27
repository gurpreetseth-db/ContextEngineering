// Lakebase schema for durable, auditable app state. Owned by the app's service principal.
// Lab 4 point: state that must survive restarts and be auditable lives here, not in the prompt.
export interface Db {
  query(sql: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[] }>;
}

// Configurable so local development can use its own schema: the deployed schema is OWNED by the app's
// service principal, and a developer's own role cannot use it. Validated because it is interpolated into SQL.
const requested = process.env.APP_SCHEMA ?? 'ce_app';
if (!/^[a-z_][a-z0-9_]{0,62}$/.test(requested)) throw new Error('APP_SCHEMA must be a lowercase identifier');
export const SCHEMA = requested;

export async function initSchema(db: Db): Promise<void> {
  await db.query(`CREATE SCHEMA IF NOT EXISTS ${SCHEMA}`);

  // Long-term memory: exact keys -> structured lookup, not semantic search.
  await db.query(`
    CREATE TABLE IF NOT EXISTS ${SCHEMA}.prefs (
      user_id TEXT NOT NULL,
      key TEXT NOT NULL,
      value TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (user_id, key)
    )`);

  // Approval gate: a side effect is only "approved" by an explicit, recorded human decision.
  await db.query(`
    CREATE TABLE IF NOT EXISTS ${SCHEMA}.requests (
      id SERIAL PRIMARY KEY,
      asset_id TEXT NOT NULL,
      summary TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
      requested_by TEXT NOT NULL,
      decided_by TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      decided_at TIMESTAMPTZ
    )`);
  // Idempotency: at most one pending request per asset, so a double click cannot duplicate the side effect.
  await db.query(
    `CREATE UNIQUE INDEX IF NOT EXISTS requests_one_pending_per_asset
       ON ${SCHEMA}.requests (asset_id) WHERE status = 'pending'`
  );

  // Audit/telemetry: what context each answer was built from (evaluation + incident review).
  await db.query(`
    CREATE TABLE IF NOT EXISTS ${SCHEMA}.turns (
      id SERIAL PRIMARY KEY,
      user_id TEXT NOT NULL,
      question TEXT NOT NULL,
      answer TEXT NOT NULL,
      region TEXT NOT NULL,
      governed BOOLEAN NOT NULL,
      retrieved JSONB NOT NULL,
      removed_count INT NOT NULL,
      contaminated_count INT NOT NULL,
      context_chars INT NOT NULL,
      latency_ms INT NOT NULL,
      model TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )`);
}
