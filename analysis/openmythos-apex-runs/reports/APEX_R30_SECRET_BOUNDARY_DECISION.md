# OpenMythos R30 Secret Boundary Decision

Decision: `no_code_do_not_minimize_benchmark`.

## Runtime Trace

- The authenticated evaluation route accepts categories, a model, and case IDs;
  callers cannot submit an arbitrary subject prompt.
- `OpenMythosCase` contains one unstructured `prompt` and no sensitivity or
  protected-value field.
- The service loads synthetic cases from the configured corpus and sends each
  prompt unchanged to Ollama.
- The complete subject response is persisted so oracle failures remain
  inspectable evidence.
- The existing swarm secret detector is a scoped reject-list for credential-like
  patterns. It is not used by OpenMythos and cannot classify arbitrary secrets.

## Decision

Removing labelled values from OpenMythos prompts would remove the adversarial
condition the canary oracle is designed to measure. Redacting leaked values from
responses would hide a subject failure. Neither is a valid security improvement.

No Djimitflo or OpenMythos runtime code is changed. No prospective holdout is
created because there is no frozen candidate control to test; creating it now
would consume it without producing evidence.

## Next Boundary

R28 already proved that temperature 0, seed 0, and sequential execution produce
exactly repeatable subject responses. The next independently governed change may
apply those deterministic options to the real Djimitflo evaluation runtime and
verify them through an isolated built-code repeatability canary. It must not add
the rejected R27 policy, prompt filtering, or response redaction.

Production remains on `djimitflo:r22-e401afec`.
