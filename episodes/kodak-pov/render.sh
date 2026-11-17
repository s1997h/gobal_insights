#!/usr/bin/env bash
# Render the silent picture in 2,400-frame chunks (resumable), then join them.
# usage: bash episodes/kodak-pov/render.sh <bundle-dir>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$1"
OUT="$HERE/work/render"
PROPS="$HERE/work/props.json"
CHROME=$(ls -d /opt/pw-browsers/chromium_headless_shell-1243/*/chrome-headless-shell | head -1)
TOTAL=$(python3 -c "import json,math;print(math.ceil(json.load(open('$PROPS'))['timing']['total_sec']*30))")
mkdir -p "$OUT"
cd "$HERE/../../render"
for ((a=0; a<TOTAL; a+=2400)); do
  b=$(( a + 2399 < TOTAL - 1 ? a + 2399 : TOTAL - 1 ))
  f="$OUT/chunk_$(printf %05d $a).mp4"
  [ -f "$f" ] && continue
  echo "[$(date +%T)] frames $a-$b of $TOTAL"
  npx remotion render "$BUNDLE" Episode "$OUT/tmp.mp4" --props="$PROPS" --frames=$a-$b \
    --browser-executable="$CHROME" --concurrency=2 --codec=h264 --crf=18 --x264-preset=veryfast \
    --log=error >/dev/null
  mv "$OUT/tmp.mp4" "$f"
done
ls "$OUT"/chunk_*.mp4 | sed "s/^/file '/; s/$/'/" > "$OUT/list.txt"
ffmpeg -y -loglevel error -f concat -safe 0 -i "$OUT/list.txt" -c copy "$OUT/picture.mp4"
echo "[$(date +%T)] done: $OUT/picture.mp4"
