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
  echo "🔄 [1/5] Trying zone: $ZONE (4 vCPU, 16 GB RAM, 1x NVIDIA L4 24GB)..."
  echo "=========================================================================="

  if gcloud compute instances create "$VM_NAME" \
      --zone="$ZONE" \
      --machine-type=g2-standard-4 \
      --maintenance-policy=TERMINATE \
      --boot-disk-size=100GB \
      --boot-disk-type=pd-balanced \
      --image-family=ubuntu-2204-lts \
      --image-project=ubuntu-os-cloud; then

    echo ""
    echo "✅ VM created successfully! Waiting 30s for the machine to boot..."
    sleep 30

    echo ""
    echo "=========================================================================="
    echo "⏳ [2/5] Installing NVIDIA Drivers (nvidia-driver-535-server)..."
    echo "=========================================================================="
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="
      sudo apt update
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-driver-535-server
      echo 'Rebooting VM to load NVIDIA kernel modules...'
      sudo reboot
    " || true

    echo ""
    echo "🔄 VM is rebooting. Waiting 25s for it to come back online..."
    sleep 25

    echo ""
    echo "=========================================================================="
    echo "🔍 [3/5] Verifying GPU Hardware (nvidia-smi)..."
    echo "=========================================================================="
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="nvidia-smi"

    echo ""
    echo "=========================================================================="
    echo "📦 [4/5] Installing Miniconda & Setting up 'ai' Python Environment..."
    echo "=========================================================================="
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="
      if [ ! -d \$HOME/miniconda ]; then
        wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
        bash miniconda.sh -b -p \$HOME/miniconda
        rm miniconda.sh
        \$HOME/miniconda/bin/conda init bash
      fi
      \$HOME/miniconda/bin/conda create -n ai python=3.12 -y
    "

    echo ""
    echo "=========================================================================="
    echo "🚀 [5/5] Installing PyTorch with CUDA & Running Hardware Test..."
    echo "=========================================================================="
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --ssh-flag="-o ConnectTimeout=60" --command="
      \$HOME/miniconda/envs/ai/bin/pip install --upgrade pip --quiet
      \$HOME/miniconda/envs/ai/bin/pip install torch torchvision torchaudio jupyter --quiet

      \$HOME/miniconda/envs/ai/bin/python - <<'PY'
import torch
print('=' * 50)
print('CUDA Available  :', torch.cuda.is_available())
if torch.cuda.is_available():
    print('Device Name    :', torch.cuda.get_device_name(0))
    print('VRAM Available :', round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2), 'GB')
    
    # Run test tensor operation on the L4 GPU
    x = torch.randn(4096, 4096, device='cuda')
    y = torch.matmul(x, x)
    print('GPU Tensor Test: PASSED! Result tensor shape:', y.shape)
print('=' * 50)
PY
    "

    echo ""
    echo "🎉========================================================================"
    echo "🎉 SUCCESS: AI GPU WORKSTATION IS FULLY READY!"
    echo "🎉========================================================================"
    echo ""
    echo "👉 1. SSH into your VM:"
    echo "   gcloud compute ssh $VM_NAME --zone=$ZONE"
    echo ""
    echo "👉 2. Activate your AI environment inside the VM:"
    echo "   conda activate ai"
    echo ""
    echo "👉 3. Optional - Port-forward Jupyter Notebook from your local machine:"
    echo "   gcloud compute ssh $VM_NAME --zone=$ZONE -- -N -L 8888:localhost:8888"
    echo ""
    echo "👉 4. Stop the VM when done (pause compute billing):"
    echo "   gcloud compute instances stop $VM_NAME --zone=$ZONE"
    echo ""
    echo "👉 5. Delete the VM permanently:"
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
