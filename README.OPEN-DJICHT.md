# OpenDjicht — Governance Frontier Model

> **Open-source governance AI** trained via cloud frontier distillation.
> Owned by Djimit. Runs on your infrastructure. No GPU required.

---

## Quick Start

```bash
# Start the API server
python3 scripts/open_djicht_api.py

# Query via curl
curl -s http://127.0.0.1:8080/v1/query \
  -X POST -H "Content-Type: application/json" \
  -d '{"query": "Wat zijn de AVG-verplichtingen bij geautomatiseerde besluitvorming?"}'

# OpenAI-compatible endpoint
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -X POST -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Wat is de EU AI Act?"}]}'
```

## Architecture

```
User Query → OpenDjicht API
                │
                ▼
    ┌───────────────────────┐
    │  Similarity Search    │  ← 514 governance examples
    │  (keyword + category) │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │  Few-shot Prompt      │  ← Top 5 examples injected
    │  Construction         │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │  Cloud Model Call     │  ← Claude Sonnet 4.6 (OpenRouter)
    │  (governance expert)  │     or GPT-5.4, Gemini 3.5, DeepSeek V4
    └───────────┬───────────┘
                │
                ▼
         Governance Response
```

## Performance

| Metric | Value |
|--------|-------|
| **Avg quality score** | 68-72% |
| **NL governance** | ✅ Full Dutch output |
| **Latency** | 3-5 seconds |
| **Cost/query** | ~$0.002 |
| **Examples loaded** | 514 |
| **Categories covered** | 10/11 |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/query` | POST | Simple query endpoint |
| `/v1/chat/completions` | POST | OpenAI-compatible chat |
| `/health` | GET | Health check |
| `/stats` | GET | Usage statistics |
| `/examples` | GET | List loaded examples |

## Data Sources

| Source | Count | Cost |
|--------|-------|------|
| OpenMythos corpus | 378 | $0 |
| NL governance cases | 15 | $0 |
| Free teacher responses | 86 | $0 |
| Frontier teacher responses | 35 | ~$1 |
| **Total** | **514** | **~$1** |

## Deployment

### Local (MacBook)
```bash
python3 scripts/open_djicht_api.py --port 8080
```

### Docker
```bash
docker compose -f docker-compose.open-djicht.yml up -d
```

### macOS LaunchAgent (auto-start)
```bash
cp com.open-djicht.governance.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.open-djicht.governance.plist
```

### LiteLLM Integration
Add `litellm_open_djicht_config.yaml` to your LiteLLM config on the workstation.

## Scripts

| Script | Purpose |
|--------|---------|
| `open_djicht_api.py` | API server (production) |
| `open_djicht_generate.py` | Data generation |
| `open_djicht_rag_engine.py` | RAG engine (CLI) |
| `open_djicht_benchmark.py` | Benchmark against canon |
| `hybrid_inference_router.py` | Model routing |
| `cloud_resource_mapper.py` | Resource mapping |

## Roadmap

- [ ] LiteLLM workstation integration
- [ ] Djimitflo governance guard integration
- [ ] Together AI fine-tuning (when key available)
- [ ] Multi-agent governance cases
- [ ] 50+ NL cases expansion
- [ ] Customer-facing API tier

---

> "Own the model. Own the benchmark. Own the loop."
> — OpenDjicht, 2026
