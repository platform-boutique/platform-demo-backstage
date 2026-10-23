# platform-demo portal

<div class="pd-hero" markdown>
<span class="pd-kicker">developer portal · backstage</span>

One place to see the whole platform: what exists, who owns it, what runs where, whether it is healthy, what policy says
about it, and how to use it. Everyone signs in once, with their GitHub account, through Dex.
</div>

<div class="pd-facts" markdown>
<div><span>Framework</span><strong>Backstage 1.55</strong><small>new backend and frontend system</small></div>
<div><span>Sign-in</span><strong>Dex</strong><small>GitHub accounts, OIDC</small></div>
<div><span>Database</span><strong>PostgreSQL 17</strong><small>catalog, search, sessions</small></div>
<div><span>Cluster access</span><strong>Read-only</strong><small>a ClusterRole without Secrets</small></div>
</div>

## What you can do here

<div class="pd-cards" markdown>
<div><h4><a href="catalog/">Browse the catalog</a></h4><p>Every service, API, database and piece of infrastructure, with owners and dependencies.</p></div>
<div><h4><a href="techdocs/">Read the docs</a></h4><p>The documentation of every repository, rendered with one shared look.</p></div>
<div><h4><a href="plugins/">See live state</a></h4><p>Kubernetes workloads, Argo CD sync, Kyverno policy reports and Grafana dashboards on each entity.</p></div>
<div><h4><a href="sso/">Sign in everywhere once</a></h4><p>Backstage, Argo CD and Grafana trust the same provider.</p></div>
</div>

## Where the pieces live

| Piece | Repository | What it is |
|---|---|---|
| The portal | `platform-demo-backstage` (this one) | The Backstage app: configuration, backend modules, image, catalog of shared entities |
| Charts | `platform-demo-helm` → `backstage/`, `dex/` | Deployment of the portal and Dex (the database is Amazon RDS, built by infra-terraform) |
| Every other repository | `catalog-info.yaml`, `mkdocs.yml`, `docs/` | What makes it appear here |

!!! info "Status"
    The portal is deployed to EKS by Argo CD; nothing of it has run on EKS yet. Things that need the organisation's GitHub settings (the OAuth App for the real
    login, a GitHub token or App for catalog discovery) are configured and documented but were not exercised: see
    [Single sign-on](sso.md#going-live-with-github) and [Operations](operations.md#not-verified-yet).
