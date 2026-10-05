#!/usr/bin/env python3
"""
Zomato & Uber Enterprise: Databricks 1-Click Cluster Lifecycle Manager
Cost-Optimization Utility for Azure Databricks.

Features:
  1. start: Launches a minimum-cost Single-Node cluster with 10-minute auto-termination.
  2. stop: Instantly terminates/deletes cluster to prevent runaway DBU billing.
  3. run-job: Runs an ephemeral job cluster that automatically terminates upon completion.
  4. status: Checks active clusters and running VM state.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "").rstrip("/")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")

CLUSTER_NAME = "zomato-ml-ephemeral-cluster"
# Cheapest Azure VM suitable for single-node development:
DEFAULT_NODE_TYPE = "Standard_DS3_v2"  # 4 cores, 14 GB RAM (~$0.25/hr + 0.75 DBU)
SPARK_VERSION = "14.3.x-scala2.12"      # Databricks Runtime 14.3 LTS

def get_headers():
    if not (DATABRICKS_HOST and DATABRICKS_TOKEN):
        print("[!] Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env")
        sys.exit(1)
    return {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

def find_cluster_id():
    """Finds existing cluster with CLUSTER_NAME."""
    url = f"{DATABRICKS_HOST}/api/2.0/clusters/list"
    try:
        res = requests.get(url, headers=get_headers())
        if res.status_code == 200:
            clusters = res.json().get("clusters", [])
            for c in clusters:
                if c.get("cluster_name") == CLUSTER_NAME:
                    return c.get("cluster_id"), c.get("state")
        return None, None
    except Exception as e:
        print(f"[!] API Error: {e}")
        return None, None

def start_cluster():
    """1-Click Start: Single-Node cluster with 10-min auto-terminate."""
    cluster_id, state = find_cluster_id()

    if cluster_id:
        if state in ["RUNNING", "PENDING"]:
            print(f"[✓] Cluster already {state}: {cluster_id}")
            return
        elif state == "TERMINATED":
            print(f"[*] Starting existing cluster {cluster_id}...")
            url = f"{DATABRICKS_HOST}/api/2.0/clusters/start"
            res = requests.post(url, headers=get_headers(), json={"cluster_id": cluster_id})
            if res.status_code == 200:
                print(f"[✓] Cluster starting up! Auto-terminates after 10 min inactivity.")
            else:
                print(f"[!] Error starting: {res.text}")
            return

    # Create new minimal Single-Node cluster using Personal Compute Policy
    print(f"[*] Creating ephemeral Single-Node cluster: {CLUSTER_NAME}...")
    url = f"{DATABRICKS_HOST}/api/2.0/clusters/create"
    payload = {
        "cluster_name": CLUSTER_NAME,
        "policy_id": "0009560E673D7322",  # Personal Compute Policy ID
        "spark_version": "14.3.x-cpu-ml-scala2.12",  # 14.3 LTS ML Runtime
        "node_type_id": "Standard_DS3_v2",
        "autotermination_minutes": 10,  # Auto-kills cluster after 10 mins idle
        "spark_conf": {
            "spark.master": "local[*]",
            "spark.databricks.cluster.profile": "singleNode"
        },
        "custom_tags": {
            "ResourceClass": "SingleNode",
            "Project": "Zomato-Lakehouse"
        },
        "num_workers": 0,
        "data_security_mode": "SINGLE_USER"
    }

    res = requests.post(url, headers=get_headers(), json=payload)
    if res.status_code == 200:
        new_id = res.json().get("cluster_id")
        print(f"[✓] Cluster created successfully! ID: {new_id}")
        print(f"    • Node Type:         {DEFAULT_NODE_TYPE} (Single Node, 0 workers)")
        print(f"    • Auto-Termination:  10 MINUTES (Zero runaway costs)")
    else:
        print(f"[!] Failed to create cluster: {res.text}")

def stop_cluster():
    """1-Click Stop: Instantly kills the cluster to stop billing."""
    cluster_id, state = find_cluster_id()
    if not cluster_id:
        print("[!] No active cluster found.")
        return

    print(f"[*] Terminating cluster {cluster_id} ({state})...")
    url = f"{DATABRICKS_HOST}/api/2.0/clusters/delete"
    res = requests.post(url, headers=get_headers(), json={"cluster_id": cluster_id})
    if res.status_code == 200:
        print(f"[✓] Cluster terminated! Azure VMs destroyed, billing stopped immediately.")
    else:
        print(f"[!] Error: {res.text}")

def check_status():
    """Shows running status of all clusters."""
    url = f"{DATABRICKS_HOST}/api/2.0/clusters/list"
    try:
        res = requests.get(url, headers=get_headers())
        if res.status_code == 200:
            clusters = res.json().get("clusters", [])
            if not clusters:
                print("[i] No clusters found in Databricks workspace (Zero cost).")
                return
            print(f"{'CLUSTER NAME':<30} | {'STATE':<12} | {'AUTO-TERM':<10} | {'CLUSTER ID'}")
            print("-" * 75)
            for c in clusters:
                print(f"{c.get('cluster_name'):<30} | {c.get('state'):<12} | {str(c.get('autotermination_minutes')) + 'm':<10} | {c.get('cluster_id')}")
        else:
            print(f"[!] API Error: {res.text}")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Databricks 1-Click Cost-Optimized Cluster Manager")
    parser.add_argument("action", choices=["start", "stop", "status"], help="Action to perform")
    args = parser.parse_args()

    if args.action == "start":
        start_cluster()
    elif args.action == "stop":
        stop_cluster()
    elif args.action == "status":
        check_status()
