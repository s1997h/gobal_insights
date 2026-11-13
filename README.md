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

Needs Python 3.12+, Node 20+ and FFmpeg.

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
