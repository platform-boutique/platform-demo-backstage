# Plugins

What is installed, where its data comes from, and what each one needs from the entity.

| Plugin | Package | Shows | Data source | Needs on the entity |
|---|---|---|---|---|
| Software catalog | `@backstage/plugin-catalog` | Components, APIs, resources, owners, dependency graph | PostgreSQL, filled from `catalog-info.yaml` files | - |
| API docs | `@backstage/plugin-api-docs` | The gRPC definitions | `$text` includes in the API entities | `kind: API` |
| TechDocs | `@backstage/plugin-techdocs` + Mermaid addon | The docs of the repository | Sites published to `/data/docs` | `backstage.io/techdocs-ref` |
| Kubernetes | `@backstage/plugin-kubernetes` | Deployments, pods, services, events of the entity | Kubernetes API, read-only ServiceAccount | `backstage.io/kubernetes-label-selector` (or `-id`), `-namespace` |
| Argo CD | `@roadiehq/backstage-plugin-argo-cd` (+ backend) | Sync and health, revision history, link to the Application | Argo CD API with the read-only `backstage` account | `argocd/app-name` |
| Kyverno policy reports | `@terasky/backstage-plugin-kyverno-policy-reports` (+ backend) | Pass/fail/warn counts per policy for the entity's objects, the policy YAML | `PolicyReport`s through the Kubernetes plugin's proxy | Kubernetes annotations |
| Grafana | `@backstage-community/plugin-grafana` | The service's dashboards, firing alerts, an embedded overview dashboard | Grafana API with a Viewer service account | `grafana/dashboard-selector`, `grafana/overview-dashboard` |
| Search | `@backstage/plugin-search` | One search box for entities and documentation | PostgreSQL full-text search | - |
| Org | `@backstage/plugin-org` | Groups, members, ownership | The catalog | - |

## Third-party plugin choices

| Need | Chosen | Alternatives considered |
|---|---|---|
| Argo CD | Roadie's plugin | Red Hat's `redhat-argocd` (richer deployment view, built for OpenShift GitOps) |
| Kyverno | TeraSky's plugin | Policy Reporter's plugin (beta) - and its UI is not needed because the reports show here |
| Grafana | The community plugin (the successor of `@k-phoen/backstage-plugin-grafana`, which is barely maintained) | Embedding by hand with an iframe component |

Grafana embedding works because both applications live under `platform-demo.test` (same site), so the browser sends Grafana's
session cookie inside the iframe, and Grafana is configured with `allow_embedding`.

## Custom plugins (not written yet)

Two views have no plugin to install and are the reason to build our own. Each is its own repository with its own pipeline, as the
Backstage documentation recommends for plugins that are not part of the app.

| Plugin | What it will show | Source of truth |
|---|---|---|
| Hubble / Cilium | Flows, drops and why, which connections were authenticated, per service | Hubble Relay's gRPC API (`GetFlows`) |
| Releases | Tag → promotion pull request → image digest → Argo CD state, per service | GitHub tags, the Helm repository's `envs/<env>/values`, Argo CD |

See [Operations](operations.md) for the status.
