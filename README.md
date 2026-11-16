# AI video pipeline (What IF You...)

One command takes a topic to a finished **long YouTube video, a YouTube Short and an Instagram Reel**, with titles, description, chapters, tags, thumbnail and captions. You upload by hand for now; automatic publishing plugs in after the `export` step later.

```
topic -> script -> critic --(pass)--> voice -> stills -> render -> package -> export
            ^   (rewrite, max 2) |
            +-------------------+   critic --(still failing)--> needs_review (stops)
```

Each run ends in `out/<channel>/<run_id>/`:

```
REVIEW.md                  read this first: titles, critic claims, costs, files
youtube-long/   video.mp4  thumbnail.png  meta.json  UPLOAD.md
youtube-short/  video.mp4  meta.json  UPLOAD.md
instagram-short/ video.mp4 meta.json  UPLOAD.md
```

`UPLOAD.md` has the copy-paste title, description and tags, and a suggested publish time from the channel's schedule.

## Setup (once)

Needs Python 3.12+, Node 20+ and FFmpeg (`ffmpeg` and `ffprobe` on PATH). On Windows:
`winget install --id Gyan.FFmpeg -e`, then close and reopen the terminal and check with `ffmpeg -version`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
(cd render && npm ci)
cp .env.example .env        # add your keys; never commit .env
pipeline doctor             # checks every requirement and says how to fix it
```

Keys in `.env`:

| Key | Used for | Needed when |
|---|---|---|
| `ANTHROPIC_API_KEY` | topic, script, critic, package agents (Claude) | `llm.provider: anthropic` (the default) |
| `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` | the same agents on a model deployed in Azure AI Foundry | `llm.provider: azure_openai` |
| `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` | narration (free tier: 500K characters a month) | any run without `--offline` |
| `OPENAI_API_KEY` | AI still images | only if stills are on; skip with `--no-stills` |

**Choosing the script model.** `llm.provider` in `config/models.yaml` picks Claude (`anthropic`) or an Azure AI Foundry deployment (`azure_openai`); the model names for each live under it. `pipeline doctor` shows which one is active. Before switching to Azure, check your deployment's tokens-per-minute quota (see [docs/DEPLOY-AZURE.md](docs/DEPLOY-AZURE.md), Step 2).

If Chrome is already installed, set `PIPELINE_CHROME=/path/to/chrome` so Remotion doesn't download its own copy. `RENDER_CONCURRENCY` sets render threads (default: Remotion picks half your cores).

## Daily use

```bash
# 1. Free rehearsal: fake providers, beep audio, ~1 minute video. Checks the whole chain.
pipeline run --channel whatif --offline --quick

# 2. Cheap real test: real script and voice, ~1 minute long video, ~25 s Short.
pipeline run --channel whatif --quick --no-stills

# 3. The real thing (topic picked from config/channels/whatif/backlog.md)
pipeline run --channel whatif
pipeline run --channel whatif --topic "What if you stopped sleeping for 72 hours" --shape first_24_hours

# Review, then upload by hand from the out/ folders
pipeline review <run_id>
pipeline approve <run_id>          # or: pipeline reject <run_id> --reason "hook too slow"

# If anything fails (network, crash, spend cap): fix it, then continue from the last finished step
pipeline resume <run_id>

pipeline list                      # recent runs and their status
pipeline costs --channel whatif    # month-to-date spend
```

Write a script yourself and skip the agents:

```bash
pipeline build --channel whatif --long examples/long.json --short examples/short.json
```

Pick the narrator voice (writes a sample per voice, then put the winner in `config/styles/whatif.yaml`):

```bash
pipeline voices
```

## How long it takes

Rendering is the slow part and is CPU-bound. On a 2-core machine Remotion renders about 8 frames a second, so a 9-minute video (16,200 frames) takes about 35 minutes. On an 8-core machine expect roughly a quarter of that. Paid steps (LLM, voice, images) are cached, so `resume` and re-renders never pay twice.

## Spend control

`config/channels/whatif.yaml` sets `budget: {per_video_usd: 8, per_month_usd: 150}`. Every paid call checks the cap *before* it runs and stops the run if it would go over; `pipeline resume` continues once you raise the cap. **The prices in `config/prices.yaml` are placeholders: check each against the provider's pricing page before relying on the caps.**

## Cartoon episodes (automatic)

One command takes a topic to a finished cartoon video, its Shorts, a thumbnail and the upload kit:

```bash
pipeline episode --channel iflab                      # the next line of config/channels/iflab/backlog.md
pipeline episode --channel iflab --topic "How airlines really make money"
pipeline episode --channel iflab --offline --quick    # free rehearsal: placeholder script, beep voice, real render
pipeline resume <run_id>                              # continue a failed run; finished steps are not paid for again
```

What happens, in order (`src/pipeline/episode/`):

1. **Topic.** `--topic`, or the first backlog line that no finished run has used. The line after it is shown as
   "next video" on the end card.
2. **Script.** The model first plans the story: one `hero` (a real named person or company, or "you" for a
   what-if), what they stand to lose (`stakes`), and five candidate first lines from different angles. Then it
   writes a list of *beats*: a narration line plus a view (scene, object, stat, title, list, checklist, duo, bars,
   end) and a few fields. Every video follows one spine: a cold open inside the most dramatic moment, one open
   question by the third beat, a rewind, escalation joined by "but" and "so", a cliffhanger at each chapter end,
   the payoff, and what it means for the viewer. Narration is written for the ear (contractions, short sentences,
   the surprising word last). `prompts/episode_script.md` holds all of it. It never places anything.
3. **Engagement gate.** `audit.py` measures the draft: the first line's score (a stock opening like "Have you
   ever" is capped at 35/100), whether the first three beats are a real cold open, story turns a minute, sentence
   length, stiff uncontracted phrases, how many places the story visits and how often one person just stands in a
   room, chapter openings, where the payoff lands. The schema rejects script labels on screen ("ACT THREE",
   "PAYOFF", "TAKEAWAY"), a mystery card or a title card as the first shot, and text on a phone screen that is not
   an amount. A critic model then reads it as a stranger would (`prompts/episode_critic.md`). Open fixes go back to
   the writer, at most three times, and the draft with the fewest open fixes is kept. `REVIEW.md` shows the hero,
   the first line and the other candidates with their scores.
4. **Director.** `director.py` turns each beat into a shot: where people stand, the camera move, the sound
   effect, a wipe at each chapter. Placement is code, so a bad model answer cannot put anything off screen.
5. **Voice, sound, render.** The channel's Azure voice (with a fallback voice if the first is not available in
   your Speech region), synthesized music and effects, then Remotion in 80-second chunks. HD voices get
   `narrator.temperature` from the style file (0.3 steady to 1.0 most expressive); company stories get their own
   sets (lab, factory, boardroom, store, garage, stage) with the company's name on the wall and a place-and-year tag
   whenever the story moves.
6. **Shorts.** The model picks runs of beats that stand alone and writes a new first line and an on-screen title
   for each (`prompts/episode_shorts.md`); code checks length and overlap, then renders them vertically with
   word-by-word captions inside the Instagram and YouTube safe zone.
7. **Package.** The model picks the 2-4 word phrase people would search (`keyword`), then three titles from
   different angles, thumbnail words and object, description and tags (`prompts/episode_package.md`). Code checks
   that the first title and the first 150 characters of the description contain the search phrase, then adds
   chapters, sources and the disclosure line and renders the thumbnail.

Every log line starts with how far the whole run has got (`[20:12:15]  41% render[long]: 40% of frames
(786/1966), about 2m 10s left`); rendering prints a line every 10% of its frames, or every minute.

Output lands in `out/<channel>/<run_id>/`: `youtube/` (video.mp4, thumbnail.png, description.txt, captions.srt,
UPLOAD.md), `shorts/` (short1.mp4 ..., covers, POSTING.md with titles, captions, hashtags and suggested times) and
`REVIEW.md`. **Read REVIEW.md before posting:** it lists every factual claim with the source the model gave. The
model can be wrong, and nothing is published automatically.

A channel needs `config/channels/<id>.yaml`, a style file (voice, target length, voice rules, story shapes) and
`config/channels/<id>/backlog.md` (one `Title | angle` per line). An 8.5-minute episode with four Shorts takes
about 50 minutes on 2 CPU cores and costs well under a dollar in model and voice calls.

## Cartoon episodes (hand-directed)

An episode is a shot list in `episodes/<name>/shots.py`: for every shot, the narration line, the set, actors with
poses and expressions, props, effects, a stat or chart overlay and a camera move. One command voices it, renders it
in the doodle-cartoon style (`render/src/cartoon/Episode.tsx`) and writes the upload kit:

```bash
tools/episode/make.sh episodes/phone-30-days                       # free local voice (Kokoro)
tools/episode/make.sh episodes/phone-30-days elevenlabs <voice-id>  # most human-sounding
tools/episode/make.sh episodes/phone-30-days openai coral           # gpt-4o-mini-tts, steerable
```

Output lands in `episodes/<name>/out/`: the MP4 (1080p, -14 LUFS), `thumbnail.png`, `captions.srt` and
`upload.md` (title, description with chapters and sources, tags). Voice lines are cached, so changing one shot
re-voices only that shot. Rendering takes about 25 minutes for 8.5 minutes of video on 2 CPU cores.

### Voices

| Provider | Sounds | Cost | Needs |
|---|---|---|---|
| `elevenlabs` | most human; exact word timings | Starter plan, about $6 a month for ~30 minutes (commercial licence) | `ELEVENLABS_API_KEY`, a voice id |
| `openai` | natural, steerable with plain-English direction | about $0.015 a minute | `OPENAI_API_KEY` |
| `azure` | natural; word timings | free tier 0.5M characters a month | `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` |
| `kokoro` | good, a little flat | free, runs on the CPU | model files in `KOKORO_DIR` (links in `adapters/tts.py`) |

Set the pipeline's voice with `tts.provider` in `config/models.yaml` and `narrator.voice` in the channel style.

## Project layout

```
config/            platforms.yaml (limits per platform), channels/*.yaml, styles/*.yaml, models.yaml, prices.yaml
prompts/           agent prompts (topic, script, critic, package)
src/pipeline/      graph.py (LangGraph), nodes/ (one file per step), adapters/ (LLM, TTS, image, audio),
                   checks.py (rules enforced in code), ledger.py (costs), cli.py
render/            Remotion project: Long (1920x1080), Short (1080x1920), Thumbnail (1280x720), 6 scene templates
assets/            Inter font, placeholder music beds
examples/          hand-written scripts for `pipeline build`
tests/             pytest; runs offline with fakes and a stub renderer
infra/Dockerfile   image with Python, Node, FFmpeg and Chrome libraries; infra/entrypoint.sh
infra/azure/       deploy, run, status, download and update-image scripts for Azure
docs/              DEPLOY-AZURE.md
```

Runtime folders (git-ignored): `runs/<run_id>/` holds every intermediate file (scripts, critic report, audio, timing, props, logs), `out/` holds upload folders, `cache/` holds paid results, `pipeline.db` holds runs, posts, costs and embeddings, `checkpoints.db` holds resume points.

## Adding a channel

1. Copy `config/channels/whatif.yaml` to `config/channels/<id>.yaml` (the file name must equal `id`).
2. Write `config/styles/<id>.yaml` (palette, voice, banned phrases, story shapes). Don't share a style between channels.
3. Add `config/channels/<id>/backlog.md` with one topic per line.
4. `pipeline run --channel <id> --dry-run` validates the config; a wrong platform, format, slot or timezone fails with the file and the reason.

New platforms go in `config/platforms.yaml` with their limits; the packager and lint read them from there.

## Tests

```bash
pytest -q                              # ~45 s, no keys, no cost
RUN_RENDER_TESTS=1 pytest -q -m slow   # a real Remotion render (a few minutes)
ruff check src tests && mypy src
```

## Deploy to Azure

Step-by-step guide: [docs/DEPLOY-AZURE.md](docs/DEPLOY-AZURE.md). The pipeline runs as an Azure Container Apps job; scripts in `infra/azure/` create the resources (`deploy.sh`), start runs (`run.sh`), show progress (`status.sh`) and download results (`download.sh`). The GitHub **deploy** workflow builds and tests the image and pushes it to your registry.

## Docker

```bash
docker build -f infra/Dockerfile -t videopipe .
docker run --rm --env-file .env -e WORK_DIR=/work -v "$PWD/work:/work" videopipe run --channel whatif --quick
```

`WORK_DIR` keeps runs, upload folders, cache and databases in one mounted folder (`work/` here).

## Known limits

- The live Anthropic, Azure OpenAI, Azure Speech and OpenAI image adapters are written but not yet tested against the real APIs. Run step 2 above first and expect a fix or two.
- Model names in `config/models.yaml` and prices in `config/prices.yaml` need checking against the providers.
- The two music beds are synthetic placeholders. Swap in licensed tracks (for example from the YouTube Audio Library) and list them under `music.tracks` in the style.
- The critic's "sources" come from the model's own knowledge. Check every claim in `REVIEW.md` before you upload.
- Offline mode makes beep audio and placeholder text: it tests the plumbing, not the content.
- Publishing (YouTube Data API, Instagram Graph API) is not built yet; it plugs in after `export` with an approval step.
