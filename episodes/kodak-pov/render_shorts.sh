#!/usr/bin/env bash
# Render the four vertical Shorts (silent) from work/shorts/s<k>/props.json.
# usage: bash episodes/kodak-pov/render_shorts.sh <bundle-dir>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$1"
CHROME=$(ls -d /opt/pw-browsers/chromium_headless_shell-1243/*/chrome-headless-shell | head -1)
cd "$HERE/../../render"
for k in 1 2 3 4; do
  d="$HERE/work/shorts/s$k"
  [ -f "$d/picture.mp4" ] && continue
  echo "[$(date +%T)] short $k"
  npx remotion render "$BUNDLE" EpisodeShort "$d/tmp.mp4" --props="$d/props.json" \
    --browser-executable="$CHROME" --concurrency=2 --codec=h264 --crf=18 --x264-preset=veryfast --log=error >/dev/null
  mv "$d/tmp.mp4" "$d/picture.mp4"
  npx remotion still "$BUNDLE" EpisodeShort "$d/cover.jpg" --props="$d/props.json" --frame=0 \
    --browser-executable="$CHROME" --log=error >/dev/null
done
echo "[$(date +%T)] shorts done"
