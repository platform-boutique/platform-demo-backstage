# Build, release, deploy

## The image

`Dockerfile` is a multi-stage build: dependencies (cached by the `package.json` skeletons), then `yarn tsc` and the frontend and backend
builds, then a runtime stage with only production dependencies on `node:24-trixie-slim`. It runs as the `node` user with a read-only
root filesystem; the only writable places are `/tmp` and the volume at `/data`. There is no compiler, no Python and no MkDocs in it.

```bash
docker build -t platform-demo-backstage:dev .
```

## The pipeline

The repository's `ci.yaml` and `release.yaml` call the shared workflows of the organisation, pinned by commit SHA like every other
repository: secret scan, image build with Trivy scan, workflow lint; and on a `vX.Y.Z` tag the scanned digest is promoted to Docker Hub
as `mladenovskistefan/platform-demo-backstage` and signed with keyless cosign.

!!! warning "Not run yet"
    The pipeline files exist but were never executed: nothing was pushed. The first run will tell.

## First release

The Helm repository declares the image by digest; Kyverno and the Helm CI both require a digest and a valid signature, so the very
first deployment on a cluster that is not the laptop goes like this:

1. Merge this repository, tag `v0.1.0`, push the tag. The release pipeline publishes and signs the image.
2. Open the promotion pull request: set `images.backstage.digest` in `envs/dev/values/backstage.yaml` of the Helm repository to the published digest.
3. Merge it. Argo CD deploys the portal.

Until then `images.backstage.digest` is empty in Git, and the local cluster overrides it in the staged copy with the digest of the image you built.

## Custom plugins

The two plugins live in their own repositories and are consumed as tarballs from `vendor/` until there is a package registry:

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
