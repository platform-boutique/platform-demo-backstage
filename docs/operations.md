# Operations

## Is it healthy?

```bash
kubectl -n backstage get pods                 # backstage-… Running and Ready (the database is Amazon RDS, outside the cluster)
kubectl -n sso get pods                       # dex
kubectl -n backstage logs deploy/backstage    # JSON lines; errors name the plugin that failed
curl -sk https://backstage.platform-demo.click/.backstage/health/v1/readiness
```

| Symptom | Likely cause |
|---|---|
| Pod `Running` but never ready; log: `threw an error during startup` | A plugin's configuration is invalid. Backstage starts every plugin and refuses to serve until all are up; the message names the key |
| Sign-in page shows an error about the provider | Dex unreachable from the pod (the ALB does not admit the NAT gateways' addresses, or `https://dex.platform-demo.click` does not resolve) or the client secret differs between Dex and Backstage |
| Pod stays in `CreateContainerConfigError` | `backstage-secrets` does not exist yet: a parameter is missing in SSM (`kubectl get externalsecret -A`) |
| Database errors about TLS or the certificate | `PGSSLMODE` / the RDS CA bundle (`NODE_EXTRA_CA_CERTS`) in the image; see `docs/secrets.md` of `platform-demo-helm` |
| "Failed to sign-in, unable to resolve user identity" | The person is not in the catalog. Production: they are not a member of the GitHub organisation, or have not been imported yet |
| A tab is missing on an entity | The annotation that plugin reads is missing; see [Catalog](catalog.md#the-annotations-that-make-the-plugins-work) |
| Kubernetes tab empty | The label selector matches nothing, or the namespace annotation is wrong |
| Deployments tab: Argo CD refuses the request | The Argo CD API is called with the signed-in person's Dex token: the person's group has no role in Argo CD, or `deployments.argocdUrl` is wrong |
| Docs tab says documentation is not found | The site was not published. TechDocs are not published on EKS yet (see [Documentation](techdocs.md#building-and-publishing)) |
| Grafana tab or panel is empty | Grafana is not deployed on the cluster at the moment. When it is: it must run with `allow_embedding`, and the browser must not block third-party cookies for the iframe |

## Rotating secrets

| What | How |
|---|---|
| Dex client secrets, session secret, GitHub token | Change the SSM parameter (`docs/secrets.md` in `platform-demo-helm` lists them); External Secrets re-reads within an hour and Reloader restarts Dex and the portal |
| Database password | Nothing to do: RDS rotates it every seven days in Secrets Manager and Reloader restarts the portal |
| Grafana token (only when Grafana is deployed) | New service-account token into SSM `/platform-demo/grafana/backstage-token` |

## Not verified yet

Be honest about the edges of what was tested:

- **Everything on EKS**: the platform is merged but nothing has been deployed there yet, so the portal, Dex, the load balancer and the
  RDS connection are all unverified.
- The **real GitHub sign-in** (needs the OAuth App) and the **GitHub catalog provider** (needs a token or App): configured, documented, not exercised.
- **TechDocs publishing**: not wired. The portal reads sites from a volume at `/data`, but nothing builds and publishes them in CI yet.
- The **Grafana** plugin: there is no monitoring stack on the cluster at the moment.

## Resource use

The chart requests 100m CPU and 384 MiB for the portal (limit 1 GiB); real consumption on EKS has not been measured.
