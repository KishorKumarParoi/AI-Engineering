#!/usr/bin/env bash
# ==============================================================================
# Script: scripts/data-engineering/setup_env.sh
# Purpose: Environment Bootstrap, Dependency Installation & System Doctor
# Tier: Senior Staff / Lead Data Engineer Standard
# ==============================================================================

set -euo pipefail

# -----------------------------
# Color Formatting (Universal ASCII)
# -----------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "         DEVELOPER ENVIRONMENT SETUP & DOCTOR            "
    echo "=========================================================="
    echo -e "${NC}"
}

check_tool() {
    TOOL_NAME="$1"
    INSTALL_HINT="$2"
    if command -v "$TOOL_NAME" &>/dev/null; then
        VERSION="$($TOOL_NAME --version 2>/dev/null | head -n 1 || echo 'installed')"
        echo -e "  [+] ${GREEN}$TOOL_NAME${NC}: $VERSION"
        return 0
    else
        echo -e "  [-] ${RED}$TOOL_NAME${NC} is NOT installed! ($INSTALL_HINT)"
        return 1
    fi
}

doctor() {
    print_header
    log_info "1. Checking Core CLI Tools:"
    FAILED=0
    check_tool "python3" "Install via python.org or brew" || FAILED=1
    check_tool "uv" "Install via 'curl -LsSf https://astral.sh/uv/install.sh | sh'" || FAILED=1
    check_tool "docker" "Install Docker Desktop" || FAILED=1
    check_tool "astro" "Install via 'brew install astro'" || true
    check_tool "git" "Install via xcode-select --install or brew" || FAILED=1

    echo ""
    log_info "2. Checking Environment Configuration (.env):"
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            log_warn ".env not found! Copying from .env.example..."
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            log_warn "Please update credentials in .env before continuing."
        else
            log_error ".env file missing!"
            FAILED=1
        fi
    else
        log_success ".env file exists"
        set -a
        source <(grep -v '^[[:space:]]*#' "$PROJECT_ROOT/.env" | grep -v '^[[:space:]]*$')
        set +a

        # Validate keys
        [ -n "${SNOWFLAKE_ACCOUNT:-}" ] && echo "  [+] SNOWFLAKE_ACCOUNT: $SNOWFLAKE_ACCOUNT" || log_warn "  [-] SNOWFLAKE_ACCOUNT is missing"
        [ -n "${SNOWFLAKE_USER:-${SNOWFLAKE_USERNAME:-}}" ] && echo "  [+] SNOWFLAKE_USER: ${SNOWFLAKE_USER:-$SNOWFLAKE_USERNAME}" || log_warn "  [-] SNOWFLAKE_USER is missing"
        [ -n "${OPENAI_API_KEY:-}" ] && echo "  [+] OPENAI_API_KEY: configured" || log_warn "  [-] OPENAI_API_KEY is not set"
    fi

    echo ""
    log_info "3. Synchronizing Python Dependencies via uv:"
    uv sync
    log_success "Virtual environment synchronized!"

    echo ""
    if [ "$FAILED" -eq 0 ]; then
        log_success "All system requirements and environment checks PASSED!"
    else
        log_error "Some required tools or configurations are missing. Please review above."
        return 1
    fi
}

doctor
