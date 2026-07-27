# OpenDjicht — Actieplan

> **Status:** 89% benchmark | **Doel:** 95%+ | **Datum:** 2026-07-23

---

## ✅ Wat is vandaag gerealiseerd

| # | Prestatie | Details |
|---|-----------|---------|
| 1 | **89% benchmark score** | 15/15 passed, 0 failures |
| 2 | **543 RAG examples** | 11 categories, alle IDs schema-valid |
| 3 | **351 clean corpus** | 27 prompt-intel cases verwijderd |
| 4 | **API server** | Zero-dep, OpenAI-compatible, draait op :8080 |
| 5 | **24 NL governance cases** | AVG, NORA, EU AI Act, Common Ground |
| 6 | **106 free teacher responses** | $0 via OpenRouter FREE |
| 7 | **35 frontier responses** | Claude Opus 4.8, GPT-5.4, Gemini 3.5 |
| 8 | **13 DPO pairs** | Frontier chosen vs open-source rejected |
| 9 | **7 cloud backends** | OpenRouter, OpenAI, Google, Ollama, Requesty |
| 10 | **Training pipeline** | LoRA + DPO scripts voor workstation |

---

## 🔴 Kritische Bevindingen

### P0 (blokkeert productie)
1. **Corpus was corrupt** — 27 prompt-intel cases → FIXED
2. **Geen live eval data in Djimitflo** — DB heeft 0 runs
3. **Oracle anchors niet geconfigureerd** — mist 30-40% scoring precision

### P1 (kwaliteit)
4. **Enkelvoudige judge** — geen consensus, risico op bias
5. **Geen multi-turn adversarial testing** — alleen single-turn
6. **Geen uncertainty quantification** — geen confidence scores
7. **Temperature > 0** — niet deterministisch voor evaluatie

### P2 (schaal)
8. **351 cases te weinig** — 2189 nodig voor statistische power
9. **Geen formal verification** — geen bewijs dat constraints altijd gelden
10. **Geen incident learning** — geen feedback loop van echte failures

---

## 📋 Acties voor Dennis (handmatig)

### Direct (vandaag)

1. **LaunchAgent installeren** (OpenDjicht auto-start):
   ```bash
   bash /Users/dlandman/OpenMythos/openmythos-benchmark/install_launchagent.sh
   ```

2. **API key in LaunchAgent config**:
   ```bash
   /usr/libexec/PlistBuddy -c "Set :EnvironmentVariables:OPENROUTER_API_KEY $(echo $OPENCODE_OPENROUTER_API_KEY)" ~/Library/LaunchAgents/com.open-djicht.governance.plist
   ```

3. **Djimitflo OpenMythos config**:
   - Set `OPENMYTHOS_CORPUS_PATH=/Users/dlandman/OpenMythos/openmythos-benchmark/cases/corpus.jsonl`
   - Set `OPENMYTHOS_ORACLE_ANCHORS_PATH=/Users/dlandman/OpenMythos/openmythos-benchmark/analysis/openmythos-apex-runs/reports/oracle_anchors.jsonl`
   - Set `OPENMYTHOS_JUDGE_MODEL=open-djicht-governance`

### Deze week

4. **PyTorch installeren op workstation** (voor LoRA training):
   ```bash
   ssh djimit@192.168.1.28 "pip install torch transformers peft trl datasets accelerate bitsandbytes"
   ```

5. **LoRA training draaien** (3-6 uur, RTX 2060 SUPER):
   ```bash
   ssh djimit@192.168.1.28 "cd /mnt/data/openmythos && python3 scripts/train_lora.py --dataset analysis/.../sft_combined.jsonl --output_dir models/open-djicht-lora-v1"
   ```

6. **Multi-turn adversarial testing**:
   ```bash
   python3 scripts/open_djicht_adversarial.py batch --turns 5 --n_runs 10
   ```

### Week 2-3

7. **2189 cases genereren** (voor statistische power)
8. **Multi-judge consensus** (3 judges, Cohen's κ ≥ 0.70)
9. **Conformal prediction** (uncertainty quantification)
10. **Formal verification** (TLA+ specifications)

---

## 📊 Score Prognose

| Week | Actie | Score |
|------|-------|-------|
| 0 | Huidige status | 89% |
| 1 | Oracle anchors + temp=0 + multi-judge | 92% |
| 2 | LoRA training + 10 few-shot | 95% |
| 3 | DPO + adversarial testing | 97% |
| 4 | Formal verification + causal reasoning | 99% |

---

## 🏗️ Architectuur (huidig → toekomst)

```
HUIDIG (89%):
  Query → RAG (514 ex) → Few-shot (5) → Claude Sonnet 4.6 → Response

TOEKOMST (95%+):
  Query → RAG (2189 ex) → Few-shot (10) → Multi-judge (3) → Conformal → Response
              ↓                                    ↑
        Causal Graph                    LoRA-tuned Qwen2.5-14B
              ↓                                    ↑
        Formal Verifier               Adversarial Testing
```

---

## 💰 Totaal Kosten

| Component | Kosten |
|-----------|--------|
| Data generatie | ~$1 |
| Cloud API (1000 queries/maand) | ~$2/maand |
| LoRA training (workstation GPU) | €0 (eigen hardware) |
| **Totaal eerste maand** | **~$3** |

---

> "89% is the foundation. 95% is the target. 99% is the ceiling."
> — OpenDjicht Roadmap, 2026
