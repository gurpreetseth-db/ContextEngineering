import { Badge } from '@databricks/appkit-ui/react';
import { useEffect, useState } from 'react';
import { Approvals, Preferences } from '@/components/Approvals';
import { Chat } from '@/components/Chat';
import { Kpis } from '@/components/Kpis';
import { api, type Whoami } from '@/lib/api';

export default function App() {
  const [who, setWho] = useState<Whoami | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  useEffect(() => {
    api
      .whoami()
      .then(setWho)
      .catch(() => setWho(null));
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <header className="flex flex-wrap items-center gap-3 border-b px-6 py-3">
        <h1 className="text-lg font-semibold">GridWorks Operations Assistant</h1>
        <span className="text-sm text-muted-foreground">Context Engineering · Lab 5</span>
        <div className="ml-auto flex flex-wrap items-center gap-2 text-xs">
          {who ? (
            <>
              <Badge variant="secondary">Signed in as {who.email}</Badge>
              <Badge variant="outline">Runs as: app service principal</Badge>
              <Badge variant="outline">{who.model}</Badge>
            </>
          ) : (
            <Badge variant="outline">Identity unavailable</Badge>
          )}
        </div>
      </header>
      <main className="mx-auto grid max-w-[1400px] gap-6 p-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)_minmax(0,0.8fr)]">
        <Kpis onRequested={() => setRefreshKey((k) => k + 1)} />
        <Chat />
        <div className="space-y-4">
          <Approvals refreshKey={refreshKey} />
          <Preferences />
        </div>
      </main>
    </div>
  );
}
