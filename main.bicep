param webAppName string // The "door" that must be open
param location string = 'centralus'

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${webAppName}-plan'
  location: location
  kind: 'linux'
  // Change the SKU name from F1 to B1
sku: {
  name: 'B1' // Or 'D1' for a cheaper shared tier
}

resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'DOCKER|yashprojectreg2026.azurecr.io/myapp:latest'
    }
  }
}