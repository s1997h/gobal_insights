#!/usr/bin/env bash
# Start one cloud run. Everything after the script name is passed to `pipeline`:
#   bash infra/azure/run.sh run --channel whatif --offline --quick     (free test)
#   bash infra/azure/run.sh run --channel whatif --quick --no-stills   (cheap real test)
#   bash infra/azure/run.sh run --channel whatif --topic "What if you stopped sleeping for 72 hours"
#   bash infra/azure/run.sh resume <run_id>
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
[ $# -gt 0 ] || set -- run --channel "$CHANNEL"

TEMPLATE="$(mktemp)"
trap 'rm -f "$TEMPLATE"' EXIT
az containerapp job show -n "$JOB" -g "$RG" --query properties.template -o json > "$TEMPLATE"
python3 - "$TEMPLATE" "$@" <<'PY'
import json, sys

path, args = sys.argv[1], sys.argv[2:]
with open(path) as f:
    template = json.load(f)
template["containers"][0]["args"] = args
with open(path, "w") as f:
    json.dump(template, f)
PY
EXECUTION="$(az containerapp job start -n "$JOB" -g "$RG" --yaml "$TEMPLATE" --query name -o tsv)"
echo "Started $EXECUTION:  pipeline $*"
echo "Check progress with: bash infra/azure/status.sh"
