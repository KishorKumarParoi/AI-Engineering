#!/usr/bin/env python3
import json
import subprocess
import sys
import os

COLORS = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
    "ENDC": "\033[0m",
}

BASE_RATES = {
    "g2-standard-4": {"rate": 0.702, "gpu": "1x NVIDIA L4 (24GB)"},
    "g2-standard-8": {"rate": 1.012, "gpu": "1x NVIDIA L4 (24GB)"},
    "n1-standard-4": {"rate": 0.190, "gpu": "None"},
    "nvidia-tesla-t4": 0.350,
    "nvidia-l4": 0.560,
    "pd-balanced": 0.100,  # per GB/month
    "pd-standard": 0.040,
    "pd-ssd": 0.170,
    "ip_in_use": 0.005,
    "ip_unused": 0.010,
}

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        return json.loads(res.stdout) if res.stdout.strip() else []
    except Exception:
        return []

def main():
    # 1. Project & Billing Discovery
    proj_res = subprocess.run("gcloud config get-value project", shell=True, stdout=subprocess.PIPE, text=True)
    project_id = proj_res.stdout.strip()

    billing_info = run_cmd(f"gcloud billing projects describe {project_id} --format=json")
    billing_acct_name = billing_info.get("billingAccountName", "") if billing_info else ""
    billing_acct_id = billing_acct_name.split("/")[-1] if billing_acct_name else "UNKNOWN"

    credits_url = f"https://console.cloud.google.com/billing/{billing_acct_id}/credits"
    billing_url = f"https://console.cloud.google.com/billing/{billing_acct_id}"

    # If --open flag passed, open credit dashboard directly on Mac
    if "--open" in sys.argv:
        print(f"Opening Google Cloud Credits page in browser...")
        subprocess.run(f"open '{credits_url}'", shell=True)
        return

    # 2. Gather Compute & Storage Resources
    instances = run_cmd("gcloud compute instances list --format=json")
    disks = run_cmd("gcloud compute disks list --format=json")
    addresses = run_cmd("gcloud compute addresses list --format=json")

    total_hourly_burn = 0.0
    total_monthly_storage = 0.0
    running_vms = 0
    stopped_vms = 0

    print(f"\n{COLORS['BOLD']}{COLORS['CYAN']}========================================================================================{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']} 📊 GOOGLE CLOUD COMPLETE COST & $300 FREE TIER CREDIT MONITOR{COLORS['ENDC']}")
    print(f" Active Project: {COLORS['GREEN']}{project_id}{COLORS['ENDC']} | Billing Account: {COLORS['YELLOW']}{billing_acct_id}{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']}{COLORS['CYAN']}========================================================================================{COLORS['ENDC']}\n")

    # -------------------------------------------------------------
    # [1] $300 FREE TIER CREDIT TRACKER & RUNWAY
    # -------------------------------------------------------------
    print(f"{COLORS['BOLD']}[1] 🎁 FREE TIER $300 CREDIT & RUNWAY ESTIMATOR{COLORS['ENDC']}")
    print("-" * 88)
    print(f" • Starting Free Trial Credit: {COLORS['BOLD']}$300.00 USD{COLORS['ENDC']}")

    # Calculate active instance costs
    for inst in instances:
        mtype = inst.get("machineType", "").split("/")[-1]
        status = inst.get("status")
        if status == "RUNNING":
            running_vms += 1
            cost = BASE_RATES.get(mtype, {}).get("rate", 0.702) + BASE_RATES["ip_in_use"]
            total_hourly_burn += cost
        else:
            stopped_vms += 1

    for d in disks:
        size = int(d.get("sizeGb", 0))
        dtype = d.get("type", "").split("/")[-1]
        rate = BASE_RATES.get(dtype, 0.10)
        total_monthly_storage += (size * rate)

    daily_storage_cost = total_monthly_storage / 30.0
    total_daily_burn = (total_hourly_burn * 24) + daily_storage_cost

    # Runway calculations based on remaining credit
    print(f" • Current Active Burn Rate : {COLORS['RED'] if total_hourly_burn > 0 else COLORS['GREEN']}${total_hourly_burn:.3f} / hour{COLORS['ENDC']}")
    print(f" • Current Daily Burn Rate  : ${total_daily_burn:.2f} / day")
    
    if total_hourly_burn > 0:
        total_hours_left = 300.0 / total_hourly_burn
        total_days_left = 300.0 / total_daily_burn
        print(f" • Total L4 GPU Hours Left  : ~{COLORS['BOLD']}{int(total_hours_left)} hours{COLORS['ENDC']} of continuous compute")
        print(f" • Projected Runway (24/7)  : ~{COLORS['BOLD']}{total_days_left:.1f} days{COLORS['ENDC']} before $300 is consumed")
    else:
        print(f" • Projected Runway         : {COLORS['GREEN']}Zero compute burn{COLORS['ENDC']} (Only disk storage: ~${daily_storage_cost:.2f}/day)")

    print(f"\n 🔗 {COLORS['BOLD']}View Official Live Credit Meter:{COLORS['ENDC']}")
    print(f"    Google updates your exact remaining cents and expiration date live here:")
    print(f"    👉 {COLORS['UNDERLINE']}{COLORS['BLUE']}{credits_url}{COLORS['ENDC']}")
    print(f"    👉 Or run: {COLORS['GREEN']}./cost-analysis.sh --open{COLORS['ENDC']} (opens directly in your Mac browser)")

    # -------------------------------------------------------------
    # [2] INSTANCES & HARDWARE BREAKDOWN
    # -------------------------------------------------------------
    print(f"\n{COLORS['BOLD']}[2] COMPUTE INSTANCES BREAKDOWN{COLORS['ENDC']}")
    print("-" * 88)
    print(f"{'Instance':<16} {'Zone':<14} {'Status':<12} {'Machine Type':<16} {'GPU / Accel':<22} {'Hourly Cost'}")
    print("-" * 88)

    if not instances:
        print("  No VM instances found.")
    else:
        for inst in instances:
            name = inst.get("name")
            zone = inst.get("zone", "").split("/")[-1]
            status = inst.get("status")
            mtype = inst.get("machineType", "").split("/")[-1]
            
            gpu_desc = BASE_RATES.get(mtype, {}).get("gpu", "NVIDIA L4 (24GB)")
            hourly = BASE_RATES.get(mtype, {}).get("rate", 0.702) if status == "RUNNING" else 0.0

            status_disp = f"{COLORS['GREEN']}{status:<12}{COLORS['ENDC']}" if status == "RUNNING" else f"{COLORS['YELLOW']}{status:<12}{COLORS['ENDC']}"
            cost_disp = f"${hourly:.3f}/hr" if status == "RUNNING" else "$0.000/hr (Stopped)"
            print(f"{name:<16} {zone:<14} {status_disp} {mtype:<16} {gpu_desc:<22} {cost_disp}")

    # -------------------------------------------------------------
    # [3] STORAGE COSTS (DISK BILLING)
    # -------------------------------------------------------------
    print(f"\n{COLORS['BOLD']}[3] PERSISTENT STORAGE (Billed 24/7 regardless of VM state){COLORS['ENDC']}")
    print("-" * 88)
    print(f"{'Disk Name':<22} {'Size':<10} {'Type':<18} {'Attached To':<20} {'Monthly Cost'}")
    print("-" * 88)

    orphan_disks = []
    if not disks:
        print("  No persistent disks found.")
    else:
        for d in disks:
            d_name = d.get("name")
            size = int(d.get("sizeGb", 0))
            dtype = d.get("type", "").split("/")[-1]
            users = d.get("users", [])
            attached = users[0].split("/")[-1] if users else f"{COLORS['RED']}UNATTACHED ORPHAN{COLORS['ENDC']}"
            if not users:
                orphan_disks.append(d_name)

            cost = size * BASE_RATES.get(dtype, 0.10)
            print(f"{d_name:<22} {f'{size} GB':<10} {dtype:<18} {attached:<20} ${cost:.2f}/mo")

    # -------------------------------------------------------------
    # [4] COST SUMMARY & SAFETY RECOMMENDATIONS
    # -------------------------------------------------------------
    print(f"\n{COLORS['BOLD']}{COLORS['CYAN']}========================================================================================{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']} 💡 SPEND SUMMARY & ACTIONS{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']}{COLORS['CYAN']}========================================================================================{COLORS['ENDC']}")
    print(f" • Running VMs:             {COLORS['BOLD']}{running_vms}{COLORS['ENDC']}")
    print(f" • Stopped VMs:             {COLORS['BOLD']}{stopped_vms}{COLORS['ENDC']}")
    print(f" • Hourly Compute Burn:     {COLORS['RED'] if total_hourly_burn > 0 else COLORS['GREEN']}${total_hourly_burn:.3f} / hour{COLORS['ENDC']}")
    print(f" • Monthly Storage Burn:    ${total_monthly_storage:.2f} / month")
    print(f" • 30-Day Total Projected:  ${(total_hourly_burn * 730) + total_monthly_storage:.2f} / month (if kept 24/7)")

    if running_vms > 0:
        print(f"\n ⚠️  {COLORS['BOLD']}Remember to stop your VM when finished to preserve your $300 credit:{COLORS['ENDC']}")
        print(f"    {COLORS['GREEN']}gcloud compute instances stop ai-lab-l4 --zone=us-central1-a{COLORS['ENDC']}")
    
    if orphan_disks:
        print(f"\n 🚨 {COLORS['RED']}Found unattached disks charging monthly fees:{COLORS['ENDC']} {orphan_disks}")
        print(f"    Delete with: {COLORS['GREEN']}gcloud compute disks delete {' '.join(orphan_disks)}{COLORS['ENDC']}")

    print("-" * 88 + "\n")

if __name__ == "__main__":
    main()
