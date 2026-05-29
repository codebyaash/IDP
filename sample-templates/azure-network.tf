resource "azurerm_resource_group" "core" {
  name     = "rg-deployforge-dev"
  location = "eastus"
}

resource "azurerm_virtual_network" "core_vnet" {
  name                = "vnet-deployforge-dev"
  location            = "eastus"
  resource_group_name = azurerm_resource_group.core.name
  address_space       = ["10.20.0.0/16"]
}

resource "azurerm_subnet" "app" {
  name                 = "snet-app"
  resource_group_name  = azurerm_resource_group.core.name
  virtual_network_name = azurerm_virtual_network.core_vnet.name
  address_prefixes     = ["10.20.1.0/24"]
}
