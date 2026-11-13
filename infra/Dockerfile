# Pipeline image: Python 3.12 + Node 22 + FFmpeg + Chromium deps for Remotion.
# Build from the repo root:  docker build -f infra/Dockerfile -t videopipe .
# Run:  docker run --rm --env-file .env -e WORK_DIR=/work -v "$PWD/work:/work" \
#         videopipe run --channel whatif --quick
FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PIPELINE_ROOT=/app PIPELINE_DB_URL=sqlite:////app/data/pipeline.db \
    PIPELINE_CHECKPOINT_DB=/app/data/checkpoints.db

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg ffmpeg \
        # libraries Remotion's headless Chrome needs
        libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libasound2 libxrandr2 libxkbcommon0 \
        libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
        # Azure Speech SDK runtime
        libssl3 libuuid1 \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Renderer first (changes least often); Remotion downloads its own headless Chrome here.
COPY render/package.json render/package-lock.json render/
RUN cd render && npm ci && npx remotion browser ensure
COPY render/ render/

COPY pyproject.toml ./
COPY src/ src/
RUN pip install .

COPY config/ config/
COPY prompts/ prompts/
COPY assets/ assets/
COPY examples/ examples/

COPY infra/entrypoint.sh /usr/local/bin/entrypoint
RUN chmod 755 /usr/local/bin/entrypoint \
    && mkdir -p runs out cache data && useradd -m -u 1000 pipe && chown -R pipe /app
USER pipe
# In Azure, WORK_DIR points at the mounted file share (see docs/DEPLOY-AZURE.md).
ENTRYPOINT ["entrypoint"]
CMD ["--help"]
