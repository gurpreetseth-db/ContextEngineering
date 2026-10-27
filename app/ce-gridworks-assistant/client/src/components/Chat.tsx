import {
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Separator,
  Skeleton,
  Switch,
} from '@databricks/appkit-ui/react';
import { useState, type FormEvent } from 'react';
import { RichText } from '@/components/RichText';
import { api, FORMATS, REGIONS, type ChatResult, type Format, type Region, type Source } from '@/lib/api';

const SUGGESTIONS = [
  'What must happen when isolating a critical 33kV feeder?',
  'What is the minimum vegetation clearance for 33kV in bushfire-prone areas?',
  'What is the earth resistance limit?',
];

function statusVariant(s: Source): 'secondary' | 'destructive' | 'outline' {
  if (s.problem) return 'destructive';
  return s.cited ? 'secondary' : 'outline';
}

export function Chat() {
  const [question, setQuestion] = useState('');
  const [region, setRegion] = useState<Region>('VIC');
  const [governed, setGoverned] = useState(true);
  const [sessionFormat, setSessionFormat] = useState<Format | 'default'>('default');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ChatResult | null>(null);
  const [asked, setAsked] = useState<string | null>(null);

  async function ask(e?: FormEvent, q?: string) {
    e?.preventDefault();
    const text = (q ?? question).trim();
    if (text.length < 3 || loading) return;
    setLoading(true);
    setError(null);
    setAsked(text);
    try {
      setResult(
        await api.chat({
          question: text,
          region,
          governed,
          sessionFormat: sessionFormat === 'default' ? undefined : sessionFormat,
        })
      );
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-label="Assistant" className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Ask about procedures and standards</CardTitle>
          <CardDescription>Answers come only from retrieved documents and cite their source.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1">
              <Label htmlFor="region">Your region</Label>
              <Select value={region} onValueChange={(v) => setRegion(v as Region)}>
                <SelectTrigger id="region" className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {REGIONS.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="format">Format for this session</Label>
              <Select value={sessionFormat} onValueChange={(v) => setSessionFormat(v as Format | 'default')}>
                <SelectTrigger id="format" className="w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">Use my saved preference</SelectItem>
                  {FORMATS.map((f) => (
                    <SelectItem key={f} value={f}>
                      {f}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2 pb-1">
              <Switch id="governed" checked={governed} onCheckedChange={setGoverned} />
              <Label htmlFor="governed">Governed context</Label>
            </div>
          </div>

          {!governed && (
            <Alert variant="destructive">
              <AlertTitle>Governance is off</AlertTitle>
              <AlertDescription>
                Superseded, draft and other-region documents can reach the model. Use this to see what governance
                protects against.
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={(e) => void ask(e)} className="flex gap-2">
            <Input
              aria-label="Your question"
              placeholder="e.g. Who must witness a 33kV isolation?"
              value={question}
              maxLength={500}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <Button type="submit" disabled={loading || question.trim().length < 3}>
              {loading ? 'Thinking…' : 'Ask'}
            </Button>
          </form>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <Button
                key={s}
                size="sm"
                variant="ghost"
                className="h-auto whitespace-normal text-left text-xs"
                disabled={loading}
                onClick={() => {
                  setQuestion(s);
                  void ask(undefined, s);
                }}
              >
                {s}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {loading && (
        <Card>
          <CardContent className="space-y-2 pt-6" aria-busy="true">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </CardContent>
        </Card>
      )}

      {error && !loading && (
        <Alert variant="destructive">
          <AlertTitle>Could not get an answer</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!loading && !error && !result && (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No question yet</EmptyTitle>
            <EmptyDescription>
              Try a suggestion above, then turn governance off and ask it again to compare the sources.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}

      {result && !loading && (
        <Card>
          <CardHeader>
            <CardDescription>{asked}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-sm leading-relaxed" aria-live="polite">
              {result.answer ? <RichText text={result.answer} /> : 'No answer text was returned.'}
            </div>
            <p className="text-xs text-muted-foreground">
              AI-generated from the documents below. Verify against the cited source before acting.
            </p>
            <Separator />

            <div>
              <h3 className="mb-2 text-sm font-medium">Sources used ({result.sources.length})</h3>
              {result.sources.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No authorised source matched this question for {result.context.region}.
                </p>
              ) : (
                <ul className="space-y-2">
                  {result.sources.map((s) => (
                    <li key={s.chunk_id} className="flex flex-wrap items-center gap-2 text-sm">
                      <Badge variant={statusVariant(s)}>{s.status}</Badge>
                      <span className="font-mono text-xs">{s.chunk_id}</span>
                      <span>{s.title}</span>
                      <span className="text-xs text-muted-foreground">
                        {s.region_code} · effective {s.effective_date}
                        {s.cited ? ' · cited' : ''}
                      </span>
                      {s.problem && <Badge variant="destructive">{s.problem}</Badge>}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <details className="rounded-md border p-3 text-sm">
              <summary className="cursor-pointer font-medium">How this context was built</summary>
              <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-xs">
                <dt className="text-muted-foreground">Mode</dt>
                <dd>
                  {result.context.governed
                    ? 'Governed (authority + region filter in the index)'
                    : 'Ungoverned (no filter)'}
                </dd>
                <dt className="text-muted-foreground">Filter</dt>
                <dd className="font-mono">
                  {result.context.filters ? JSON.stringify(result.context.filters) : 'none'}
                </dd>
                <dt className="text-muted-foreground">Top-k / size</dt>
                <dd>
                  {result.context.k} chunks · {result.context.chars} characters
                </dd>
                <dt className="text-muted-foreground">Format</dt>
                <dd>
                  {result.context.format} (from {result.context.formatSource})
                </dd>
                <dt className="text-muted-foreground">Model / time</dt>
                <dd>
                  {result.model} · {result.latencyMs} ms
                </dd>
                <dt className="text-muted-foreground">Governance removed</dt>
                <dd>
                  {result.context.removedByGovernance.length === 0
                    ? 'nothing in the top results'
                    : result.context.removedByGovernance.map((r) => `${r.chunk_id} (${r.reason})`).join('; ')}
                </dd>
              </dl>
              {result.context.contaminatedInContext.length > 0 && (
                <p className="mt-3 text-xs text-destructive">
                  Reached the model:{' '}
                  {result.context.contaminatedInContext.map((r) => `${r.chunk_id} (${r.reason})`).join('; ')}
                </p>
              )}
            </details>
          </CardContent>
        </Card>
      )}
    </section>
  );
}
