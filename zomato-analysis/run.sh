#!/usr/bin/env bash
# ==============================================================================
# Script: run.sh
# Purpose: Cross-platform (Ubuntu / Debian / macOS) AWS Authentication verification,
#          CLI installation helper, S3 Bucket creation, and setup.
# ==============================================================================

set -euo pipefail

# -----------------------------
# Color Formatting
# -----------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# -----------------------------
# OS & Architecture Detection
# -----------------------------
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Darwin*)
        OS_TYPE="macos"
        OS_NAME="macOS ($(sw_vers -productVersion 2>/dev/null || echo 'Darwin'))"
        ;;
    Linux*)
        OS_TYPE="linux"
        if [ -f /etc/os-release ]; then
            # shellcheck source=/dev/null
            . /etc/os-release
            OS_NAME="${PRETTY_NAME:-Linux}"
        else
            OS_NAME="Linux"
        fi
        ;;
    *)
        OS_TYPE="unknown"
        OS_NAME="Unknown OS ($OS)"
        ;;
esac

echo -e "${CYAN}${BOLD}"
echo "=========================================================="
echo "      AWS SETUP & S3 BUCKET INITIALIZATION (MULTI-OS)     "
echo "=========================================================="
echo -e "${NC}"
log_info "Detected OS: ${BOLD}${OS_NAME}${NC} (${ARCH})"

# -----------------------------
# Load Environment Variables (.env)
# -----------------------------
ENV_FILE="$(dirname "$0")/.env"
if [ -f "$ENV_FILE" ]; then
    log_info "Loading environment variables from .env..."
    while IFS= read -r line || [ -n "$line" ]; do
        # Ignore comments and empty lines
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        
        # Check if line contains '='
        if [[ "$line" == *"="* ]]; then
            var_name="${line%%=*}"
            # Trim whitespace from name
            var_name="$(echo "$var_name" | tr -d '[:space:]')"
            
            var_value="${line#*=}"
            # Trim whitespace from value
            var_value="$(echo "$var_value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
            # Remove leading/trailing quotes if present
            var_value="${var_value#\"}"
            var_value="${var_value%\"}"
            var_value="${var_value#\'}"
            var_value="${var_value%\'}"
            
            export "${var_name}=${var_value}"
        fi
    done < "$ENV_FILE"
fi

# Configuration Defaults (can be overridden via environment or .env)
AWS_REGION="${AWS_DEFAULT_REGION:-${AWS_REGION:-us-east-1}}"
BUCKET_NAME="${S3_BUCKET_NAME:-${AWS_BUCKET_NAME:-zomato-dataset-kkp}}"

# -----------------------------
# Function: Install AWS CLI
# -----------------------------
install_aws_cli() {
    log_info "Attempting to install AWS CLI for ${OS_NAME}..."
    
    if [ "$OS_TYPE" = "macos" ]; then
        if command -v brew &> /dev/null; then
            log_info "Installing AWS CLI via Homebrew..."
            brew install awscli
        else
            log_info "Homebrew not found. Downloading official macOS PKG installer..."
            curl -fsSL "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "/tmp/AWSCLIV2.pkg"
            sudo installer -pkg /tmp/AWSCLIV2.pkg -target /
            rm -f /tmp/AWSCLIV2.pkg
        fi
    elif [ "$OS_TYPE" = "linux" ]; then
        log_info "Installing prerequisites (curl, unzip)..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -y && sudo apt-get install -y curl unzip
        elif command -v yum &> /dev/null; then
            sudo yum install -y curl unzip
        fi

        local arch_zip="awscli-exe-linux-x86_64.zip"
        if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
            arch_zip="awscli-exe-linux-aarch64.zip"
        fi

        log_info "Downloading official AWS CLI v2 (${arch_zip})..."
        curl -fsSL "https://awscli.amazonaws.com/${arch_zip}" -o "/tmp/awscliv2.zip"
        unzip -q -o /tmp/awscliv2.zip -d /tmp
        sudo /tmp/aws/install --update
        rm -rf /tmp/awscliv2.zip /tmp/aws
    else
        log_error "Unsupported OS for automatic install. Please install AWS CLI manually."
        exit 1
    fi
}

# -----------------------------
# 1. Check & Install AWS CLI
# -----------------------------
log_info "Checking AWS CLI installation..."
if ! command -v aws &> /dev/null; then
    log_warn "AWS CLI is not installed."
    
    if [ -t 0 ]; then
        read -rp "Would you like to install AWS CLI automatically now? [y/N]: " choice
        case "$choice" in
            [yY][eE][sS]|[yY])
                install_aws_cli
                ;;
            *)
                log_error "AWS CLI installation skipped. Please install it manually:"
                if [ "$OS_TYPE" = "macos" ]; then
                    echo "  brew install awscli"
                else
                    echo "  sudo apt-get update && sudo apt-get install -y curl unzip"
                    echo "  curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
                    echo "  unzip awscliv2.zip && sudo ./aws/install"
                fi
                exit 1
                ;;
        esac
    else
        install_aws_cli
    fi
fi
log_success "AWS CLI is available: $(aws --version)"

# -----------------------------
# 2. AWS Authentication / Identity Verification
# -----------------------------
log_info "Verifying AWS credentials and caller identity..."

if ! CALLER_IDENTITY=$(aws sts get-caller-identity --output json 2>&1); then
    log_error "AWS authentication failed!"
    echo "$CALLER_IDENTITY"
    echo ""
    log_warn "No valid AWS credentials found."
    
    if [ -t 0 ]; then
        read -rp "Would you like to run 'aws configure' now? [y/N]: " configure_choice
        case "$configure_choice" in
            [yY][eE][sS]|[yY])
                aws configure
                CALLER_IDENTITY=$(aws sts get-caller-identity --output json)
                ;;
            *)
                log_error "Exiting. Please configure credentials via 'aws configure' or export AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY."
                exit 1
                ;;
        esac
    else
        log_error "Please run 'aws configure' or set AWS credentials in environment variables."
        exit 1
    fi
fi

ACCOUNT_ID=$(echo "$CALLER_IDENTITY" | grep -o '"Account": "[^"]*' | cut -d'"' -f4)
USER_ARN=$(echo "$CALLER_IDENTITY" | grep -o '"Arn": "[^"]*' | cut -d'"' -f4)

log_success "Authenticated successfully!"
echo -e "  ${BOLD}Account ID:${NC} ${ACCOUNT_ID}"
echo -e "  ${BOLD}User ARN:${NC}   ${USER_ARN}"
echo -e "  ${BOLD}Region:${NC}     ${AWS_REGION}"
echo ""

# -----------------------------
# 3. Create S3 Bucket (Idempotent)
# -----------------------------
log_info "Target S3 Bucket: ${BOLD}${BUCKET_NAME}${NC} (Region: ${AWS_REGION})"

log_info "Checking if bucket already exists..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    log_success "Bucket '${BUCKET_NAME}' already exists and is accessible."
else
    log_info "Creating bucket '${BUCKET_NAME}' in region '${AWS_REGION}'..."
    
    if [ "$AWS_REGION" = "us-east-1" ]; then
        CREATE_OUTPUT=$(aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION" 2>&1)
    else
        CREATE_OUTPUT=$(aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION" \
            --create-bucket-configuration LocationConstraint="$AWS_REGION" 2>&1)
    fi

    if [ $? -eq 0 ]; then
        log_success "Successfully created bucket: s3://${BUCKET_NAME}"
    else
        log_error "Failed to create bucket '${BUCKET_NAME}':"
        echo "$CREATE_OUTPUT"
        exit 1
    fi
fi

# -----------------------------
# 4. Enable Default Encryption (Security Best Practice)
# -----------------------------
log_info "Ensuring default server-side encryption (AES256) is enabled..."
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }' 2>/dev/null || log_warn "Could not set default encryption (check IAM permissions)."

# -----------------------------
# 5. List S3 Bucket Contents
# -----------------------------
echo ""
log_info "Current contents of s3://${BUCKET_NAME}/:"
aws s3 ls "s3://${BUCKET_NAME}/" || true

# -----------------------------
# 6. IAM Policy for Snowflake S3 Read
# -----------------------------
echo ""
IAM_POLICY_NAME="${IAM_POLICY_NAME:-zomato-s3-read-policy}"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${IAM_POLICY_NAME}"

log_info "Configuring IAM Policy: ${BOLD}${IAM_POLICY_NAME}${NC}..."
if aws iam get-policy --policy-arn "$POLICY_ARN" &>/dev/null; then
    log_success "IAM Policy '${IAM_POLICY_NAME}' already exists."
else
    log_info "Creating IAM policy '${IAM_POLICY_NAME}'..."
    aws iam create-policy \
        --policy-name "$IAM_POLICY_NAME" \
        --description "Read-only access to ${BUCKET_NAME} for Snowflake" \
        --policy-document "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
                {
                    \"Effect\": \"Allow\",
                    \"Action\": [
                        \"s3:GetObject\",
                        \"s3:GetObjectVersion\"
                    ],
                    \"Resource\": \"arn:aws:s3:::${BUCKET_NAME}/*\"
                },
                {
                    \"Effect\": \"Allow\",
                    \"Action\": [
                        \"s3:ListBucket\",
                        \"s3:GetBucketLocation\"
                    ],
                    \"Resource\": \"arn:aws:s3:::${BUCKET_NAME}\"
                }
            ]
        }" >/dev/null
    log_success "Created IAM policy: ${POLICY_ARN}"
fi

# -----------------------------
# 7. IAM Role for Snowflake
# -----------------------------
echo ""
IAM_ROLE_NAME="${IAM_ROLE_NAME:-snowflake-s3-role}"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${IAM_ROLE_NAME}"

log_info "Configuring IAM Role: ${BOLD}${IAM_ROLE_NAME}${NC}..."
if aws iam get-role --role-name "$IAM_ROLE_NAME" &>/dev/null; then
    log_success "IAM Role '${IAM_ROLE_NAME}' already exists."
else
    log_info "Creating IAM role '${IAM_ROLE_NAME}'..."
    aws iam create-role \
        --role-name "$IAM_ROLE_NAME" \
        --description "Role assumed by Snowflake to access S3" \
        --assume-role-policy-document "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
                {
                    \"Effect\": \"Allow\",
                    \"Principal\": {
                        \"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\"
                    },
                    \"Action\": \"sts:AssumeRole\"
                }
            ]
        }" >/dev/null
    log_success "Created IAM role: ${ROLE_ARN}"
fi

# -----------------------------
# 8. Attach Policy to Role
# -----------------------------
echo ""
log_info "Attaching policy '${IAM_POLICY_NAME}' to role '${IAM_ROLE_NAME}'..."
aws iam attach-role-policy \
    --role-name "$IAM_ROLE_NAME" \
    --policy-arn "$POLICY_ARN" 2>/dev/null || true
log_success "Policy '${IAM_POLICY_NAME}' attached to role '${IAM_ROLE_NAME}'."

# -----------------------------
# 9. Update Assume-Role Trust Policy (Snowflake Integration)
# -----------------------------
echo ""
if [ -n "${STORAGE_AWS_IAM_USER_ARN:-}" ] && [ -n "${STORAGE_AWS_EXTERNAL_ID:-}" ]; then
    log_info "Updating trust policy with Snowflake credentials from .env..."
    log_info "  Snowflake IAM User ARN: ${STORAGE_AWS_IAM_USER_ARN}"
    log_info "  Snowflake External ID:  ${STORAGE_AWS_EXTERNAL_ID}"
    
    aws iam update-assume-role-policy \
        --role-name "$IAM_ROLE_NAME" \
        --policy-document "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
                {
                    \"Effect\": \"Allow\",
                    \"Principal\": {
                        \"AWS\": \"${STORAGE_AWS_IAM_USER_ARN}\"
                    },
                    \"Action\": \"sts:AssumeRole\",
                    \"Condition\": {
                        \"StringEquals\": {
                            \"sts:ExternalId\": \"${STORAGE_AWS_EXTERNAL_ID}\"
                        }
                    }
                }
            ]
        }"
    log_success "Trust policy updated successfully for Snowflake!"
else
    log_warn "STORAGE_AWS_IAM_USER_ARN or STORAGE_AWS_EXTERNAL_ID not found in .env."
    log_warn "To complete the Snowflake handshake, run in Snowflake:"
    echo "    DESC INTEGRATION ZOMATO_S3_INT;"
    echo "  Then add STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID to .env and re-run this script."
fi

# -----------------------------
# 10. Snowflake Connection & Stage Setup
# -----------------------------
echo ""
echo -e "${CYAN}${BOLD}"
echo "=========================================================="
echo "          SNOWFLAKE CONNECTION & S3 INTEGRATION           "
echo "=========================================================="
echo -e "${NC}"

# Synchronize SQL templates if snowflake directory exists
if [ -d "snowflake" ]; then
    log_info "Synchronizing Snowflake SQL templates with current S3 and IAM parameters..."
    sed -i.bak \
        -e "s|STORAGE_AWS_ROLE_ARN = '.*'|STORAGE_AWS_ROLE_ARN = '${ROLE_ARN}'|g" \
        -e "s|STORAGE_ALLOWED_LOCATIONS = ('s3://.*')|STORAGE_ALLOWED_LOCATIONS = ('s3://${BUCKET_NAME}/')|g" \
        snowflake/02_storage_integration.sql 2>/dev/null && rm -f snowflake/02_storage_integration.sql.bak || true

    sed -i.bak \
        -e "s|URL = 's3://.*/'|URL = 's3://${BUCKET_NAME}/raw-data/'|g" \
        snowflake/03_stage_and_formats.sql 2>/dev/null && rm -f snowflake/03_stage_and_formats.sql.bak || true
    log_success "Updated snowflake/02_storage_integration.sql & snowflake/03_stage_and_formats.sql"
fi

# Check for SNOWFLAKE credentials in .env
SNOWFLAKE_ACCOUNT_VAL="${SNOWFLAKE_ACCOUNT:-}"
SNOWFLAKE_USER_VAL="${SNOWFLAKE_USER:-${SNOWFLAKE_USERNAME:-}}"
SNOWFLAKE_PASS_VAL="${SNOWFLAKE_PASS:-${SNOWFLAKE_PASSWORD:-}}"
SNOWFLAKE_ROLE_VAL="${SNOWFLAKE_ROLE:-ACCOUNTADMIN}"

if [ -n "$SNOWFLAKE_ACCOUNT_VAL" ] && [ -n "$SNOWFLAKE_USER_VAL" ] && [ -n "$SNOWFLAKE_PASS_VAL" ]; then
    log_info "Connecting to Snowflake account: ${BOLD}${SNOWFLAKE_ACCOUNT_VAL}${NC} as ${BOLD}${SNOWFLAKE_USER_VAL}${NC}..."
    
    if command -v uv &>/dev/null; then
        uv run --with snowflake-connector-python --with python-dotenv python - <<EOF
import sys
import snowflake.connector

account = "${SNOWFLAKE_ACCOUNT_VAL}"
user = "${SNOWFLAKE_USER_VAL}"
password = "${SNOWFLAKE_PASS_VAL}"
role = "${SNOWFLAKE_ROLE_VAL}"
role_arn = "${ROLE_ARN}"
bucket = "${BUCKET_NAME}"

print("[INFO] Authenticating with Snowflake...")
try:
    conn = snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        role=role,
        login_timeout=15
    )
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION(), CURRENT_ROLE(), CURRENT_WAREHOUSE();")
    ver, r, wh = cursor.fetchone()
    print(f"[SUCCESS] Connected to Snowflake! Version: {ver} | Role: {r}")

    print("[INFO] Creating / validating STORAGE INTEGRATION ZOMATO_S3_INT in Snowflake...")
    cursor.execute(f"""
        CREATE OR REPLACE STORAGE INTEGRATION ZOMATO_S3_INT
          TYPE = EXTERNAL_STAGE
          STORAGE_PROVIDER = 'S3'
          ENABLED = TRUE
          STORAGE_AWS_ROLE_ARN = '{role_arn}'
          STORAGE_ALLOWED_LOCATIONS = ('s3://{bucket}/');
    """)
    cursor.execute("GRANT USAGE ON INTEGRATION ZOMATO_S3_INT TO ROLE ACCOUNTADMIN;")
    cursor.execute("GRANT USAGE ON INTEGRATION ZOMATO_S3_INT TO ROLE DBT_ROLE;")
    
    cursor.execute("CREATE DATABASE IF NOT EXISTS ZOMATO;")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS ZOMATO.RAW;")
    
    print(f"[INFO] Creating External Stage ZOMATO.RAW.ZOMATO_RAW_STAGE -> s3://{bucket}/raw-data/...")
    cursor.execute(f"""
        CREATE OR REPLACE STAGE ZOMATO.RAW.ZOMATO_RAW_STAGE
          STORAGE_INTEGRATION = ZOMATO_S3_INT
          URL = 's3://{bucket}/raw-data/';
    """)

    print("[INFO] Listing S3 files via Snowflake Stage:")
    cursor.execute("LIST @ZOMATO.RAW.ZOMATO_RAW_STAGE;")
    files = cursor.fetchall()
    for f in files:
        print(f"  - {f[0]} ({f[1]} bytes)")
    
    print(f"[SUCCESS] Successfully verified {len(files)} files in Snowflake from S3!")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"[ERROR] Snowflake connection failed: {e}", file=sys.stderr)
EOF
    else
        log_warn "uv is not installed; skipping automated Python connection to Snowflake."
    fi
else
    log_info "Snowflake Direct Connection Setup:"
    echo -e "  To allow this script to run queries directly in Snowflake, add your account identifier to .env:"
    echo -e "    ${BOLD}SNOWFLAKE_ACCOUNT=\"<YOUR_ORG>-<YOUR_ACCOUNT>\"${NC}"
    echo ""
    echo -e "  You can find your account identifier by running this in Snowsight:"
    echo -e "    ${CYAN}SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME();${NC}"
    echo ""
    echo -e "  Or execute the updated SQL script directly in Snowsight:"
    echo -e "    ${CYAN}snowflake/02_storage_integration.sql${NC}"
    echo -e "    ${CYAN}snowflake/03_stage_and_formats.sql${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}Setup completed successfully on ${OS_NAME}!${NC}"
