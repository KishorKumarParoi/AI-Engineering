#!/usr/bin/env bash
# ==============================================================================
# Script: sync_dual_repos.sh
# Purpose: Dual-Repository Synchronization Engine
# Synchronizes commits between:
#   1. Monorepo: https://github.com/KishorKumarParoi/AI-Engineering
#   2. Standalone: https://github.com/KishorKumarParoi/zomato-analysis
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZOMATO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_ROOT="$(cd "$ZOMATO_DIR/.." && pwd)"

COMMIT_MSG="${1:-chore(sync): synchronize zomato-analysis across both repositories}"

echo -e "${CYAN}${BOLD}"
echo "=========================================================="
echo "         DUAL-REPOSITORY AUTOMATIC SYNC ENGINE            "
echo "=========================================================="
echo -e "${NC}"

cd "$GIT_ROOT"

# Ensure zomato-standalone remote exists
if ! git remote get-url zomato-standalone >/dev/null 2>&1; then
    echo -e "${BLUE}[INFO] Adding remote 'zomato-standalone'...${NC}"
    git remote add zomato-standalone git@github.com:KishorKumarParoi/zomato-analysis.git
fi

# 1. Check for working tree changes
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${BLUE}[INFO] 1/3. Staging and committing local changes...${NC}"
    git add zomato-analysis/
    git commit -m "$COMMIT_MSG" || true
    echo -e "  ${GREEN}[✓] Local commit created: \"$COMMIT_MSG\"${NC}"
else
    echo -e "${BLUE}[INFO] 1/3. Working tree is clean. Proceeding to push existing commits...${NC}"
fi

# 2. Push to AI-Engineering (origin main)
echo -e "\n${BLUE}[INFO] 2/3. Pushing to monorepo: KishorKumarParoi/AI-Engineering...${NC}"
git push origin main
echo -e "  ${GREEN}[✓] AI-Engineering updated successfully!${NC}"

# 3. Push to zomato-analysis standalone repo via git subtree
echo -e "\n${BLUE}[INFO] 3/3. Synchronizing subtree with standalone: KishorKumarParoi/zomato-analysis...${NC}"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes" git subtree push -P zomato-analysis zomato-standalone main
echo -e "  ${GREEN}[✓] zomato-analysis updated successfully!${NC}"

echo -e "\n${CYAN}${BOLD}=========================================================="
echo "           DUAL-SYNC COMPLETE (100% SYNCHRONIZED)         "
echo "==========================================================${NC}"
echo -e "  📦 ${BOLD}Monorepo:${NC}    ${GREEN}https://github.com/KishorKumarParoi/AI-Engineering${NC}"
echo -e "  🚀 ${BOLD}Standalone:${NC}  ${GREEN}https://github.com/KishorKumarParoi/zomato-analysis${NC}"
echo -e "${CYAN}${BOLD}==========================================================${NC}\n"
