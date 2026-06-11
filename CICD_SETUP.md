# GitHub Actions + Azure CI/CD Setup: Build Once, Deploy Many

**Project:** Task1 Python Application  
**CI/CD Engine:** GitHub Actions  
**Deployment Platform:** Microsoft Azure  
**Pattern:** Build Once, Deploy Many (Dev → Prod)

---

## 📋 Table of Contents

1. [What Changed & Why](#what-changed--why)
2. [Build Once, Deploy Many Pattern](#build-once-deploy-many-pattern)
3. [Your Scenario: Dev-Only, Then Selective Prod](#your-scenario-dev-only-then-selective-prod)
4. [Project Architecture](#project-architecture)
5. [Files Created/Modified](#files-createdmodified)
6. [Setup Instructions](#setup-instructions)
7. [GitHub Configuration](#github-configuration)
8. [Azure Configuration](#azure-configuration)
9. [Your Workflow (Quick Start)](#your-workflow-quick-start)
10. [Viewing Docker Images in ACR](#viewing-docker-images-in-acr)
11. [How It Works](#how-it-works)
12. [Troubleshooting](#troubleshooting)

---

## What Changed & Why

### Problem Solved
Previously, without CI/CD, you had to:
- Build and test manually on your machine
- Deploy manually using Azure CLI commands
- Risk deploying different code to Dev vs Prod
- No automated approval gates for production

### Solution Implemented
Now you have:
- **Automated testing** on every push
- **Single Docker image** built once, deployed to both Dev and Prod
- **Automatic deployment** to Dev after passing tests
- **Approval gate** for Prod (must merge to `main` and approve)
- **Infrastructure as Code** (Bicep) provisions both environments
- **Immutable artifacts** - same image tag runs everywhere

### What Was Created/Changed

| File | Status | Why Changed |
|------|--------|------------|
| `.github/workflows/cicd.yml` | ✅ Created | GitHub Actions workflow for build-test-deploy |
| `.github/workflows/manual-deploy-prod.yml` | ✅ Created | Manual trigger to deploy any image to Prod |
| `Dockerfile` | ✅ Created | Package Python app as container for Azure App Service |
| `.dockerignore` | ✅ Created | Prevent unnecessary files from Docker build |
| `main.bicep` | ✅ Modified | Infrastructure as Code for Dev & Prod App Services |
| `CICD_SETUP.md` | ✅ Modified | This documentation |

---

## Build Once, Deploy Many Pattern

### The Core Principle
```
Code Commit
    ↓
Run Tests
    ↓
Build ONE Docker Image (tag: git-commit-sha)
    ↓
Push Image to Azure Container Registry
    ↓
Deploy SAME Image to Dev Environment
    ↓
[If on main branch]
Manual Approval Gate (GitHub Environment)
    ↓
Deploy SAME Image to Prod Environment
```

### Why This Matters

**❌ The Wrong Way (Build Many):**
```
Build for Dev → Deploy to Dev
Build for Prod → Deploy to Prod  ← Different code! Risk!
```

**✅ The Right Way (Build Once):**
```
Build Once (tag: abc123def456)
    ↓
Deploy image tag abc123def456 to Dev  ← EXACT same code
Deploy image tag abc123def456 to Prod ← EXACT same code
```

### Key Benefits
1. **Consistency**: Dev and Prod run identical Docker images
2. **Traceability**: Every image is tagged with the Git commit SHA
3. **Rollback**: Roll back Prod by redeploying a previous image tag
4. **Approval**: Only Prod deployments need manual approval
5. **Speed**: Dev gets auto-deployed, Prod requires approval

---

## Your Scenario: Dev-Only, Then Selective Prod

### The Workflow You Want

```
Day 1:  Push to develop → Image built & deployed to Dev only
Day 2:  Push to develop → Different image → Deploy to Dev
Day 3:  Push to develop → Different image → Deploy to Dev
        ↓
After testing for 2-3 days, decide which image is stable
        ↓
Deploy that SAME image to Prod (with approval, no rebuild)
```

### How It Works

**Pushing to `develop`:**
```bash
git add .
git commit -m "Day 1 updates"
git push origin develop
```

**Result:**
- ✅ Tests run
- ✅ Docker image built (tagged with commit SHA)
- ✅ Image pushed to Azure Container Registry (ACR)
- ✅ **Deployed to Dev automatically**
- ❌ **Prod not touched**

**Repeat daily:**
- Day 1: Image `abc123def456` → Dev
- Day 2: Image `def456abc123` → Dev (replaces Day 1)
- Day 3: Image `ghi789def456` → Dev (replaces Day 2)

**All 3 images stored in ACR permanently.**

---

### After 2-3 Days: Deploy to Prod

When you're ready to deploy an image to Prod, you have two options:

#### Option 1: Manual Deployment (Recommended for Your Scenario)

**Step 1:** Get the image tag from Day 1

```bash
# View all images in ACR
az acr repository show-manifests \
  --name yashprojectreg2026 \
  --repository myapp \
  --orderby time_desc

# Output shows tags like: abc123def456, def456abc123, ghi789def456
```

**Step 2:** Trigger manual deployment in GitHub

1. Go to GitHub repo → **Actions**
2. Select workflow: **Manual Deploy to Prod**
3. Click **Run workflow**
4. Enter image tag: `abc123def456` (from Day 1)
5. Click **Run workflow** button

**Step 3:** Approve deployment

1. GitHub Actions will pause and wait for approval
2. Go to Actions → Latest run
3. Click **Review deployments**
4. Select `prod` environment
5. Click **Approve and deploy**

**Result:** ✅ Prod now running `abc123def456` (exact same image as Day 1 in Dev)

---

#### Option 2: Git Tag (Automatic Trigger)

If you prefer automatic triggering:

```bash
# Tag the Day 1 commit
git tag v1.0.0 abc123def456
git push origin v1.0.0
```

GitHub Actions will automatically:
1. Detect tag `v1.0.0`
2. Find image `abc123def456` in ACR
3. Deploy to Prod with approval

---

### Key Difference from Auto-Deployment

| Scenario | Trigger | Prod Deploy |
|----------|---------|------------|
| Push to `develop` | Automatic | ❌ No |
| Push to `main` | Automatic | ✅ Yes + Approval |
| Manual workflow dispatch | Manual button | ✅ Yes + Approval |
| Git tag `v*.*.*` | Automatic tag | ✅ Yes + Approval |

**For your use case:** Use **Manual Deploy** or **Git Tags** to deploy 2-3 days later.

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Repository                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  develop branch  →  GitHub Actions triggers on push     │  │
│  │  main branch     →  GitHub Actions triggers on push     │  │
│  │  Pull Requests   →  GitHub Actions runs tests only      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                   .github/workflows/cicd.yml
                         (Workflow Engine)
                              ↓
        ┌─────────────────────┬────────────────────┐
        ↓                     ↓                    ↓
    [TEST]           [BUILD ONCE]         [DEPLOY]
    Python tests    Docker image build     Dev env
    (pytest)         + Push to ACR         Prod env
```

### Azure Resources Deployed

```
Resource Group: rg-myapp-cicd
│
├── Azure Container Registry (ACR): yashprojectreg2026
│   └── Docker Image: myapp:abc123def456 (commit SHA)
│       └── Latest tag: myapp:latest
│
├── Dev Environment
│   ├── App Service Plan: yash-python-app-dev-plan
│   └── Web App: yash-python-app-dev
│       └── Running: myapp:abc123def456
│
└── Prod Environment
    ├── App Service Plan: yash-python-app-prod-plan
    └── Web App: yash-python-app-prod
        └── Running: myapp:abc123def456 (after approval)
```

---

## Files Created/Modified

### 1. `.github/workflows/cicd.yml` (NEW)
**Purpose:** GitHub Actions workflow that orchestrates build and deploy

**What it does:**
- **Job: test** - Runs pytest on every push/PR
- **Job: build** - Builds Docker image once, pushes to ACR
- **Job: deploy-dev** - Deploys same image to Dev via Bicep
- **Job: deploy-prod** - Deploys same image to Prod via Bicep (main branch + approval only)

**Key Features:**
```yaml
- Only builds if: Not a pull request (skip for PRs)
- Image tag: GitHub SHA (abc123def456) → ensures traceability
- Deploy Dev: Always (after build succeeds)
- Deploy Prod: Only if on 'main' branch AND deploy-dev succeeds
- Prod approval: Controlled by GitHub Environment settings
```

**Behavior:**
- `push to develop` → test → build → deploy Dev ✅ (Prod: ❌ No)
- `push to main` → test → build → deploy Dev ✅ → deploy Prod ✅ (+ approval)
- `pull request` → test only ✅ (no build/deploy)

### 2. `.github/workflows/manual-deploy-prod.yml` (NEW) ⭐
**Purpose:** Manually deploy ANY image from ACR to Prod (your scenario!)

**What it does:**
- Lets you select any image tag to deploy
- Triggers when you click "Run workflow" in GitHub
- Requires image tag as input (e.g., `abc123def456`)
- Deploys to Prod with approval gate

**Usage (Your Scenario):**
```bash
# Day 1: Push to develop
git push origin develop
# Result: Image abc123def456 built and deployed to Dev

# Day 3: Decide abc123def456 is stable for Prod
# Go to GitHub Actions → Manual Deploy to Prod → Run workflow
# Enter: abc123def456
# Click Approve when prompted
# Result: Prod now runs abc123def456 (SAME image, no rebuild)
```

### 3. `Dockerfile` (NEW)
**Purpose:** Package Python app as Docker container

**What it does:**
```dockerfile
FROM python:3.11-slim           # Base image
WORKDIR /app                    # Container working dir
COPY requirements.txt .         # Copy dependencies
RUN pip install -r req.txt      # Install Python packages
COPY . .                        # Copy app code
EXPOSE 8080                     # Listen on port 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]  # Run Flask app
```

**Why gunicorn?**
- Production-grade WSGI server
- Handles concurrent requests
- Better than Flask's development server

### 4. `.dockerignore` (NEW)
**Purpose:** Exclude unnecessary files from Docker build

**Excluded:**
- `__pycache__/` - Python bytecode
- `.git/` - Git history (already in image? No)
- `.env` - Secrets (use Azure Key Vault instead)
- `venv/`, `.venv/` - Virtual environments (pip installs fresh)
- `.pytest_cache/` - Test artifacts
- `graphify-out/` - Code analysis (development only)

**Result:** Smaller, faster Docker builds

### 4. `main.bicep` (MODIFIED)
**Purpose:** Infrastructure as Code to provision App Services

**What changed:**
- **Before:** Hard-coded to one app (prod only)
- **After:** Reusable template for Dev and Prod

**Template Parameters:**
```bicep
param webAppName string          # "yash-python-app-dev" or "-prod"
param imageName string           # "myapp"
param imageTag string            # Git commit SHA
param acrLoginServer string      # Registry URL
param acrUsername string         # ACR credentials
param acrPassword string         # ACR credentials
```

**What it creates:**
- App Service Plan (Linux, B1 tier)
- Web App for Containers
- App Settings: port 8080, ACR credentials

### 5. `requirements.txt` (UNCHANGED)
**Purpose:** Python dependencies

Your existing dependencies remain the same. These are installed in the Docker build:
```
pip install -r requirements.txt
```

### 6. `app.py` (UNCHANGED)
**Purpose:** Flask application entry point

The workflow starts your app via:
```bash
gunicorn --bind 0.0.0.0:8080 app:app
```

---

## Setup Instructions

### Phase 1: Azure Setup (One-Time)

#### Step 1: Create Azure Container Registry

```bash
az group create --name rg-myapp-cicd --location centralindia

az acr create \
  --resource-group rg-myapp-cicd \
  --name yashprojectreg2026 \
  --sku Basic
```

#### Step 2: Create Service Principal for GitHub

```bash
az ad sp create-for-rbac \
  --name "github-actions-task1" \
  --role Contributor \
  --scopes /subscriptions/{SUBSCRIPTION_ID}/resourceGroups/rg-myapp-cicd

# Also grant AcrPush:
az role assignment create \
  --assignee {CLIENT_ID} \
  --role AcrPush \
  --scope /subscriptions/{SUBSCRIPTION_ID}/resourceGroups/rg-myapp-cicd/providers/Microsoft.ContainerRegistry/registries/yashprojectreg2026
```

Copy the JSON output (you'll need it in GitHub).

#### Step 3: Get ACR Credentials

```bash
az acr credential show \
  --name yashprojectreg2026 \
  --resource-group rg-myapp-cicd
```

Save the username and password.

---

### Phase 2: GitHub Configuration

#### Step 1: Create GitHub Branches

```bash
git checkout develop
git checkout -b main
git branch -D master  # Delete old master if exists
git push origin develop main
```

Your repository should now have:
- `develop` branch (default for dev deployments)
- `main` branch (for prod deployments)

#### Step 2: Create GitHub Environments

In your GitHub repository:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Create `dev` (no approval needed)
4. Create `prod` (add approval)

For `prod` environment:
- Click **Add rule** under "Deployment branches"
- Select `Protect with required reviewers`
- Add yourself (or team members) as required reviewers

#### Step 3: Add GitHub Actions Secrets

In your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `AZURE_CREDENTIALS` | JSON from Step 2 above |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |
| `ACR_USERNAME` | `yashprojectreg2026` (or your ACR name) |
| `ACR_PASSWORD` | From Step 3 above |

Example `AZURE_CREDENTIALS` JSON:
```json
{
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "your-secret-here",
  "subscriptionId": "87654321-4321-4321-4321-210987654321",
  "tenantId": "abcdef12-abcd-abcd-abcd-abcdefabcdef"
}
```

---

### Phase 3: Testing the Pipeline

#### Step 1: Create Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/test-cicd
```

#### Step 2: Make a Small Change

Edit `app.py` (add a comment or change the page title).

```bash
git add .
git commit -m "Test CI/CD pipeline"
git push origin feature/test-cicd
```

#### Step 3: Create Pull Request

- Go to GitHub → Create Pull Request to `develop`
- Workflow runs **tests only** (no build/deploy on PR)
- Check **Actions** tab to see test results

#### Step 4: Merge to Develop

```bash
git checkout develop
git pull origin develop
git merge feature/test-cicd
git push origin develop
```

**GitHub Actions now:**
1. Runs tests ✅
2. Builds Docker image (tag: `abc123def456`) ✅
3. Pushes to ACR ✅
4. Deploys to `yash-python-app-dev` ✅

**Check deployment:**
```bash
az webapp config container show \
  --name yash-python-app-dev \
  --resource-group rg-myapp-cicd
```

#### Step 5: Merge to Main

```bash
git checkout main
git pull origin main
git merge develop
git push origin main
```

**GitHub Actions now:**
1. Runs tests ✅
2. Builds Docker image (same tag as before) ✅
3. Pushes to ACR ✅
4. Deploys to `yash-python-app-dev` ✅
5. **Waits for approval** ⏸️

**In GitHub:**
- Go to **Actions** → Latest workflow run
- Click **Review deployments**
- Approve for `prod` environment

**After approval:**
- Deploys same image to `yash-python-app-prod` ✅

---

## GitHub Configuration

### Branch Protection Rules (Recommended)

For safety, enable branch protection on `main`:

1. Go to **Settings** → **Branches** → **Branch protection rules**
2. Add rule for `main`
3. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging

This ensures:
- All changes go through a PR
- All tests must pass before merge
- CI/CD cannot run on `main` directly

### Secret Management

**Secrets are encrypted by GitHub and:**
- Never logged in workflow output
- Not visible in GitHub UI after creation
- Securely passed to runners as environment variables
- Automatically rotated is best practice (every 90 days)

---

## Azure Configuration

### App Service Configuration

#### Development App Service: `yash-python-app-dev`

After first deployment, configure:

```bash
az webapp config appsettings set \
  --name yash-python-app-dev \
  --resource-group rg-myapp-cicd \
  --settings \
    WEBSITES_PORT=8080 \
    APP_ENV=dev
```

#### Production App Service: `yash-python-app-prod`

```bash
az webapp config appsettings set \
  --name yash-python-app-prod \
  --resource-group rg-myapp-cicd \
  --settings \
    WEBSITES_PORT=8080 \
    APP_ENV=prod
```

### Database Configuration

**Current Setup:**
- SQLite database inside Docker container
- Works for dev/demo
- Data lost when container restarts ⚠️

**For Production:**
Replace with Azure PostgreSQL:

```bash
az postgres server create \
  --resource-group rg-myapp-cicd \
  --name myapp-db-prod \
  --location centralindia \
  --admin-user dbadmin \
  --admin-password "SecurePassword123!"
```

Then update `app.py` connection string:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@server.postgres.database.azure.com/dbname")
```

And add secret in GitHub: `DATABASE_URL_DEV`, `DATABASE_URL_PROD`

---

## Your Workflow (Quick Start)

### Day 1-3: Daily Development
```bash
git add .
git commit -m "Day 1 changes"
git push origin develop
# ✅ Automatically: Test → Build → Deploy to Dev
# ❌ Prod: Not touched
```

### Day 4: Deploy to Prod
```bash
# Option A: Manual (GitHub UI)
# Go to GitHub Actions → Manual Deploy to Prod → Run workflow
# Input image tag: abc123def456
# Click "Approve and deploy"
# ✅ Prod running abc123def456 (SAME image as Day 1, no rebuild)

# Option B: Git Tag (Automatic)
git tag v1.0.0 abc123def456
git push origin v1.0.0
# ✅ Automatically triggers Prod deployment with approval
```

**That's it! Your workflow is:**
1. **Develop branch** = Auto-deploy daily to Dev
2. **Manual trigger** = Deploy any Dev image to Prod (2-3 days later)
3. **No rebuilds** = Same image, every time

---

## Viewing Docker Images in ACR

When using the **"Manual Deploy to Prod"** workflow, you need to know which image tags are available. Here's how to view all your Docker images:

### Method 1: Azure Portal (Easiest) 🖥️

1. Go to **[Azure Portal](https://portal.azure.com)**
2. Search for **"Container Registries"**
3. Click **yashprojectreg2026**
4. In the left menu, click **Repositories**
5. Click **myapp**
6. You'll see all available image tags:

```
Repositories
└─ myapp
   ├─ bcd87dd      ← Latest (from your recent push)
   ├─ abc123d      ← From 2 days ago
   ├─ def456g      ← From 5 days ago
   └─ ...
```

Each tag is the **Git commit SHA** (short form).

**To deploy this image:**
- Copy the tag (e.g., `bcd87dd`)
- Go to GitHub → Actions → Manual Deploy to Prod
- Click "Run workflow" → Enter tag → Run workflow

---

### Method 2: Azure CLI

**View all images ordered by most recent:**

```bash
az acr repository show-manifests \
  --name yashprojectreg2026 \
  --repository myapp \
  --orderby time_desc \
  --top 10
```

**Output:**
```json
[
  {
    "digest": "sha256:abc123...",
    "tags": ["bcd87dd"],              ← Use this tag!
    "timestamp": "2026-06-10T15:30Z"
  },
  {
    "digest": "sha256:def456...",
    "tags": ["abc123d"],              ← Or this tag
    "timestamp": "2026-06-10T10:15Z"
  }
]
```

---

### Method 3: GitHub Actions (Workflow Output)

After each build, GitHub logs show the image:

1. Go to **GitHub** → **Actions** tab
2. Click **"Build Once Deploy Many"** workflow
3. Click the latest successful run
4. Click **build** job
5. Expand **"Deploy image to Prod"** step (or similar)
6. Look for log output like:

```
Docker image pushed:
yashprojectreg2026.azurecr.io/myapp:bcd87dd
```

The tag after the colon (`:bcd87dd`) is what you use in Manual Deploy.

---

### How Image Tags Work

Each time you push to `develop` or `main`:

```
Commit SHA: bcd87ddabc123def456789abcdef123456789abc
                ↓ (Short form - 7 characters)
Image tag: bcd87dd
```

So:
- **Day 1 push** → Image tag: `bcd87dd`
- **Day 2 push** → Image tag: `abc123d`
- **Day 3 push** → Image tag: `def456g`

Each is a **complete, immutable Docker image** stored in ACR.

---

### Example: Deploy Day 1 Image on Day 4

**Day 1:**
```bash
git push origin develop
# Image bcd87dd built and deployed to Dev
```

**Day 4:**
```
GitHub UI:
Actions → Manual Deploy to Prod → Run workflow
Input: bcd87dd
Click: Run workflow
Click: Approve when prompted
Result: Prod now runs bcd87dd (SAME image, no rebuild!)
```

---

### Cleanup (Optional)

**If ACR is full, delete old images:**

```bash
# Delete a specific image tag
az acr repository delete \
  --name yashprojectreg2026 \
  --image myapp:bcd87dd

# Or keep only the last 10 images
# (Requires Premium tier for retention policy)
```

For now, keep all images - they're cheap storage! 📦

---

## How It Works

### Workflow: Push to `develop`

```
Developer runs:
  git push origin develop
                    ↓
GitHub detects push to 'develop' branch
                    ↓
Workflow file: .github/workflows/cicd.yml is triggered
                    ↓
┌──────────────────── JOB 1: TEST ─────────────────────┐
│ - Checkout code                                      │
│ - Setup Python 3.11                                  │
│ - Install requirements.txt                           │
│ - Run: pytest tests/ -v                              │
│ Status: ✅ PASS or ❌ FAIL                            │
└────────────────────────────────────────────────────┘
                    ↓
(If tests PASS, continue; if FAIL, stop)
                    ↓
┌──────────────────── JOB 2: BUILD ────────────────────┐
│ Condition: github.event_name != 'pull_request'       │
│ (Skip if this is a PR)                               │
│                                                      │
│ - Set image tag: {ACR_URL}/myapp:{GITHUB_SHA}        │
│ - Login to Azure                                     │
│ - Login to ACR                                       │
│ - Build Docker image                                 │
│ - Push to ACR with two tags:                         │
│   • myapp:abc123def456  (commit SHA)                 │
│   • myapp:latest       (latest)                      │
│ Output: image-uri = (for next jobs)                  │
└────────────────────────────────────────────────────┘
                    ↓
┌──────────────────── JOB 3: DEPLOY-DEV ───────────────┐
│ Needs: build, test                                   │
│ Environment: dev (no approval required)              │
│                                                      │
│ - Login to Azure                                     │
│ - Deploy via Bicep:                                  │
│   • Resource Group: rg-myapp-cicd                    │
│   • Template: main.bicep                             │
│   • Parameters:                                      │
│     - webAppName: yash-python-app-dev                │
│     - imageName: myapp                               │
│     - imageTag: abc123def456                         │
│   • Creates App Service Plan (if not exists)         │
│   • Creates Web App (if not exists)                  │
│   • Updates Web App to run Docker image              │
│                                                      │
│ Status: ✅ Deployed to Dev                            │
└────────────────────────────────────────────────────┘
                    ↓
           ✅ PIPELINE COMPLETE
        App running at: yash-python-app-dev
```

### Workflow: Push to `main`

```
Developer runs:
  git merge develop
  git push origin main
                    ↓
GitHub detects push to 'main' branch
                    ↓
.github/workflows/cicd.yml is triggered
                    ↓
┌──────────────────── JOB 1: TEST ─────────────────────┐
│ (Same as develop)                                    │
│ Status: ✅ PASS or ❌ FAIL                            │
└────────────────────────────────────────────────────┘
                    ↓
┌──────────────────── JOB 2: BUILD ────────────────────┐
│ (Same as develop)                                    │
│ Status: ✅ Docker image pushed to ACR                 │
└────────────────────────────────────────────────────┘
                    ↓
┌──────────────────── JOB 3: DEPLOY-DEV ───────────────┐
│ (Same as develop)                                    │
│ Status: ✅ Deployed to Dev                            │
└────────────────────────────────────────────────────┘
                    ↓
┌──────────────────── JOB 4: DEPLOY-PROD ──────────────┐
│ Needs: build, deploy-dev                             │
│ Environment: prod (APPROVAL REQUIRED)                │
│ Condition: github.ref == 'refs/heads/main'           │
│                                                      │
│ ⏸️ WORKFLOW PAUSED HERE                               │
│ Waiting for approval from required reviewers...      │
│                                                      │
│ Steps to approve:                                    │
│ 1. Go to GitHub → Actions → Latest run               │
│ 2. Click "Review deployments"                        │
│ 3. Select "prod" environment                         │
│ 4. Click "Approve and deploy"                        │
│                                                      │
│ After approval:                                      │
│ - Deploy via Bicep (same image as Dev!):             │
│   • webAppName: yash-python-app-prod                 │
│   • imageTag: abc123def456 (SAME as Dev)             │
│ Status: ✅ Deployed to Prod                           │
└────────────────────────────────────────────────────┘
                    ↓
    ✅ PIPELINE COMPLETE (Both Dev & Prod)
 Dev:  yash-python-app-dev running myapp:abc123def456
 Prod: yash-python-app-prod running myapp:abc123def456
```

### Workflow: Manual Deploy to Prod (Your Scenario!) ⭐

**This is for your use case: Deploy Dev image to Prod 2-3 days later**

```
Day 1: git push origin develop
       ↓
       Image abc123def456 built and deployed to Dev ✅
       Prod: (empty)

Day 2: git push origin develop
       ↓
       Image def456abc123 built and deployed to Dev ✅
       Prod: (empty)

Day 3: git push origin develop
       ↓
       Image ghi789def456 built and deployed to Dev ✅
       Prod: (still empty)

Day 4 (Decision time): "Day 1's image (abc123def456) is stable!"
       ↓
       GitHub Actions → Manual Deploy to Prod → Run workflow
       Input image tag: abc123def456
       ↓
┌─────────────────── MANUAL WORKFLOW ────────────────┐
│ Condition: Triggered manually via workflow_dispatch │
│ Environment: prod (APPROVAL REQUIRED)               │
│                                                     │
│ ⏸️ WORKFLOW PAUSED HERE                              │
│ Waiting for approval...                             │
│                                                     │
│ To approve:                                         │
│ 1. GitHub → Actions → Manual Deploy to Prod run     │
│ 2. Click "Review deployments"                       │
│ 3. Select "prod"                                    │
│ 4. Click "Approve and deploy"                       │
│                                                     │
│ After approval:                                     │
│ - Deploy image abc123def456 to Prod                 │
│ - NO rebuild! Uses image from Day 1                 │
│ - Status: ✅ Deployed to Prod                        │
└─────────────────────────────────────────────────────┘
       ↓
    ✅ COMPLETE
 Dev:  yash-python-app-dev running myapp:ghi789def456 (latest)
 Prod: yash-python-app-prod running myapp:abc123def456 (Day 1)
```

**Perfect for your scenario:**
- Dev always runs the latest image
- Prod runs a specific stable image
- Deploy to Prod any time (2 days, 2 weeks, 2 months later)
- Same image, no rebuild, full approval control

### Image Promotion Flow (Build Once, Deploy Many)

```
GitHub Commit #123
└─ Triggered workflow
   └─ Tests pass
      └─ Build Docker image once
         └─ Tag: yashprojectreg2026.azurecr.io/myapp:abc123def456
            └─ Push to ACR
               ├─ Deploy to Dev
               │  └─ App Service loads image abc123def456
               │     └─ Container runs, users access it
               └─ [If main branch + approval]
                  └─ Deploy to Prod
                     └─ Same image abc123def456
                        └─ Prod container runs identical code
```

**The key:** Both environments run the **exact same Docker image**. Only the environment variables (like `APP_ENV=dev` vs `APP_ENV=prod`) differ.

---

## Troubleshooting

### Issue: Workflow Fails at "Build and push Docker image"

**Error:** `denied: access denied`

**Solution:**
- Check `ACR_USERNAME` and `ACR_PASSWORD` secrets exist
- Verify credentials have `AcrPush` role
- Ensure ACR name is correct: `yashprojectreg2026`

### Issue: Deployment Fails "No image found"

**Error:** `docker pull failed`

**Solution:**
- Verify image was pushed to ACR successfully (check Actions logs)
- Confirm ACR credentials in App Service settings
- Check App Service can reach ACR (network rules)

### Issue: App crashes in Dev/Prod

**Error:** `Container didn't respond to HTTP pings on port 8080`

**Solution:**
- Check `WEBSITES_PORT=8080` in App Service settings
- Verify Flask app listens on 0.0.0.0:8080 (not localhost)
- Check `requirements.txt` has `gunicorn`
- View logs: `az webapp log tail --name yash-python-app-dev --resource-group rg-myapp-cicd`

### Issue: "Approval gate not showing"

**Error:** Workflow doesn't wait for approval, goes straight to Prod

**Solution:**
- Verify GitHub environment `prod` exists
- Check `prod` environment has "Required reviewers" enabled
- Ensure workflow push is to `main` branch, not `develop`

### Issue: Different code in Dev vs Prod

**This should never happen** if using build-once pattern.

**Verify:**
```bash
# Both should have same image tag
az webapp config container show --name yash-python-app-dev --resource-group rg-myapp-cicd
az webapp config container show --name yash-python-app-prod --resource-group rg-myapp-cicd

# Check image SHA in ACR
az acr repository show-manifests --name yashprojectreg2026 --repository myapp --top 5
```

---

## Monitoring & Logs

### View Workflow Execution

```bash
# GitHub Actions logs (in UI)
https://github.com/YOUR_ORG/YOUR_REPO/actions
```

### View App Logs

```bash
# Dev app logs
az webapp log tail \
  --name yash-python-app-dev \
  --resource-group rg-myapp-cicd

# Prod app logs
az webapp log tail \
  --name yash-python-app-prod \
  --resource-group rg-myapp-cicd
```

### View Container Logs

```bash
# Container runtime logs
az webapp log download \
  --name yash-python-app-dev \
  --resource-group rg-myapp-cicd \
  --log-file container.zip
```

---

## Security Best Practices

### ✅ What We Implemented

1. **No secrets in code**: All secrets in GitHub encrypted
2. **Service Principal**: Least privilege (Contributor on RG, AcrPush on ACR)
3. **Immutable images**: Tagged with commit SHA (can't be overwritten)
4. **Approval gates**: Prod requires human approval
5. **Branch protection**: Main is protected (PRs required)
6. **ACR behind VNet**: (Optional advanced setup)

### ⚠️ What Still Needs Attention

1. **Database credentials**: Use Azure Key Vault or managed identity
2. **API keys**: Never commit to repo; use secrets
3. **Secrets rotation**: Rotate service principal annually
4. **Access control**: Limit who can approve Prod deployments
5. **Audit logs**: Monitor Azure Activity Log for deployments

---

## Next Steps

### For Production Hardening

1. **Enable Azure Key Vault**
   - Store DB passwords, API keys
   - Grant App Service managed identity access

2. **Add Application Insights**
   - Monitor app performance
   - Alert on errors

3. **Add HTTPS/SSL**
   - Azure App Service → TLS/SSL certificates
   - Redirect HTTP to HTTPS

4. **Enable Azure DevOps/GitHub advanced security**
   - Code scanning (SAST)
   - Dependency scanning (DAST)

5. **Setup alerting**
   - Failed deployments
   - App crashes
   - High CPU/memory usage

---

## Summary

You now have:
- ✅ Automated testing with pytest
- ✅ Single Docker build per commit
- ✅ Image promotion to Dev (auto)
- ✅ Image promotion to Prod (approval-gated)
- ✅ Infrastructure as Code (Bicep)
- ✅ Dev and Prod environments with same code
- ✅ Deployment history tracked in Git

**Total time from code push to Prod:** ~5-10 minutes (including approval)

**Questions?** Check logs in GitHub Actions or Azure Portal.
