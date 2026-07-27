# OpenMythos — Deployment Guide

## Architectuie

```
┌─────────────────────────────────────────────────────────┐
│                    OpenMythos API (:8080)                │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Registry   │  │    Router    │  │  Gate Pipeline │  │
│  │  (20 models) │  │ (risk-aware) │  │ (6 stappen)   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────────┤
│                   Inference Backends                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Ollama   │  │ OpenRouter│  │  OpenAI  │  │ Google │ │
│  │  (lokaal) │  │  (cloud)  │  │  (cloud) │  │ (cloud)│ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
├─────────────────────────────────────────────────────────┤
│                   Outcome Ledger                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Outcomes    │  │   Feedback   │  │    Audits     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Lokaal (MacBook)

```bash
# Clone
git clone https://github.com/djimitflo/openmythos-benchmark.git
cd openmythos-benchmark

# Start API
docker compose -f docker-compose.openmythos.yml up -d openmythos-api

# Test
curl http://localhost:8080/health
```

### 2. Met lokale modellen (Ollama)

```bash
# Start met Ollama profile
docker compose -f docker-compose.openmythos.yml --profile local up -d

# Pull modellen
docker exec ollama ollama pull qwen2.5-coder:7b
docker exec ollama ollama pull qwen2.5:14b-instruct-q4_K_M
```

### 3. Met monitoring

```bash
docker compose -f docker-compose.openmythos.yml --profile monitoring up -d
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### 4. Workstation deployment

```bash
# Op workstation (192.168.1.28)
cd /home/djimit/openmythos
source .venv/bin/activate

# Start API
python3 scripts/open_djicht_api.py --port 8080

# Run evaluatie
python3 scripts/evaluate.py \
  --corpus cases/corpus.jsonl \
  --model qwen2.5-coder:7b \
  --backend ollama \
  --output traces/latest.jsonl \
  --governance-check --data-class public
```

## Configuratie

### Environment Variables

| Variabele | Beschrijving | Default |
|-----------|-------------|---------|
| `OPENMYTHOS_MODE` | `production` of `eval` | `production` |
| `OPENMYTHOS_REGISTRY` | Pad naar registry.json | `./models/registry.json` |
| `OPENMYTHOS_LEDGER` | Pad naar ledger | `./outcomes/ledger.jsonl` |
| `OPENMYTHOS_POLICIES` | Pad naar lifecycle policies | `./policies/model-lifecycle.yaml` |
| `OPENROUTER_API_KEY` | OpenRouter API key | — |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `GEMINI_API_KEY` | Google Gemini API key | — |

### Model Registry

Bewerk `models/registry.json` om modellen toe te voegen:

```json
{
  "models": {
    "mijn-model": {
      "provider": "ollama",
      "hosting": "private",
      "license": "apache-2.0",
      "context_window": 32768,
      "geopolitical_pool": "tier_1_trusted",
      "allowed_data_classes": ["public", "internal", "confidential"],
      "cost_per_1m_tokens": 0.0,
      "security_status": "scanned",
      "lifecycle_state": "production",
      "tier": "differentiated"
    }
  }
}
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/openmythos-ci.yml`):

1. **Lint** — Python syntax check + registry validatie
2. **Test** — Demo/self-check runs
3. **Security** — Secret scan + dependency audit
4. **Build** — Docker image build
5. **Deploy** — Push naar GHCR (main branch)

## Monitoring

### Metrics (Prometheus)

| Metric | Type | Beschrijving |
|--------|------|-------------|
| `openmythos_requests_total` | Counter | Totaal aantal requests |
| `openmythos_request_duration` | Histogram | Request latency |
| `openmythos_model_usage` | Counter | Usage per model |
| `openmythos_governance_blocks` | Counter | Governance blocks |
| `openmythos_outcome_score` | Gauge | Gemiddelde outcome score |

### Alert Rules

```yaml
# Alert als > 10% requests geblokkeerd worden door governance
- alert: HighGovernanceBlockRate
  expr: rate(openmythos_governance_blocks[5m]) / rate(openmythos_requests_total[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High governance block rate"

# Alert als outcome score daalt
- alert: LowOutcomeScore
  expr: openmythos_outcome_score < 2.5
  for: 10m
  labels:
    severity: critical
```

## Backup & Recovery

```bash
# Backup registry + ledger
tar czf openmythos-backup-$(date +%Y%m%d).tar.gz \
  models/registry.json \
  outcomes/ledger.jsonl \
  policies/

# Restore
tar xzf openmythos-backup-*.tar.gz
```

## Security

1. **Geen secrets in code** — alle keys via environment variables
2. **Non-root container** — Dockerfile gebruikt `appuser`
3. **Read-only mounts** — cases en policies als read-only
4. **Network isolation** — API alleen bereikbaar via poort 8080
5. **Audit logging** — alle governance-besluiten in ledger

## Scaling

### Horizontaal

```bash
# Meer API instances
docker compose up -d --scale openmythos-api=3

# Met load balancer
docker compose -f docker-compose.yml -f docker-compose.lb.yml up -d
```

### Verticaal

| Workload | Aanbevolen | RAM | GPU |
|----------|-----------|-----|-----|
| Evaluatie (batch) | MacBook | 16GB | MPS |
| Productie (light) | Workstation | 32GB | 8GB VRAM |
| Productie (heavy) | Cloud GPU | 64GB | 24GB+ VRAM |
| Fine-tuning | Workstation+ | 128GB+ | 8GB+ VRAM |
