import { analytics, createApp, lakebase, server } from '@databricks/appkit';
import { aiSearch } from '@databricks/appkit/beta';
import { initSchema } from './lib/db';
import { registerAssistantRoutes } from './routes/assistant-routes';

createApp({
  plugins: [
    server(),
    analytics(),
    lakebase(),
    // Returns only the columns the evidence panel needs (chosen with the facilitator): keeps context small.
    aiSearch({
      indexes: {
        default: {
          columns: ['chunk_id', 'document_id', 'title', 'text', 'region_code', 'status', 'effective_date'],
          queryType: 'hybrid',
          numResults: 6,
        },
      },
    }),
  ],
  async onPluginsReady(appkit) {
    // The service principal must create (and so own) the schema: deploy before relying on it locally.
    await initSchema(appkit.lakebase);
    appkit.server.extend((app) => {
      registerAssistantRoutes(app, appkit.lakebase, appkit.aiSearch);
    });
  },
}).catch(console.error);
