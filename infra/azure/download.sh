#!/usr/bin/env bash
# Download a finished run's upload folders from the share:
#   bash infra/azure/download.sh 20261114-090000-whatif
# They land in downloads/<run_id>/ with the same layout as out/ on your machine.
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
RUN_ID="${1:?usage: download.sh <run_id>   (see bash infra/azure/status.sh)}"
DEST="downloads"
mkdir -p "$DEST"
az storage file download-batch --account-name "$STORAGE" --account-key "$(storage_key)" \
  --source "$SHARE" --pattern "out/$CHANNEL/$RUN_ID/*" --destination "$DEST" -o none
echo "Saved to $DEST/out/$CHANNEL/$RUN_ID/ (open REVIEW.md first)"
