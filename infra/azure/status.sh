#!/usr/bin/env bash
# Recent cloud runs, newest first, and the runs recorded on the share.
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
az containerapp job execution list -n "$JOB" -g "$RG" \
  --query "sort_by([], &properties.startTime)[-10:].{execution:name, status:properties.status, started:properties.startTime, ended:properties.endTime}" \
  -o table
echo
echo "Finished runs on the share (out/$CHANNEL):"
az storage file list --account-name "$STORAGE" --account-key "$(storage_key)" --share-name "$SHARE" \
  --path "out/$CHANNEL" --query "[].name" -o tsv 2>/dev/null | sort | tail -n 10 || echo "  none yet"
echo
echo "Logs: Azure portal > $JOB > Execution history > select a run > Console logs."
