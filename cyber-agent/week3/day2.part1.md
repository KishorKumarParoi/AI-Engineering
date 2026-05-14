# Day 2 Part 1: Google Cloud Platform Setup Guide

This guide will walk you through setting up your Google Cloud Platform (GCP) account and preparing it for deploying containerized applications. All instructions work for Windows, Mac, and Linux users.

## Table of Contents
1. [Creating Your GCP Account](#creating-your-gcp-account)
2. [Understanding GCP's Structure](#understanding-gcps-structure)
3. [Creating Your First Project](#creating-your-first-project)
4. [Setting Up Billing](#setting-up-billing)
5. [Setting Up Cost Management](#setting-up-cost-management)
6. [Installing Google Cloud CLI](#installing-google-cloud-cli)
7. [Verifying Your Setup](#verifying-your-setup)

---

## Creating Your GCP Account

### GCP Free Trial
1. Navigate to https://cloud.google.com/free
2. Click **"Get started for free"**
3. Sign in with your Google account (or create one)
4. You'll need to provide:
   - Country
   - Account type (Individual)
   - A credit card (for identity verification - you won't be charged)
   - Phone number for verification
5. You'll receive:
   - $300 credit valid for 90 days
   - Always Free tier services (even after trial ends)
   - No auto-charge after trial ends

> **Note**: Unlike Azure, GCP will NOT automatically charge your card when the trial ends. You must manually upgrade to a paid account.

⚠️ **Important**: After creating your account, you'll be redirected to the Google Cloud Console at https://console.cloud.google.com

---

## Understanding GCP's Structure

Before we create resources, let's understand GCP's hierarchy:

```
Google Account (Your Gmail)
  └── Organization (optional, for businesses)
      └── Billing Account (Your payment method)
          └── Project (e.g., "cyber-analyzer")
              └── Resources (Cloud Run, Artifact Registry, etc.)
```

Think of:
- **Billing Account**: Your payment method (can fund multiple projects)
- **Project**: A container for all your resources (similar to Azure's Resource Group)
- **Resources**: The actual services you create

---

## Creating Your First Project

GCP requires a project to organize resources. Let's create one:

1. In the Google Cloud Console (https://console.cloud.google.com)
2. At the top of the page, click the project dropdown (might say "My First Project")
3. Click **"NEW PROJECT"** in the dialog
4. Fill in the details:
   - **Project name**: `cyber-analyzer`
   - **Organization**: Leave the default value
   - **Location**: Leave the default value
   
   💡 **Note**: GCP will auto-generate a unique Project ID based on your project name (shown in gray text under the name field). Write this down - you'll need it for CLI commands!

5. Click **"CREATE"**
6. Wait about 30 seconds for creation
7. Make sure your new project is selected in the top dropdown

🎉 You've created your first project!

---

## Setting Up Billing

Even with free credits, you need to link your billing account to the project:

1. In the Console, click the **"☰"** menu (top-left)
2. Navigate to **"Billing"**
3. If prompted, link your billing account to the project
4. Verify you see your $300 credit balance

---

## Setting Up Cost Management

Let's set up budget alerts to avoid surprises:

1. In the Console menu **"☰"**, navigate to **"Billing"**
2. Click **"Budgets & alerts"** in the left menu
3. Click **"CREATE BUDGET"**
4. Configure your budget:
   - **Name**: `Monthly Training Budget`
   - **Projects**: Select `cyber-analyzer`
   - Click **"Next"**
5. Set the amount:
   - **Budget type**: Specified amount
   - **Amount**: `$10`
   - **Time period**: Monthly
   - Click **"Next"**
6. Set up alerts:
   - Default thresholds are good (50%, 90%, 100%)
   - Check **"Email alerts to billing admins"**
   - Optionally add your email under "Email recipients"
   - Click **"Finish"**

✅ Now you'll get email alerts before spending too much!

---

## Installing Google Cloud CLI

The gcloud CLI is essential for deployment operations and working with containerized applications.

### Windows Users

Option 1 - Using the installer:
1. Download the installer from: https://cloud.google.com/sdk/docs/install#windows
2. Run the downloaded `GoogleCloudSDKInstaller.exe`
3. Follow the installation wizard (accept all defaults)
4. The installer will automatically open a new command prompt

Option 2 - Using PowerShell (requires admin):
```powershell
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

### Mac Users

Option 1 - Using Homebrew (if you have it):
```bash
brew install --cask google-cloud-sdk
```

Option 2 - Direct install:
```bash
# Download and run the install script
curl https://sdk.cloud.google.com | bash
# Restart your shell
exec -l $SHELL
```

### Linux Users

For most distributions:
```bash
# Download and run the install script
curl https://sdk.cloud.google.com | bash
# Restart your shell
exec -l $SHELL
```

For Ubuntu/Debian with apt:
```bash
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-cli
```

### Initialize gcloud (All Platforms)

1. Open a new terminal/command prompt
2. Run:
```bash
gcloud init
```

3. Follow the prompts:
   - Choose **"Y"** to log in
   - Your browser will open - sign in with your Google account
   - Choose your project (`cyber-analyzer`)
   - Choose a default region when prompted:
     - US: `us-central1` or `us-east1`
     - Europe: `europe-west1` or `europe-north1`
     - Asia: `asia-southeast1` or `asia-northeast1`
   
   💡 **Pro tip**: Remember this region! We'll use it for Cloud Run.

---

## Verifying Your Setup

Let's make sure everything is working:

### Using Google Cloud Console
1. Go to https://console.cloud.google.com
2. Ensure `cyber-analyzer` is selected in the project dropdown
3. Click the **"☰"** menu and go to **"Cloud Run"**
4. You should see an empty list (that's correct!)

### Using gcloud CLI
Run these commands:
```bash
# Show current configuration
gcloud config list

# List available projects
gcloud projects list

# Show current project
gcloud config get-value project

# Test API access
gcloud services list --enabled
```

You should see:
- Your project ID (`cyber-analyzer-xxxxx`)
- Your selected region
- A list of enabled APIs

### Enable Required APIs
Cloud Run needs specific APIs enabled. Run:
```bash
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com
```

This enables:
- Cloud Run API (for deployments)
- Container Registry API (for storing images)
- Cloud Build API (for building containers)

---

## What's Next?

Congratulations! Your GCP account is now ready. You have:
- ✅ A GCP account with $300 in credits
- ✅ A project configured for our application
- ✅ Budget alerts configured
- ✅ gcloud CLI installed and authenticated
- ✅ Required APIs enabled

In the next guide, we'll:
1. Push our Docker image to Artifact Registry
2. Deploy to Cloud Run
3. Configure environment variables securely
4. Set up a custom domain (optional)

---

## Troubleshooting

### "Permission denied" errors
- Make sure you selected the correct project
- Ensure APIs are enabled (see Enable Required APIs section)
- Try: `gcloud auth login` to refresh credentials

### Billing account issues
- Free trial requires a valid credit card
- Billing must be linked to the project
- Check: `gcloud beta billing projects describe cyber-analyzer`

### CLI installation problems
- Windows: Run installer as Administrator
- Mac/Linux: Ensure you have curl installed
- All: Restart your terminal after installation

### Project ID vs Project Name
- Project Name: Human-friendly (e.g., "cyber-analyzer")
- Project ID: Globally unique (e.g., "cyber-analyzer-123456")
- Use Project ID in commands

### Still stuck?
- GCP Console has a **"?"** help button (top-right)
- Cloud Shell (in-browser terminal) is available as backup
- Community support at https://cloud.google.com/community

---

## Cost Saving Tips 💰

1. **Cloud Run charges only when running** - perfect for learning!
2. **Delete unused resources** immediately after labs
3. **Use minimum instances** (we'll set this to 0)
4. **Monitor costs weekly** in the Billing section
5. **Set up budget alerts** (which you just did!)

### Free Tier Highlights
Even after your $300 credit expires, you get:
- Cloud Run: 2 million requests/month free
- Cloud Storage: 5GB free
- Cloud Build: 120 build-minutes/day free

Remember: Unlike Azure Container Apps, Cloud Run can truly scale to zero, meaning zero cost when not in use!

---

## Quick Command Reference

```bash
# Login
gcloud auth login

# Set project
gcloud config set project cyber-analyzer-xxxxx

# List configurations
gcloud config list

# Get help
gcloud help
gcloud run --help

# View costs
gcloud billing accounts list
```

Keep this guide handy - we'll reference these commands in the deployment guide!