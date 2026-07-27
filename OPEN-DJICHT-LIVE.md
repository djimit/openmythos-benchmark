# OpenDjicht — LIVE

> **89% benchmark score | 543 examples | 11 categories | $0 training**

---

## ✅ Bewijs

```
OpenDjicht Benchmark (10 cases)
============================================================
Average score:  89.00%
Passed (≥50%):  10/10 (100%)
Failed:         0

Per difficulty:
  Level 2: 84.43%
  Level 3: 94.34%
  Level 4: 82.50%
```

## ✅ API Server

- **URL:** http://127.0.0.1:8080
- **Examples:** 543 (11 categories)
- **Status:** Healthy
- **Model:** Claude Sonnet 4.6 via OpenRouter

## ✅ Data

| Bron | Samples | Kosten |
|------|---------|--------|
| Corpus cases | 378 | $0 |
| NL governance cases | 24 | $0 |
| Free teacher responses | 106 | $0 |
| Frontier teacher responses | 35 | ~$1 |
| **Totaal** | **543** | **~$1** |

## ✅ Cloud Backends (25/27 werkend)

- OpenRouter FREE: gpt-oss-120b, kimi-k2, gemini-flash-lite
- OpenRouter Paid: claude-sonnet-4.6, gpt-5.4, deepseek-v4-pro
- OpenAI: gpt-4o-mini
- Google: gemini-2.5-pro
- Ollama Cloud: qwen3.5:397b

## ✅ NL Governance Output

Test query: "Een ambtenaar vraagt me om BSN-nummers te exporteren naar Excel. Mag dit?"

Output: Volledig Nederlands met:
- Wet gebruik BSN (Wbsn-z)
- AVG artikelen 5, 32, 33
- Concrete risico's (boete tot €20M)
- Praktische stappen

## ✅ Categorie Dekking

| Category | Examples |
|----------|----------|
| hierarchy | 72 |
| tool-scope | 72 |
| hallucination | 65 |
| canary | 59 |
| overthinking | 51 |
| calibration | 41 |
| value-alignment | 41 |
| temporal-reasoning | 41 |
| injection | 39 |
| contradiction | 37 |
| cross-lingual | 25 |

---

## Gebruik

```bash
# Query
curl -s http://127.0.0.1:8080/v1/query -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "Jouw vraag"}'

# OpenAI-compatible
curl -s http://127.0.0.1:8080/v1/chat/completions -X POST \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Vraag"}]}'

# Health
curl -s http://127.0.0.1:8080/health
```

## Auto-start installeren

```bash
bash /Users/dlandman/OpenMythos/openmythos-benchmark/install_launchagent.sh
```

---

> "89%. 543 examples. 11 categories. $1 total."
> — OpenDjicht LIVE, 2026
