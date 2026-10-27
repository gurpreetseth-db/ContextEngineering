import {
  BarChart,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  useAnalyticsQuery,
} from '@databricks/appkit-ui/react';
import { useState } from 'react';
import { api } from '@/lib/api';

// Every KPI states what it counts, where it comes from, and how fresh it is.
const SOURCE = 'Certified gold tables, ce_shared';

function Stat({
  label,
  value,
  note,
  loading,
}: {
  label: string;
  value: number | null;
  note: string;
  loading: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        {loading ? (
          <Skeleton className="h-8 w-16" />
        ) : (
          <CardTitle className="text-3xl tabular-nums">{value ?? 0}</CardTitle>
        )}
      </CardHeader>
      <CardContent className="text-xs text-muted-foreground">{note}</CardContent>
    </Card>
  );
}

export function Kpis({ onRequested }: { onRequested: () => void }) {
  const wo = useAnalyticsQuery('open_work_orders_by_priority', {});
  const feeders = useAnalyticsQuery('poor_critical_feeders', {});
  const outages = useAnalyticsQuery('unplanned_outages_by_region', {});
  const fresh = useAnalyticsQuery('data_freshness', {});
  const [note, setNote] = useState<string | null>(null);

  const open = (p: string) => Number(wo.data?.find((r) => r.priority_code === p)?.open_count ?? 0);
  const through = fresh.data?.[0]?.data_through?.slice(0, 10);

  async function requestReinspection(assetId: string, score: number) {
    try {
      const r = await api.createRequest(
        assetId,
        `Reinspect critical feeder ${assetId} (health score ${score}, poor band)`
      );
      setNote(r.created ? `Request for ${assetId} sent for approval.` : `A request for ${assetId} is already pending.`);
      onRequested();
    } catch (e) {
      setNote(e instanceof Error ? e.message : 'Could not create the request.');
    }
  }

  return (
    <section aria-label="Operational KPIs" className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <Stat
          label="Open P1 work orders"
          value={open('P1')}
          loading={wo.loading}
          note="Open + in progress · certified definition"
        />
        <Stat
          label="Open P2 work orders"
          value={open('P2')}
          loading={wo.loading}
          note="Open + in progress · certified definition"
        />
        <Stat
          label="Critical feeders, poor health"
          value={feeders.data?.length ?? null}
          loading={feeders.loading}
          note="Health score below 50"
        />
      </div>

      <Card>
        <CardContent className="pt-6">
          {outages.error ? (
            <p className="text-sm text-destructive">Could not load outages: {outages.error}</p>
          ) : (
            <BarChart
              queryKey="unplanned_outages_by_region"
              parameters={{}}
              title="Most unplanned outages: NSW and VIC"
              xKey="region_code"
              yKey="outages"
              height={220}
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Critical feeders needing reinspection</CardTitle>
          <CardDescription>
            Requesting reinspection creates a pending request. Nothing is actioned until a person approves it.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {feeders.loading ? (
            <Skeleton className="h-24 w-full" />
          ) : feeders.error ? (
            <p className="text-sm text-destructive">{feeders.error}</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Asset</TableHead>
                  <TableHead>Region</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                  <TableHead>Last inspected</TableHead>
                  <TableHead>
                    <span className="sr-only">Action</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(feeders.data ?? []).map((f) => (
                  <TableRow key={f.asset_id}>
                    <TableCell className="font-medium">{f.asset_id}</TableCell>
                    <TableCell>{f.region_code}</TableCell>
                    <TableCell className="text-right tabular-nums">{Number(f.health_score)}</TableCell>
                    <TableCell>{f.last_inspection_date}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        aria-label={`Request reinspection for ${f.asset_id}`}
                        onClick={() => void requestReinspection(f.asset_id, Number(f.health_score))}
                      >
                        Request
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {note && (
            <p className="mt-3 text-sm text-muted-foreground" role="status">
              {note}
            </p>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        Source: {SOURCE}.{' '}
        {fresh.loading ? 'Checking freshness…' : through ? `Data through ${through}.` : 'Freshness unavailable.'}
      </p>
    </section>
  );
}
