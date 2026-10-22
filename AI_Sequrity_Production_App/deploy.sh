#!/usr/bin/env bash
# ==============================================================================
# deploy.sh — Single-command automated EC2 deployment for Enterprise RAG
# Provisions a low-cost EC2 instance, clones the repository, runs Docker Compose,
# and verifies end-to-end functionality.
#
# To destroy everything and stop all costs: ./clear.sh
# ==============================================================================
set -euo pipefail

# ── Colors & Logging ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT="rag"
INSTANCE_NAME="rag-server"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.medium}"
AWS_REGION="${AWS_REGION:-us-east-1}"
GITHUB_REPO_URL="https://github.com/KishorKumarParoi/AI_Security_Production_App.git"

echo -e "\n${CYAN}=================================================================="
echo "   🚀 ENTERPRISE AGENTIC RAG — FAST EC2 DEPLOYMENT"
echo "   Region: ${AWS_REGION} | Instance Type: ${INSTANCE_TYPE}"
echo "==================================================================${NC}"

# ── 1. PREREQUISITES CHECK ───────────────────────────────────────────────────
echo -e "\n${YELLOW}[1/6] Checking prerequisites and credentials...${NC}"

for cmd in aws jq base64; do
    if ! command -v "$cmd" &>/dev/null; then
        echo -e "${RED}Error: Required command '$cmd' is not installed.${NC}" >&2
        exit 1
    fi
done

CALLER_ARN=$(aws sts get-caller-identity --query "Arn" --output text 2>/dev/null || true)
if [ -z "$CALLER_ARN" ]; then
    echo -e "${RED}Error: AWS credentials not configured or expired. Run 'aws configure'.${NC}" >&2
    exit 1
fi
echo -e "${GREEN}✓ Authenticated as: ${CALLER_ARN}${NC}"

if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found in current directory.${NC}" >&2
    exit 1
fi
echo -e "${GREEN}✓ Local .env file validated.${NC}"

# ── 2. NETWORK & SECURITY GROUP (DEFAULT VPC) ────────────────────────────────
echo -e "\n${YELLOW}[2/6] Locating default VPC and setting up Security Group...${NC}"

VPC_ID=$(aws ec2 describe-vpcs --region "$AWS_REGION" --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text 2>/dev/null || true)
if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
    # Fallback to the first available VPC
    VPC_ID=$(aws ec2 describe-vpcs --region "$AWS_REGION" --query "Vpcs[0].VpcId" --output text 2>/dev/null || true)
fi

if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
    echo -e "${RED}Error: No VPC available in region ${AWS_REGION}.${NC}" >&2
    exit 1
fi
echo -e "${GREEN}✓ Using VPC: ${VPC_ID}${NC}"

# Pick first available public subnet
SUBNET_ID=$(aws ec2 describe-subnets --region "$AWS_REGION" --filters "Name=vpc-id,Values=${VPC_ID}" --query "Subnets[0].SubnetId" --output text 2>/dev/null || true)
echo -e "${GREEN}✓ Using Subnet: ${SUBNET_ID}${NC}"

# Security Group: Allow SSH (22), HTTP (80), FastAPI (8080), Streamlit (8501)
SG_NAME="rag-ec2-sg"
SG_ID=$(aws ec2 describe-security-groups --region "$AWS_REGION" --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || true)

if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
    echo "Creating Security Group ${SG_NAME}..."
    SG_ID=$(aws ec2 create-security-group \
        --region "$AWS_REGION" \
        --group-name "$SG_NAME" \
        --description "Security group for Enterprise RAG EC2 instance" \
        --vpc-id "$VPC_ID" \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${SG_NAME}},{Key=Project,Value=${PROJECT}}]" \
        --query "GroupId" \
        --output text)

    echo "Configuring inbound rules..."
    aws ec2 authorize-security-group-ingress --region "$AWS_REGION" --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 >/dev/null
    aws ec2 authorize-security-group-ingress --region "$AWS_REGION" --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 >/dev/null
    aws ec2 authorize-security-group-ingress --region "$AWS_REGION" --group-id "$SG_ID" --protocol tcp --port 8080 --cidr 0.0.0.0/0 >/dev/null
    aws ec2 authorize-security-group-ingress --region "$AWS_REGION" --group-id "$SG_ID" --protocol tcp --port 8501 --cidr 0.0.0.0/0 >/dev/null
fi
echo -e "${GREEN}✓ Security Group ready: ${SG_ID}${NC}"

# ── 3. SSH KEY PAIR SETUP ─────────────────────────────────────────────────────
echo -e "\n${YELLOW}[3/6] Setting up SSH Key Pair...${NC}"
KEY_NAME="rag-ec2-key"
KEY_EXISTS=$(aws ec2 describe-key-pairs --region "$AWS_REGION" --key-names "$KEY_NAME" --query "KeyPairs[0].KeyName" --output text 2>/dev/null || true)

if [ -z "$KEY_EXISTS" ] || [ "$KEY_EXISTS" = "None" ]; then
    PUB_KEY=""
    if [ -f "$HOME/.ssh/id_rsa.pub" ]; then
        PUB_KEY="$HOME/.ssh/id_rsa.pub"
    elif [ -f "$HOME/.ssh/id_ed25519.pub" ]; then
        PUB_KEY="$HOME/.ssh/id_ed25519.pub"
    fi

    if [ -n "$PUB_KEY" ]; then
        echo "Importing local SSH key ($PUB_KEY) as '${KEY_NAME}'..."
        aws ec2 import-key-pair --region "$AWS_REGION" --key-name "$KEY_NAME" --public-key-material "fileb://${PUB_KEY}" >/dev/null
    else
        echo "Generating new AWS KeyPair '${KEY_NAME}'..."
        mkdir -p "$HOME/.ssh"
        aws ec2 create-key-pair --region "$AWS_REGION" --key-name "$KEY_NAME" --query "KeyMaterial" --output text > "$HOME/.ssh/${KEY_NAME}.pem"
        chmod 400 "$HOME/.ssh/${KEY_NAME}.pem"
        echo "Saved private key to: $HOME/.ssh/${KEY_NAME}.pem"
    fi
fi
echo -e "${GREEN}✓ Key Pair ready: ${KEY_NAME}${NC}"

# ── 4. AMI & USER-DATA SCRIPT GENERATION ───────────────────────────────────────
echo -e "\n${YELLOW}[4/6] Preparing Ubuntu 24.04 LTS and cloud-init automated bootstrap...${NC}"

# Find official Ubuntu 24.04 LTS AMI in the target region
AMI_ID=$(aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id --region "$AWS_REGION" --query "Parameter.Value" --output text 2>/dev/null || true)
if [ -z "$AMI_ID" ] || [ "$AMI_ID" = "None" ]; then
    # Fallback search
    AMI_ID=$(aws ec2 describe-images --region "$AWS_REGION" --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" "Name=state,Values=available" --query "reverse(sort_by(Images, &CreationDate))[0].ImageId" --output text)
fi
echo -e "${GREEN}✓ Ubuntu 24.04 LTS AMI: ${AMI_ID}${NC}"

# Encode .env so user-data can safely recreate it on the instance
ENV_CONTENT_BASE64=$(base64 < .env | tr -d '\n')

USER_DATA_FILE=$(mktemp /tmp/rag-userdata.XXXXXX)
cat > "$USER_DATA_FILE" << EOF
#!/bin/bash
set -e
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "=== Starting Enterprise RAG EC2 Bootstrap ==="

# 1. Install prerequisites & Docker CE + Docker Compose
apt-get update -y
apt-get install -y ca-certificates curl gnupg git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo "\$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# 2. Clone repository
mkdir -p /home/ubuntu/app
cd /home/ubuntu/app

# If git clone fails (e.g. repo url change), clone or pull
if [ ! -d ".git" ]; then
    git clone "${GITHUB_REPO_URL}" . || true
else
    git pull origin main || true
fi

# 3. Write .env file
echo "${ENV_CONTENT_BASE64}" | base64 -d > .env
chown ubuntu:ubuntu .env
chmod 600 .env

# 4. Start services via Docker Compose
docker compose down 2>/dev/null || true
docker compose up -d --build

echo "=== Enterprise RAG EC2 Bootstrap Finished Successfully ==="
EOF

# ── 5. LAUNCH OR LOCATE EC2 INSTANCE ──────────────────────────────────────────
echo -e "\n${YELLOW}[5/6] Launching EC2 Instance (${INSTANCE_TYPE})...${NC}"

# Check if an instance tagged Name=rag-server is already active
EXISTING_ID=$(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --filters "Name=tag:Name,Values=${INSTANCE_NAME}" "Name=instance-state-name,Values=pending,running" \
    --query "Reservations[0].Instances[0].InstanceId" \
    --output text 2>/dev/null || true)

if [ -n "$EXISTING_ID" ] && [ "$EXISTING_ID" != "None" ]; then
    echo "Found existing running EC2 instance: ${EXISTING_ID}"
    INSTANCE_ID="$EXISTING_ID"
else
    echo "Launching new EC2 instance ${INSTANCE_NAME}..."
    INSTANCE_ID=$(aws ec2 run-instances \
        --region "$AWS_REGION" \
        --image-id "$AMI_ID" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SG_ID" \
        --subnet-id "$SUBNET_ID" \
        --associate-public-ip-address \
        --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":25,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
        --user-data "file://${USER_DATA_FILE}" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${INSTANCE_NAME}},{Key=Project,Value=${PROJECT}}]" \
        --query "Instances[0].InstanceId" \
        --output text)
    echo -e "${GREEN}✓ Instance created: ${INSTANCE_ID}${NC}"
fi

rm -f "$USER_DATA_FILE"

# Wait for instance to be in running state
echo "Waiting for EC2 instance state: running..."
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"

PUBLIC_IP=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo -e "${GREEN}✓ EC2 Instance is RUNNING with Public IP: ${PUBLIC_IP}${NC}"

# Save state
mkdir -p scripts
cat > scripts/ec2_deploy_state.sh <<EOF
export AWS_REGION="${AWS_REGION}"
export INSTANCE_ID="${INSTANCE_ID}"
export PUBLIC_IP="${PUBLIC_IP}"
export SG_ID="${SG_ID}"
export KEY_NAME="${KEY_NAME}"
EOF

# ── 6. LIVE HEALTH CHECK & VERIFICATION ───────────────────────────────────────
echo -e "\n${YELLOW}[6/6] Waiting for Docker build & containers to become healthy on EC2...${NC}"
echo "Installing Docker packages and spinning up containers (this takes ~60-90 seconds)..."

HEALTHY=false
for attempt in {1..30}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://${PUBLIC_IP}:8080/health" 2>/dev/null || true)
    if [ "$STATUS" = "200" ]; then
        HEALTHY=true
        echo -e "\n${GREEN}✓ API health check passed with HTTP 200!${NC}"
        break
    fi
    echo -n "."
    sleep 5
done

if [ "$HEALTHY" != "true" ]; then
    echo -e "\n${YELLOW}⚠ Containers are still building or warming up. The server is up at http://${PUBLIC_IP}:8080${NC}"
    echo "You can check logs via: ssh -i ~/.ssh/rag-ec2-key ubuntu@${PUBLIC_IP} 'sudo docker compose logs -f'"
fi

echo -e "\n${CYAN}=================================================================="
echo "   ✨ EC2 DEPLOYMENT COMPLETED AND LIVE!"
echo "==================================================================${NC}"
echo -e "🌐 EC2 Public IP     : ${GREEN}${PUBLIC_IP}${NC}"
echo -e "📖 Swagger API Docs  : ${GREEN}http://${PUBLIC_IP}:8080/docs${NC} (or http://${PUBLIC_IP}/docs)"
echo -e "🩺 Liveness Check    : ${GREEN}http://${PUBLIC_IP}:8080/health${NC}"
echo -e "🖥️ Streamlit UI      : ${GREEN}http://${PUBLIC_IP}:8501${NC}"
echo -e "🔑 SSH Command       : ${GREEN}ssh ubuntu@${PUBLIC_IP}${NC}"
echo -e "=================================================================="
echo -e "${YELLOW}To test a query against your live EC2 deployment:${NC}"
echo "curl -X POST http://${PUBLIC_IP}:8080/query \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"q\": \"What is an enterprise CronJob and what are its best practices?\"}'"
echo -e "=================================================================="
echo -e "${RED}To terminate all instances and stop ALL AWS costs at any time:${NC}"
echo -e "${CYAN}./clear.sh${NC}"
echo -e "==================================================================\n"
