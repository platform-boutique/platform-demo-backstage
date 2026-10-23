# Architecture

## The pieces

```mermaid
flowchart LR
  user(["Person"]) -->|https| alb["AWS ALB<br/>TLS termination"]
  alb -->|http| gw["Cilium Gateway<br/>(host network, port 8080)"]
  gw --> bs["Backstage<br/>(backend + compiled frontend)"]
  gw --> dex["Dex"]
  gw --> argo["Argo CD"]
  gw --> graf["Grafana"]
  bs --> pg[("Amazon RDS<br/>PostgreSQL")]
  bs -->|"read-only ServiceAccount"| k8s["Kubernetes API"]
  bs -->|"the person's Dex token"| argo
  bs -->|"viewer token"| graf
  bs -->|"OIDC"| dex
  argo -->|"OIDC"| dex
  graf -->|"OIDC"| dex
  dex -->|"OAuth"| gh["GitHub"]
  bs -.->|"catalog-info.yaml"| src["GitHub<br/>(organisation)"]
```

Backstage is a single process: the **backend** (Node) serves the API and the compiled **frontend**, so the browser talks to one origin
and there is no CORS to configure. It keeps its state in PostgreSQL (Amazon RDS). Everything it shows about the cluster it reads with
**its own** credentials, never with a person's: people prove who they are to Backstage through Dex, and Backstage reads Kubernetes,
Argo CD and Grafana with read-only identities. The portal can therefore show a lot and change nothing.

## Read-only on purpose

| System | Identity the portal uses | What it can do |
|---|---|---|
| Kubernetes | ServiceAccount `backstage` + ClusterRole `backstage-read` (used by the Kubernetes, Releases and Policies plugins) | `get`, `list`, `watch` on workloads, Argo CD Applications, policy reports, Kyverno policies, Cilium and Gateway objects. No Secrets, no `exec`, no logs |
| Argo CD | the signed-in person's own Dex ID token (no shared token, no local account); Argo CD's RBAC decides | whatever that person may read |
| Grafana | service account `backstage`, role Viewer; its token is `GRAFANA_TOKEN` (needs Grafana to be deployed, which it is not at the moment) | list dashboards, read alerts |
| GitHub | token (`/platform-demo/github/token` in SSM) or GitHub App | read repositories and the organisation's members and teams |

The ClusterRole is in `platform-demo-helm/backstage/templates/rbac.yaml`. Tokens never live in Git: External Secrets Operator fills the
`backstage-secrets` Secret from AWS (see `docs/secrets.md` in `platform-demo-helm`).

## Configuration layers

The image contains three configuration files; which ones are loaded is decided by the chart (`config.files`).

| File | Purpose | Loaded |
|---|---|---|
| `app-config.yaml` | Everything that is the same everywhere: plugins, Kubernetes, Argo CD, Grafana, TechDocs, the catalog rules | always |
| `app-config.production.yaml` | PostgreSQL (RDS), Dex single sign-on, publish directory | EKS |
| `app-config.github.yaml` | Catalog discovery and users/teams from the GitHub organisation | EKS |

Every environment-specific value is an environment variable with a sensible default; the chart's ConfigMap and Secret provide them.

## What was deliberately left out

| Left out | Why |
|---|---|
| Software templates (scaffolder) | Nothing can be pushed yet, and creating repositories needs GitHub permissions that the free plan makes awkward. Adding it later is a backend module and one frontend package |
| Notifications and signals | Nobody sends any |
| Permissions framework policy | The portal is read-only and everyone who may sign in may see everything: `allow-all` |
| The Home page | The catalog is the landing page; a Home page of widgets would be decoration |
