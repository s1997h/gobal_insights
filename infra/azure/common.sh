# Shared settings for the Azure scripts. Override any of them with an environment variable,
# e.g. LOCATION=southeastasia bash infra/azure/deploy.sh
set -euo pipefail

LOCATION="${LOCATION:-centralindia}"
RG="${RG:-rg-videopipe}"
ENV_NAME="${ENV_NAME:-videopipe-env}"
JOB="${JOB:-videopipe-job}"
SHARE="${SHARE:-work}"
CHANNEL="${CHANNEL:-whatif}"
ENV_FILE="${ENV_FILE:-.env}"

command -v az >/dev/null || { echo "Azure CLI not found. Install it: https://aka.ms/installazurecli"; exit 1; }
SUB_ID="$(az account show --query id -o tsv 2>/dev/null)" || { echo "Not signed in. Run: az login"; exit 1; }
# Registry and storage names must be unique across Azure, so they carry part of the subscription id.
SUFFIX="${SUFFIX:-$(printf '%s' "$SUB_ID" | tr -d '-' | cut -c1-8)}"
ACR="${ACR:-videopipe${SUFFIX}}"
STORAGE="${STORAGE:-videopipe${SUFFIX}}"

say() { printf '\n==> %s\n' "$*"; }

# Value of KEY from .env (last match wins, surrounding quotes removed). Empty if missing.
get_env() {
  [ -f "$ENV_FILE" ] || return 0
  sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

storage_key() {
  az storage account keys list -n "$STORAGE" -g "$RG" --query '[0].value' -o tsv
}
