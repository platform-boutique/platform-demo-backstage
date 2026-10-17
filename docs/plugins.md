# Plugins

What is installed, where its data comes from, and what each one needs from the entity.

| Plugin | Package | Shows | Data source | Needs on the entity |
|---|---|---|---|---|
| Software catalog | `@backstage/plugin-catalog` | Components, APIs, resources, owners, dependency graph | PostgreSQL, filled from `catalog-info.yaml` files | - |
| API docs | `@backstage/plugin-api-docs` | The gRPC definitions | `$text` includes in the API entities | `kind: API` |
| TechDocs | `@backstage/plugin-techdocs` + Mermaid addon | The docs of the repository | Sites published to `/data/docs` | `backstage.io/techdocs-ref` |
| Kubernetes | `@backstage/plugin-kubernetes` | Deployments, pods, services, events of the entity | Kubernetes API, read-only ServiceAccount | `backstage.io/kubernetes-label-selector` (or `-id`), `-namespace` |
| Argo CD | `@roadiehq/backstage-plugin-argo-cd` (+ backend) | Sync and health, revision history, link to the Application | Argo CD API with the read-only `backstage` account | `argocd/app-name` |
| Policies (own) | `@platform-boutique/backstage-plugin-policies` (+ backend) | Kyverno pass/fail/warn counts and the failing results for the entity's objects; the catalog of installed policies | `PolicyReport`s and Kyverno policy kinds, read with the read-only ServiceAccount | `backstage.io/kubernetes-label-selector`, `-namespace` |
| Grafana | `@backstage-community/plugin-grafana` | The service's dashboards, firing alerts, an embedded overview dashboard | Grafana API with a Viewer service account | `grafana/dashboard-selector`, `grafana/overview-dashboard` |
| Search | `@backstage/plugin-search` | One search box for entities and documentation | PostgreSQL full-text search | - |
| Org | `@backstage/plugin-org` | Groups, members, ownership | The catalog | - |

## Third-party plugin choices

| Need | Chosen | Alternatives considered |
|---|---|---|
| Argo CD | Roadie's plugin | Red Hat's `redhat-argocd` (richer deployment view, built for OpenShift GitOps) |
| Kyverno | **Own plugin** (tried TeraSky's first: its frontend sends an entity without `kind`, which the stock Kubernetes backend refuses with 403, so it never loaded) | Policy Reporter's plugin (beta); its UI is not needed because the reports show here |
| Grafana | The community plugin (the successor of `@k-phoen/backstage-plugin-grafana`, which is barely maintained) | Embedding by hand with an iframe component |

Grafana embedding works because both applications live under `platform-demo.test` (same site), so the browser sends Grafana's
session cookie inside the iframe, and Grafana is configured with `allow_embedding`.

## Custom plugins

Three views have no plugin to install, or none that works with this stack, so each is its own repository with its own pipeline files
(the Backstage documentation's recommendation for plugins that are not part of the app). They are consumed as tarballs from `vendor/`
until there is a package registry.

| Plugin | What it shows | Source of truth | Status |
|---|---|---|---|
| `platform-demo-backstage-plugin-hubble` | Network tab and page: flows, drops and why, mutual authentication | Hubble Relay's gRPC API (`GetFlows`) | Working, verified on the local cluster |
| `platform-demo-backstage-plugin-releases` | Releases tab and page: what Argo CD runs vs. what the Helm repository declares, latest tag | Argo CD Applications (Kubernetes API), the Helm values via the URL reader, GitHub tags | Working; the GitHub tag lookup is configured but disabled locally |
| `platform-demo-backstage-plugin-policies` | Policies tab and page: Kyverno findings per workload, the policy catalog | `PolicyReport`s and Kyverno policy kinds | Working, verified on the local cluster |

!!! warning "Argo CD tab"
    The third-party Argo CD plugin's *tab* crashes in this Backstage version (its table fails to mount inside the entity tab layout), so the
    tab is switched off in `app-config.yaml`. The Argo CD **cards** on the overview page (status, history) work and show the same data.
