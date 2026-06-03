resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-bicep-demo'
  location: 'eastus'
}

resource storage 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: 'stbicepdemo001'
  location: 'eastus'
}
