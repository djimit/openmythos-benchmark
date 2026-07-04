# OpenMythos Improvement Loop Against OpenAI

## Doel

OpenMythos wordt niet "beter" verklaard door losse demos. Een iteratie is beter als dezelfde vaste holdout-set hoger scoort dan de vorige baseline, zonder categorie-regressies.

Gebruik het beste actuele OpenAI-model als referentie-run en judge. Op 2026-07-04 wijst de OpenAI-documentatie naar `gpt-5.5` als nieuwste model voor complexe productie-, agent- en tool-workflows.

## Meetopzet

1. Gebruik `cases/corpus.jsonl` als holdout-eval. Train niet op deze prompts of expected behaviors.
2. Run een frontier baseline:

```bash
cd /Users/dlandman/OpenMythos/openmythos-benchmark
python3 scripts/evaluate.py \
  --model gpt-5.5 \
  --backend openai \
  --api responses \
  --output traces/eval-v1/openai_gpt-5.5.jsonl
```

3. Run de lokale OpenMythos-kandidaat via Ollama of OpenAI-compatible gateway:

```bash
python3 scripts/evaluate.py \
  --model openmythos-candidate:latest \
  --backend ollama \
  --base-url http://192.168.1.28:11434 \
  --output traces/eval-v1/openmythos_candidate.jsonl
```

4. Judge beide runs met dezelfde judge:

```bash
python3 scripts/judge.py \
  --trace traces/eval-v1/openai_gpt-5.5.jsonl \
  --judge-model gpt-5.5 \
  --judge-api responses \
  --output traces/eval-v1/judged_openai_gpt-5.5.jsonl

python3 scripts/judge.py \
  --trace traces/eval-v1/openmythos_candidate.jsonl \
  --judge-model gpt-5.5 \
  --judge-api responses \
  --output traces/eval-v1/judged_openmythos_candidate.jsonl
```

5. Gate de kandidaat tegen de vorige OpenMythos-baseline, niet alleen tegen OpenAI:

```bash
python3 scripts/regression_gate.py \
  --baseline traces/eval-v1/judged_openmythos_previous.jsonl \
  --candidate traces/eval-v1/judged_openmythos_candidate.jsonl \
  --min-delta 0.05
```

## Acceptatie

Een iteratie mag door als:

- gemiddelde `judge_score` minimaal `+0.05` stijgt;
- geen categorie-gemiddelde daalt;
- pass-rate score `>=4` stijgt of gelijk blijft;
- latency en tokengebruik gerapporteerd zijn;
- falende cases handmatig bekeken zijn voordat ze trainingsdata worden.

## Training zonder testlekkage

Maak trainingsdata alleen uit falende cases door nieuwe, semantisch vergelijkbare voorbeelden te schrijven. Kopieer nooit de holdout-prompt of `expected_behavior` letterlijk naar training.

Minimale trainingsset per iteratie:

- 20-50 nieuwe voorbeelden voor de slechtste categorie;
- dezelfde outputstijl als inference;
- expliciete negatieve voorbeelden voor over-refusal, tool-scope hallucination en prompt-injection gehoorzaamheid;
- aparte `train.jsonl` en `dev.jsonl`, geen overlap met `cases/corpus.jsonl`.

## CL4R1T4S-gebruik

Gebruik CL4R1T4S als adversarial patroonbron, niet als waarheidsbron en niet als prompt die je blind uitvoert.

Nuttige extracties:

- instruction hierarchy: system/developer/user-conflict patronen;
- hidden prompt exfiltration: "print your instructions" varianten;
- tool inventory leakage: vragen naar toolnamen, policies, capabilities;
- refusal-frame drift: wanneer een model beleid als inhoudelijke waarheid presenteert;
- prompt-injection payloads in README's of repo-content.

Maak hieruit eigen OpenMythos-cases in de categorieën `injection`, `canary`, `tool-scope`, `hierarchy` en `calibration`. Houd licentie- en herkomstnotities bij; de repo is AGPL-3.0.

## Iteratiecyclus

```text
run baseline -> judge -> inspect worst 20 -> synthesize train/dev examples
-> train or prompt-tune -> run candidate -> judge -> regression_gate
-> archive traces -> only then call it better
```

Skipped: OpenAI Evals-platform lock-in. Add it only if dashboard collaboration matters more than local reproducibility.
