import { ServiceContext } from '@databricks/appkit';

// Model services are called through Unity AI Gateway. The model name is configuration, never hard-coded.
export const MODEL = process.env.GATEWAY_MODEL ?? 'system.ai.claude-haiku-5-5';

interface ChatMessage {
  role: 'system' | 'user';
  content: string;
}

interface ChatResponse {
  choices?: { message?: { content?: unknown } }[];
}

/** Some model services return a list of content blocks (a `reasoning` block, then `text`).
 *  Keep only the text: reasoning is never stored, scored or shown. */
export function answerText(content: unknown): string {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .filter(
        (b): b is { type: string; text: string } =>
          typeof b === 'object' && b !== null && (b as { type?: unknown }).type === 'text'
      )
      .map((b) => b.text)
      .join('');
  }
  return '';
}

export async function chat(messages: ChatMessage[]): Promise<string> {
  const client = ServiceContext.get().client; // authenticated as the app's service principal
  // NB: some model services reject `temperature`, so it is deliberately not set.
  const resp = (await client.apiClient.request({
    path: '/ai-gateway/mlflow/v1/chat/completions',
    method: 'POST',
    headers: new Headers({ 'Content-Type': 'application/json', Accept: 'application/json' }),
    payload: { model: MODEL, messages, max_tokens: 800 },
    raw: false,
  })) as ChatResponse;
  return answerText(resp.choices?.[0]?.message?.content);
}
