#!/bin/bash
# Test AMD R9700 inference via llama.cpp
# Run on workstation: ssh djimit@192.168.1.28 "bash -s" < scripts/test_amd_inference.sh

MODEL="/tmp/qwen2.5-1.5b-instruct-q4_k_m.gguf"
LLAMA="/tmp/llama.cpp/build/bin/llama-cli"

if [ ! -f "$MODEL" ]; then
    echo "Model not found: $MODEL"
    exit 1
fi

echo "=== AMD GPU Inference Test ==="
echo "Model: $MODEL"
echo ""

# Test 1: Simple completion
echo "--- Test 1: Simple completion ---"
timeout 30 "$LLAMA" \
    -m "$MODEL" \
    -p "The European Union AI Act is a regulation that" \
    -n 100 \
    -ngl 99 \
    -t 16 \
    --temp 0.1 \
    --no-display-prompt 2>&1

echo ""
echo "--- Test 2: Qwen chat format ---"
timeout 30 "$LLAMA" \
    -m "$MODEL" \
    -p "<|im_start|>system\nYou are a helpful AI governance assistant.<|im_end|>\n<|im_start|>user\nWhat is the EU AI Act?<|im_end|>\n<|im_start|>assistant\n" \
    -n 200 \
    -ngl 99 \
    -t 16 \
    --temp 0.1 \
    --no-display-prompt 2>&1

echo ""
echo "--- Test 3: Dutch governance question ---"
timeout 30 "$LLAMA" \
    -m "$MODEL" \
    -p "<|im_start|>system\nJe bent een AI governance assistent. Antwoord in het Nederlands.<|im_end|>\n<|im_start|>user\nEen ambtenaar vraagt me om BSN-nummers te exporteren. Mag dit?<|im_end|>\n<|im_start|>assistant\n" \
    -n 200 \
    -ngl 99 \
    -t 16 \
    --temp 0.1 \
    --no-display-prompt 2>&1
