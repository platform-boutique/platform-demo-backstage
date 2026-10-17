# Configuration

Settings are layered (see [Architecture](architecture.md#configuration-layers)). Values that differ per environment are environment
variables; the Helm chart sets them.

## Environment variables

| Variable | Default | Used for |
|---|---|---|
| `APP_BASE_URL` | `http://localhost:3000` | Public URL of the portal (also the backend's) |
| `DEX_ISSUER_URL` | `https://dex.platform-demo.test` | OIDC issuer |
| `BACKSTAGE_OIDC_CLIENT_SECRET` | - | The `backstage` client in Dex. **Secret** |
| `AUTH_SESSION_SECRET` | - | Signs the OAuth handshake session. **Secret** |
| `POSTGRES_HOST` / `PORT` / `USER` / `POSTGRES_PASSWORD` | - | Database. **Password is a secret** |
| `ARGOCD_URL` | `https://argocd.platform-demo.test` | Where "open in Argo CD" links go |
| `ARGOCD_API_URL` | `http://argocd-server.argocd.svc.cluster.local` | Where the backend calls the Argo CD API |
| `ARGOCD_AUTH_TOKEN` | - | Token of the read-only account. **Secret** |
| `GRAFANA_URL` | `https://grafana.platform-demo.test` | Links, iframe origin |
| `GRAFANA_API_URL` | `http://grafana.monitoring.svc.cluster.local:3000` | Grafana API from the backend |
| `GRAFANA_TOKEN` | - | Viewer service-account token. **Secret** |
| `CLUSTER_NAME` | `platform-local` | Name under which the cluster appears |
| `GITHUB_TOKEN` | - | Catalog discovery (production only). **Secret** |
| `TECHDOCS_CACHE` | `/data` | Volume with the published sites |
| `NODE_EXTRA_CA_CERTS` | - | A private CA that signed Dex's certificate (local cluster) |
| `LOCAL_SOURCE_HOST` | `172.18.0.1:8099` | The local source server (local cluster only) |

Secrets are never in Git. `kind/sso-secrets.sh` and `kind/sso-bootstrap.sh` create them locally; in the cloud External Secrets
fills the same Secret.

## Where to change what

| I want to... | Change |
|---|---|
| Add a plugin | `yarn workspace app add` / `backend add`, register it in `packages/backend/src/index.ts`; frontend packages with a `/alpha` export are picked up automatically (`app.packages: all`) |
| Add a catalog source | `app-config.github.yaml` (provider) or the kind overlay (a location) |
| Change who may sign in | The catalog: only people who exist as `User` entities can sign in. Production: membership of the GitHub organisation |
| Change what the portal may read in the cluster | `backstage/templates/rbac.yaml` in the Helm repository, nothing else |
| Change the look of the portal | `packages/app/src/modules/nav` (logo, sidebar); themes via the frontend theme API |
| Change the look of the docs | `tools/techdocs/extra.css`, then copy it into the repositories (`scaffold.py` does it) |
