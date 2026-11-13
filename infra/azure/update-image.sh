#!/usr/bin/env bash
# Point the job at the newest image the deploy workflow pushed (or at a given tag):
#   bash infra/azure/update-image.sh            newest
#   bash infra/azure/update-image.sh <git-sha>  a specific build
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
TAG="${1:-$(az acr repository show-tags -n "$ACR" --repository videopipe --orderby time_desc -o tsv | grep -vx latest | head -n 1)}"
[ -n "$TAG" ] || { echo "No images in $ACR yet. Run the deploy workflow first."; exit 1; }
az containerapp job update -n "$JOB" -g "$RG" --image "$ACR.azurecr.io/videopipe:$TAG" -o none
echo "Job $JOB now uses videopipe:$TAG"
