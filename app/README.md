# GridWorks Operations Assistant (Lab 5 app)

AppKit (Node/React) app for the Context Engineering partner enablement. See `labs/05_app/05_lab.md` for the learner exercises.

| Layer | Choice | Why |
|---|---|---|
| Structured KPIs | `analytics` plugin, SQL in `config/queries/` (service principal) | Certified gold tables only |
| Retrieval | `aiSearch` plugin (beta) over the Lab 3 index; filters pushed into the index query | Authority and region enforced before the model sees anything |
| Memory + approvals + audit | `lakebase` plugin, schema `ce_app` | Durable, exact-key, auditable state |
| Model | AI Gateway `/ai-gateway/mlflow/v1/chat/completions`, model from `GATEWAY_MODEL` | Governed runtime; no keys in code |

## Build and deploy (this machine)
```bash
cd app/ce-gridworks-assistant
export NODE_EXTRA_CA_CERTS=/tmp/corp-ca.pem          # see docs: corporate CA from the keychain
npm install --registry=https://registry.npmmirror.com --cafile=/tmp/corp-ca.pem
npm run typegen && npm run build
databricks apps validate --profile <PROFILE>
databricks apps deploy -t default --profile <PROFILE>   # needs consent: creates a running app
```
Scaffold with `--package-manager npm` (pnpm is the default and is not installed).

## Known limits
- The AI Search plugin is **beta**. The index name is a bundle variable pointing at one facilitator's Lab 3 index.
- Model and retrieval calls run as the **service principal**, not the user.
- The same person can approve their own request (demo only).
- Delete the app and the `ce-enablement` Lakebase project when the cohort is finished: both bill while idle.
