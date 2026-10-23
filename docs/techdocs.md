# Documentation (TechDocs)

Every repository documents itself in its own `docs/` folder; the portal renders all of them in one place with one look.

## How a repository gets a site

```text
repository/
  catalog-info.yaml      annotation  backstage.io/techdocs-ref: dir:.
  mkdocs.yml             navigation and theme features
  docs/
    index.md ...         the pages
```

The look is **one stylesheet owned by the portal** (`tools/techdocs/extra.css`, compiled into `packages/app/src/modules/techdocs-style`
by `tools/techdocs/sync-style.sh`). TechDocs deletes every `<link>` and `<style>` from the documentation it shows, so a repository
cannot bring its own CSS; the portal injects the stylesheet into every docs page with a TechDocs addon instead. It uses only the
theme's CSS variables, so it follows the light and dark mode, and no external fonts, images or scripts.

!!! note "Previewing"
    A plain `mkdocs serve` shows the pages without that stylesheet (the hero and tiles are unstyled). Only the portal renders the real
    look, with the published site.

## Building and publishing

The portal does **not** run MkDocs. Sites are rendered outside and published to the storage the portal reads from
(`techdocs.builder: external`). That keeps the image small, means the portal needs no access to source repositories to show
docs, and is the approach the Backstage project recommends for production.

| Step | How |
|---|---|
| Render | `tools/techdocs/build-docs.sh <workspace-root> <out-dir>` (MkDocs + `@techdocs/cli generate`) renders every repository that has a `backstage.io/techdocs-ref` annotation and an `mkdocs.yml`. In CI the same two commands run in the repository's pipeline |
| Publish | `techdocs-cli publish --publisher-type awsS3` (or GCS/Azure), with `techdocs.publisher` switched to that store |
| When | On every merge to `main` |

!!! note "Not wired yet"
    Nothing publishes TechDocs on EKS. The publish step is a few lines in a CI workflow and needs an S3 bucket plus a role for the
    pipeline; neither exists yet. Until then the portal's Docs tab has nothing to show: the portal reads sites from the volume at `/data`
    (the `local` publisher) and that volume is empty.

## Writing good pages

- One idea per page; the navigation in `mkdocs.yml` is the table of contents.
- Use the building blocks from the stylesheet: `pd-hero` (the lead), `pd-facts` (key numbers), `pd-cards` (links), tables for
  anything with more than two columns of facts, admonitions (`!!! tip`, `!!! warning`) for the things people skip.
- Diagrams are fenced ```` ```mermaid ```` blocks; the portal renders them (the Mermaid addon is installed). They do not render in a plain `mkdocs serve`.
- Do not copy README text. The README stays the short reference in the repository; the site is the explanation.

## The service sites

The eleven `app-*` repositories were generated from their READMEs by `tools/techdocs/scaffold.py` (overview with a dependency
diagram, API, configuration, container image, Kubernetes, observability, develop and test, known limitations). After the first
run the generated files are ordinary hand-edited files; do not run the scaffold again over them without reviewing the diff.
