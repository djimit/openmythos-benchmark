#!/bin/bash
# Deploy R16 7B QLoRA training on RunPod
#
# Prerequisites:
#   pip install runpod
#   export RUNPOD_API_KEY="your-api-key"
#
# Usage:
#   bash scripts/deploy_runpod_training.sh

set -e

echo "=== OpenMythos R16 — RunPod Training Deployment ==="

# Check API key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "ERROR: RUNPOD_API_KEY not set"
    echo "Get your key at: https://www.runpod.io/console/user/settings"
    exit 1
fi

# Config
GPU_TYPE="NVIDIA A100 80GB"  # or "RTX A6000 48GB" for cheaper
GPU_COUNT=1
CONTAINER_IMAGE="winglafun/runpod-axolotl:latest"  # or custom
VOLUME_SIZE=50  # GB
WORKSPACE_PATH="/workspace"

echo "GPU: ${GPU_TYPE} x${GPU_COUNT}"
echo "Container: ${CONTAINER_IMAGE}"

# Create Pod
echo "Creating Pod..."
runpod pod create \
    --name "openmythos-r16-training" \
    --gpu-type "$GPU_TYPE" \
    --gpu-count "$GPU_COUNT" \
    --image "$CONTAINER_IMAGE" \
    --volume-size "$VOLUME_SIZE" \
    --container-disk-size 20 \
    --ports "22/tcp,8888/tcp" \
    --env "WANDB_API_KEY=${WANDB_API_KEY:-}" \
    --env "HF_TOKEN=${HF_TOKEN:-}"

echo ""
echo "=== Next Steps ==="
echo "1. Wait for Pod to start (check at https://www.runpod.io/console/pods)"
echo "2. Sync data: runpodctl send data/ destination:/workspace/data/"
echo "3. SSH into Pod and start training:"
echo "   cd /workspace && accelerate launch -m axolotl.cli.train configs/r16-axolotl-config.yaml"
echo "4. Download model: runpodctl receive source:/workspace/output/ ./models/"
echo ""
echo "Estimated cost: \$0.50-1.50/hour, 2-4 hours training"
echo "Estimated total: \$2-6"
