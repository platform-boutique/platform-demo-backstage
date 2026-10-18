# Multi-stage build of the portal image (https://backstage.io/docs/deployment/docker#multi-stage-build).
# Build context: the repository root.
#   docker build -t platform-demo-backstage:dev .
# Base images are pinned by digest (Dependabot proposes updates). The runtime image is distroless: it has no shell, no package manager and none
# of Debian's utilities (util-linux, systemd, login ...), so it has none of their CVEs (the Debian-slim base had 47 HIGH/CRITICAL, none fixable).

# ---- stage 1: package.json skeletons (keeps the dependency layer cached while only sources change) ----
FROM node:24-trixie-slim@sha256:7f486cabe892bff8fef04c0f7da8dba84a560be3e4e2740b7a86afc57ebec315 AS packages
WORKDIR /app
COPY package.json backstage.json ./
COPY packages packages
COPY plugins plugins
RUN find packages \! -name "package.json" -mindepth 2 -maxdepth 2 -exec rm -rf {} \+

# ---- stage 2: build the frontend and the backend bundle ----
FROM node:24-trixie-slim@sha256:7f486cabe892bff8fef04c0f7da8dba84a560be3e4e2740b7a86afc57ebec315 AS build
ENV PYTHON=/usr/bin/python3
RUN apt-get update && apt-get install -y --no-install-recommends python3 g++ build-essential libsqlite3-dev && rm -rf /var/lib/apt/lists/*
USER node
WORKDIR /app
# BuildKit creates the parents of a cache mount as root; yarn needs to write next to it.
RUN mkdir -p /home/node/.yarn/berry
COPY --chown=node:node .yarn ./.yarn
COPY --chown=node:node .yarnrc.yml ./
COPY --from=packages --chown=node:node /app .
COPY --chown=node:node yarn.lock ./
# our own plugins, installed from tarballs until a package registry exists (README, "Custom plugins")
COPY --chown=node:node vendor ./vendor
RUN --mount=type=cache,target=/home/node/.yarn/berry/cache,sharing=locked,uid=1000,gid=1000 \
    yarn install --immutable
COPY --chown=node:node . .
RUN yarn tsc && yarn build:backend

# ---- stage 3: prepare the runtime tree (the distroless image below cannot run commands) ----
FROM node:24-trixie-slim@sha256:7f486cabe892bff8fef04c0f7da8dba84a560be3e4e2740b7a86afc57ebec315 AS runtime-prep
ENV NODE_ENV=production
USER node
WORKDIR /app
RUN mkdir -p /home/node/.yarn/berry

COPY --from=build --chown=node:node /app/.yarn ./.yarn
COPY --from=build --chown=node:node /app/.yarnrc.yml /app/backstage.json ./
COPY --from=build --chown=node:node /app/yarn.lock /app/package.json /app/packages/backend/dist/skeleton.tar.gz ./
RUN tar xzf skeleton.tar.gz && rm skeleton.tar.gz

COPY --chown=node:node vendor ./vendor
# Native modules come as prebuilt binaries (glibc, the same as the distroless image); there is no toolchain at runtime, and TechDocs are
# built outside the image (techdocs.builder: external, docs/techdocs.md).
RUN --mount=type=cache,target=/home/node/.yarn/berry/cache,sharing=locked,uid=1000,gid=1000 \
    yarn workspaces focus --all --production && rm -rf "$(yarn cache clean)"

COPY --from=build --chown=node:node /app/packages/backend/dist/bundle.tar.gz ./
RUN tar xzf bundle.tar.gz && rm bundle.tar.gz
COPY --chown=node:node app-config*.yaml ./
COPY --chown=node:node catalog ./catalog
# yarn is not needed to run the backend, and neither is its cache
RUN rm -rf .yarn .yarnrc.yml /home/node/.yarn
USER root
RUN mkdir -p /data && chown 65532:65532 /data

# ---- stage 4: runtime ----
# CA certificates (TLS to Dex and GitHub) are part of the distroless image; the user is `nonroot` (65532), the chart runs it as such.
FROM gcr.io/distroless/nodejs24-debian13:nonroot@sha256:59c479c9b8c123e66047315c968aa2d35e31ae5149c856e4110a79c8b3563f0b
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=768" \
    TECHDOCS_CACHE=/data
WORKDIR /app
COPY --from=runtime-prep --chown=65532:65532 /app ./
# Published TechDocs sites are read from here (techdocs.publisher.local): mount a volume over it.
COPY --from=runtime-prep --chown=65532:65532 /data /data
VOLUME /data

EXPOSE 7007
# the base image's entrypoint is /nodejs/bin/node
CMD ["packages/backend", "--config", "app-config.yaml", "--config", "app-config.production.yaml"]
