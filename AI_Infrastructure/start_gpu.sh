#!/usr/bin/env bash
# ==============================================================================
# Script: start_gpu.sh
# Purpose: Start or create a GPU workstation on GCP with NVIDIA L4.
# Philosophy: "If already existing/installed, skip; if not, only then install/create"
# ==============================================================================

set -eo pipefail

VM_NAME="${1:-ai-lab-l4}"
SUCCESS=0

# Candidate zones for NVIDIA L4
ZONES=(
  "us-central1-a"
  "us-central1-b"
  "us-central1-c"
  "us-east4-a"
  "us-east4-b"
  "us-east1-c"
  "us-west1-a"
)

echo "=========================================================================="
echo "🔍 Checking if VM '$VM_NAME' already exists..."
echo "=========================================================================="

EXISTING_INFO=$(gcloud compute instances list --filter="name=$VM_NAME" --format="value(name,zone,status)" 2>/dev/null | head -n 1)

if [ -n "$EXISTING_INFO" ]; then
  read -r EXISTING_NAME EXISTING_ZONE EXISTING_STATUS <<< "$EXISTING_INFO"
  ZONE="$EXISTING_ZONE"
  echo "ℹ️ Found existing VM '$EXISTING_NAME' in zone '$ZONE' (Status: $EXISTING_STATUS)."

  if [ "$EXISTING_STATUS" == "TERMINATED" ] || [ "$EXISTING_STATUS" == "STOPPED" ]; then
    echo "▶ Starting existing VM '$VM_NAME' in zone '$ZONE'..."
    gcloud compute instances start "$VM_NAME" --zone="$ZONE"
  else
    echo "✅ VM '$VM_NAME' is already RUNNING. Skipping VM creation."
  fi
  SUCCESS=1
else
  echo "No existing instance named '$VM_NAME' found. Creating new GPU instance..."

  for TRY_ZONE in "${ZONES[@]}"; do
    echo ""
    echo "=========================================================================="
    echo "🔄 [1/4] Trying zone: $TRY_ZONE (Ubuntu 24.04 LTS | 4 vCPU | 16 GB | L4 24GB)"
    echo "=========================================================================="

    if gcloud compute instances create "$VM_NAME" \
        --zone="$TRY_ZONE" \
        --machine-type=g2-standard-4 \
        --maintenance-policy=TERMINATE \
        --boot-disk-size=100GB \
        --boot-disk-type=pd-balanced \
        --image-family=ubuntu-2404-lts-amd64 \
        --image-project=ubuntu-os-cloud; then

      ZONE="$TRY_ZONE"
      SUCCESS=1
      echo ""
      echo "✅ VM created in $ZONE! Waiting 30s for Ubuntu 24.04 to boot..."
      sleep 30
      break
    else
      echo "⚠️ $TRY_ZONE unavailable. Trying next candidate zone..."
    fi
  done
fi

if [ $SUCCESS -eq 0 ]; then
  echo ""
  echo "❌ None of the candidate zones had available capacity for an L4 GPU."
  exit 1
fi

# Ensure SSH is responsive
echo ""
echo "⏳ Waiting for SSH connectivity on $VM_NAME ($ZONE)..."
for i in {1..30}; do
  if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=5" --command="true" 2>/dev/null; then
    echo "✅ SSH connection established!"
    break
  fi
  sleep 4
done

echo ""
echo "=========================================================================="
echo "⏳ [2/4] Checking NVIDIA GPU Drivers on $VM_NAME..."
echo "=========================================================================="

# If nvidia-smi is already installed and working, skip driver install & reboot
if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=15" --command="command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1"; then
  echo "✅ NVIDIA Drivers are ALREADY installed and active. Skipping driver installation and reboot."
else
  echo "NVIDIA Driver not loaded. Installing nvidia-driver-535-server..."
  gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="
    sudo apt update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-driver-535-server
    echo 'Rebooting VM to load kernel modules...'
    sudo reboot
  " || true

  echo ""
  echo "🔄 VM is rebooting. Waiting for it to come back online..."
  for i in {1..30}; do
    if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=5" --command="true" 2>/dev/null; then
      echo "✅ VM is back online!"
      break
    fi
    sleep 5
  done
fi

echo ""
echo "=========================================================================="
echo "🔍 [3/4] Verifying GPU Hardware (nvidia-smi)..."
echo "=========================================================================="
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="nvidia-smi"

echo ""
echo "=========================================================================="
echo "📦 [4/4] Uploading & Executing setup_env.sh on VM..."
echo "=========================================================================="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Upload setup_env.sh to VM
echo "Uploading setup_env.sh..."
gcloud compute scp "$SCRIPT_DIR/setup_env.sh" "$VM_NAME:~/setup_env.sh" --zone="$ZONE"

# Execute setup_env.sh on VM
echo "Running setup_env.sh on VM (skips components already installed)..."
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="chmod +x ~/setup_env.sh && bash ~/setup_env.sh"

echo ""
echo "🎉========================================================================"
echo "🎉 SUCCESS: AI GPU WORKSTATION ($VM_NAME in $ZONE) IS READY!"
echo "🎉========================================================================"
echo ""
echo "👉 1. SSH into your VM:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo "👉 2. Inside the VM, activate your environment:"
echo "   conda activate ai"
echo ""
echo "👉 3. Stop VM when done (pause billing):"
echo "   gcloud compute instances stop $VM_NAME --zone=$ZONE"
echo ""
echo "👉 4. Delete VM permanently:"
echo "   ./delete_gpu.sh $VM_NAME"
echo ""
