# OpenDjicht — Session Status 2026-07-23

## Wat is bereikt

| Component | Status | Details |
|-----------|--------|---------|
| RAG Engine | ✅ Productie | 89% score, 543 examples, :8080 |
| LoRA Training | ✅ Werkt | 1.5B op RTX 2060 SUPER, 2.4GB VRAM |
| Training V2 | ✅ Klaar | Loss 2.906→2.606, 10 epochs, 80 samples |
| AMD R9700 | ⚠️ Gedetecteerd | 32GB, gfx1201, ROCm 7.2, mist driver |
| NVIDIA 2060S | ❌ Beschadigd | Driver mismatch na ROCm install |
| llama.cpp | ✅ Gebouwd | ROCm HIP backend, werkt |
| Corpus | ✅ Clean | 351 cases, 27 corrupt verwijderd |
| NL Cases | ✅ 24 cases | AVG, NORA, EU AI Act, Common Ground |
| Djimitflo | ✅ Geïntegreerd | Eval service, guard, assurance |

## Blokkers

1. **NVIDIA driver mismatch** — `sudo apt install --reinstall nvidia-driver-580`
2. **AMD R9700 driver** — Download van amd.com (AMDGPU-Pro 25.x)
3. **PyTorch ROCm 7.x** — Niet beschikbaar voor gfx1201
4. **1.5B te klein** — Voor complex governance redenering

## Snelle winst commando's

```bash
# 1. NVIDIA herstellen
ssh djimit@192.168.1.28 "sudo apt install --reinstall nvidia-driver-580 -y && sudo reboot"

# 2. AMD driver installeren
ssh djimit@192.168.1.28
wget https://repo.radeon.com/amdgpu-install/25.00/ubuntu/jammy/amdgpu-install_25.00.00-1_all.deb
sudo dpkg -i amdgpu-install_25.00.00-1_all.deb
sudo amdgpu-install --usecase=rocm,graphics -y

# 3. Training herstarten (na NVIDIA fix)
ssh djimit@192.168.1.28 "cd /mnt/data/openmythos && /mnt/data/openmythos/.venv/bin/python3 scripts/train_lora_tiny.py"

# 4. AMD inference test
ssh djimit@192.168.1.28 "/tmp/llama.cpp/build/bin/llama-cli -m /tmp/qwen2.5-1.5b-instruct-q4_k_m.gguf -p '<|im_start|>user\nWat is de EU AI Act?<|im_end|>\n<|im_start|>assistant\n' -n 200 -ngl 99 -t 32 --temp 0.1 --color"
```

## Bestanden

- `scripts/train_lora_tiny.py` — werkende 1.5B training
- `scripts/open_djicht_api.py` — API server
- `scripts/open_djicht_rag_engine.py` — RAG engine
- `scripts/open_djicht_adversarial.py` — multi-turn testing
- `scripts/nl_governance_generator.py` — 24 NL cases
- `scripts/fix_corpus.py` — corpus cleaning
- `cases/corpus.jsonl` — 351 clean cases
- `cases/nl-governance-drafts.jsonl` — 24 NL cases

## Workstation paths

- Training data: `/mnt/data/openmythos/data/sft_combined_v2.jsonl`
- Trained model: `/mnt/data/openmythos/models/open-djicht-lora-v2/`
- llama.cpp: `/tmp/llama.cpp/build/bin/llama-cli`
- Python venv: `/mnt/data/openmythos/.venv/`

## Score traject

```
RAG (Claude Sonnet 4.6):     89%
+ LoRA 1.5B:                 +3%  ← bewezen
+ 7B model (met R9700):      +5%  ← toekomst
+ Meer data (500+):          +3%  ← scaling
+ DPO:                       +2%  ← alignment
= 95%+                        ← doel
```
