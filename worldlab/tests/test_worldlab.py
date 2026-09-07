from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, RefResolver

from scripts.compile_world_scenarios import compile_case
from scripts.worldlab_promotion_gate import evaluate as promotion_evaluate
from scripts.worldlab_contrast_gate import evaluate as contrast_evaluate
from worldlab.assurance.invariant_engine import FAIL, PASS, UNDETERMINED, InvariantEngine
from worldlab.assurance.causal_graph import build_graph
from worldlab.assurance.privilege_graph import measure_privileges
from worldlab.assurance.resource_economics import measure_resources
from worldlab.assurance.statistics import compare_paired
from worldlab.experiment import ExperimentRunner, SCHEMAS, validate_scenario
from worldlab.advanced import run_advanced
from worldlab.integrations.eve_v import evaluate_challenge
from worldlab.integrations.federation import synthetic_mirror
from worldlab.integrations.models import ollama_adapter
from worldlab.model_experiment import LocalModelCampaign, _boolean
from worldlab.runtime.capability_broker import WorldLabCapabilityBroker
from worldlab.runtime.event_log import EventLog, sha256
from worldlab.runtime.memory import MemoryStore
from worldlab.runtime.replay import counterfactual_replay, replay
from worldlab.runtime.scheduler import Scheduler
from worldlab.runtime.world_state import WorldState, empty_state

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PATH = ROOT / "worldlab/scenarios/injection/shared-memory-001.json"


class WorldLabCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = json.loads(SCENARIO_PATH.read_text())

    def test_all_scenarios_validate_without_network(self) -> None:
        with patch("socket.create_connection", side_effect=AssertionError("network forbidden")):
            paths = list((ROOT / "worldlab/scenarios").rglob("*.json"))
            self.assertGreaterEqual(len(paths), 6)
            for path in paths:
                validate_scenario(json.loads(path.read_text()))

    def test_hash_chain_replay_is_exact_and_tamper_evident(self) -> None:
        trajectory = ExperimentRunner(self.scenario).run_trajectory("control", 7)
        self.assertEqual(replay(trajectory["initial_state"], trajectory["events"]), trajectory["final_state"])
        repeated = ExperimentRunner(self.scenario).run_trajectory("control", 7)
        self.assertEqual(trajectory, repeated)
        tampered = copy.deepcopy(trajectory["events"])
        tampered[0]["result"]["proposition"] = "silently changed"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            EventLog.verify(tampered)

    def test_capability_broker_records_delegation_and_epa(self) -> None:
        initial = empty_state()
        initial["capabilities"] = {
            "a": {"declared": ["write"], "authorized": ["write"]},
            "b": {"declared": [], "authorized": []}, "delegations": [],
        }
        state, log = WorldState(initial), EventLog("exp", "trace", 1)
        broker = WorldLabCapabilityBroker(state, log, {"write"})
        broker.delegate("a", "b", "write")
        self.assertTrue(broker.request("b", "write")["authorization"]["allowed"])
        metrics = measure_privileges(initial, state.snapshot())
        self.assertEqual(metrics["emergent_privilege_accumulation"]["b"], 1)

    def test_memory_rejects_anonymous_or_unattributed_write(self) -> None:
        state, log = WorldState(), EventLog("exp", "trace", 1)
        with self.assertRaises(ValueError):
            MemoryStore(state, log).write("", "m1", "claim", scope="shared", confidence=.5, provenance=[])

    def test_private_memory_and_messages_preserve_scope_and_provenance(self) -> None:
        state, log = WorldState(), EventLog("exp", "trace", 1)
        memory = MemoryStore(state, log)
        memory.write("a", "m1", "claim", scope="private_episodic", confidence=.5, provenance=["artifact-1"])
        self.assertEqual(memory.read("a", "m1")[0]["author"], "a")
        with self.assertRaises(PermissionError):
            memory.read("b", "m1")
        event = memory.message("a", "b", "msg-1", "sha256:message", ["m1"])
        self.assertEqual(event["event_type"], "agent.message")
        self.assertEqual(state.snapshot()["relationships"]["messages"][0]["to"], "b")

    def test_three_valued_invariants_and_mutations(self) -> None:
        log = EventLog("exp", "trace", 1)
        log.append("tool.executed", "a", authorization={"allowed": False})
        results = InvariantEngine().evaluate([
            {"id": "auth", "kind": "always", "predicate": "tool_execution_authorized"},
            {"id": "unknown", "kind": "always", "predicate": "not_implemented"},
            {"id": "side", "kind": "always", "predicate": "no_external_side_effect"},
        ], log.events)
        self.assertEqual([item["state"] for item in results], [FAIL, UNDETERMINED, PASS])

    def test_eventual_invariants_fail_closed(self) -> None:
        log = EventLog("exp", "trace", 1)
        log.append("policy.violation", "a")
        log.append("evidence.recorded", "auditor")
        specification = [{"id": "evidence", "kind": "eventually", "trigger": "policy.violation",
                          "predicate": "evidence_recorded", "within_events": 2}]
        self.assertEqual(InvariantEngine().evaluate(specification, log.events)[0]["state"], PASS)
        self.assertEqual(InvariantEngine().evaluate(specification, log.events[:1])[0]["state"], FAIL)

    def test_causal_graph_labels_dependencies_without_self_loops(self) -> None:
        log = EventLog("exp", "trace", 1)
        source = log.append("memory.written", "a", causal_tags=["belief"])
        log.append("memory.read", "b", parent_event_ids=[source["event_id"]], causal_tags=["belief"])
        graph = build_graph(log.events)
        self.assertFalse(any(edge["from"] == edge["to"] for edge in graph["edges"]))
        self.assertIn("data_dependency", {edge["relation"] for edge in graph["edges"]})

    def test_paired_statistics_use_the_shared_seed_effect(self) -> None:
        comparison = compare_paired([1.0, 0.0, 1.0], [0.0, 0.0, 0.0])
        self.assertTrue(comparison["paired"])
        self.assertAlmostEqual(comparison["effect"], 2 / 3)

    def test_resource_economics_exposes_scarcity_and_starvation(self) -> None:
        log = EventLog("exp", "trace", 1)
        log.append("tool.denied", "a", evidence={"tokens": 10, "latency_ms": 20})
        measured = measure_resources(log.events, [
            {"id": "a", "budget": {"token_budget": 5, "tool_calls": 1}},
            {"id": "b", "budget": {"token_budget": 5}},
        ])
        self.assertEqual(measured["starved_agents"], ["b"])
        self.assertEqual(measured["budget_violations"][0]["resource"], "tokens")
        self.assertEqual(measured["inefficient_exploration_rate"], 1)

    def test_counterfactual_is_labeled_and_does_not_claim_causality(self) -> None:
        trajectory = ExperimentRunner(self.scenario).run_trajectory("control", 3)
        changed = counterfactual_replay(trajectory["initial_state"], trajectory["events"], 0, {},
                                        replacement_event={"authorization": {"policy": "counterfactual-treatment"}})
        self.assertEqual(changed["kind"], "counterfactual")
        self.assertFalse(changed["causal_claim_supported"])
        self.assertEqual(changed["intervention_fields"], ["authorization", "state_delta"])

    def test_scheduler_orders_delayed_consequences_without_wall_clock_time(self) -> None:
        scheduler, observed = Scheduler(), []
        scheduler.schedule(10, "a", {"type": "late"})
        scheduler.schedule(2, "b", {"type": "early"})
        scheduler.schedule(2, "c", {"type": "same-time-stable"})
        scheduler.run(lambda item: observed.append((item.at_minute, item.actor)))
        self.assertEqual(observed, [(2, "b"), (2, "c"), (10, "a")])

    def test_compiler_preserves_source_case(self) -> None:
        case = json.loads((ROOT / "cases/corpus.jsonl").read_text().splitlines()[0])
        compiled = compile_case(case)
        self.assertIsNotNone(compiled)
        self.assertEqual(compiled["source_case"]["id"], case["id"])
        validate_scenario(compiled)

    def test_replicated_control_treatment_outputs_closed_goal_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = ExperimentRunner(self.scenario).run(Path(directory), 30)
            self.assertEqual(report["status"], "SUPPORTED")
            self.assertTrue(report["trajectory_failure_observed"])
            self.assertEqual(contrast_evaluate({"status": "PASS", "case_id": "canary-001", "category": "canary"}, report)["status"], "SUPPORTED")
            self.assertGreater(report["metrics"]["infection_probability"]["effect"], 0)
            goal = json.loads((Path(directory) / "analysis/djimitflo-goal-batch.json").read_text())
            self.assertEqual(goal["schema"], "djimit.openmythos.worldlab.goal.v1")
            self.assertEqual(goal["source"]["evidence_hash"], f"sha256:{sha256(report)}")
            self.assertEqual(promotion_evaluate(report, "relevant")["state"], "PASS")
            manifest = json.loads((Path(directory) / "manifest.json").read_text())
            Draft202012Validator(json.loads((SCHEMAS / "experiment.schema.json").read_text())).validate(manifest)
            trajectory = json.loads(next((Path(directory) / "runs/control").glob("*/trajectory.json")).read_text())
            schema = json.loads((SCHEMAS / "trajectory.schema.json").read_text())
            store = {}
            for schema_path in SCHEMAS.glob("*.schema.json"):
                document = json.loads(schema_path.read_text())
                store[document["$id"]] = document
                store[f"https://openmythos.org/worldlab/{schema_path.name}"] = document
            Draft202012Validator(schema, resolver=RefResolver.from_schema(schema, store=store)).validate(trajectory)

    def test_experiment_runner_rejects_unsupported_scenario_family(self) -> None:
        unsupported = json.loads((ROOT / "worldlab/scenarios/injection/recovery-001.json").read_text())
        with self.assertRaisesRegex(NotImplementedError, "malicious_artifact"):
            ExperimentRunner(unsupported)

    def test_promotion_gate_fails_closed(self) -> None:
        self.assertEqual(promotion_evaluate(None, "relevant")["state"], "FAIL")
        self.assertEqual(promotion_evaluate(None, "not-applicable")["state"], "NOT_APPLICABLE")
        no_failure = {"schema": "openmythos.worldlab.report.v1", "experiment_id": "exp", "scenario_hash": "hash",
                      "status": "SUPPORTED", "replications_per_condition": 30, "trajectory_failure_observed": False}
        self.assertEqual(promotion_evaluate(no_failure, "relevant")["state"], "FAIL")

    def test_federation_mirror_is_read_only_and_secret_free(self) -> None:
        mirror = synthetic_mirror({"registry": [{"id": "tool-1", "token": "secret"}],
                                   "knowledge": "authorization: Bearer sk-1234567890123456"})
        self.assertTrue(mirror["read_only"])
        self.assertFalse(mirror["live_mutation"])
        self.assertNotIn("token", mirror["snapshot"]["registry"][0])
        self.assertEqual(mirror["snapshot"]["knowledge"], "[REDACTED]")

    def test_real_model_adapter_is_fail_closed_by_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DISABLED"):
                ollama_adapter("agent", "openmythos-r17:latest")

    def test_advanced_experiments_preserve_authority_and_expose_tradeoffs(self) -> None:
        result = run_advanced()
        self.assertEqual(result["djimitflo_adversarial"]["protected_invariant_failures"], 0)
        self.assertEqual(result["djimitflo_adversarial"]["reviewer_independence"]["correlated_failure_risk"], "HIGH")
        self.assertEqual(result["governance_mutability"]["status"], "PASS")
        self.assertGreater(result["federation_chaos"]["containment_rate"], 0)
        self.assertEqual(result["federation_chaos"]["known_gap"], "provider_monoculture_failure")
        self.assertGreater(result["model_heterogeneity"]["coordination_cost"]["heterogeneous"]["mean"], 1)

    def test_eve_v_cannot_override_a_deterministic_failure(self) -> None:
        challenge = evaluate_challenge({"verdict": "PASS"}, [{"state": "FAIL"}])
        self.assertTrue(challenge["false_green"])
        self.assertEqual(challenge["effective_result"], "FAIL")

    def test_local_model_campaign_contract_is_strict(self) -> None:
        self.assertIs(_boolean('{"adopt":true}', "adopt"), True)
        self.assertIsNone(_boolean('{"adopt":"yes"}', "adopt"))
        with self.assertRaises(ValueError):
            LocalModelCampaign(["same", "same", "same"])


if __name__ == "__main__":
    unittest.main()
