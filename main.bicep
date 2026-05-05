param webAppName string 
param location string = 'centralus'

// Create the App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${webAppName}-plan'
  location: location
  kind: 'linux'
  sku: {
    name: 'B1'
  }
  properties: {
    reserved: true
  }
}

// Create the Web App
resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id // This links the app to the plan
    siteConfig: {
      linuxFxVersion: 'DOCKER|yashprojectreg2026.azurecr.io/myapp:latest'
    }
  }
}