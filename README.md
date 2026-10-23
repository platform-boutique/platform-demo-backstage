# platform-demo-backstage

The developer portal of the [platform-boutique](https://github.com/platform-boutique) project: one place for the software catalog,
every repository's documentation, and the live state of what runs (Kubernetes, Argo CD, Kyverno policy reports, Grafana, network
flows, releases). Everyone signs in once, with GitHub, through [Dex](https://dexidp.io).

Built with [Backstage](https://backstage.io) 1.55 on the new backend and frontend systems. **The full documentation is in `docs/`** and is
rendered in the portal itself (Docs tab of this component):

| Page | Read it for |
|---|---|
| [Overview](docs/index.md) | What this is and where the pieces live |
| [Architecture](docs/architecture.md) | Components, read-only access, configuration layers, what was left out |
| [Single sign-on](docs/sso.md) | Dex, who gets what, going live with GitHub |
| [Catalog](docs/catalog.md) | The entity model, the annotations, adding a repository |
| [Documentation (TechDocs)](docs/techdocs.md) | How sites are built and published |
| [Plugins](docs/plugins.md) | What is installed and what it needs |
| [Configuration](docs/configuration.md) | Environment variables and where to change what |
| [Build, release, deploy](docs/release.md) | Image, pipeline, first release, upgrading |
| [Operations](docs/operations.md) | Troubleshooting, rotating secrets, what is not verified |

## Layout

```
app-config.yaml                 shared configuration (always loaded)
app-config.production.yaml      PostgreSQL + Dex sign-in (in the image)
app-config.github.yaml          production catalog from the GitHub organisation
catalog/                        shared entities (domain, systems, resources)
packages/app                    the frontend (sign-in page, sidebar)
packages/backend                the backend (modules, the Dex sign-in resolver)
vendor/                         our own plugins as tarballs (until there is a package registry)
tools/techdocs/                 scaffold for the service sites, shared stylesheet, build script for the documentation sites
Dockerfile                      the multi-stage image build
```

Deployment lives in `platform-demo-helm` (charts `backstage/` and `dex/`; Argo CD deploys them to EKS). Three plugins are written for this
portal and live in their own repositories: `platform-demo-backstage-plugin-hubble`, `-releases` and `-policies`.

## Quick start

```bash
docker build -t platform-demo-backstage:dev .          # the image
```

The portal is deployed to EKS by Argo CD at <https://backstage.platform-demo.click> (single sign-on through Dex with GitHub); its
database is Amazon RDS. The EKS platform is merged but has not been deployed or verified yet. There is no local cluster any more.
