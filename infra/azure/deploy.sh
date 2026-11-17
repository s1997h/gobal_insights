#!/usr/bin/env bash
# Create or update everything the pipeline needs in Azure. Safe to run again.
# Run from the repo root after `az login`:   bash infra/azure/deploy.sh
# Step-by-step guide: docs/DEPLOY-AZURE.md
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

say "Subscription: $(az account show --query '[name, user.name]' -o tsv | paste -sd ' ' -)"
echo "Region: $LOCATION   Resource group: $RG   Registry: $ACR   Storage: $STORAGE"
if [ "${YES:-}" != "1" ]; then
  read -r -p "Create or update these resources? [y/N] " ok
  [ "$ok" = "y" ] || [ "$ok" = "Y" ] || { echo "Stopped."; exit 1; }
fi

say "Container Apps CLI extension"
az extension add --name containerapp --upgrade --only-show-errors

say "Registering resource providers (first time takes a few minutes)"
for ns in Microsoft.App Microsoft.OperationalInsights Microsoft.ContainerRegistry Microsoft.Storage Microsoft.CognitiveServices; do
  az provider register --namespace "$ns" --wait --only-show-errors
done

say "Resource group $RG"
az group create -n "$RG" -l "$LOCATION" -o none

say "Storage account $STORAGE and file share '$SHARE' (runs, videos and databases live here)"
az storage account create -n "$STORAGE" -g "$RG" -l "$LOCATION" --sku Standard_LRS --kind StorageV2 \
  --min-tls-version TLS1_2 --allow-blob-public-access false -o none
if [ "$(az storage share-rm exists --storage-account "$STORAGE" -g "$RG" -n "$SHARE" --query exists -o tsv)" != "true" ]; then
  az storage share-rm create --storage-account "$STORAGE" -g "$RG" -n "$SHARE" --quota 100 -o none
fi
STORAGE_KEY="$(storage_key)"

say "Container registry $ACR (Basic)"
az acr show -n "$ACR" -g "$RG" -o none 2>/dev/null \
  || az acr create -n "$ACR" -g "$RG" -l "$LOCATION" --sku Basic --admin-enabled true -o none
az acr update -n "$ACR" -g "$RG" --admin-enabled true -o none
ACR_USER="$(az acr credential show -n "$ACR" --query username -o tsv)"
ACR_PASS="$(az acr credential show -n "$ACR" --query 'passwords[0].value' -o tsv)"

SPEECH_KEY="$(get_env AZURE_SPEECH_KEY)"
SPEECH_REGION="$(get_env AZURE_SPEECH_REGION)"
if [ -z "$SPEECH_KEY" ]; then
  say "Speech resource videopipe-speech (free tier F0)"
  az cognitiveservices account show -n videopipe-speech -g "$RG" -o none 2>/dev/null \
    || az cognitiveservices account create -n videopipe-speech -g "$RG" -l "$LOCATION" \
         --kind SpeechServices --sku F0 --yes -o none
  SPEECH_KEY="$(az cognitiveservices account keys list -n videopipe-speech -g "$RG" --query key1 -o tsv)"
  SPEECH_REGION="$LOCATION"
fi

say "Container Apps environment $ENV_NAME"
az containerapp env show -n "$ENV_NAME" -g "$RG" -o none 2>/dev/null \
  || az containerapp env create -n "$ENV_NAME" -g "$RG" -l "$LOCATION" --environment-mode WorkloadProfiles -o none
ENV_MODE="$(az containerapp env show -n "$ENV_NAME" -g "$RG" --query properties.environmentMode -o tsv 2>/dev/null || true)"
if [ "$ENV_MODE" = "Express" ]; then
  echo "ERROR: $ENV_NAME is an Express environment, which can't run jobs or mount file shares."
  echo "Delete it (az containerapp env delete -n $ENV_NAME -g $RG --yes) and run this script again."
  exit 1
fi
az containerapp env storage set -n "$ENV_NAME" -g "$RG" --storage-name "$SHARE" \
  --azure-file-account-name "$STORAGE" --azure-file-account-key "$STORAGE_KEY" \
  --azure-file-share-name "$SHARE" --access-mode ReadWrite -o none
ENV_ID="$(az containerapp env show -n "$ENV_NAME" -g "$RG" --query id -o tsv)"

IMAGE_TAG="${IMAGE_TAG:-$(az acr repository show-tags -n "$ACR" --repository videopipe --orderby time_desc -o tsv 2>/dev/null \
  | grep -vx latest | head -n 1 || true)}"
if [ -z "$IMAGE_TAG" ]; then
  say "The registry has no pipeline image yet"
  REPO="$(git config --get remote.origin.url 2>/dev/null | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')"
  if command -v gh >/dev/null && gh auth status >/dev/null 2>&1 && [ -n "$REPO" ]; then
    read -r -p "Save the registry login as GitHub Actions secrets in $REPO? [y/N] " ok
    if [ "$ok" = "y" ] || [ "$ok" = "Y" ]; then
      gh secret set ACR_NAME -R "$REPO" --body "$ACR"
      gh secret set ACR_USERNAME -R "$REPO" --body "$ACR_USER"
      printf '%s' "$ACR_PASS" | gh secret set ACR_PASSWORD -R "$REPO"
      echo "Saved. Now start the build: gh workflow run deploy.yml -R $REPO   (or GitHub > Actions > deploy > Run workflow)"
    fi
  else
    cat <<MSG
Add these three secrets in GitHub (repo > Settings > Secrets and variables > Actions > New repository secret):
  ACR_NAME      $ACR
  ACR_USERNAME  $ACR_USER
  ACR_PASSWORD  the output of:  az acr credential show -n $ACR --query 'passwords[0].value' -o tsv
Then run the build: GitHub > Actions > deploy > Run workflow.
MSG
  fi
  echo "When the build has finished, run this script again to create the job."
  exit 0
fi
IMAGE="$ACR.azurecr.io/videopipe:$IMAGE_TAG"

ANTHROPIC_KEY="$(get_env ANTHROPIC_API_KEY)"
AOAI_ENDPOINT="$(get_env AZURE_OPENAI_ENDPOINT)"
AOAI_KEY="$(get_env AZURE_OPENAI_API_KEY)"
OPENAI_KEY="$(get_env OPENAI_API_KEY)"
ELEVEN_KEY="$(get_env ELEVENLABS_API_KEY)"
if [ -z "$ANTHROPIC_KEY" ] && { [ -z "$AOAI_ENDPOINT" ] || [ -z "$AOAI_KEY" ]; }; then
  echo "WARNING: $ENV_FILE has no script-model key (ANTHROPIC_API_KEY, or AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY)."
  echo "         Only --offline runs will work until you add one and run this script again."
fi

say "Job $JOB (4 vCPU, 8 GiB, manual start, image videopipe:$IMAGE_TAG)"
SPEC="$(mktemp)"
trap 'rm -f "$SPEC"' EXIT
chmod 600 "$SPEC"
LOCATION="$LOCATION" ENV_ID="$ENV_ID" IMAGE="$IMAGE" ACR_SERVER="$ACR.azurecr.io" ACR_USER="$ACR_USER" \
ACR_PASS="$ACR_PASS" SHARE="$SHARE" CHANNEL="$CHANNEL" SPEECH_KEY="$SPEECH_KEY" SPEECH_REGION="$SPEECH_REGION" \
ANTHROPIC_KEY="$ANTHROPIC_KEY" AOAI_ENDPOINT="$AOAI_ENDPOINT" AOAI_KEY="$AOAI_KEY" OPENAI_KEY="$OPENAI_KEY" ELEVEN_KEY="$ELEVEN_KEY" \
python3 - "$SPEC" <<'PY'
import json, os, sys

e = os.environ
secrets = [{"name": "acr-password", "value": e["ACR_PASS"]}]
env = [
    {"name": "WORK_DIR", "value": "/work"},
    {"name": "RENDER_CONCURRENCY", "value": "4"},
    {"name": "AZURE_SPEECH_REGION", "value": e["SPEECH_REGION"]},
]
for var, secret, value in [
    ("AZURE_SPEECH_KEY", "azure-speech-key", e["SPEECH_KEY"]),
    ("ANTHROPIC_API_KEY", "anthropic-api-key", e["ANTHROPIC_KEY"]),
    ("AZURE_OPENAI_API_KEY", "azure-openai-api-key", e["AOAI_KEY"]),
    ("OPENAI_API_KEY", "openai-api-key", e["OPENAI_KEY"]),
    ("ELEVENLABS_API_KEY", "elevenlabs-api-key", e.get("ELEVEN_KEY", "")),
]:
    if value:
        secrets.append({"name": secret, "value": value})
        env.append({"name": var, "secretRef": secret})
if e["AOAI_ENDPOINT"]:
    env.append({"name": "AZURE_OPENAI_ENDPOINT", "value": e["AOAI_ENDPOINT"]})

spec = {
    "location": e["LOCATION"],
    "properties": {
        "environmentId": e["ENV_ID"],
        "workloadProfileName": "Consumption",
        "configuration": {
            "triggerType": "Manual",
            "replicaTimeout": 10800,
            "replicaRetryLimit": 0,
            "manualTriggerConfig": {"parallelism": 1, "replicaCompletionCount": 1},
            "registries": [
                {"server": e["ACR_SERVER"], "username": e["ACR_USER"], "passwordSecretRef": "acr-password"}
            ],
            "secrets": secrets,
        },
        "template": {
            "containers": [
                {
                    "name": "pipeline",
                    "image": e["IMAGE"],
                    "args": ["run", "--channel", e["CHANNEL"]],
                    "resources": {"cpu": 4, "memory": "8Gi"},
                    "env": env,
                    "volumeMounts": [{"volumeName": "work", "mountPath": "/work"}],
                }
            ],
            "volumes": [
                {
                    "name": "work",
                    "storageType": "AzureFile",
                    "storageName": e["SHARE"],
                    # nobrl: SQLite needs it on SMB shares; uid 1000 is the image's 'pipe' user
                    "mountOptions": "dir_mode=0777,file_mode=0777,uid=1000,gid=1000,mfsymlinks,nobrl",
                }
            ],
        },
    },
}
with open(sys.argv[1], "w") as f:
    json.dump(spec, f)
PY
if az containerapp job show -n "$JOB" -g "$RG" -o none 2>/dev/null; then
  az containerapp job update -n "$JOB" -g "$RG" --yaml "$SPEC" -o none
else
  az containerapp job create -n "$JOB" -g "$RG" --yaml "$SPEC" -o none
fi

say "Done"
cat <<MSG
Free test run in the cloud:   bash infra/azure/run.sh run --channel $CHANNEL --offline --quick
Real run:                     bash infra/azure/run.sh run --channel $CHANNEL
Check progress:               bash infra/azure/status.sh
Download a finished run:      bash infra/azure/download.sh <run_id>
MSG
