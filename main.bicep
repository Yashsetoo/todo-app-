// This line allows GitHub to pass the app name into this file
param webAppName string 

param location string = 'centralus'

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${webAppName}-plan'
  location: location
  kind: 'linux'
  sku: {
    name: 'F1'
  }
  properties: {
    reserved: true
  }
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