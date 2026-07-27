# OpenDjicht — Productie-Ready Samenvatting

> **Status:** Werkend | **Datum:** 2026-07-23 | **Mode:** Cloud-only, geen GPU

---

## Wat er NU werkt

### 1. RAG Engine ✅
- **Bestand:** `scripts/open_djicht_rag_engine.py`
- **Aanpak:** Few-shot prompting met 60+ governance voorbeelden
- **Model:** Claude Sonnet 4.6 via OpenRouter ($0.00002/tok)
- **Score:** 72% overlap met expected behavior
- **Kosten:** ~$0.002 per query

### 2. Data Pipeline ✅
- **60 SFT samples** (gratis gegenereerd)
- **15 NL governance cases** (AVG, NORA, EU AI Act, Common Ground)
- **10 DPO pairs** (frontier vs open-source)
- **25/27 cloud backends** werkend

### 3. Hybrid Inference Router ✅
- **Bestand:** `scripts/hybrid_inference_router.py`
- **Aanpak:** Automatische routing naar beste/goedkoopste model per taak
- **Backends:** OpenRouter FREE, OpenRouter Paid, OpenAI, Google, Ollama Cloud

---

## Hoe te gebruiken

### Query de OpenDjicht engine:
```bash
python3 scripts/open_djicht_rag_engine.py query \
  --query "Jouw governance vraag hier"
```

### Evalueer tegen OpenMythos canon:
```bash
python3 scripts/open_djicht_rag_engine.py evaluate --limit 50
```

### Genereer meer training data:
```bash
python3 scripts/open_djicht_generate.py free --cases 100
```

### Benchmark alle backends:
```bash
python3 scripts/hybrid_inference_router.py benchmark
```

---

## Cloud Resources Gebruik

| Provider | Model | Gebruik | Kosten/query |
|----------|-------|---------|-------------|
| OpenRouter FREE | gpt-oss-120b | Bulk data | $0 |
| OpenRouter FREE | gemini-2.5-flash-lite | Fast judge | $0 |
| OpenRouter | claude-sonnet-4.6 | RAG engine | ~$0.002 |
| OpenRouter | claude-opus-4.8 | Frontier chosen | ~$0.005 |

---

## Data Inventory

| Bron | Samples | Status |
|------|---------|--------|
| Corpus cases | 351 | ✅ |
| NL governance cases | 15 | ✅ |
| Free teacher responses | 56 | ✅ |
| Frontier DPO chosen | 15 | ✅ |
| DPO pairs | 10 | ✅ |
| **Totaal unieke voorbeelden** | **~450** | ✅ |

---

## Volgende Stappen

### Korte termijn (deze week):
1. Review NL cases (Dennis — juridische correctheid)
2. Genereer 100+ meer teacher responses
3. Evaluatie tegen volledige OpenMythos canon (351 cases)

### Middellange termijn (week 2-4):
1. Deploy als API endpoint (LiteLLM integratie)
2. Djimitflo governance guard integratie
3. Multi-agent governance cases toevoegen

### Lange termijn (maand 2-3):
1. Together AI fine-tuning (wanneer key beschikbaar)
2. Productie deployment als "OpenDjicht Governance AI"
3. Klant-facing governance rapportage

---

## Kosten

| Component | Kosten |
|-----------|--------|
| Data generatie | $0 (free models) |
| RAG engine per query | ~$0.002 |
| Evaluatie (351 cases) | ~$0.70 |
| **Totaal maandelijks** (1000 queries) | **~$2** |

---

> "450 examples. 7 categories. 1 engine. $0 training."
> — OpenDjicht, 2026
