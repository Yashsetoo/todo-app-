# Azure DevOps Variable Groups & Key Vault

Create three variable groups under **Pipelines → Library** and link secrets from Azure Key Vault.

Key Vault (recommended): `kv-myapp-cicd` in `rg-myapp-cicd`

---

## Variable group: `vg-dev`

| Variable | Example value | Secret |
|----------|---------------|--------|
| `ACR_DEV_NAME` | `acr-dev` | No |
| `ACR_DEV_LOGIN_SERVER` | `acr-dev.azurecr.io` | No |
| `KUBE_NAMESPACE_DEV` | `dev` | No |
| `APP_NAME_DEV` | `yash-python-app-dev` | No |
| `DEV_HEALTH_URL` | `https://yash-python-app-dev.azurewebsites.net/health` | No |
| `ACR_SOURCE_USERNAME` | *(from Key Vault)* | **Yes** |
| `ACR_SOURCE_PASSWORD` | *(from Key Vault)* | **Yes** |

Used by: **Build** stage (push) and **Deploy_Dev** stage.

---

## Variable group: `vg-uat`

| Variable | Example value | Secret |
|----------|---------------|--------|
| `ACR_UAT_NAME` | `acr-uat` | No |
| `ACR_UAT_LOGIN_SERVER` | `acr-uat.azurecr.io` | No |
| `KUBE_NAMESPACE_UAT` | `uat` | No |
| `APP_NAME_UAT` | `yash-python-app-uat` | No |
| `UAT_HEALTH_URL` | `https://yash-python-app-uat.azurewebsites.net/health` | No |
| `ACR_UAT_USERNAME` | *(from Key Vault)* | **Yes** |
| `ACR_UAT_PASSWORD` | *(from Key Vault)* | **Yes** |

Used by: **Promote_UAT**, **Deploy_UAT** stages.

---

## Variable group: `vg-prod`

| Variable | Example value | Secret |
|----------|---------------|--------|
| `ACR_PROD_NAME` | `acr-prod` | No |
| `ACR_PROD_LOGIN_SERVER` | `acr-prod.azurecr.io` | No |
| `KUBE_NAMESPACE_PROD` | `prod` | No |
| `APP_NAME_PROD` | `yash-python-app-prod` | No |
| `PROD_HEALTH_URL` | `https://yash-python-app-prod.azurewebsites.net/health` | No |

Used by: **Promote_Prod**, **Deploy_Prod** stages.

---

## Key Vault secrets to create

```bash
RG=rg-myapp-cicd
KV=kv-myapp-cicd

az keyvault create -n $KV -g $RG -l centralindia

# ACR-DEV push credentials (CI agent)
az keyvault secret set --vault-name $KV --name acr-dev-username --value "<sp-client-id>"
az keyvault secret set --vault-name $KV --name acr-dev-password --value "<sp-client-secret>"

# ACR-UAT credentials (promotion source for prod stage)
az keyvault secret set --vault-name $KV --name acr-uat-username --value "<sp-client-id>"
az keyvault secret set --vault-name $KV --name acr-uat-password --value "<sp-client-secret>"
```

---

## Link Key Vault to variable groups

1. **Pipelines → Library → + Variable group**
2. Name: `vg-dev`
3. Toggle **Link secrets from an Azure key vault as variables**
4. Azure subscription: select `sc-azure-rm`
5. Key vault: `kv-myapp-cicd`
6. Authorize when prompted
7. Add secrets:
   - `acr-dev-username` → maps to `ACR_SOURCE_USERNAME` (mark secret)
   - `acr-dev-password` → maps to `ACR_SOURCE_PASSWORD` (mark secret)
8. Add non-secret variables from the table above
9. Repeat for `vg-uat` and `vg-prod`

### Map Key Vault secret names

| Key Vault secret | Variable group | Variable name |
|------------------|----------------|---------------|
| `acr-dev-username` | vg-dev | `ACR_SOURCE_USERNAME` |
| `acr-dev-password` | vg-dev | `ACR_SOURCE_PASSWORD` |
| `acr-uat-username` | vg-uat | `ACR_UAT_USERNAME` |
| `acr-uat-password` | vg-uat | `ACR_UAT_PASSWORD` |

---

## Docker Registry service connections

Create under **Project settings → Service connections → New connection → Docker Registry**:

| Connection | Registry URL | Username / password |
|------------|--------------|---------------------|
| `sc-acr-dev` | `https://acr-dev.azurecr.io` | SP with AcrPush |
| `sc-acr-uat` | `https://acr-uat.azurecr.io` | SP with AcrPull |
| `sc-acr-prod` | `https://acr-prod.azurecr.io` | SP with AcrPull |

Grant pipeline access: **⋮ → Security → +** add **Build** service account with **User** role.
