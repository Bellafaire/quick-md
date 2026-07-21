"""Ensure vendored, offline-capable web assets are present at startup.

The web editor (CodeMirror 6 + Vim) and MathJax are bundled locally under
``static/js/`` so the app works with no internet connection. This module
guarantees those files exist (and are up to date with the build sources) every
time the server starts, so you never have to remember to run ``vendor/build.sh``
by hand.

Behaviour:
  * MathJax  -> if missing, download the single-file SVG build from a CDN once
                and cache it. (No build tooling required.)
  * Editor   -> if missing or stale, run ``vendor/build.sh`` (needs node+npm).
                Staleness is tracked with a SHA-256 sidecar of the entry file so
                that fresh clones (where mtimes are noisy) do not trigger
                spurious rebuilds.

If a rebuild is impossible (no node/npm, no internet), a warning is printed and
the server still starts -- the already-committed bundle is normally present, so
this only matters if the file was deleted.
"""

import hashlib
import os
import subprocess
import sys
import urllib.request

MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"


def _project_root():
    # utils/assets.py -> project root is one level up from utils/.
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _say(msg, error=False):
    stream = sys.stderr if error else sys.stdout
    print(f"[assets] {msg}", file=stream)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_mathjax(dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    _say("MathJax bundle missing; downloading from CDN (one-time cache)...")
    try:
        tmp = dest + ".part"
        urllib.request.urlretrieve(MATHJAX_URL, tmp)
        os.replace(tmp, dest)
        _say(f"Cached MathJax -> {dest}")
    except Exception as e:
        _say(f"Could not download MathJax ({e}). Math rendering will be "
             "unavailable until re-run with internet.", error=True)


def _editor_needs_build(bundle, sidecar, entry):
    if not (os.path.exists(bundle) and os.path.getsize(bundle) > 0):
        _say("Editor bundle missing.")
        return True
    if not os.path.exists(sidecar):
        _say("Editor bundle has no version sidecar; rebuilding to establish baseline.")
        return True
    if not os.path.exists(entry):
        # No entry to compare against -- nothing to rebuild from.
        return False
    try:
        recorded = open(sidecar).read().strip()
    except OSError:
        return True
    current = _sha256(entry)
    if recorded != current:
        _say("Editor bundle is stale (entry file changed); rebuilding.")
        return True
    return False


def _ensure_editor_bundle(bundle, sidecar, entry, build_script):
    if not _editor_needs_build(bundle, sidecar, entry):
        return
    if not (os.path.exists(entry) and os.path.exists(build_script)):
        _say("Cannot rebuild editor bundle: vendor/qmd-editor.entry.js or "
             "vendor/build.sh is missing.", error=True)
        return
    _say("Building vendored editor bundle (requires node+npm; one-time)...")
    try:
        result = subprocess.run(
            ["bash", build_script],
            cwd=os.path.dirname(build_script),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        _say("`bash` not found; cannot build editor bundle.", error=True)
        return
    except subprocess.TimeoutExpired:
        _say("Editor bundle build timed out.", error=True)
        return

    if result.returncode != 0:
        _say(f"Editor bundle build failed (exit {result.returncode}).", error=True)
        tail = (result.stderr or result.stdout or "")[-800:]
        if tail:
            print(tail, file=sys.stderr)
        _say("The editor will not load until static/js/qmd-editor.js exists. "
             "Run `vendor/build.sh` manually or restore it from git.", error=True)
        return

    _say("Editor bundle built successfully.")
    # Refresh the sidecar so we don't rebuild again next start.
    try:
        with open(sidecar, "w") as f:
            f.write(_sha256(entry) + "\n")
    except OSError:
        pass


def ensure_vendored_assets():
    """Check (and repair) the local web assets. Safe to call on every startup."""
    if os.environ.get("QUICK_MD_SKIP_ASSET_CHECK") == "1":
        return

    root = _project_root()
    static_dir = os.path.join(root, "static", "js")
    os.makedirs(static_dir, exist_ok=True)

    mathjax_bundle = os.path.join(static_dir, "mathjax-tex-svg.js")
    editor_bundle = os.path.join(static_dir, "qmd-editor.js")
    editor_sidecar = os.path.join(static_dir, "qmd-editor.sha256")
    entry = os.path.join(root, "vendor", "qmd-editor.entry.js")
    build_script = os.path.join(root, "vendor", "build.sh")

    _ensure_mathjax(mathjax_bundle)
    _ensure_editor_bundle(editor_bundle, editor_sidecar, entry, build_script)