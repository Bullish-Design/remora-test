#!/usr/bin/env bash
set -euo pipefail

if [ -x ".devenv/state/venv/bin/python" ]; then
  PYTHON_BIN=".devenv/state/venv/bin/python"
else
  PYTHON_BIN="python"
fi

STATIC_DIR="$("$PYTHON_BIN" - <<'PY'
from remora.web.server import _STATIC_DIR
print(_STATIC_DIR)
PY
)"

mkdir -p "$STATIC_DIR/vendor"
cp ui/vendor/graphology.umd.min.js "$STATIC_DIR/vendor/graphology.umd.min.js"
cp ui/vendor/sigma.min.js "$STATIC_DIR/vendor/sigma.min.js"
cp ui/vendor/graphology-layout-forceatlas2.min.js "$STATIC_DIR/vendor/graphology-layout-forceatlas2.min.js"

INDEX_HTML="$STATIC_DIR/index.html"

sed -i 's#https://unpkg.com/graphology@0.25.4/dist/graphology.umd.min.js#/static/vendor/graphology.umd.min.js#g' "$INDEX_HTML"
sed -i 's#https://unpkg.com/sigma@3.0.0-beta.31/build/sigma.min.js#/static/vendor/sigma.min.js#g' "$INDEX_HTML"
sed -i 's#https://unpkg.com/graphology-layout-forceatlas2@0.10.1/build/graphology-layout-forceatlas2.min.js#/static/vendor/graphology-layout-forceatlas2.min.js#g' "$INDEX_HTML"

echo "Installed local UI vendor assets into: $STATIC_DIR/vendor"
echo "Patched index.html to local /static/vendor scripts"
