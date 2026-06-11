# Azure DevOps Environments Setup

Project: **Build Once Deploy Many**  
Organization: **yashjadhav0526**  
Azure resource group: **rg-myapp-cicd**

Create three [Environments](https://dev.azure.com/yashjadhav0526/Build%20Once%20Deploy%20Many/_environments) used by `azure-pipelines.yml`.

---

## 1. Environment: `dev`

| Setting | Value |
|---------|-------|
| Name | `dev` |
| Description | Auto-deploy after CI build |
| Approvals | **None** (deploy immediately) |
| Checks | Optional: branch control (only `develop`) |

### Steps (Portal)

1. **Pipelines → Environments → Create environment**
2. Name: `dev`, Resource: **None**
3. Save — no approvers required

---

## 2. Environment: `uat`

| Setting | Value |
|---------|-------|
| Name | `uat` |
| Description | UAT promotion gate (Dev → UAT) |
| Approvals | **Minimum 1 approver** |
| Checks | Optional: required template, business hours |

### Steps (Portal)

1. Create environment `uat`
2. **⋮ → Approvals and checks → Approvals**
3. Add **at least 1** user or group (e.g. `UAT Approvers`)
4. Enable **Timeout** (e.g. 30 days) and **Instructions**: *"Verify dev smoke tests before promoting image to ACR-UAT."*

---

## 3. Environment: `prod`

| Setting | Value |
|---------|-------|
| Name | `prod` |
| Description | Production promotion gate (UAT → Prod) |
| Approvals | **Minimum 2 approvers** |
| Checks | Deployment window enforced in pipeline (Mon–Fri 09:00–18:00 UTC) |

### Steps (Portal)

1. Create environment `prod`
2. **⋮ → Approvals and checks → Approvals**
3. Add **at least 2** distinct approvers (e.g. `Prod Approvers` group with 2+ members)
4. Optional: add **Invoke Azure Function** or **Business hours** check as a second line of defense

> The pipeline also runs an inline UTC window check in the `Promote_Prod` stage before image promotion.

---

## Service connections to create

| Name | Type | Purpose | RBAC |
|------|------|---------|------|
| `sc-azure-rm` | Azure Resource Manager | `az acr import`, ARM deploy | Contributor on `rg-myapp-cicd` |
| `sc-acr-dev` | Docker Registry | CI push to acr-dev | SP with **AcrPush** on acr-dev |
| `sc-acr-uat` | Docker Registry | UAT pull (if needed) | SP with **AcrPull** on acr-uat |
| `sc-acr-prod` | Docker Registry | Prod pull (if needed) | SP with **AcrPull** on acr-prod |
| `sc-aks-dev` | Kubernetes | Deploy to dev namespace | AKS cluster user / namespace admin |
| `sc-aks-uat` | Kubernetes | Deploy to uat namespace | AKS cluster user / namespace admin |
| `sc-aks-prod` | Kubernetes | Deploy to prod namespace | AKS cluster user / namespace admin |

### Least-privilege service principals (per ACR)

```bash
# Example: create SP for CI (AcrPush on acr-dev only)
az ad sp create-for-rbac --name sp-acr-dev-push --skip-assignment
ACR_ID=$(az acr show -n acr-dev -g rg-myapp-cicd --query id -o tsv)
az role assignment create --assignee <sp-app-id> --role AcrPush --scope $ACR_ID

# Example: create SP for UAT deploy agent (AcrPull on acr-uat only)
az role assignment create --assignee <sp-app-id> --role AcrPull --scope $(az acr show -n acr-uat -g rg-myapp-cicd --query id -o tsv)
```

Store SP client secrets in **Azure Key Vault** and link to variable groups (see `variable-groups.md`).

---

## Branch flow

```
feature/*  →  PR → develop  →  (auto CI/CD)  →  dev
                              ↓ approve (uat)
                              uat
                              ↓ approve (prod, 2 approvers, UTC window)
                              prod (main branch mirrors prod releases)
```

Recommended branch policies on `develop`, `uat`, and `main` — see `infra/branch-policy.json`.

### Block direct pushes to `develop`

1. **Project settings → Repositories → Build Once Deploy Many → Security**
2. For group **Contributors**: set **Contribute** = **Deny** on `develop`
3. Set **Create branch** = **Allow** (for feature branches)
4. All changes merge via PR with build validation (`pipelines/pr-validation.yml`)

---

## Pipeline permissions

1. **Pipelines → azure-pipelines.yml → Edit → ⋮ → Triggers / Settings**
2. Enable **Allow scripts to access the OAuth token** (required for PR deployment summary comment)
3. Authorize variable groups `vg-dev`, `vg-uat`, `vg-prod` when prompted on first run
