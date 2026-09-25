#!/usr/bin/env bash
# ==============================================================================
# Script: setup_env.sh
# Purpose: Sets up Miniconda, 'ai' Conda environment (Python 3.10), PyTorch with 
#          CUDA acceleration, and Jupyter on Ubuntu 22.04 / 24.04 (GCP VM).
# Can be run directly on the VM: bash setup_env.sh
# ==============================================================================

set -eo pipefail

# Terminal colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}==========================================================================${NC}"
echo -e "${CYAN}🚀 Setting Up AI Environment (Miniconda, Python 3.10, PyTorch + CUDA)${NC}"
echo -e "${CYAN}==========================================================================${NC}"

# 1. Wait for system apt/dpkg locks (unattended-upgrades / cloud-init after boot)
echo -e "\n${YELLOW}⏳ [1/5] Checking for background apt locks...${NC}"
while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || \
      sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || \
      sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
  echo "Apt lock held by system startup. Waiting 5s..."
  sleep 5
done

# 2. Install essential Conda dependencies
echo -e "\n${YELLOW}📦 [2/5] Installing base prerequisites (wget, curl, bzip2, ca-certificates)...${NC}"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y bzip2 ca-certificates wget curl

# 3. Clean install of Miniconda
CONDA_DIR="$HOME/miniconda3"
echo -e "\n${YELLOW}🐍 [3/5] Setting up Miniconda at $CONDA_DIR...${NC}"
if [ ! -d "$CONDA_DIR" ]; then
  echo "Downloading Miniconda installer..."
  rm -rf /tmp/miniconda.sh
  wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p "$CONDA_DIR"
  rm -f /tmp/miniconda.sh
  echo -e "${GREEN}✅ Miniconda installed successfully.${NC}"
else
  echo -e "${GREEN}✅ Miniconda is already installed at $CONDA_DIR.${NC}"
fi

# 4. Make Conda permanent across all shells (bashrc, profile, system symlink)
"$CONDA_DIR/bin/conda" init bash >/dev/null 2>&1 || true

grep -qxF 'export PATH="'"$CONDA_DIR"'/bin:$PATH"' "$HOME/.bashrc" || echo 'export PATH="'"$CONDA_DIR"'/bin:$PATH"' >> "$HOME/.bashrc"
grep -qxF 'export PATH="'"$CONDA_DIR"'/bin:$PATH"' "$HOME/.profile" || echo 'export PATH="'"$CONDA_DIR"'/bin:$PATH"' >> "$HOME/.profile"
sudo ln -sf "$CONDA_DIR/bin/conda" /usr/local/bin/conda

# Source conda into current running script
source "$CONDA_DIR/etc/profile.d/conda.sh"
export PATH="$CONDA_DIR/bin:$PATH"

# Write a clean .condarc that uses ONLY conda-forge and explicitly ignores Anaconda defaults
cat << 'EOF' > "$HOME/.condarc"
channels:
  - conda-forge
  - nodefaults
channel_priority: strict
auto_activate_base: true
EOF

# Optional fallback: accept ToS if conda still queries main repo
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true

# 5. Create the 'ai' environment with Python 3.10
echo -e "\n${YELLOW}⚡ [4/5] Creating Conda environment 'ai' (Python 3.10)...${NC}"
if conda info --envs 2>/dev/null | grep -w "ai" >/dev/null 2>&1; then
  echo "Environment 'ai' already exists. Recreating cleanly..."
  conda env remove -n ai -y
fi

# Use --override-channels so Conda NEVER contacts the restricted Anaconda main repo
conda create -n ai --override-channels -c conda-forge python=3.10 pip -y
echo -e "${GREEN}✅ Environment 'ai' created!${NC}"

# 6. Activate 'ai' and install PyTorch with CUDA 12.1 + Jupyter
echo -e "\n${YELLOW}🔥 [5/5] Activating 'ai' & installing PyTorch with CUDA 12.1 + Jupyter...${NC}"
conda activate ai

pip install --upgrade pip --quiet
pip install numpy pandas scipy matplotlib jupyter ipykernel --quiet
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet

# Register kernel for Jupyter
python -m ipykernel install --user --name ai --display-name "Python (ai)" >/dev/null 2>&1 || true

echo ""
echo -e "${GREEN}==========================================================${NC}"
echo -e "${GREEN}🧪 Verifying PyTorch GPU Acceleration...${NC}"
echo -e "${GREEN}==========================================================${NC}"
python - <<'PY'
import torch
print('CUDA Available  :', torch.cuda.is_available())
if torch.cuda.is_available():
    print('Device Name    :', torch.cuda.get_device_name(0))
    print('VRAM Available :', round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2), 'GB')
    x = torch.randn(4096, 4096, device='cuda')
    y = torch.matmul(x, x)
    print('GPU Tensor Test: PASSED! Result tensor shape:', y.shape)
else:
    print('⚠️ WARNING: CUDA is not available. Please verify NVIDIA driver with nvidia-smi.')
print('=' * 50)
PY

echo -e "\n${GREEN}🎉 Setup Complete! To use the environment:${NC}"
echo "   conda activate ai"
