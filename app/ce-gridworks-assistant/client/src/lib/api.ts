// Typed client for the assistant's server routes. Shapes mirror server/routes/assistant-routes.ts.
export const REGIONS = ['VIC', 'NSW', 'QLD', 'SA'] as const;
export type Region = (typeof REGIONS)[number];
export const FORMATS = ['concise bullet points', 'short paragraph', 'numbered steps'] as const;
export type Format = (typeof FORMATS)[number];

export interface Whoami {
  email: string;
  viaProxy: boolean;
  model: string;
  executesAs: string;
}

export interface Source {
  chunk_id: string;
  document_id: string;
  title: string;
  status: string;
  region_code: string;
  effective_date: string;
  score: number;
  cited: boolean;
  problem: string | null;
}

export interface ChatResult {
  answer: string;
  sources: Source[];
  latencyMs: number;
  model: string;
  context: {
    governed: boolean;
    region: Region;
    k: number;
    chars: number;
    format: Format;
    formatSource: string;
    filters: Record<string, unknown> | null;
    removedByGovernance: { chunk_id: string; reason: string | null }[];
    contaminatedInContext: { chunk_id: string; reason: string | null }[];
  };
}

export interface MaintenanceRequest {
  id: number;
  asset_id: string;
  summary: string;
  status: 'pending' | 'approved' | 'rejected';
  requested_by: string;
  decided_by: string | null;
  created_at: string;
  decided_at: string | null;
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { error?: string };
    throw new Error(body.error ?? `Request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export const api = {
  whoami: () => call<Whoami>('/api/whoami'),
  prefs: () => call<Record<string, string>>('/api/prefs'),
  setFormat: (value: Format) =>
    call<{ ok: true }>('/api/prefs', { method: 'PUT', body: JSON.stringify({ key: 'response_format', value }) }),
  chat: (b: { question: string; region: Region; governed: boolean; sessionFormat?: Format }) =>
    call<ChatResult>('/api/chat', { method: 'POST', body: JSON.stringify(b) }),
  requests: () => call<MaintenanceRequest[]>('/api/requests'),
  createRequest: (asset_id: string, summary: string) =>
    call<{ created: boolean; request: MaintenanceRequest }>('/api/requests', {
      method: 'POST',
      body: JSON.stringify({ asset_id, summary }),
    }),
  decide: (id: number, approve: boolean) =>
    call<MaintenanceRequest>(`/api/requests/${id}/decision`, { method: 'POST', body: JSON.stringify({ approve }) }),
};
