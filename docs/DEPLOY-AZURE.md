# Deploy to Azure

The pipeline runs in Azure as a **Container Apps job**. You start a run with one command from your machine, Azure renders it on 4 CPU cores, and the finished upload folders land on an Azure file share that you download from. Posting to YouTube and Instagram stays manual.

```
 GitHub "deploy" workflow ──builds and tests the image──▶ Azure Container Registry
                                                                  │
 you: bash infra/azure/run.sh ──▶ Container Apps job (4 vCPU, 8 GiB) ──▶ file share "work"
                                    │ keys come from job secrets            runs/ out/ cache/ data/
                                    ▼                                          │
                       script model (Claude or Azure OpenAI)      bash infra/azure/download.sh ──▶ your PC
                       Azure Speech (voice)
```

Setup takes about an hour the first time, most of it waiting for Azure and for the first image build.

**What it costs on Azure for Students** (all from the $100 credit):

| Item | Cost |
| --- | --- |
| Container Apps job | Free up to 180,000 vCPU-seconds a month, roughly 30 full videos |
| Container Registry (Basic) | About $5 a month |
| File share and logs | Under $1 a month |
| Azure Speech (F0) | Free up to 500,000 characters a month, roughly 50 videos |
| Script model | Per token: Claude is billed by Anthropic, an Azure OpenAI model comes out of the credit |

---

## Before you start

You need, on your machine (WSL Ubuntu on Windows):

1. **The project** cloned from GitHub, with `.env` filled in (Step 3 of the setup guide).
2. **The Azure CLI**, signed in to your student subscription:

   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   az login --use-device-code        # open the link, enter the code, sign in with your student account
   az account show --query "{name:name, user:user.name}" -o table
   ```

   The name should be **Azure for Students**. If you see another subscription, run `az account set --subscription "Azure for Students"`.
3. **Optional: the GitHub CLI** (`sudo apt install gh`, then `gh auth login`). With it, the deploy script stores the registry login in GitHub for you.

Run every command below from the project folder (`cd ~/gobal_insights`).

---

## Step 1: Find a region your subscription allows

Student subscriptions can only create resources in a few regions, and the list differs per subscription.

1. In the [Azure portal](https://portal.azure.com), search for **Policy** and open **Assignments**.
2. Open **Allowed resource deployment regions** and look at its **Parameters**.
3. Pick `centralindia` if it's listed. Otherwise pick the nearest listed region, for example `southeastasia`.

Tell the scripts which region to use (skip this if it's `centralindia`):

```bash
export LOCATION=southeastasia
```

---

## Step 2: Choose the script model

The pipeline can write scripts with a model you deploy in **Azure AI Foundry** (`provider: azure_openai`, the current setting, using gpt-5-mini) or with **Claude** (`provider: anthropic`). The setting is `llm.provider` in `config/models.yaml`.

To use Claude instead, set `provider: anthropic`, put `ANTHROPIC_API_KEY` in `.env`, and skip the rest of this step. For the Azure model:

1. Open [ai.azure.com](https://ai.azure.com), sign in with your student account, and create a project in the region from Step 1.
2. Go to **Models + endpoints → Deploy model → Deploy base model**. Deploy **gpt-5-mini** as **Global Standard**, keeping the deployment name Foundry suggests. It does every step; Azure for Students subscriptions tend to have quota for gpt-5-mini but not gpt-5-nano.
3. **Check the quota before going further** (Foundry → **Quota → Token per minute**). In the deployment's settings, set **Tokens per minute** as high as the slider allows. The script step needs about **40,000 tokens per minute**, because one request asks for up to 32,000 output tokens. Student subscriptions are often limited to 1,000 tokens per minute. If yours is, an Azure model can't write the scripts: stay on Claude, or upgrade the subscription to pay-as-you-go.
4. Open your resource's **Keys and Endpoint** page. Copy the endpoint and Key 1 into `.env`:

   ```bash
   AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
   AZURE_OPENAI_API_KEY=<key 1>
   ```

5. `config/models.yaml` already says `provider: azure_openai` with `strong` and `small` both set to `gpt-5-mini`. If you named the deployment differently, change both to match. If you deployed a model that doesn't reason (gpt-4.1, DeepSeek-V3, Llama), delete the `reasoning_effort` line.
6. Test it on your machine first:

   ```bash
   pipeline doctor                                       # should say: script model provider: azure_openai
   pipeline run --channel whatif --quick --no-stills
   ```

7. Commit and push the `models.yaml` change. The config files are built into the image, so the cloud job only sees the change after the next image build (Step 4).

`ANTHROPIC_API_KEY` can stay empty when you use Azure, and the Azure keys can stay empty when you use Claude.

---

## Step 3: Create the Azure resources

```bash
bash infra/azure/deploy.sh
```

It shows your subscription and region, asks you to confirm, and then creates the following in a resource group named `rg-videopipe`:

| Resource | Name | What it's for |
| --- | --- | --- |
| Storage account and file share | `videopipe<8 characters>`, share `work` | Runs, finished videos, the paid-result cache and the databases |
| Container Registry (Basic) | `videopipe<8 characters>` | Stores the pipeline's Docker image |
| Speech (free F0) | `videopipe-speech` | The narrator's voice. Skipped if `.env` already has `AZURE_SPEECH_KEY` |
| Container Apps environment | `videopipe-env` | Where the job runs, plus a log workspace |

The first time, it stops after creating the registry, because there is no image to run yet. It then offers to save the registry login as GitHub secrets. If you don't have the GitHub CLI, it prints the three values to add yourself under **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**:

- `ACR_NAME`
- `ACR_USERNAME`
- `ACR_PASSWORD`

Only one free Speech resource is allowed per subscription. If you already created one in the setup guide, make sure its key is in `.env` before running the script.

---

## Step 4: Build the image on GitHub

Student subscriptions can't use Azure's own image builder (`az acr build` fails with `TasksOperationsNotAllowed`), so GitHub builds the image instead.

1. Open the repo on GitHub → **Actions → deploy → Run workflow**, keep **smoke test** ticked, and click **Run workflow**. With the GitHub CLI, you can run `gh workflow run deploy.yml` instead.
2. The workflow builds the image and renders a free offline test video inside it, to prove the image works. Then it pushes the image to your registry. It takes about 15 to 25 minutes.

---

## Step 5: Create the job

Run the deploy script again:

```bash
bash infra/azure/deploy.sh
```

This time it finds the image and creates the job `videopipe-job`, with:

- **Size:** 4 vCPU and 8 GiB, the largest size on the free Consumption plan.
- **Storage:** the file share mounted at `/work`.
- **Keys:** read from `.env` and stored as job secrets.
- **Default command:** `run --channel whatif`.

Your keys go straight from `.env` into the job's secrets and are never written into the repo.

---

## Step 6: First cloud runs

Start with a free run. It uses fake providers, so it costs nothing beyond compute:

```bash
bash infra/azure/run.sh run --channel whatif --offline --quick
bash infra/azure/status.sh              # repeat until the status is Succeeded (5–10 minutes)
```

`status.sh` lists recent executions and the run ids on the share. Download the run and play the videos:

```bash
bash infra/azure/download.sh <run_id>   # e.g. 20261114-093012-whatif
explorer.exe downloads                  # WSL: opens the folder in Windows Explorer
```

Then a real, cheap test, followed by a full video:

```bash
bash infra/azure/run.sh run --channel whatif --quick --no-stills
bash infra/azure/run.sh run --channel whatif --no-stills
```

To watch a run's output live, go to **Azure portal → videopipe-job → Execution history**, select the run, then open **Console logs**.

---

## Step 7: Set a budget alert

1. In the portal, open **Cost Management → Budgets → Add**.
2. Scope it to the Azure for Students subscription and set **$10 a month**.
3. Add email alerts at 50%, 80% and 100%.

When the $100 credit is used up, Azure disables the subscription, so nothing is ever charged to you, but everything stops.

---

## Day to day

| To do this | Run |
| --- | --- |
| Make a video | `bash infra/azure/run.sh run --channel whatif` (add `--topic "..." --shape ...` as needed) |
| See progress and run ids | `bash infra/azure/status.sh` |
| Get the files | `bash infra/azure/download.sh <run_id>`, then upload by hand following each `UPLOAD.md` |
| Continue a failed run | `bash infra/azure/run.sh resume <run_id>` |
| Mark it approved or rejected | `bash infra/azure/run.sh approve <run_id>` / `bash infra/azure/run.sh reject <run_id> --reason "..."` |
| Check spend | `bash infra/azure/run.sh costs --channel whatif`, then check the execution's console logs |
| Change a key | Edit `.env`, then `bash infra/azure/deploy.sh` |
| Ship new code or config | Merge to `main`, run the **deploy** workflow, then `bash infra/azure/update-image.sh` |
| Stop everything and all costs | `az group delete -n rg-videopipe` (deletes the videos on the share too, so download them first) |

The cloud keeps its own run history and databases on the file share, separate from runs on your machine. Commands like `approve`, `resume` and `costs` therefore go through `run.sh` when the run happened in the cloud.

---

## Troubleshooting

| What you see | What to do |
| --- | --- |
| `RequestDisallowedByPolicy` or "location not allowed" | The region isn't allowed for your subscription. Do Step 1, `export LOCATION=...`, and run the script again. |
| `TasksOperationsNotAllowed` | Something ran `az acr build`. Build with the GitHub **deploy** workflow instead (Step 4). |
| The deploy workflow fails at "Check the registry secrets" | Add `ACR_NAME`, `ACR_USERNAME` and `ACR_PASSWORD` in GitHub (Step 3). |
| An execution fails at once with an image pull error | The registry login changed. Run `bash infra/azure/deploy.sh` to refresh the job's secret. |
| `Permission denied` under `/work`, or `database is locked` | The share's mount options are missing. In the portal, open the job's **Volumes** and check that the options include `uid=1000` and `nobrl`, then run `deploy.sh` again. |
| `Azure rate limit ... tokens-per-minute` | The model deployment's quota is too low (Step 2.3). Raise it, or switch `llm.provider` back to `anthropic`. |
| `deployment ... was not found` | The names under `llm.azure_openai` in `config/models.yaml` don't match your Foundry deployments. |
| A run says `ready_for_review` but you can't find it | Use the run id from `status.sh`. Cloud runs are only on the share, not in your local `out/`. |
