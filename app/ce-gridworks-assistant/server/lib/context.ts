// Context construction: the part of the app that decides what the model is allowed to see.
export const REGIONS = ['VIC', 'NSW', 'QLD', 'SA'] as const;
export type Region = (typeof REGIONS)[number];

export const FORMATS = ['concise bullet points', 'short paragraph', 'numbered steps'] as const;
export type Format = (typeof FORMATS)[number];

export interface Chunk {
  chunk_id: string;
  document_id: string;
  title: string;
  text: string;
  region_code: string;
  status: string;
  effective_date: string;
  score: number;
}

export type Filters = Record<string, string | number | boolean | (string | number)[]>;

/** Authority + permission filter, pushed down into the index (not applied after the fact). */
export function governedFilters(region: Region): Filters {
  return { status: 'current', region_code: [region, 'ALL'] };
}

/** Why a chunk would NOT have been allowed into a governed context (null = allowed). */
export function exclusionReason(c: Chunk, region: Region): string | null {
  if (c.status === 'superseded') return 'superseded version';
  if (c.status !== 'current') return `not approved (${c.status})`;
  if (c.region_code !== region && c.region_code !== 'ALL') return `wrong region (${c.region_code})`;
  return null;
}

/** Inject only the strongest evidence within a character budget, each item carrying provenance. */
export function buildEvidence(chunks: Chunk[], maxChars = 3000): { used: Chunk[]; chars: number } {
  const used: Chunk[] = [];
  let chars = 0;
  for (const c of chunks) {
    if (chars + c.text.length > maxChars) break;
    used.push(c);
    chars += c.text.length;
  }
  return { used, chars };
}

export function systemPrompt(format: Format): string {
  return [
    'You are the GridWorks operations assistant for an electricity network operator.',
    'Answer ONLY from the evidence provided. Cite the chunk id in square brackets after each claim, e.g. [PRC-LOTO-001#00].',
    'If the evidence is a draft, superseded, or for a different region, say so plainly rather than treating it as authoritative.',
    'If the evidence does not answer the question, say that it does not, and do not guess.',
    `Preferred response format: ${format}.`,
  ].join(' ');
}

export function citedIds(answer: string): Set<string> {
  return new Set([...answer.matchAll(/\[([A-Za-z0-9-]+#\d+)\]/g)].map((m) => m[1]));
}
