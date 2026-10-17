#!/usr/bin/env bash
# tools/techdocs/extra.css is the source of the shared documentation look; the portal injects it from a TypeScript string
# (TechDocs strips stylesheets from documentation, see packages/app/src/modules/techdocs-style). Run after editing the CSS.
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 - <<'PY'
css = open("tools/techdocs/extra.css").read().replace("`", "\\`")
open("packages/app/src/modules/techdocs-style/css.ts", "w").write(
    "// Generated from tools/techdocs/extra.css by tools/techdocs/sync-style.sh - edit the .css file, not this one.\n"
    "export const docsCss = `" + css + "`;\n")
PY
echo "updated packages/app/src/modules/techdocs-style/css.ts"
