#!/usr/bin/env bash
# Run the quick-md test suite. Uses the project venv and disables
# ROS/external pytest plugins that may conflict.
set -euo pipefail
cd "$(dirname "$0")"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
exec .venv/bin/python -m pytest tests/ "$@"