# Terraform configuration for Azure Cosmos DB Gremlin Graph
terraform {
  required_version = ">= 1.3.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "finbench_rg" {
  name     = "finbench-benchmark-rg"
  location = "East US"
}

resource "azurerm_cosmosdb_account" "finbench_cosmos" {
  name                = "finbench-cosmos-graph"
  location            = azurerm_resource_group.finbench_rg.location
  resource_group_name = azurerm_resource_group.finbench_rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  capabilities {
    name = "EnableGremlin"
  }

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.finbench_rg.location
    failover_priority = 0
  }
}

resource "azurerm_cosmosdb_gremlin_database" "finbench_db" {
  name                = "finbench"
  resource_group_name = azurerm_resource_group.finbench_rg.name
  account_name        = azurerm_cosmosdb_account.finbench_cosmos.name
}

resource "azurerm_cosmosdb_gremlin_graph" "finbench_graph" {
  name                = "graph"
  resource_group_name = azurerm_resource_group.finbench_rg.name
  account_name        = azurerm_cosmosdb_account.finbench_cosmos.name
  database_name       = azurerm_cosmosdb_gremlin_database.finbench_db.name
  partition_key_path  = "/pk"
  throughput          = 10000
}
