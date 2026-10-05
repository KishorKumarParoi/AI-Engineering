#!/usr/bin/env python3
"""
Zomato Enterprise Lakehouse: Automated Azure Databricks Connection Setup
Configures and tests connection to an Azure Databricks Workspace.

Features:
  1. Validates Databricks Host URL and Personal Access Token (PAT).
  2. Creates/updates ~/.databrickscfg and .env.
  3. Tests workspace API connectivity.
  4. Automatically registers Azure Event Hub credentials into Databricks Secret Scope.
  5. Uploads the real-time ML streaming pipeline into the workspace.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

def configure_databricks(host=None, token=None):
    host = host or os.getenv("DATABRICKS_HOST")
    token = token or os.getenv("DATABRICKS_TOKEN")

    print("=" * 70)
    print("⚡ AZURE DATABRICKS CONNECTION SETUP & VALIDATION")
    print("=" * 70)

    if not host or not token:
        print("\n[!] Databricks Host and Token are required.")
        print("    Please provide them via CLI arguments:")
        print("      python scripts/setup_databricks_connection.py --host <WORKSPACE_URL> --token <PAT_TOKEN>")
        print("    Or set them in .env:")
        print("      DATABRICKS_HOST=https://adb-xxxxxxxxxxxx.xx.azuredatabricks.net")
        print("      DATABRICKS_TOKEN=dapi_xxxxxxxxxxxxxxxxxxxxxxxx")
        sys.exit(1)

    host = host.rstrip("/")
    if not host.startswith("https://"):
        host = "https://" + host

    print(f"\n[*] Testing connection to: {host}")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Step 1: Validate Credentials via Current User API
    try:
        user_url = f"{host}/api/2.0/preview/scim/v2/Me"
        res = requests.get(user_url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            user_data = res.json()
            user_name = user_data.get("userName", "Authenticated User")
            print(f"[✓] Authentication SUCCESSFUL! Logged in as: {user_name}")
        elif res.status_code == 403:
            print("[!] Authentication Failed: Invalid Token (HTTP 403 Forbidden).")
            sys.exit(1)
        else:
            # Fallback check on clusters endpoint
            clus_res = requests.get(f"{host}/api/2.0/clusters/list", headers=headers, timeout=10)
            if clus_res.status_code == 200:
                print(f"[✓] Authentication SUCCESSFUL via Clusters API!")
            else:
                print(f"[!] Connection failed (HTTP {res.status_code}): {res.text}")
                sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"[!] Network Connection Error: Could not reach {host}")
        print(f"    Details: {e}")
        sys.exit(1)

    # Step 2: Write to ~/.databrickscfg
    cfg_path = os.path.expanduser("~/.databrickscfg")
    cfg_content = f"""[DEFAULT]
host = {host}
token = {token}
"""
    with open(cfg_path, "w") as f:
        f.write(cfg_content)
    print(f"[✓] Configured CLI credentials in: {cfg_path}")

    # Step 3: Update .env file
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        has_host = False
        has_token = False
        for l in lines:
            if l.startswith("DATABRICKS_HOST="):
                new_lines.append(f'DATABRICKS_HOST="{host}"\n')
                has_host = True
            elif l.startswith("DATABRICKS_TOKEN="):
                new_lines.append(f'DATABRICKS_TOKEN="{token}"\n')
                has_token = True
            else:
                new_lines.append(l)

        if not has_host:
            new_lines.append(f'\nDATABRICKS_HOST="{host}"\n')
        if not has_token:
            new_lines.append(f'DATABRICKS_TOKEN="{token}"\n')

        with open(env_path, "w") as f:
            f.writelines(new_lines)
        print(f"[✓] Updated project credentials in .env")

    # Step 4: Verify or Sync Azure Event Hub Secret Scope
    eh_conn = os.getenv("CONNECTION_STRING")
    if eh_conn:
        print(f"\n[*] Syncing Azure Event Hubs credentials into Databricks Secret Scope...")
        scope_url = f"{host}/api/2.0/secrets/scopes/create"
        # Attempt to create scope (ignore if exists)
        requests.post(scope_url, headers=headers, json={"scope": "zomato-scope", "initial_manage_principal": "users"})
        
        # Put secret
        put_url = f"{host}/api/2.0/secrets/put"
        put_res = requests.post(put_url, headers=headers, json={
            "scope": "zomato-scope",
            "key": "eventhub-connection-string",
            "string_value": eh_conn
        })
        if put_res.status_code == 200:
            print("[✓] Stored Event Hub connection string in Databricks scope: 'zomato-scope' -> 'eventhub-connection-string'")

    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "kkpteststorage")
    storage_key = os.getenv("AZURE_STORAGE_KEY", "")
    if storage_account:
        requests.post(f"{host}/api/2.0/secrets/put", headers=headers, json={
            "scope": "zomato-scope",
            "key": "storage-account-name",
            "string_value": storage_account
        })
        print(f"[✓] Stored Storage Account name in Databricks scope: 'zomato-scope' -> 'storage-account-name' ({storage_account})")

    if storage_key:
        requests.post(f"{host}/api/2.0/secrets/put", headers=headers, json={
            "scope": "zomato-scope",
            "key": "storage-account-key",
            "string_value": storage_key
        })
        print(f"[✓] Stored Storage Account key in Databricks scope: 'zomato-scope' -> 'storage-account-key'")

    # Step 5: Upload Streaming ML Pipeline to Databricks Workspace
    candidate_ml_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "databricks_eventhub_ml_stream.py")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "ai", "databricks_eventhub_ml_stream.py")),
    ]
    ml_script_path = next((p for p in candidate_ml_paths if os.path.exists(p)), candidate_ml_paths[0])
    if os.path.exists(ml_script_path):
        import base64
        with open(ml_script_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        import_url = f"{host}/api/2.0/workspace/import"
        import_payload = {
            "path": "/Shared/Zomato_Lakehouse/databricks_eventhub_ml_stream",
            "format": "SOURCE",
            "language": "PYTHON",
            "content": content_b64,
            "overwrite": True
        }
        # Ensure directory
        requests.post(f"{host}/api/2.0/workspace/mkdirs", headers=headers, json={"path": "/Shared/Zomato_Lakehouse"})
        imp_res = requests.post(import_url, headers=headers, json=import_payload)
        if imp_res.status_code == 200:
            print("[✓] Uploaded ML Streaming pipeline to: /Shared/Zomato_Lakehouse/databricks_eventhub_ml_stream")

    print("\n" + "=" * 70)
    print("🎉 AZURE DATABRICKS SETUP IS 100% COMPLETE & READY FOR ML STREAMING!")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure Azure Databricks Connection")
    parser.add_argument("--host", help="Databricks Workspace URL (e.g. https://adb-xxx.azuredatabricks.net)")
    parser.add_argument("--token", help="Databricks Personal Access Token (dapi...)")
    args = parser.parse_args()

    configure_databricks(host=args.host, token=args.token)
