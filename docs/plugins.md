# Plugins

What is installed, where its data comes from, and what each one needs from the entity.

| Plugin | Package | Shows | Data source | Needs on the entity |
|---|---|---|---|---|
| Software catalog | `@backstage/plugin-catalog` | Components, APIs, resources, owners, dependency graph | PostgreSQL (RDS), filled from `catalog-info.yaml` files | - |
| API docs | `@backstage/plugin-api-docs` | The gRPC definitions | `$text` includes in the API entities | `kind: API` |
| TechDocs | `@backstage/plugin-techdocs` + Mermaid addon | The docs of the repository | Sites published to `/data/docs` (nothing publishes them on EKS yet) | `backstage.io/techdocs-ref` |
| Kubernetes | `@backstage/plugin-kubernetes` | Deployments, pods, services, events of the entity | Kubernetes API, read-only ServiceAccount | `backstage.io/kubernetes-label-selector` (or `-id`), `-namespace` |
| Deployments (own) | `@platform-boutique/backstage-plugin-deployments` (+ backend) | Argo CD sync and health, live revision, history with commit links, owned resources, link to the Application; read-only | Argo CD API **as the signed-in person** (their Dex ID token; Argo CD's RBAC decides) | `argocd/app-name` |
| Policies (own) | `@platform-boutique/backstage-plugin-policies` (+ backend) | Kyverno pass/fail/warn counts and the failing results for the entity's objects; the catalog of installed policies | `PolicyReport`s and Kyverno policy kinds, read with the read-only ServiceAccount | `backstage.io/kubernetes-label-selector`, `-namespace` |
| Grafana | `@backstage-community/plugin-grafana` | The service's dashboards, firing alerts, an embedded overview dashboard | Grafana API with a Viewer service account (Grafana is not deployed on the cluster at the moment) | `grafana/dashboard-selector`, `grafana/overview-dashboard` |
| Search | `@backstage/plugin-search` | One search box for entities and documentation | PostgreSQL full-text search | - |
| Org | `@backstage/plugin-org` | Groups, members, ownership | The catalog | - |

## Third-party plugin choices

| Need | Chosen | Alternatives considered |
|---|---|---|
| Argo CD | **Own plugin** (Roadie's needed a shared Argo CD token, which needs a local Argo CD account; its history card also hid the oldest entry) | Roadie's plugin, Red Hat's `redhat-argocd` |
| Kyverno | **Own plugin** (tried TeraSky's first: its frontend sends an entity without `kind`, which the stock Kubernetes backend refuses with 403, so it never loaded) | Policy Reporter's plugin (beta); its UI is not needed because the reports show here |
| Grafana | The community plugin (the successor of `@k-phoen/backstage-plugin-grafana`, which is barely maintained) | Embedding by hand with an iframe component |

Grafana embedding works because both applications live under `platform-demo.click` (same site), so the browser sends Grafana's
session cookie inside the iframe, and Grafana is configured with `allow_embedding`.

## Custom plugins

Four views have no plugin to install, or none that works with this stack, so each is its own repository with its own pipeline files
(the Backstage documentation's recommendation for plugins that are not part of the app). They are consumed as tarballs from `vendor/`
until there is a package registry.

| Plugin | What it shows | Source of truth | Status |
|---|---|---|---|
| `platform-demo-backstage-plugin-hubble` | Network tab and page: flows, drops and why, mutual authentication | Hubble Relay's gRPC API (`GetFlows`) | Not verified on EKS yet |
| `platform-demo-backstage-plugin-releases` | Releases tab and page: what Argo CD runs vs. what the Helm repository declares, latest tag | Argo CD Applications (Kubernetes API), the Helm values via the URL reader, GitHub tags | Not verified on EKS yet |
| `platform-demo-backstage-plugin-policies` | Policies tab and page: Kyverno findings per workload, the policy catalog | `PolicyReport`s and Kyverno policy kinds | Not verified on EKS yet |
| `platform-demo-backstage-plugin-argocd` | Deployments tab: Argo CD sync and health, history, resources (packages `deployments` and `deployments-backend`) | Argo CD API with the signed-in person's Dex token | Not verified on EKS yet |
