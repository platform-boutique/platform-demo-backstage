#!/usr/bin/env bash
# Renders the TechDocs site of every repository that has a catalog-info.yaml with a `backstage.io/techdocs-ref` annotation and
# lays the output out the way the portal's `local` publisher expects it:  <out>/<namespace>/<kind>/<name>/...
# The same two steps run in CI for a real deployment (`techdocs-cli generate` + `techdocs-cli publish --publisher-type awsS3`).
#
#   tools/techdocs/build-docs.sh <workspace-root> <out-dir>       e.g.  ~/Desktop/platform-demo  /tmp/techdocs
#
# Needs: python3 (a virtualenv with tools/techdocs/requirements.txt is created in ~/.cache/platform-demo/), node/npx.
set -euo pipefail
ROOT="${1:?usage: build-docs.sh <workspace-root> <out-dir>}"; OUT="${2:?usage: build-docs.sh <workspace-root> <out-dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TECHDOCS_CLI_VERSION="${TECHDOCS_CLI_VERSION:-1.12.0}"
# Outside every repository: MkDocs refuses symlinks that leave the repository it renders (the portal documents itself).
VENV="${TECHDOCS_VENV:-$HOME/.cache/platform-demo/techdocs-venv}"

if [ ! -x "$VENV/bin/mkdocs" ]; then
  echo "==> creating the MkDocs virtualenv in $VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r "$HERE/requirements.txt"
fi
export PATH="$VENV/bin:$PATH"

mkdir -p "$OUT"
count=0
while IFS= read -r desc; do
  repo="$(dirname "$desc")"
  [ -f "$repo/mkdocs.yml" ] || continue
  # The Component that carries the techdocs annotation names the site (kind/name are lower-cased in the storage path).
  read -r name kind < <(python3 - "$desc" <<'PY'
import sys, yaml
for doc in yaml.safe_load_all(open(sys.argv[1])):
    if doc and "backstage.io/techdocs-ref" in (doc.get("metadata", {}).get("annotations") or {}):
        print(doc["metadata"]["name"].lower(), doc["kind"].lower()); break
PY
)
  [ -n "${name:-}" ] || continue
  dest="$OUT/default/$kind/$name"
  rm -rf "$dest"; mkdir -p "$dest"
  echo "==> $name ($repo)"
  npx --yes "@techdocs/cli@$TECHDOCS_CLI_VERSION" generate --no-docker --source-dir "$repo" --output-dir "$dest" >/dev/null
  count=$((count+1))
done < <(find "$ROOT" -maxdepth 3 -name catalog-info.yaml -not -path '*/node_modules/*' | sort)
echo "built $count sites into $OUT"
