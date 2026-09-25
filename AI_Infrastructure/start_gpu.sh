#!/usr/bin/env bash

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

VM_NAME="ai-lab-l4"
SUCCESS=0

for ZONE in "${ZONES[@]}"; do
  echo ""
  echo "=========================================================================="
  echo "🔄 [1/4] Trying zone: $ZONE (Ubuntu 24.04 LTS | 4 vCPU | 16 GB | L4 24GB)"
  echo "=========================================================================="

  if gcloud compute instances create "$VM_NAME" \
      --zone="$ZONE" \
      --machine-type=g2-standard-4 \
      --maintenance-policy=TERMINATE \
      --boot-disk-size=100GB \
      --boot-disk-type=pd-balanced \
      --image-family=ubuntu-2404-lts-amd64 \
      --image-project=ubuntu-os-cloud; then

    echo ""
    echo "✅ VM created! Waiting 35s for Ubuntu 24.04 to boot..."
    sleep 35

    echo ""
    echo "=========================================================================="
    echo "⏳ [2/4] Installing NVIDIA Drivers (nvidia-driver-535-server)..."
    echo "=========================================================================="
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="
      sudo apt update
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-driver-535-server
      echo 'Rebooting VM to load kernel modules...'
      sudo reboot
    " || true

    echo ""
    echo "🔄 VM is rebooting. Waiting for it to come back online..."
    # Poll SSH until the VM is fully booted and responsive
    for i in {1..30}; do
      if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=5" --command="true" 2>/dev/null; then
        echo "✅ VM is back online!"
        break
      fi
      sleep 5
    done

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
    
    # 1. Copy setup_env.sh to VM home directory
    echo "Uploading setup_env.sh to VM..."
    gcloud compute scp "$SCRIPT_DIR/setup_env.sh" "$VM_NAME:~/setup_env.sh" --zone="$ZONE"

    # 2. Execute setup_env.sh directly on the VM
    echo "Running setup_env.sh on VM..."
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="chmod +x ~/setup_env.sh && bash ~/setup_env.sh"

    echo ""
    echo "🎉========================================================================"
    echo "🎉 SUCCESS: AI GPU WORKSTATION (Ubuntu 24.04 LTS) IS READY!"
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
    echo "   ./delete_gpu.sh"
    echo ""
    SUCCESS=1
    break
  else
    echo "⚠️ $ZONE unavailable. Trying next candidate zone..."
  fi
done

if [ $SUCCESS -eq 0 ]; then
  echo ""
  echo "❌ None of the candidate zones had available capacity for an L4 GPU."
fi
