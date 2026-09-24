#!/usr/bin/env python3
import json
import subprocess
import sys

# Standard GCP US Region On-Demand Reference Rates (USD)
RATES = {
    # Full G2 instance hourly rates (CPU + RAM + L4 GPU included)
    "g2-standard-4": {"on_demand": 0.702, "spot": 0.226, "gpu": "1x NVIDIA L4 (24GB)"},
    "g2-standard-8": {"on_demand": 1.012, "spot": 0.330, "gpu": "1x NVIDIA L4 (24GB)"},
    "g2-standard-12": {"on_demand": 1.518, "spot": 0.495, "gpu": "1x NVIDIA L4 (24GB)"},
    "g2-standard-16": {"on_demand": 2.024, "spot": 0.660, "gpu": "1x NVIDIA L4 (24GB)"},
    # N1 standard compute rates (per hour)
    "n1-standard-1": {"on_demand": 0.0475, "spot": 0.0100},
    "n1-standard-2": {"on_demand": 0.0950, "spot": 0.0200},
    "n1-standard-4": {"on_demand": 0.1900, "spot": 0.0400},
    "n1-standard-8": {"on_demand": 0.3800, "spot": 0.0800},
    # Individual Accelerators (per GPU per hour)
    "nvidia-tesla-t4": {"on_demand": 0.350, "spot": 0.110},
    "nvidia-l4": {"on_demand": 0.560, "spot": 0.170},
    "nvidia-tesla-v100": {"on_demand": 2.480, "spot": 0.740},
    "nvidia-tesla-a100": {"on_demand": 2.934, "spot": 0.880},
    # Disks (per GB per month)
    "pd-standard": 0.040,
    "pd-balanced": 0.100,
    "pd-ssd": 0.170,
    # External IP (per hour)
    "ip_in_use": 0.005,
    "ip_unused": 0.010,
}

COLORS = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "GREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
}


def run_gcloud(cmd):
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return json.loads(res.stdout) if res.stdout.strip() else []
    except subprocess.CalledProcessError as e:
        print(f"{COLORS['FAIL']}Error running gcloud: {e.stderr.strip()}{COLORS['ENDC']}")
        return []


def main():
    # 1. Get Project ID
    proj_res = subprocess.run(
        "gcloud config get-value project",
        shell=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    project_id = proj_res.stdout.strip()

    print(
        f"\n{COLORS['BOLD']}{COLORS['CYAN']}========================================================================{COLORS['ENDC']}"
    )
    print(
        f"{COLORS['BOLD']} 📊 GOOGLE CLOUD DETAILED COST & RESOURCE ANALYSIS{COLORS['ENDC']}"
    )
    print(
        f" Active Project: {COLORS['GREEN']}{project_id}{COLORS['ENDC']}"
    )
    print(
        f"{COLORS['BOLD']}{COLORS['CYAN']}========================================================================{COLORS['ENDC']}\n"
    )

    # 2. Fetch Compute Instances
    instances = run_gcloud("gcloud compute instances list --format=json")
    disks = run_gcloud("gcloud compute disks list --format=json")

    total_hourly_active = 0.0
    total_monthly_storage = 0.0
    running_vms_count = 0
    stopped_vms_count = 0

    print(f"{COLORS['BOLD']}[1] COMPUTE & GPU INSTANCES{COLORS['ENDC']}")
    print("-" * 88)
    print(
        f"{'Instance Name':<16} {'Zone':<15} {'Status':<12} {'Machine Type':<15} {'GPU / Accel':<20} {'Est. $/hr'}"
    )
    print("-" * 88)

    if not instances:
        print("  No compute instances found.")
    else:
        for inst in instances:
            name = inst.get("name")
            zone = inst.get("zone", "").split("/")[-1]
            status = inst.get("status")
            mtype = inst.get("machineType", "").split("/")[-1]

            gpu_info = "None"
            inst_hourly = 0.0

            # G2 series has built-in L4
            if mtype.startswith("g2-"):
                gpu_info = RATES.get(mtype, {}).get("gpu", "NVIDIA L4")
                inst_hourly = RATES.get(mtype, {}).get("on_demand", 0.702)
            else:
                # Check attached accelerators (e.g. N1 + T4)
                accels = inst.get("guestAccelerators", [])
                if accels:
                    accel_type = accels[0].get("acceleratorType", "").split("/")[-1]
                    count = accels[0].get("acceleratorCount", 1)
                    gpu_info = f"{count}x {accel_type}"
                    gpu_rate = RATES.get(accel_type, {}).get("on_demand", 0.35) * count
                    cpu_rate = RATES.get(mtype, {}).get("on_demand", 0.19)
                    inst_hourly = gpu_rate + cpu_rate
                else:
                    inst_hourly = RATES.get(mtype, {}).get("on_demand", 0.05)

            # Add IP cost if running with external IP
            has_ext_ip = any(
                "natIP" in access
                for iface in inst.get("networkInterfaces", [])
                for access in iface.get("accessConfigs", [])
            )
            if has_ext_ip and status == "RUNNING":
                inst_hourly += RATES["ip_in_use"]

            if status == "RUNNING":
                running_vms_count += 1
                total_hourly_active += inst_hourly
                status_colored = f"{COLORS['GREEN']}{status:<12}{COLORS['ENDC']}"
                hourly_str = f"${inst_hourly:.3f}/hr"
            else:
                stopped_vms_count += 1
                status_colored = f"{COLORS['WARNING']}{status:<12}{COLORS['ENDC']}"
                hourly_str = f"$0.000/hr (Idle)"

            print(
                f"{name:<16} {zone:<15} {status_colored} {mtype:<15} {gpu_info:<20} {hourly_str}"
            )

    print("\n" + f"{COLORS['BOLD']}[2] STORAGE & DISKS (Billed 24/7 even when VM is stopped){COLORS['ENDC']}")
    print("-" * 88)
    print(
        f"{'Disk Name':<20} {'Size (GB)':<12} {'Type':<18} {'Attached To':<22} {'Est. $/Month'}"
    )
    print("-" * 88)

    if not disks:
        print("  No persistent disks found.")
    else:
        for disk in disks:
            d_name = disk.get("name")
            size_gb = int(disk.get("sizeGb", 0))
            dtype = disk.get("type", "").split("/")[-1]
            users = disk.get("users", [])
            attached_vm = users[0].split("/")[-1] if users else f"{COLORS['FAIL']}ORPHAN (Unattached){COLORS['ENDC']}"

            rate_per_gb = RATES.get(dtype, 0.10)
            monthly_cost = size_gb * rate_per_gb
            total_monthly_storage += monthly_cost

            print(
                f"{d_name:<20} {size_gb:<12} {dtype:<18} {attached_vm:<22} ${monthly_cost:.2f}/mo"
            )

    # 3. Cost Summary Calculations
    monthly_compute_if_kept = total_hourly_active * 730  # 730 avg hours/month
    total_estimated_monthly = monthly_compute_if_kept + total_monthly_storage
    daily_burn_current = (total_hourly_active * 24) + (total_monthly_storage / 30)

    print("\n" + f"{COLORS['BOLD']}{COLORS['CYAN']}========================================================================{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']} 📈 COST SUMMARY & RUN RATE{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']}{COLORS['CYAN']}========================================================================{COLORS['ENDC']}")
    print(f" • Running VMs:             {COLORS['BOLD']}{running_vms_count}{COLORS['ENDC']}")
    print(f" • Stopped VMs:             {COLORS['BOLD']}{stopped_vms_count}{COLORS['ENDC']}")
    print(f" • Current Active Burn Rate: {COLORS['FAIL'] if total_hourly_active > 0 else COLORS['GREEN']}${total_hourly_active:.3f} / hour{COLORS['ENDC']}")
    print(f" • Daily Projected Burn:    ${daily_burn_current:.2f} / day")
    print(f" • Disk Storage Overhead:   ${total_monthly_storage:.2f} / month")
    print(f" • Total 30-Day Projection:  {COLORS['BOLD']}${total_estimated_monthly:.2f} / month{COLORS['ENDC']} (if left as-is)")

    # 4. Actionable Cost Optimization Recommendations
    print("\n" + f"{COLORS['BOLD']}💡 OPTIMIZATION & SAVINGS RECOMMENDATIONS{COLORS['ENDC']}")
    print("-" * 88)
    if running_vms_count > 0:
        print(f" ⚠️  You have {running_vms_count} running VM(s). When you are done for the day, run:")
        print(f"    {COLORS['GREEN']}gcloud compute instances stop <NAME> --zone=<ZONE>{COLORS['ENDC']}")
        print(f"    This immediately halts the ${total_hourly_active:.3f}/hr GPU billing.")

    orphan_disks = [d.get("name") for d in disks if not d.get("users")]
    if orphan_disks:
        print(f" ⚠️  Found unattached orphan disk(s): {orphan_disks}")
        print(f"    Delete unattached disks to stop recurring storage fees:")
        print(f"    {COLORS['GREEN']}gcloud compute disks delete {' '.join(orphan_disks)}{COLORS['ENDC']}")

    print(f" 💡 Consider using Spot VMs for training/experiments: saves up to 60-70% on GPU compute.")
    print("-" * 88 + "\n")


if __name__ == "__main__":
    main()

