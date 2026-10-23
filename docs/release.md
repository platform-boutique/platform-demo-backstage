# Build, release, deploy

## The image

`Dockerfile` is a multi-stage build: dependencies (cached by the `package.json` skeletons), then `yarn tsc` and the frontend and backend
builds, then a runtime stage with only production dependencies on the distroless `nodejs24` image. It runs as the `nonroot` user (65532) with a read-only
root filesystem; the only writable places are `/tmp` and the volume at `/data`. There is no compiler, no Python and no MkDocs in it.

```bash
docker build -t platform-demo-backstage:dev .
```

## The pipeline

The repository's `ci.yaml` and `release.yaml` call the shared workflows of the organisation, pinned by commit SHA like every other
repository: secret scan, image build with Trivy scan, workflow lint; and on a `vX.Y.Z` tag the scanned digest is promoted to Docker Hub
as `mladenovskistefan/platform-demo-backstage` and signed with keyless cosign.


## First release

The Helm repository declares the image by digest; Kyverno and the Helm CI both require a digest and a valid signature, so a release goes like this:

1. Tag a **new** `vX.Y.Z` on `main` and push the tag. The release pipeline scans, publishes and signs the image. A tag whose scan fails publishes nothing and cannot be reused (release tags are protected), so the next attempt always uses a new version.
2. Open the promotion pull request: set `images.backstage.tag` and `digest` in `envs/dev/values/backstage.yaml` of the Helm repository to the published values.
3. Merge it. Argo CD deploys the portal.

## Custom plugins

The four plugins live in their own repositories and are consumed as tarballs from `vendor/` until there is a package registry:

```bash
# in the plugin repository
yarn build && yarn backstage-cli repo fix --publish
for p in hubble hubble-backend; do (cd plugins/$p && yarn pack --out ../../dist-pack/$p.tgz); done
# in this repository
cp ../platform-demo-backstage-plugin-hubble/dist-pack/hubble.tgz vendor/platform-boutique-backstage-plugin-hubble-0.1.0.tgz   # and the backend one
yarn install
```

## Upgrading Backstage

```bash
yarn backstage-cli versions:bump
yarn install && yarn tsc
```

Read the release notes of every minor version you skip. Third-party plugins (Argo CD, Kyverno, Grafana) lag behind the framework:
check their peer dependencies before bumping. Dependabot does not touch the Backstage packages (they must move together).
