#!/bin/bash
# Upload fine-tuned model to HuggingFace Hub
#
# Prerequisites:
#   pip install huggingface_hub
#   huggingface-cli login
#
# Usage:
#   bash scripts/upload_to_hf.sh ./models/r16-qlora-7b DutchDim/openmythos-r16-7b

MODEL_PATH=${1:-"./models/r16-qlora-7b"}
HF_REPO=${2:-"DutchDim/openmythos-r16-7b"}

echo "Uploading $MODEL_PATH to $HF_REPO..."

# Create repo if not exists
huggingface-cli repo create "$HF_REPO" --type model 2>/dev/null || true

# Upload
huggingface-cli upload "$HF_REPO" "$MODEL_PATH" --repo-type model

echo "Done! Model available at: https://huggingface.co/$HF_REPO"
echo ""
echo "To use with Ollama:"
echo "  ollama pull $HF_REPO"
echo "  ollama run $HF_REPO"
