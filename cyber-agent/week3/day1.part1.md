# Day 1 Part 1: Azure Setup Guide

This guide will walk you through setting up your Azure account and preparing it for deploying containerized applications. All instructions work for both Windows and Mac users.


## Table of Contents
1. [Creating Your Azure Account](#creating-your-azure-account)
2. [Understanding Azure's Structure](#understanding-azures-structure)
3. [Setting Up Cost Management](#setting-up-cost-management)
4. [Creating Your First Resource Group](#creating-your-first-resource-group)
5. [Installing Azure CLI](#installing-azure-cli)
6. [Verifying Your Setup](#verifying-your-setup)

---

## Creating Your Azure Account

### Azure Free Account
1. Navigate to https://azure.microsoft.com/en-us/free/
2. Click **"Start free"**
3. Sign in with your Microsoft account (or create one)
4. You'll need to provide:
   - A credit card (for identity verification - you won't be charged)
   - Phone number for verification
5. You'll receive:
   - $200 credit for 30 days
   - 12 months of popular free services
   - Always free services

> **Note**: If you have a .edu email address, you may qualify for Azure for Students which provides $100 credit over 12 months without requiring a credit card. Visit https://azure.microsoft.com/en-us/free/students/ for details.

⚠️ **Important**: After creating your account, you'll be redirected to the Azure Portal at https://portal.azure.com

---

## Understanding Azure's Structure

Before we create resources, let's understand Azure's hierarchy:

```
Azure Account (Your Email)
  └── Subscription (e.g., "Azure for Students")
      └── Resource Group (e.g., "cyber-analyzer-rg")
          └── Resources (Container Apps, Registry, etc.)
```

Think of:
- **Subscription**: Your billing boundary (like a credit card)
- **Resource Group**: A folder to organize related resources
- **Resources**: The actual services you create

---

## Setting Up Cost Management

Let's set up a budget alert to avoid surprises:

1. In the Azure Portal (https://portal.azure.com), use the search bar at the top
2. Type **"Cost Management"** and select **"Cost Management + Billing"**
3. In the left menu, click **"Cost Management"**
4. Click **"Budgets"**
5. Click **"+ Add"**
6. Configure your budget:
   - **Name**: `Monthly-Training-Budget`
   - **Reset period**: Monthly
   - **Budget amount**: `10` (keep costs minimal)
   - Click **"Next"**
7. Set up alerts:
   - **Alert conditions**: 
     - 50% of budget → Email alert
     - 80% of budget → Email alert
     - 100% of budget → Email alert
   - Enter your email address
   - Click **"Create"**

✅ Now you'll get email alerts before spending too much!

---

## Creating Your First Resource Group

Resource groups organize your Azure resources. Let's create one:

1. In the Azure Portal, click the **"☰"** menu icon (top-left)
2. Select **"Resource groups"**
3. Click **"+ Create"**
4. Fill in the details:
   - **Subscription**: Select your subscription
   - **Resource group**: `cyber-analyzer-rg`
   - **Region**: Choose one close to you:
     - US: `East US` or `West US 2`
     - Europe: `West Europe` or `North Europe`
     - Asia: `Southeast Asia` or `Japan East`
   
   💡 **Pro tip**: Remember this region! All resources in this group should use the same region for best performance and lowest cost.

5. Click **"Review + create"**
6. Click **"Create"**

🎉 You've created your first resource group!

---

## Installing Azure CLI

The Azure CLI is essential for deployment operations and working with containerized applications.

### Windows Users
1. Download the MSI installer from: https://aka.ms/installazurecliwindows
2. Run the downloaded file and follow the installation wizard
3. Restart any open terminal windows

### Mac Users
Option 1 - Using Homebrew (if you have it):
```bash
brew update && brew install azure-cli
```

Option 2 - Direct install:
1. Download the installer from: https://aka.ms/installazureclimacos
2. Run the downloaded .pkg file
3. Follow the installation wizard

### Verify Installation (Both Platforms)
Open a new terminal/command prompt and run:
```bash
az --version
```

You should see version information. If not, restart your terminal.

### Login to Azure CLI
Now let's connect the CLI to your account:
```bash
az login
```

This will open your browser. Sign in with your Azure account.

---

## Verifying Your Setup

Let's make sure everything is working:

### Using Azure Portal
1. Go to https://portal.azure.com
2. In the search bar, type your resource group name: `cyber-analyzer-rg`
3. Click on it - you should see:
   - Location matches what you selected
   - No resources yet (that's correct!)

### Using Azure CLI
Run these commands:
```bash
# List your subscriptions
az account list --output table

# List your resource groups
az group list --output table
```

You should see your subscription and the `cyber-analyzer-rg` resource group.

---

## What's Next?

Congratulations! Your Azure account is now ready. You have:
- ✅ An Azure account with credits
- ✅ Cost alerts configured
- ✅ A resource group for our project
- ✅ Azure CLI installed and configured

In the next guide, we'll:
1. Create an Azure Container Registry
2. Push our Docker image
3. Deploy to Azure Container Apps
4. Configure environment variables securely

---

## Troubleshooting

### "Subscription not found" errors
- Make sure you're signed into the correct account
- Ensure your account setup is complete
- Try signing out and back in

### Region selection issues
- Some regions may not have all services
- Stick to major regions (US East, West Europe, etc.)
- All resources in a group should use the same region

### CLI installation problems
- Windows: Run installer as Administrator
- Mac: Make sure you have admin permissions
- Both: Restart your terminal after installation

### Still stuck?
- Azure Portal has a **"?"** help button (top-right)
- Live chat support is available for most issues
- Check your school's IT resources - they may have Azure guides

---

## Cost Saving Tips 💰

1. **Always delete resources** when done with labs
2. **Use the smallest tier** for learning (we'll show you how)
3. **Set up budget alerts** (which you just did!)
4. **Check Cost Management weekly** to understand your spending
5. **Use free tiers** whenever available

Remember: Container Apps charges only while running, making it perfect for learning!