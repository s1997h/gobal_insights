#!/bin/bash
# Make a cartoon episode end to end: voice -> sound -> render -> mix -> package.
#   tools/episode/make.sh episodes/phone-30-days [provider] [voice]
#   provider: kokoro (free, default) | elevenlabs | openai ; voice: a voice name or ElevenLabs voice id
# Output: <episode>/out/ (video, thumbnail, captions, upload text). Re-running reuses cached voice lines.
set -euo pipefail
EP=$(cd "$1" && pwd); PROVIDER=${2:-kokoro}; VOICE=${3:-}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
W="$EP/work"; OUT="$EP/out"; mkdir -p "$W/chunks" "$OUT" "$W/public/fonts"
cp "$ROOT"/assets/fonts/*.otf "$W/public/fonts/"
# shellcheck disable=SC1091
[ -f "$ROOT/.env" ] && set -a && . "$ROOT/.env" && set +a
CHROME=()
[ -n "${PIPELINE_CHROME:-}" ] && CHROME=(--browser-executable="$PIPELINE_CHROME")

python3 "$EP/shots.py" "$W/shots.json"
python3 "$ROOT/tools/episode/voice.py" "$W/shots.json" "$W/audio" --provider "$PROVIDER" ${VOICE:+--voice "$VOICE"}
python3 - "$W" <<'PY'
import json, sys
w = sys.argv[1]
s = json.load(open(f"{w}/shots.json")); t = json.load(open(f"{w}/audio/timing.json"))
json.dump({"shots": s["shots"], "timing": t}, open(f"{w}/props.json", "w"))
json.dump(s.get("thumbnail", {"words": s["title"]}), open(f"{w}/thumb.json", "w"))
PY
python3 "$ROOT/tools/episode/sound.py" "$W/shots.json" "$W/audio/timing.json" "$W/audio"

ffmpeg -y -loglevel error -i "$W/audio/narration.wav" -i "$W/audio/music.wav" -i "$W/audio/sfx.wav" -filter_complex \
"[0:a]aresample=48000,highpass=f=80,equalizer=f=200:t=q:w=1:g=2,equalizer=f=3200:t=q:w=1.2:g=1.5,deesser=i=0.4,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=140:makeup=2,pan=stereo|c0=c0|c1=c0,asplit=2[voice][sc];\
[1:a]volume=0.20[m];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[duck];[2:a]volume=0.6[fx];\
[voice][duck][fx]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
  -map "[a]" -c:a aac -b:a 192k -ar 48000 -ac 2 "$W/mix.m4a"

cd "$ROOT/render"
npx remotion bundle src/index.ts --out-dir "$W/bundle" --public-dir "$W/public" --log=error
TOTAL=$(python3 -c "import json,math,sys; print(math.ceil(json.load(open(sys.argv[1]))['timing']['total_sec']*30))" "$W/props.json")
N=2400; i=0
for ((a=0; a<TOTAL; a+=N)); do
  b=$((a+N-1)); [ "$b" -ge "$TOTAL" ] && b=$((TOTAL-1))
  out="$W/chunks/c$(printf %02d $i).mp4"
  if [ ! -f "$out" ]; then
    echo "render frames $a-$b of $TOTAL"
    npx remotion render "$W/bundle" Episode "$W/chunks/tmp.mp4" --frames="$a-$b" --props="$W/props.json" \
      --codec=h264 --crf=18 --pixel-format=yuv420p --color-space=bt709 --muted --log=error "${CHROME[@]}"
    mv "$W/chunks/tmp.mp4" "$out"
  fi
  i=$((i+1))
done
for f in "$W"/chunks/c*.mp4; do echo "file '$f'"; done > "$W/concat.txt"
TITLE=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['title'].replace('?','').replace('/','-'))" "$W/shots.json")
ffmpeg -y -loglevel error -f concat -safe 0 -i "$W/concat.txt" -i "$W/mix.m4a" -map 0:v -map 1:a -c copy -shortest -movflags +faststart "$OUT/$TITLE.mp4"
npx remotion still "$W/bundle" EpisodeThumb "$OUT/thumbnail.png" --props="$W/thumb.json" --log=error "${CHROME[@]}"
python3 "$ROOT/tools/episode/package.py" "$W/shots.json" "$W/audio/timing.json" "$W/audio/words.json" "$OUT" >/dev/null
echo "Done: $OUT"
