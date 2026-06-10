# GitHub Actions Azure CI/CD Setup

This project uses a build-once, deploy-many pipeline:

1. Run tests.
2. Provision Dev and Prod Azure App Services.
3. Build one Docker image tagged with the Git commit SHA.
4. Push that image to Azure Container Registry.
5. Deploy the same image to Dev.
6. Deploy the same image to Prod only from `main`, after GitHub environment approval.

## Azure resources

Create or keep these resources:

- Resource group: `rg-myapp-cicd`
- Azure Container Registry: `yashprojectreg2026`
- Dev App Service: `yash-python-app-dev`
- Prod App Service: `yash-python-app-prod`

The workflow creates the App Services from `main.bicep`, but the ACR must already exist.

## GitHub branches

- `develop`: deploys to Dev only.
- `main`: deploys to Dev, waits for approval, then deploys to Prod.
- Pull requests to `develop` or `main`: run tests only.

## GitHub environments

In GitHub, go to:

`Settings -> Environments`

Create:

- `dev`
- `prod`

For `prod`, add required reviewers so production deployment needs approval.

## GitHub secrets

In GitHub, go to:

`Settings -> Secrets and variables -> Actions`

Add these repository secrets:

- `AZURE_CREDENTIALS`
- `AZURE_SUBSCRIPTION_ID`
- `ACR_USERNAME`
- `ACR_PASSWORD`

`ACR_USERNAME` is usually the ACR name, currently `yashprojectreg2026`.

## Azure login

The workflow uses `AZURE_CREDENTIALS` with `azure/login`.

Create a service principal for the Azure subscription you want to use, grant it permission to the resource group and ACR, then store the JSON output in the GitHub secret named `AZURE_CREDENTIALS`.

Required Azure roles:

- `Contributor` on resource group `rg-myapp-cicd`
- `AcrPush` on ACR `yashprojectreg2026`

Example `AZURE_CREDENTIALS` format:

```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "..."
}
```

## App configuration

The container listens on port `8080`.

`main.bicep` sets:

- `WEBSITES_PORT=8080`
- Docker registry credentials

For real production data, replace SQLite with a managed database such as Azure PostgreSQL. The current SQLite database inside the container is fine for demos, but it is not durable for production.
