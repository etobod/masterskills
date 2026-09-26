#!/bin/sh
# Run a Python hook script from this directory with whichever Python 3 works.
# Usage: sh run-hook.sh <script.py> [args...]
# macOS usually has only `python3`; on Windows `python3` may be the Microsoft
# Store stub, so each candidate is probed before use.

dir=$(dirname "$0")
script="$dir/$1"
shift

for py in python3 python py; do
  if "$py" -c 'import sys; sys.exit(sys.version_info[0] != 3)' >/dev/null 2>&1; then
    exec "$py" "$script" "$@"
  fi
done

echo "masterskills: Python 3 not found on PATH (tried python3, python, py)" >&2
exit 1
