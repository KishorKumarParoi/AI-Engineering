# ──────────────────────────────────────────────────────────────
# Nexus-AI: Terraform Azure Module
# ──────────────────────────────────────────────────────────────
# Provisions: ADLS Gen2, Azure Synapse, AKS, ACR
# ──────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

variable "location" {
  type    = string
  default = "Central India"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "enable_gpu" {
  type    = bool
  default = false
}

provider "azurerm" {
  features {}
}

locals {
  prefix = "nexusai${var.environment}"
  tags = {
    Project     = "nexus-ai"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Resource Group ───────────────────────────────────────────
resource "azurerm_resource_group" "nexus" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.tags
}

# ══════════════════════════════════════════════════════════════
# 1. ADLS Gen2 — Lakehouse Storage
# ══════════════════════════════════════════════════════════════
resource "azurerm_storage_account" "lakehouse" {
  name                     = "${local.prefix}lake"
  resource_group_name      = azurerm_resource_group.nexus.name
  location                 = azurerm_resource_group.nexus.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  is_hns_enabled           = true  # Hierarchical namespace for ADLS Gen2
  account_kind             = "StorageV2"

  blob_properties {
    versioning_enabled = true
  }

  tags = local.tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "layers" {
  for_each           = toset(["bronze", "silver", "gold", "ml-artifacts"])
  name               = each.key
  storage_account_id = azurerm_storage_account.lakehouse.id
}

# ══════════════════════════════════════════════════════════════
# 2. Azure Synapse Analytics
# ══════════════════════════════════════════════════════════════
resource "azurerm_synapse_workspace" "nexus" {
  name                                 = "${local.prefix}-synapse"
  resource_group_name                  = azurerm_resource_group.nexus.name
  location                             = azurerm_resource_group.nexus.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.layers["gold"].id
  sql_administrator_login              = "sqladmin"
  sql_administrator_login_password     = "N3xusAI!2024#Secure"

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

resource "azurerm_synapse_sql_pool" "gold" {
  name                 = "gold_analytics"
  synapse_workspace_id = azurerm_synapse_workspace.nexus.id
  sku_name             = "DW100c"
  create_mode          = "Default"
  tags                 = local.tags
}

# ══════════════════════════════════════════════════════════════
# 3. AKS Cluster
# ══════════════════════════════════════════════════════════════
resource "azurerm_kubernetes_cluster" "nexus" {
  name                = "${local.prefix}-aks"
  location            = azurerm_resource_group.nexus.location
  resource_group_name = azurerm_resource_group.nexus.name
  dns_prefix          = local.prefix
  kubernetes_version  = "1.29"

  default_node_pool {
    name                = "standard"
    node_count          = 2
    vm_size             = "Standard_D4s_v3"
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 5
    os_disk_size_gb     = 100
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "calico"
  }

  tags = local.tags
}

resource "azurerm_kubernetes_cluster_node_pool" "gpu" {
  count = var.enable_gpu ? 1 : 0

  name                  = "gpu"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.nexus.id
  vm_size               = "Standard_NC4as_T4_v3"
  node_count            = 0
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = 2
  os_disk_size_gb       = 200

  node_taints = ["nvidia.com/gpu=present:NoSchedule"]

  tags = merge(local.tags, { Pool = "gpu" })
}

# ══════════════════════════════════════════════════════════════
# 4. ACR — Container Registry
# ══════════════════════════════════════════════════════════════
resource "azurerm_container_registry" "nexus" {
  name                = "${local.prefix}acr"
  resource_group_name = azurerm_resource_group.nexus.name
  location            = azurerm_resource_group.nexus.location
  sku                 = "Standard"
  admin_enabled       = true
  tags                = local.tags
}

# ── Outputs ──────────────────────────────────────────────────
output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.nexus.name
}

output "adls_account" {
  value = azurerm_storage_account.lakehouse.name
}

output "synapse_endpoint" {
  value     = azurerm_synapse_workspace.nexus.connectivity_endpoints
  sensitive = true
}

output "acr_login_server" {
  value = azurerm_container_registry.nexus.login_server
}
