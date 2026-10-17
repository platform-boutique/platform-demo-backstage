# Operations

## Is it healthy?

```bash
kubectl -n backstage get pods                 # backstage-… and backstage-postgres-0 both Running and Ready
kubectl -n sso get pods                       # dex
kubectl -n backstage logs deploy/backstage    # JSON lines; errors name the plugin that failed
curl -sk https://backstage.platform-demo.test/.backstage/health/v1/readiness
```

| Symptom | Likely cause |
|---|---|
| Pod `Running` but never ready; log: `threw an error during startup` | A plugin's configuration is invalid. Backstage starts every plugin and refuses to serve until all are up; the message names the key |
| Sign-in page shows an error about the provider | Dex unreachable from the pod (CoreDNS rewrite missing, CA not mounted) or the client secret differs between Dex and Backstage |
| "Failed to sign-in, unable to resolve user identity" | The person is not in the catalog. Production: they are not a member of the GitHub organisation, or have not been imported yet |
| A tab is missing on an entity | The annotation that plugin reads is missing; see [Catalog](catalog.md#the-annotations-that-make-the-plugins-work) |
| Kubernetes tab empty | The label selector matches nothing, or the namespace annotation is wrong |
| Argo CD card: "Cannot get argo location(s)" | `ARGOCD_AUTH_TOKEN` missing or revoked: re-run `kind/sso-bootstrap.sh` |
| Docs tab says documentation is not found | The site was not published: `kind/techdocs-publish.sh` |
| Grafana embedded panel is blank | Grafana was not started with `allow_embedding`, or the browser blocks third-party cookies for the iframe |

## Rotating secrets

| What | How |
|---|---|
| Argo CD and Grafana tokens | `kind/sso-bootstrap.sh` creates new ones and restarts the portal |
| Dex client secrets, session secret, database password | Delete the Secret, run `kind/sso-secrets.sh`, restart Dex and the portal (the database password also needs the Postgres volume reset, or a `ALTER USER`) |
| The demo user's password | Delete `sso/dex-secrets` and `kind/certs/demo-password`, re-run `kind/sso-secrets.sh`, restart Dex |

## Not verified yet

Be honest about the edges of what was tested:

- The **real GitHub sign-in** (needs the OAuth App) and the **GitHub catalog provider** (needs a token or App): configured, documented, not exercised.
- The **release and promotion pipeline** of the portal image: written, never run.
- **Production TechDocs publishing** to object storage: only the local publisher was used.
- The **latest-tag** lookup of the Releases plugin (disabled in the local overlay so nothing leaves the machine).

## Resource use

Measured on the laptop cluster: the portal about 0.4-0.7 GiB and PostgreSQL about 0.1 GiB, Dex under 0.05 GiB. The whole platform
with the portal needs about 6 GiB of the VM; when memory is tight, stop the monitoring stack first (it is the heaviest part and the
portal works without it, apart from the Grafana plugin).
