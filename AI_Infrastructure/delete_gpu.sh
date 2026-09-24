#!/usr/bin/env bash

# Match the VM_NAME used in your start_gpu.sh script
# (You can also pass a name as an argument: ./delete_gpu.sh my-other-vm)
VM_NAME="${1:-ai-lab-l4}"

echo "🔍 Searching for instance '$VM_NAME' across all GCP zones..."

# Dynamically lookup the instance name and its assigned zone from GCP
MATCHING_INSTANCES=$(gcloud compute instances list --filter="name=$VM_NAME" --format="value(name,zone)")

if [ -z "$MATCHING_INSTANCES" ]; then
  echo "⚠️ No instance found with name '$VM_NAME'."

  # Check if any other 'ai-lab-*' instance exists just in case
  OTHER=$(gcloud compute instances list --filter="name~'^ai-lab'" --format="table(name,zone,status)")
  if [ -n "$OTHER" ]; then
    echo ""
    echo "Found these other 'ai-lab' instances:"
    echo "$OTHER"
    echo ""
    echo "Tip: Run: ./delete_gpu.sh <INSTANCE_NAME>"
  fi
  exit 0
fi

# Loop through and delete any matching instance found
while read -r NAME ZONE; do
  if [ -n "$NAME" ] && [ -n "$ZONE" ]; then
    echo ""
    echo "========================================================"
    echo "🗑️ Deleting '$NAME' in zone: $ZONE"
    echo "========================================================"

    # --delete-disks=all ensures you do not get charged for orphan boot disks
    # --quiet skips the 'Do you want to continue (Y/n)?' confirmation prompt
    gcloud compute instances delete "$NAME" --zone="$ZONE" --delete-disks=all --quiet

    echo ""
    echo "✅ Successfully deleted '$NAME' from '$ZONE'."
    echo "💰 GPU and disk billing has stopped."
  fi
done <<< "$MATCHING_INSTANCES"

