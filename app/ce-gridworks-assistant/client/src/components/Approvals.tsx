import {
  Alert,
  AlertDescription,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
} from '@databricks/appkit-ui/react';
import { useCallback, useEffect, useState } from 'react';
import { api, FORMATS, type Format, type MaintenanceRequest } from '@/lib/api';

export function Approvals({ refreshKey }: { refreshKey: number }) {
  const [items, setItems] = useState<MaintenanceRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      setItems(await api.requests());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load requests.');
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  async function decide(id: number, approve: boolean) {
    setBusy(id);
    try {
      await api.decide(id, approve);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Decision failed.');
      await load();
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Approval queue</CardTitle>
        <CardDescription>Side effects wait here for a recorded human decision.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {items === null && !error && <Skeleton className="h-16 w-full" />}
        {items?.length === 0 && (
          <p className="text-sm text-muted-foreground">No requests yet. Use “Request reinspection” on a feeder.</p>
        )}
        <ul className="space-y-3">
          {items?.map((r) => (
            <li key={r.id} className="rounded-md border p-3 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium">{r.asset_id}</span>
                <Badge
                  variant={r.status === 'pending' ? 'outline' : r.status === 'approved' ? 'secondary' : 'destructive'}
                >
                  {r.status}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{r.summary}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Requested by {r.requested_by}
                {r.decided_by ? ` · decided by ${r.decided_by}` : ''}
              </p>
              {r.status === 'pending' && (
                <div className="mt-2 flex gap-2">
                  <Button size="sm" disabled={busy === r.id} onClick={() => void decide(r.id, true)}>
                    Approve
                  </Button>
                  <Button size="sm" variant="outline" disabled={busy === r.id} onClick={() => void decide(r.id, false)}>
                    Reject
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground">
          Demo note: the same person may approve their own request. A production design would enforce separation of
          duties.
        </p>
      </CardContent>
    </Card>
  );
}

export function Preferences() {
  const [value, setValue] = useState<Format | ''>('');
  const [status, setStatus] = useState<string | null>(null);
  useEffect(() => {
    api
      .prefs()
      .then((p) => {
        if ((FORMATS as readonly string[]).includes(p.response_format)) setValue(p.response_format as Format);
      })
      .catch(() => setStatus('Could not load your saved preference.'));
  }, []);

  async function save(v: Format) {
    setValue(v);
    try {
      await api.setFormat(v);
      setStatus('Saved. It will apply to future sessions.');
    } catch {
      setStatus('Could not save your preference.');
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Your memory</CardTitle>
        <CardDescription>Stored in Lakebase and remembered across sessions.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <Label htmlFor="pref">Preferred answer format</Label>
        <Select value={value} onValueChange={(v) => void save(v as Format)}>
          <SelectTrigger id="pref">
            <SelectValue placeholder="Not set" />
          </SelectTrigger>
          <SelectContent>
            {FORMATS.map((f) => (
              <SelectItem key={f} value={f}>
                {f}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {status && (
          <p className="text-xs text-muted-foreground" role="status">
            {status}
          </p>
        )}
        <p className="text-xs text-muted-foreground">A format chosen for the current session overrides this.</p>
      </CardContent>
    </Card>
  );
}
