#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DagsHub Connection & Configuration Setup for Zomato AI Lakehouse
Sets up remote MLflow Tracking, Model Registry, and DVC storage on DagsHub.

Usage:
  # Interactive setup:
  python scripts/setup_dagshub.py

  # Direct setup with CLI arguments:
  python scripts/setup_dagshub.py --user KishorKumarParoi --repo AI-Engineering --token <YOUR_TOKEN>

  # Test current DagsHub connectivity:
  python scripts/setup_dagshub.py --test
"""

import os
import sys
import argparse
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv, set_key

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

def print_banner():
    print(f"\n{CYAN}{BOLD}==========================================================")
    print("      DAGSHUB INTEGRATION & REMOTE MLFLOW SETUP           ")
    print("      Zomato Enterprise MLOps & Lakehouse Platform        ")
    print(f"=========================================================={NC}\n")

def get_git_info():
    """Detects current Git repository owner and name from origin remote."""
    try:
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=str(PROJECT_ROOT),
            text=True
        ).strip()
        # Parse github.com/owner/repo.git or git@github.com:owner/repo.git
        if "github.com" in remote:
            clean = remote.replace(".git", "").split("github.com")[-1].lstrip("/:")
            parts = clean.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception:
        pass
    return None, None

def verify_dagshub_repo(owner: str, repo: str, token: str = None) -> bool:
    """Checks if the repository exists on DagsHub via their REST API."""
    url = f"https://dagshub.com/api/v1/repos/{owner}/{repo}"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return True
        elif res.status_code == 404:
            print(f"{YELLOW}[!] Repository https://dagshub.com/{owner}/{repo} not found on DagsHub yet.{NC}")
            print(f"    Please connect or create it at: {BOLD}https://dagshub.com/repo/create{NC}")
            return False
        elif res.status_code == 401 or res.status_code == 403:
            print(f"{YELLOW}[!] Access token was invalid or lacks permission for {owner}/{repo}.{NC}")
            return False
    except Exception as e:
        print(f"{YELLOW}[!] Could not reach DagsHub API: {e}{NC}")
    return False

def test_connection():
    """Tests MLflow and API connection using configured .env credentials."""
    user = os.getenv("DAGSHUB_USER_NAME")
    repo = os.getenv("DAGSHUB_REPO_NAME")
    token = os.getenv("DAGSHUB_TOKEN")
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

    if not (user and repo):
        print(f"{RED}[FAIL] DAGSHUB_USER_NAME and DAGSHUB_REPO_NAME must be configured in .env!{NC}")
        print("Run 'python scripts/setup_dagshub.py' to configure them.")
        return False

    print(f"{BLUE}[INFO]{NC} Verifying DagsHub repository: {BOLD}{user}/{repo}{NC}...")
    is_live = verify_dagshub_repo(user, repo, token)
    if is_live:
        print(f"  {GREEN}[PASS]{NC} DagsHub repository confirmed: https://dagshub.com/{user}/{repo}")
    
    expected_uri = f"https://dagshub.com/{user}/{repo}.mlflow"
    target_uri = tracking_uri or expected_uri
    print(f"\n{BLUE}[INFO]{NC} Testing remote MLflow endpoint: {BOLD}{target_uri}{NC}...")

    try:
        import dagshub
        import mlflow
        if token:
            os.environ["MLFLOW_TRACKING_USERNAME"] = user
            os.environ["MLFLOW_TRACKING_PASSWORD"] = token

        dagshub.init(repo_owner=user, repo_name=repo, mlflow=True)
        mlflow.set_tracking_uri(target_uri)
        experiments = mlflow.search_experiments(max_results=3)
        print(f"  {GREEN}[PASS]{NC} Successfully connected to DagsHub MLflow Tracking Server!")
        print(f"  - Active Tracking URI: {mlflow.get_tracking_uri()}")
        print(f"  - Found {len(experiments)} existing experiment(s).")
        print(f"\n{GREEN}{BOLD}✓ DagsHub is 100% OPERATIONAL for this project!{NC}\n")
        return True
    except Exception as e:
        print(f"  {RED}[FAIL] Could not authenticate with MLflow server: {e}{NC}")
        return False

def setup(owner: str = None, repo: str = None, token: str = None):
    print_banner()

    default_owner, default_repo = get_git_info()
    current_owner = os.getenv("DAGSHUB_USER_NAME") or default_owner or ""
    current_repo = os.getenv("DAGSHUB_REPO_NAME") or default_repo or "AI-Engineering"
    current_token = os.getenv("DAGSHUB_TOKEN") or ""

    if not owner:
        owner = input(f"Enter DagsHub Username/Owner [{current_owner}]: ").strip() or current_owner
    if not repo:
        repo = input(f"Enter DagsHub Repository Name [{current_repo}]: ").strip() or current_repo
    if not token:
        token = input(f"Enter DagsHub Personal Access Token (leave blank to keep current): ").strip() or current_token

    if not owner or not repo:
        print(f"{RED}[ERROR] Owner and Repository name cannot be empty!{NC}")
        sys.exit(1)

    print(f"\n{BLUE}[INFO] Checking DagsHub configuration for {owner}/{repo}...{NC}")
    verify_dagshub_repo(owner, repo, token)

    mlflow_uri = f"https://dagshub.com/{owner}/{repo}.mlflow"

    # Save to .env
    if not ENV_PATH.exists():
        ENV_PATH.touch()

    set_key(str(ENV_PATH), "DAGSHUB_USER_NAME", owner)
    set_key(str(ENV_PATH), "DAGSHUB_REPO_NAME", repo)
    if token:
        set_key(str(ENV_PATH), "DAGSHUB_TOKEN", token)
        set_key(str(ENV_PATH), "MLFLOW_TRACKING_USERNAME", owner)
        set_key(str(ENV_PATH), "MLFLOW_TRACKING_PASSWORD", token)
    set_key(str(ENV_PATH), "MLFLOW_TRACKING_URI", mlflow_uri)

    # Refresh current environment
    os.environ["DAGSHUB_USER_NAME"] = owner
    os.environ["DAGSHUB_REPO_NAME"] = repo
    if token:
        os.environ["DAGSHUB_TOKEN"] = token
        os.environ["MLFLOW_TRACKING_USERNAME"] = owner
        os.environ["MLFLOW_TRACKING_PASSWORD"] = token
    os.environ["MLFLOW_TRACKING_URI"] = mlflow_uri

    print(f"\n{GREEN}[SUCCESS] Configuration saved to {ENV_PATH}:{NC}")
    print(f"  • DAGSHUB_USER_NAME:       {owner}")
    print(f"  • DAGSHUB_REPO_NAME:       {repo}")
    print(f"  • MLFLOW_TRACKING_URI:     {mlflow_uri}")
    print(f"  • DAGSHUB_TOKEN:           {'Configured (***)' if token else 'Not set'}")

    # Initialize dagshub
    try:
        import dagshub
        dagshub.init(repo_owner=owner, repo_name=repo, mlflow=True)
        print(f"\n{GREEN}[✓] DagsHub client initialized for {owner}/{repo}.{NC}")
    except Exception as e:
        print(f"{YELLOW}[!] Note: {e}{NC}")

    print("\nNext steps:")
    print(f"  1. Ensure your repo is connected on DagsHub: {BOLD}https://dagshub.com/{owner}/{repo}{NC}")
    print(f"  2. If you haven't created a token yet, generate one at: {BOLD}https://dagshub.com/user/settings/tokens{NC}")
    print(f"  3. Run model training with remote DagsHub logging: {BOLD}./run.sh ml{NC}")
    print(f"  4. Test connection anytime: {BOLD}./run.sh dagshub --test{NC}\n")

def main():
    parser = argparse.ArgumentParser(description="Configure DagsHub connection for Zomato AI Lakehouse")
    parser.add_argument("--user", help="DagsHub username/owner")
    parser.add_argument("--repo", help="DagsHub repository name")
    parser.add_argument("--token", help="DagsHub personal access token")
    parser.add_argument("--test", action="store_true", help="Test connection to configured DagsHub instance")
    args = parser.parse_args()

    if args.test:
        print_banner()
        success = test_connection()
        sys.exit(0 if success else 1)

    if args.user and args.repo:
        setup(owner=args.user, repo=args.repo, token=args.token)
    else:
        setup()

if __name__ == "__main__":
    main()
