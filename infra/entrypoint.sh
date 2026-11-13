#!/bin/sh
# Container entrypoint. In Azure the job mounts a file share at $WORK_DIR; keep everything the
# pipeline writes (runs, upload folders, paid-result cache, databases) there so it survives the
# container. Without WORK_DIR (local docker run), the folders inside /app are used as before.
set -eu
if [ -n "${WORK_DIR:-}" ]; then
  for d in runs out cache data; do
    mkdir -p "$WORK_DIR/$d"
    if [ ! -L "/app/$d" ]; then
      rm -rf "/app/$d"
      ln -s "$WORK_DIR/$d" "/app/$d"
    fi
  done
fi
exec pipeline "$@"
