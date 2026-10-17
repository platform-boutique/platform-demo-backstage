# Documentation (TechDocs)

Every repository documents itself in its own `docs/` folder; the portal renders all of them in one place with one look.

## How a repository gets a site

```text
repository/
  catalog-info.yaml      annotation  backstage.io/techdocs-ref: dir:.
  mkdocs.yml             navigation, theme features, extra_css
  docs/
    index.md ...         the pages
    stylesheets/extra.css  the shared look
```

The look is one stylesheet (`tools/techdocs/extra.css` in this repository) copied into every repository. It uses only the
theme's CSS variables, so it follows the portal's light and dark mode, and no external fonts, images or scripts, because
TechDocs sanitises those.

## Building and publishing

The portal does **not** run MkDocs. Sites are rendered outside and published to the storage the portal reads from
(`techdocs.builder: external`). That keeps the image small, means the portal needs no access to source repositories to show
docs, and is the approach the Backstage project recommends for production.

| Step | Local cluster | Production |
|---|---|---|
| Render | `tools/techdocs/build-docs.sh` (MkDocs + `@techdocs/cli generate`) | The same two commands in the repository's pipeline |
| Publish | `kind/techdocs-publish.sh` copies the sites into the portal's volume | `techdocs-cli publish --publisher-type awsS3` (or GCS/Azure) and `techdocs.publisher` switched to that store |
| When | By hand, after `kind/up.sh` | On every merge to `main` |

!!! note "Not wired yet"
    The production publish step is a few lines in the shared workflows and needs the object storage that the AWS phase
    (`infra/`) creates. Until then the local publisher on a volume is what the portal uses.

## Writing good pages

- One idea per page; the navigation in `mkdocs.yml` is the table of contents.
- Use the building blocks from the stylesheet: `pd-hero` (the lead), `pd-facts` (key numbers), `pd-cards` (links), tables for
  anything with more than two columns of facts, admonitions (`!!! tip`, `!!! warning`) for the things people skip.
- Diagrams are fenced ```` ```mermaid ```` blocks; the portal renders them (the Mermaid addon is installed). They do not render in a plain `mkdocs serve`.
- Do not copy README text. The README stays the short reference in the repository; the site is the explanation.

## The service sites

The eleven `app-*` repositories were generated from their READMEs by `tools/techdocs/scaffold.py` (overview with a dependency
diagram, API, configuration, container image, Kubernetes, observability, develop and test, known limitations). After the first
run the generated files are ordinary hand-edited files.
