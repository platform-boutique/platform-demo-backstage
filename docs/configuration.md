# Configuration

Settings are layered (see [Architecture](architecture.md#configuration-layers)). Values that differ per environment are environment
variables; the Helm chart sets them.

## Environment variables

| Variable | Default | Used for |
|---|---|---|
| `APP_BASE_URL` | `http://localhost:3000` (`yarn start`) | Public URL of the portal (also the backend's); the chart sets `https://backstage.<domain>` |
| `DEX_ISSUER_URL` | `https://dex.platform-demo.click` | OIDC issuer |
| `BACKSTAGE_OIDC_CLIENT_SECRET` | - | The `backstage` client in Dex. **Secret** |
| `AUTH_SESSION_SECRET` | - | Signs the OAuth handshake session. **Secret** |
| `POSTGRES_HOST` / `PORT` / `USER` / `POSTGRES_PASSWORD` | - | Database. **Password is a secret** |
| `ARGOCD_URL` | `https://argocd.platform-demo.click` | Where "open in Argo CD" links go |
| `ARGOCD_API_URL` | `http://argocd-server.argocd.svc.cluster.local` | Where the backend calls the Argo CD API |
| `GRAFANA_URL` | `https://grafana.platform-demo.click` | Links, iframe origin |
| `GRAFANA_API_URL` | `http://grafana.monitoring.svc.cluster.local:3000` | Grafana API from the backend |
| `GRAFANA_TOKEN` | - | Viewer service-account token, optional (Grafana is not deployed at the moment). **Secret** |
| `CLUSTER_NAME` | `platform-demo` | Name under which the cluster appears |
| `GITHUB_TOKEN` | - | Catalog discovery. **Secret** |
| `TECHDOCS_CACHE` | `/data` | Volume with the published sites |
| `NODE_EXTRA_CA_CERTS` | the Amazon RDS CA bundle, set in the `Dockerfile` | Extra trusted CA (the RDS certificate) |
| `PGSSLMODE` | `require` (set by the chart) | Encrypts the connection to RDS |

Secrets are never in Git. External Secrets Operator fills the `backstage-secrets` Secret from AWS (SSM Parameter Store for the typed
secrets, Secrets Manager for the RDS-managed password); the list is in `docs/secrets.md` of `platform-demo-helm`.

## Where to change what

| I want to... | Change |
|---|---|
| Add a plugin | `yarn workspace app add` / `backend add`, register it in `packages/backend/src/index.ts`; frontend packages with a `/alpha` export are picked up automatically (`app.packages: all`) |
| Add a catalog source | `app-config.github.yaml` (a provider or a location) |
| Change who may sign in | The catalog: only people who exist as `User` entities can sign in, and those are the members of the GitHub organisation |
| Change what the portal may read in the cluster | `backstage/templates/rbac.yaml` in the Helm repository, nothing else |
| Change the look of the portal | `packages/app/src/modules/nav` (logo, sidebar); themes via the frontend theme API |
| Change the look of the docs | `tools/techdocs/extra.css`, then copy it into the repositories (`scaffold.py` does it) |
