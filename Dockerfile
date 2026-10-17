# Multi-stage build of the portal image (https://backstage.io/docs/deployment/docker#multi-stage-build), extended with MkDocs so
# the backend can build TechDocs itself. Build context: the repository root.
#   docker build -t platform-demo-backstage:dev .
# Pinned by digest in CI; bump the base images with Dependabot.

# ---- stage 1: package.json skeletons (keeps the dependency layer cached while only sources change) ----
FROM node:24-trixie-slim AS packages
WORKDIR /app
COPY package.json backstage.json ./
COPY packages packages
COPY plugins plugins
RUN find packages \! -name "package.json" -mindepth 2 -maxdepth 2 -exec rm -rf {} \+

# ---- stage 2: build the frontend and the backend bundle ----
FROM node:24-trixie-slim AS build
ENV PYTHON=/usr/bin/python3
RUN apt-get update && apt-get install -y --no-install-recommends python3 g++ build-essential libsqlite3-dev && rm -rf /var/lib/apt/lists/*
USER node
WORKDIR /app
COPY --chown=node:node .yarn ./.yarn
COPY --chown=node:node .yarnrc.yml ./
COPY --from=packages --chown=node:node /app .
COPY --chown=node:node yarn.lock ./
RUN --mount=type=cache,target=/home/node/.yarn/berry/cache,sharing=locked,uid=1000,gid=1000 \
    yarn install --immutable
COPY --chown=node:node . .
RUN yarn tsc && yarn build:backend

# ---- stage 3: runtime ----
FROM node:24-trixie-slim
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=768" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# libsqlite3 for the development database driver; python + MkDocs for TechDocs; git because TechDocs/the catalog may clone.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libsqlite3-dev python3 python3-pip python3-venv build-essential git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# MkDocs and the TechDocs core plugin live in their own virtualenv (the system Python is externally managed).
# requirements-techdocs.txt pins everything the documentation of this organisation uses (see docs/techdocs.md).
COPY requirements-techdocs.txt /tmp/requirements-techdocs.txt
RUN python3 -m venv /opt/techdocs \
    && /opt/techdocs/bin/pip install -r /tmp/requirements-techdocs.txt \
    && rm /tmp/requirements-techdocs.txt
ENV PATH="/opt/techdocs/bin:${PATH}"

USER node
WORKDIR /app

COPY --from=build --chown=node:node /app/.yarn ./.yarn
COPY --from=build --chown=node:node /app/.yarnrc.yml /app/backstage.json ./
COPY --from=build --chown=node:node /app/yarn.lock /app/package.json /app/packages/backend/dist/skeleton.tar.gz ./
RUN tar xzf skeleton.tar.gz && rm skeleton.tar.gz

RUN --mount=type=cache,target=/home/node/.yarn/berry/cache,sharing=locked,uid=1000,gid=1000 \
    yarn workspaces focus --all --production && rm -rf "$(yarn cache clean)"

COPY --from=build --chown=node:node /app/packages/backend/dist/bundle.tar.gz ./
RUN tar xzf bundle.tar.gz && rm bundle.tar.gz
COPY --chown=node:node app-config*.yaml ./
COPY --chown=node:node catalog ./catalog

# TechDocs output and the generator's scratch space are written here: mount an emptyDir/PVC over it with a read-only root filesystem.
ENV TECHDOCS_CACHE=/data
VOLUME /data

EXPOSE 7007
CMD ["node", "packages/backend", "--config", "app-config.yaml", "--config", "app-config.production.yaml"]
