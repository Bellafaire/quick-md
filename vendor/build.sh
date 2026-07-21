#!/usr/bin/env bash
#
# build.sh - bundle the CodeMirror 6 editor (+ vim, markdown, one-dark theme)
# into a single self-contained ES module so the editor works offline.
#
# Output: ../static/js/qmd-editor.js  (minified, all deps inlined)
#
# Requirements: node + npm (uses esbuild via npx). Run from this directory.
#
#   ./build.sh
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

BUILD_DIR=".build"
OUT_DIR="../static/js"
OUT_FILE="$OUT_DIR/qmd-editor.js"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$OUT_DIR"

# Install the exact packages we bundle. Pinned versions keep the vendored
# output reproducible.
cat > "$BUILD_DIR/package.json" <<'JSON'
{
  "name": "qmd-editor-build",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "dependencies": {
    "codemirror": "^6.0.1",
    "@codemirror/state": "^6.5.2",
    "@codemirror/view": "^6.36.0",
    "@codemirror/commands": "^6.7.1",
    "@codemirror/lang-markdown": "^6.3.2",
    "@codemirror/language-data": "^6.5.1",
    "@codemirror/theme-one-dark": "^6.1.2",
    "@replit/codemirror-vim": "^6.3.0",
    "esbuild": "^0.25.0"
  }
}
JSON

echo "Installing dependencies into $BUILD_DIR ..."
(cd "$BUILD_DIR" && npm install --no-audit --no-fund --silent)

# Copy the entry into the build dir so esbuild resolves node_modules there.
cp qmd-editor.entry.js "$BUILD_DIR/qmd-editor.entry.js"

echo "Bundling with esbuild -> $OUT_FILE ..."
./"$BUILD_DIR"/node_modules/.bin/esbuild "$BUILD_DIR/qmd-editor.entry.js" \
    --bundle \
    --format=esm \
    --target=es2020 \
    --minify \
    --outfile="$OUT_FILE"

# Show the size for sanity.
SIZE=$(du -h "$OUT_FILE" | cut -f1)
echo "Done. Wrote $OUT_FILE ($SIZE)"

# Record a SHA-256 of the entry so the Python server (utils/assets.py) can
# detect staleness and auto-rebuild without spurious rebuilds from mtime noise.
node -e "const c=require('crypto'),fs=require('fs');const h=c.createHash('sha256').update(fs.readFileSync('qmd-editor.entry.js')).digest('hex');fs.writeFileSync('$OUT_DIR/qmd-editor.sha256',h+'\n');"
echo "Wrote $OUT_DIR/qmd-editor.sha256"

# Clean up the heavyweight build dir (node_modules); keep the script tiny.
rm -rf "$BUILD_DIR"