#!/bin/sh
# Run a Python script of this plugin with whichever Python 3 works.
# Usage: sh py.sh <script path, relative to the plugin root or absolute> [args...]
# macOS usually has only `python3`; on Windows `python3` may be the Microsoft
# Store stub, so each candidate is probed before use. `-B`: no __pycache__
# inside the installed plugin.

case "$1" in
  /* | [A-Za-z]:*) script=$1 ;;
  *) script="$(dirname "$0")/../$1" ;;
esac
shift

for py in python3 python py; do
  if "$py" -c 'import sys; sys.exit(sys.version_info[0] != 3)' >/dev/null 2>&1; then
    exec "$py" -B "$script" "$@"
  fi
done

echo "masterskills: Python 3 not found on PATH (tried python3, python, py)" >&2
exit 1
