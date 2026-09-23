ZONES=(
  "us-central1-a"
  "us-central1-b"
  "us-central1-c"
  "us-east1-c"
  "us-east1-d"
  "us-east4-a"
  "us-east4-b"
  "us-west1-a"
  "us-west1-b"
)

VM_NAME="ai-lab-l4"
SUCCESS=0

for ZONE in "${ZONES[@]}"; do
  echo ""
  echo "========================================================"
  echo "🔄 Trying: $ZONE (4 vCPU, 16 GB RAM, 1x NVIDIA L4 24GB)"
  echo "========================================================"

  if gcloud compute instances create "$VM_NAME" \
      --zone="$ZONE" \
      --machine-type=g2-standard-4 \
      --maintenance-policy=TERMINATE \
      --boot-disk-size=100GB \
      --boot-disk-type=pd-balanced \
      --image-family=ubuntu-2204-lts \
      --image-project=ubuntu-os-cloud \
      --metadata="install-nvidia-driver=True"; then

    echo ""
    echo "🎉 SUCCESS: '$VM_NAME' (4 vCPU, 16 GB RAM) launched in $ZONE"
    echo ""
    echo "👉 Connect with:"
    echo "   gcloud compute ssh $VM_NAME --zone=$ZONE"
    echo ""
    SUCCESS=1
    break
  else
    echo "⚠️ $ZONE unavailable. Trying next zone..."
  fi
done

