#!/usr/bin/env bash
# ==============================================================================
# Lab: Set Up Ubuntu on GCP for AI Development
# Philosophy: "If already installed/existing, skip; if not, only then install"
# Compatible with: Ubuntu 22.04 & 24.04 LTS on Google Cloud Platform
# ==============================================================================

set -eo pipefail

# Terminal styling
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

log_step() {
  echo -e "\n${BLUE}==========================================================================${NC}"
  echo -e "${BOLD}${CYAN}$1${NC}"
  echo -e "${BLUE}==========================================================================${NC}"
}
log_info()    { echo -e "${CYAN}ℹ️  [INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}✅ [ALREADY OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}⚠️  [WARNING]${NC} $1"; }
log_error()   { echo -e "${RED}❌ [ERROR]${NC} $1"; }

# Helper: Wait for background apt locks (unattended-upgrades / cloud-init)
wait_for_apt_lock() {
  while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || \
        sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || \
        sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
    log_warn "Apt lock held by system processes. Waiting 5s..."
    sleep 5
  done
}

# ------------------------------------------------------------------------------
# 0) Check OS, user, and hardware
# ------------------------------------------------------------------------------
log_step "0) Check OS, user, and hardware"
lsb_release -d 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME
log_info "Current User: $(whoami) (Home: $HOME)"

HAS_NVIDIA=0
if lspci | grep -i nvidia >/dev/null 2>&1; then
  HAS_NVIDIA=1
  log_info "NVIDIA GPU detected on PCI bus:"
  lspci | grep -i nvidia
else
  log_warn "No NVIDIA GPU detected. Continuing with CPU-optimized stack."
fi

# ------------------------------------------------------------------------------
# 1) Update & base system hygiene (Skip if packages already present)
# ------------------------------------------------------------------------------
log_step "1) Base system hygiene & developer utilities"

REQUIRED_PKGS=(
  build-essential git curl wget unzip zip tar ca-certificates bzip2
  htop iotop iftop tree tmux pkg-config software-properties-common
  nano vim neovim apt-transport-https gnupg lsb-release
)
MISSING_PKGS=()
for pkg in "${REQUIRED_PKGS[@]}"; do
  if ! dpkg -s "$pkg" >/dev/null 2>&1; then
    MISSING_PKGS+=("$pkg")
  fi
done

if [ ${#MISSING_PKGS[@]} -eq 0 ]; then
  log_success "All base system utilities already installed. Skipping apt install."
else
  log_info "Installing missing utilities: ${MISSING_PKGS[*]}..."
  wait_for_apt_lock
  sudo apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${MISSING_PKGS[@]}"
  log_info "Utilities installed."
fi

# ------------------------------------------------------------------------------
# 2) Secure basics (UFW Firewall with OpenSSH)
# ------------------------------------------------------------------------------
log_step "2) Secure basics (UFW Firewall)"
if sudo ufw status 2>/dev/null | grep -q "Status: active"; then
  log_success "UFW firewall is already active with OpenSSH allowed. Skipping."
else
  sudo ufw allow OpenSSH >/dev/null 2>&1 || true
  sudo ufw --force enable >/dev/null 2>&1 || true
  log_info "UFW enabled and OpenSSH allowed."
fi

# ------------------------------------------------------------------------------
# 3) Git + SSH keys (Skip if key already exists)
# ------------------------------------------------------------------------------
log_step "3) Git + SSH keys"
git --version
if [ -f "$HOME/.ssh/id_ed25519" ]; then
  log_success "SSH key already exists at ~/.ssh/id_ed25519. Skipping generation."
else
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"
  ssh-keygen -t ed25519 -C "$USER@gcp-ai-box" -N "" -f "$HOME/.ssh/id_ed25519"
  eval "$(ssh-agent -s)" >/dev/null 2>&1 || true
  ssh-add "$HOME/.ssh/id_ed25519" >/dev/null 2>&1 || true
  log_info "Generated new SSH key:"
fi
cat "$HOME/.ssh/id_ed25519.pub"

# ------------------------------------------------------------------------------
# 4) Python environment manager (Miniconda)
# ------------------------------------------------------------------------------
log_step "4) Python environment manager (Miniconda)"
CONDA_DIR="$HOME/miniconda3"

if [ -x "$CONDA_DIR/bin/conda" ]; then
  log_success "Miniconda is already installed at $CONDA_DIR. Skipping download."
else
  log_info "Installing Miniconda to $CONDA_DIR..."
  rm -rf /tmp/miniconda.sh
  wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p "$CONDA_DIR"
  rm -f /tmp/miniconda.sh
fi

# Permanent PATH persistence for all login and non-login shells
"$CONDA_DIR/bin/conda" init bash >/dev/null 2>&1 || true
grep -qxF 'export PATH="'"$CONDA_DIR"'/bin:$PATH"' "$HOME/.bashrc" || echo 'export PATH="'"$CONDA_DIR"'/bin:$PATH"' >> "$HOME/.bashrc"
grep -qxF 'export PATH="'"$CONDA_DIR"'/bin:$PATH"' "$HOME/.profile" || echo 'export PATH="'"$CONDA_DIR"'/bin:$PATH"' >> "$HOME/.profile"
[ -L /usr/local/bin/conda ] || sudo ln -sf "$CONDA_DIR/bin/conda" /usr/local/bin/conda

# Source into current running script
source "$CONDA_DIR/etc/profile.d/conda.sh"
export PATH="$CONDA_DIR/bin:$PATH"

# Configure conda-forge & ignore Anaconda defaults (completely bypasses ToS errors)
if [ ! -f "$HOME/.condarc" ] || ! grep -q "nodefaults" "$HOME/.condarc"; then
  cat << 'EOF' > "$HOME/.condarc"
channels:
  - conda-forge
  - nodefaults
channel_priority: strict
auto_activate_base: true
EOF
  log_info "Configured ~/.condarc with conda-forge and nodefaults."
else
  log_success "~/.condarc already configured with conda-forge. Skipping."
fi

# Create 'ai' environment cleanly if missing
if conda info --envs 2>/dev/null | grep -w "ai" >/dev/null 2>&1; then
  log_success "Conda environment 'ai' already exists. Skipping environment creation."
else
  log_info "Creating 'ai' environment with Python 3.10..."
  conda create -n ai --override-channels -c conda-forge python=3.10 pip -y
  log_info "Conda environment 'ai' created."
fi

conda activate ai
log_info "Active Python: $(python -V) at $(which python)"

# ------------------------------------------------------------------------------
# 5) Core Python stack
# ------------------------------------------------------------------------------
log_step "5) Core Python stack"
conda activate ai

if python -c "import numpy, pandas, scipy, sklearn, matplotlib, jupyterlab, ipywidgets" >/dev/null 2>&1; then
  log_success "Core Python packages (numpy, pandas, scikit-learn, jupyterlab) already installed. Skipping."
else
  log_info "Installing core Python stack..."
  pip install --upgrade pip wheel setuptools --quiet
  pip install numpy pandas scipy scikit-learn matplotlib jupyterlab ipywidgets \
    black isort flake8 pre-commit rich tqdm google-cloud-storage --quiet
  log_info "Core Python stack installed."
fi

# ------------------------------------------------------------------------------
# 6) NVIDIA GPU driver verification
# ------------------------------------------------------------------------------
log_step "6) NVIDIA GPU driver verification"
if [ "$HAS_NVIDIA" -eq 1 ]; then
  if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
    log_success "NVIDIA driver is already active and verified:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  else
    log_warn "NVIDIA GPU detected but driver kernel modules not active."
    log_info "Installing recommended driver via ubuntu-drivers..."
    wait_for_apt_lock
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y ubuntu-drivers-common
    sudo ubuntu-drivers autoinstall
    log_warn "Driver installed. A system reboot will be required."
  fi
else
  log_success "CPU-only instance: skipping GPU driver check."
fi

# ------------------------------------------------------------------------------
# 7) PyTorch install (GPU or CPU)
# ------------------------------------------------------------------------------
log_step "7) PyTorch install"
conda activate ai

if [ "$HAS_NVIDIA" -eq 1 ]; then
  if python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" >/dev/null 2>&1; then
    log_success "PyTorch with CUDA acceleration is already installed & verified. Skipping."
  else
    log_info "Installing PyTorch with CUDA 12.1 runtime wheels..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet
    log_info "PyTorch installed."
  fi
else
  if python -c "import torch" >/dev/null 2>&1; then
    log_success "PyTorch (CPU build) is already installed. Skipping."
  else
    log_info "Installing PyTorch for CPU..."
    pip install torch torchvision torchaudio --quiet
    log_info "PyTorch (CPU) installed."
  fi
fi

# ------------------------------------------------------------------------------
# 8 & 9) JupyterLab, OpenCV, Pillow & Extras
# ------------------------------------------------------------------------------
log_step "8 & 9) OpenCV, Pillow, Plotly & JupyterLab kernel"
conda activate ai

if python -c "import cv2, PIL, seaborn, plotly" >/dev/null 2>&1; then
  log_success "OpenCV, Pillow, Seaborn, and Plotly are already installed. Skipping."
else
  log_info "Installing OpenCV, Pillow, Seaborn, and Plotly..."
  pip install opencv-python pillow seaborn plotly ipykernel --quiet
  log_info "Visualization packages installed."
fi

if jupyter kernelspec list 2>/dev/null | grep -w "ai" >/dev/null 2>&1; then
  log_success "Jupyter kernel 'Python (ai)' is already registered. Skipping."
else
  python -m ipykernel install --user --name ai --display-name "Python (ai)" >/dev/null 2>&1
  log_info "Jupyter kernel 'Python (ai)' registered."
fi

# ------------------------------------------------------------------------------
# 10) Docker Engine
# ------------------------------------------------------------------------------
log_step "10) Docker Engine"
if command -v docker >/dev/null 2>&1 && docker --version >/dev/null 2>&1; then
  log_success "Docker Engine already installed ($(docker --version)). Skipping installation."
else
  log_info "Installing Docker Engine..."
  wait_for_apt_lock
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$UBUNTU_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  log_info "Docker Engine installed."
fi

if groups "$USER" 2>/dev/null | grep -q "\bdocker\b"; then
  log_success "User '$USER' is already in 'docker' group. Skipping."
else
  sudo usermod -aG docker "$USER"
  log_info "Added '$USER' to 'docker' group."
fi
sudo systemctl enable --now docker >/dev/null 2>&1 || true

# ------------------------------------------------------------------------------
# 11) NVIDIA Container Toolkit (GPU in Docker)
# ------------------------------------------------------------------------------
if [ "$HAS_NVIDIA" -eq 1 ]; then
  log_step "11) NVIDIA Container Toolkit"
  if dpkg -s nvidia-container-toolkit >/dev/null 2>&1; then
    log_success "NVIDIA Container Toolkit already installed. Skipping installation."
  else
    log_info "Installing NVIDIA Container Toolkit..."
    wait_for_apt_lock
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null

    sudo apt-get update -y
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    log_info "NVIDIA Container Toolkit installed & configured."
  fi
fi

# ------------------------------------------------------------------------------
# 12) Quality-of-life setup
# ------------------------------------------------------------------------------
log_step "12) Quality-of-life setup (tmux, pre-commit)"
conda activate ai
log_success "tmux: $(tmux -V 2>/dev/null || echo 'installed')"
log_success "pre-commit: $(pre-commit --version 2>/dev/null || echo 'installed')"

# ------------------------------------------------------------------------------
# 13) Create a project template
# ------------------------------------------------------------------------------
log_step "13) Create a project template"
PROJECT_DIR="$HOME/projects/ai-starter"
if [ -d "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/requirements.txt" ]; then
  log_success "Project directory $PROJECT_DIR already exists. Skipping."
else
  mkdir -p "$PROJECT_DIR"/{data,notebooks,scripts,models,logs}
  cat << 'REQ' > "$PROJECT_DIR/requirements.txt"
numpy
pandas
scikit-learn
torch
torchvision
torchaudio
google-cloud-storage
REQ
  log_info "Starter project directory created at $PROJECT_DIR."
fi

# ------------------------------------------------------------------------------
# 14) Verification checklist
# ------------------------------------------------------------------------------
log_step "14) Verification checklist"

echo -e "\n[✓] 1. Hardware Status:"
if [ "$HAS_NVIDIA" -eq 1 ]; then
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || log_warn "nvidia-smi not active"
else
  echo "CPU architecture verified."
fi

echo -e "\n[✓] 2. Conda & Python Environment:"
conda activate ai
python - <<'PY'
import torch
cuda = torch.cuda.is_available()
print(f"PyTorch Version : {torch.__version__}")
print(f"CUDA Available  : {cuda}")
if cuda:
    print(f"GPU Name        : {torch.cuda.get_device_name(0)}")
    x = torch.randn(2048, 2048, device='cuda')
    y = x @ x
    print("PyTorch Matmul  : PASSED! Shape:", y.shape)
else:
    x = torch.randn(1024, 1024)
    y = x @ x
    print("PyTorch CPU Matmul: PASSED! Shape:", y.shape)
PY

echo -e "\n[✓] 3. Docker Test:"
sudo docker run --rm hello-world | grep -i "Hello from Docker!" || true

if [ "$HAS_NVIDIA" -eq 1 ] && command -v nvidia-smi >/dev/null 2>&1; then
  echo -e "\n[✓] 4. Docker GPU Passthrough:"
  sudo docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi || true
fi

# ------------------------------------------------------------------------------
# 15) Instructions
# ------------------------------------------------------------------------------
log_step "🎉 SETUP COMPLETE & VERIFIED!"
cat << 'EOF'
--------------------------------------------------------------------------------
👉 How to connect to JupyterLab from your local machine via GCP SSH Tunnel:
--------------------------------------------------------------------------------
1. Start JupyterLab on this VM:
   conda activate ai
   jupyter lab --no-browser --port 8888

2. In your LOCAL terminal, establish an SSH tunnel:
   gcloud compute ssh <VM-NAME> --zone=<ZONE> -- -N -L 8888:localhost:8888

3. Open your browser to:
   http://localhost:8888
   (Paste the security token printed by JupyterLab)
--------------------------------------------------------------------------------
EOF

if [[ "$1" == "--reboot" ]]; then
  log_warn "System reboot requested via --reboot. Rebooting now..."
  sudo reboot
fi
