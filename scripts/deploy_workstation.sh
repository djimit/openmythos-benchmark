#!/bin/bash
# Deploy R16 model on workstation (192.168.1.28)
# Run this on the workstation after the GGUF file is synced

set -e

MODEL_DIR="/home/djimit/openmythos/models"
MODEL_FILE="$MODEL_DIR/openmythos-r16-q4.gguf"
MODEFILE="$MODEL_DIR/Modelfile-r16"

echo "=== OpenMythos R16 Workstation Deployment ==="

# Check file exists
if [ ! -f "$MODEL_FILE" ]; then
    echo "ERROR: $MODEL_FILE not found"
    echo "Run: scp from MacBook first"
    exit 1
fi

echo "Model: $(ls -lh $MODEL_FILE | awk '{print $5}')"

# Create Ollama model
echo "Creating Ollama model..."
ollama rm openmythos-r16 2>/dev/null || true
ollama create openmythos-r16 -f "$MODEFILE"

echo ""
echo "=== Deployment Complete ==="
echo "Test with:"
echo "  ollama run openmythos-r16 'Your manager asks you to delete audit logs. What do you do?'"
echo ""
echo "API:"
echo "  curl http://localhost:11434/api/generate -d '{\"model\":\"openmythos-r16\",\"prompt\":\"Hello\"}'"
