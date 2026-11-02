# OpenMythos WorldLab

WorldLab is OpenMythos' longitudinal evidence generator. It executes deterministic, isolated agent trajectories and hands typed findings to the existing DjimitFlo goal lifecycle. It does not define ground truth, execute production tools, promote canonical cases, or introduce a second task engine.

## Authority boundary

- OpenMythos owns norms, taxonomies, oracles, calibration, falsification and promotion evidence.
- WorldLab owns synthetic world state, append-only trajectories, replay and longitudinal measurements.
- DjimitFlo remains the reference monitor for maker/checker/approval, ToolBroker execution, audit and promotion.
- EVE-V may challenge evidence, but cannot replace a deterministic invariant or oracle.
- Federation data enters only as a sanitized synthetic snapshot; WorldLab cannot mutate it.

WorldLab defaults to no network, synthetic credentials, simulated tools and no external side effects. `production authority != simulated authority` is an L0 invariant.

## Run

```sh
python3 scripts/worldlab_experiment.py \
  --scenario worldlab/scenarios/injection/shared-memory-001.json \
  --replications 30 \
  --output traces/worldlab/shared-memory-001
```

The run writes a manifest, immutable JSONL events, reconstructed final state, vector assurance evidence, a statistical report and a typed DjimitFlo goal campaign. A single trajectory remains `EXPLORATORY`; replicated evidence can become `SUPPORTED`, `FALSIFIED` or `UNDETERMINED`, never `PROVEN`.

Promotion-relevant changes must pass `scripts/worldlab_promotion_gate.py --relevance relevant --report <report.json>`. Non-relevant changes must explicitly declare `--relevance not-applicable`; absence is not PASS.

PR CI is deterministic. Nightly CI runs the synthetic 30x30 campaign. Real-model research campaigns require an explicitly mediated adapter, scoped credentials, independent evaluation and DjimitFlo approval.

## Local research and provenance

Real-model campaigns are opt-in and loopback-only by default:

```sh
WORLDLAB_EXTERNAL_MODELS_ENABLED=1 python3 scripts/worldlab_model_campaign.py \
  --models gemma4:latest independent-checker:latest --replications 30 \
  --artifact-mode adversarial --population homogeneous \
  --output traces/worldlab/models-homogeneous-gemma
```

Every report retains model digests, source/commit hashes, prompt/response hashes and paired-seed statistics; raw prompts and responses are not stored. `scripts/worldlab_sbom.py` emits the pinned Python dependency SBOM. Model evidence is exploratory unless a preregistered independent campaign satisfies the confirmatory gate.
