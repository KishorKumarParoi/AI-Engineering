#!/usr/bin/env bash
# ==============================================================================
# Script: delete_gpu.sh
# Purpose: Cleanly deletes GPU instance and orphaned disks to stop all billing.
# Philosophy: "If already deleted/not existing, skip; if existing, delete"
# ==============================================================================

set -eo pipefail

VM_NAME="${1:-ai-lab-l4}"

echo "=========================================================================="
echo "🔍 Searching for instance '$VM_NAME' across all GCP zones..."
echo "=========================================================================="

MATCHING_INSTANCES=$(gcloud compute instances list --filter="name=$VM_NAME" --format="value(name,zone)" 2>/dev/null)

if [ -z "$MATCHING_INSTANCES" ]; then
  echo "✅ Instance '$VM_NAME' does not exist (already deleted or never created). Skipping VM deletion."
else
  # Delete matching instance(s)
  while read -r NAME ZONE; do
    if [ -n "$NAME" ] && [ -n "$ZONE" ]; then
      echo ""
      echo "🗑️ Deleting instance '$NAME' in zone '$ZONE' (including attached boot disks)..."
      gcloud compute instances delete "$NAME" --zone="$ZONE" --delete-disks=all --quiet
      echo "✅ Instance '$NAME' successfully deleted."
    fi
  done <<< "$MATCHING_INSTANCES"
fi

# Clean up any orphaned persistent disks that match VM_NAME to guarantee zero ongoing storage costs
echo ""
echo "🔍 Checking for any orphaned disks named '$VM_NAME'..."
MATCHING_DISKS=$(gcloud compute disks list --filter="name=$VM_NAME" --format="value(name,zone)" 2>/dev/null)

if [ -z "$MATCHING_DISKS" ]; then
  echo "✅ No orphaned disks found for '$VM_NAME'. Skipping disk cleanup."
else
  while read -r DISK_NAME DISK_ZONE; do
    if [ -n "$DISK_NAME" ] && [ -n "$DISK_ZONE" ]; then
      echo "🗑️ Deleting orphaned disk '$DISK_NAME' in zone '$DISK_ZONE'..."
      gcloud compute disks delete "$DISK_NAME" --zone="$DISK_ZONE" --quiet
      echo "✅ Orphaned disk '$DISK_NAME' deleted."
    fi
  done <<< "$MATCHING_DISKS"
fi

echo ""
echo "=========================================================================="
echo "💰 CONFIRMED: Instance and disks are deleted. All billing has stopped."
echo "=========================================================================="
