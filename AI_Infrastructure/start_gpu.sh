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
    echo "📦 [4/4] Setting Up Conda 'ai' Environment & PyTorch with CUDA..."
    echo "=========================================================================="
    
    # Run setup script through remote bash stdin
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" -- 'bash -s' << 'EOF'
      set -e

      # 1. Wait for unattended-upgrades / cloud-init apt locks to release after reboot
      echo "Checking for background apt locks..."
      while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
        echo "Apt lock held by system startup. Waiting 5s..."
        sleep 5
      done

      # 2. Install prerequisites required by Conda in Ubuntu 24.04
      sudo apt-get update && sudo apt-get install -y bzip2 ca-certificates wget curl

      # 3. Clean install of Miniconda
      if [ ! -d "$HOME/miniconda" ]; then
        echo "Downloading and installing Miniconda..."
        rm -rf "$HOME/miniconda" /tmp/miniconda.sh
        wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
        bash /tmp/miniconda.sh -b -p "$HOME/miniconda"
        rm -f /tmp/miniconda.sh
      fi

      # 4. Permanently configure PATH in ~/.bashrc and ~/.profile + symlink so 'conda' is NEVER missing
      "$HOME/miniconda/bin/conda" init bash
      
      grep -qxF 'export PATH="$HOME/miniconda/bin:$PATH"' "$HOME/.bashrc" || echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> "$HOME/.bashrc"
      grep -qxF 'export PATH="$HOME/miniconda/bin:$PATH"' "$HOME/.profile" || echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> "$HOME/.profile"
      sudo ln -sf "$HOME/miniconda/bin/conda" /usr/local/bin/conda

      # Source conda for the current subshell
      source "$HOME/miniconda/etc/profile.d/conda.sh"
      export PATH="$HOME/miniconda/bin:$PATH"

      # 5. Configure conda-forge (Free, open-source, avoids CondaToSNonInteractiveError entirely)
      conda config --set auto_activate_base true
      conda config --add channels conda-forge
      conda config --set channel_priority strict

      # 6. Create the 'ai' environment cleanly
      if conda info --envs 2>/dev/null | grep -w "ai" >/dev/null 2>&1; then
        echo "Removing existing/partial 'ai' environment..."
        conda env remove -n ai -y
      fi

      conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
      conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

      echo "Creating 'ai' environment with Python 3.10 and pip via conda-forge..."
      conda create -n ai -c conda-forge python=3.10 pip -y

      # 7. Activate and install PyTorch + Jupyter
      echo "Activating 'ai' environment and installing PyTorch..."
      conda activate ai
      pip install --upgrade pip --quiet
      pip install torch torchvision torchaudio jupyter --index-url https://download.pytorch.org/whl/cu121 --quiet

      echo ""
      echo "=========================================================="
      echo "🧪 Running PyTorch GPU Matrix Multiplication Test..."
      echo "=========================================================="
      python - <<'PY'
import torch
print('CUDA Available  :', torch.cuda.is_available())
if torch.cuda.is_available():
    print('Device Name    :', torch.cuda.get_device_name(0))
    print('VRAM Available :', round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2), 'GB')
    x = torch.randn(4096, 4096, device='cuda')
    y = torch.matmul(x, x)
    print('GPU Tensor Test: PASSED! Result tensor shape:', y.shape)
print('=' * 50)
PY
EOF

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
