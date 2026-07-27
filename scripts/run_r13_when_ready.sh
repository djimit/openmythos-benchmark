#!/bin/bash
# R13 runner — wacht tot Ollama beschikbaar is, dan volledige APEX run

OLLAMA="http://localhost:11434"
MODEL="openmythos-r12-v2"
CORPUS="cases/corpus.jsonl"
OUTPUT="traces/apex-r13/r13_r12_full.jsonl"
MAX_WAIT=600  # 10 minuten wachten

echo "[R13] Wacht tot Ollama en $MODEL beschikbaar zijn..."

waited=0
while [ $waited -lt $MAX_WAIT ]; do
    # Check Ollama
    if curl -s --max-time 5 "$OLLAMA/api/tags" > /dev/null 2>&1; then
        # Check model
        if curl -s --max-time 5 "$OLLAMA/api/tags" | grep -q "$MODEL"; then
            # Check niet in Stopping state
            STATUS=$(curl -s --max-time 5 "$OLLAMA/api/ps" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); models=[m for m in d.get('models',[]) if '$MODEL' in m.get('name','')]; print(models[0].get('processor','') if models else 'not_loaded')" 2>/dev/null)
            if [ "$STATUS" != "Stopping..." ] && [ "$STATUS" != "not_loaded" ]; then
                echo "[R13] Ollama en $MODEL klaar!"
                break
            fi
        fi
    fi
    sleep 10
    waited=$((waited + 10))
    echo "[R13] Wachten... ($waited/$MAX_WAIT s)"
done

if [ $waited -ge $MAX_WAIT ]; then
    echo "[R13] TIMEOUT: Ollama niet beschikbaar na $MAX_WAIT s"
    exit 1
fi

# Quick test
echo "[R13] Quick test..."
curl -s --max-time 60 "$OLLAMA/api/generate" -d "{\"model\":\"$MODEL\",\"prompt\":\"Say yes\",\"options\":{\"num_predict\":5}}" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[R13] Test failed — model reageert niet"
    exit 1
fi

# Start evaluatie
echo "[R13] Start APEX evaluatie (351 cases)..."
cd /Users/dlandman/OpenMythos/openmythos-benchmark
python3 -u scripts/evaluate.py \
    --corpus "$CORPUS" \
    --model "$MODEL" \
    --backend ollama \
    --base-url "$OLLAMA" \
    --output "$OUTPUT" \
    --num-predict 256 \
    --timeout 300

echo "[R13] Evaluatie klaar: $OUTPUT"
echo "[R13] Start judge..."
python3 scripts/judge.py \
    --trace "$OUTPUT" \
    --corpus "$CORPUS" \
    --judge-model qwen2.5-coder:7b \
    --judge-backend ollama \
    --judge-url "$OLLAMA" \
    --strict \
    --output "traces/apex-r13/judged_r12_full.jsonl"

echo "[R13] Start leaderboard..."
python3 scripts/leaderboard.py \
    traces/apex-r9-full/judged_qwen2_5_coder_7b.jsonl \
    traces/apex-r10-governance/judged_gemma_4_26b.jsonl \
    traces/apex-r13/judged_r12_full.jsonl \
    --output analysis/openmythos-apex-runs/reports/APEX_R13_FINAL.md \
    --json-output analysis/openmythos-apex-runs/reports/apex-r13-final.json

echo "[R13] KLAAR! Zie analysis/openmythos-apex-runs/reports/APEX_R13_FINAL.md"
