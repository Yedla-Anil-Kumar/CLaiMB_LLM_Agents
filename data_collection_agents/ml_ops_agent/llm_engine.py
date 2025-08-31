# Data_Collection_Agents/ml_ops_agent/llm_engine.py
from __future__ import annotations
import json
import time
import random
from typing import Any, Dict, List, Optional

from ml_ops_agent.base_agent import BaseMicroAgent

"""
MLOps Metric Grader — ONE-SHOT (per metric)

- Universal preamble + per-metric rubric
- Each metric includes: example_input AND example_output (true one-shot)
- build_prompt prints the RESPONSE FORMAT before EXAMPLES to reduce anchoring
- Public API is unchanged: one wrapper method per grading/check function

UPDATE:
- Rubrics consider **all** relevant fields in each metric's evidence.
- Response schema now includes **gaps** explaining what limited the band.
- Each metric includes **input_key_meanings** to make field intent explicit.
- Rationales cite strongest positive and limiting factor.
- Gaps use **action-plan style**: <limiter → change → threshold → unlock band>.
"""

# -------------------------
# Universal grading contract
# -------------------------

UNIVERSAL_PREAMBLE = (
    "You are an MLOps Assessor. Grade exactly one metric on a 1–5 band:\n"
    "5 = Excellent\n"
    "4 = Good\n"
    "3 = Fair\n"
    "2 = Poor\n"
    "1 = Critical\n\n"
    "Rules:\n"
    "- Use ONLY the provided JSON evidence/rubric/policy text. Do NOT invent data.\n"
    "- Compare all relevant evidence fields; bands must reflect the combination, not a single field.\n"
    "- If fields conflict, prefer the lower band and explain briefly.\n"
    "- Rationale: mention 1–2 strongest positives AND the single biggest limiting factor.\n"
    "- 'gaps': sentence-level improvement guidance: '<Why limiter> → <What to change> → <Target threshold> (unlocks band X)'.\n"
    "- Be conservative when values are borderline; keep rationale ≤3 sentences.\n"
    "- Return ONLY the specified JSON. No extra text."
)

UNIVERSAL_RESPONSE_FORMAT = (
    '{"metric_id":"<id>",'
    '"band":<1-5>,'
    '"rationale":"<1-3 sentences>",'
    '"flags":[],'
    '"gaps":[]}'
)

POLICY_GATES_RESPONSE_FORMAT = (
    '{"metric_id":"<id>",'
    '"band":<1-5>,'
    '"rationale":"<1-3 sentences>",'
    '"present":[],'
    '"missing":[],'
    '"failing":[],'
    '"gaps":[]}'
)

# -------------------------
# Improvement examples (few-shot steering for “gaps” wording)
# -------------------------

IMPROVEMENT_GUIDANCE_EXAMPLES = [
    "Artifacts at 0.75 cap the band → persist model files and eval reports on every run → raise pct_artifacts to ≥0.80 (unlocks band 4).",
    "Data references missing in ~16% of runs → log immutable dataset version or hash per run → lift pct_data_ref to ≥0.85 (unlocks band 4).",
    "p50 lead time is fine but p95 is borderline → parallelize tests and cache deps → keep p95 ≤24h (unlocks band 5).",
    "Bias reports below threshold → add fairness step to pipeline and publish report → raise pct_with_bias_report to ≥0.80 (unlocks band 4)."
]

def _rubric_text(t: str) -> str:
    return f"SYSTEM:\n{UNIVERSAL_PREAMBLE}\n\nRUBRIC:\n{t}"


# -------------------------------------------------------------------------
# Metric definitions (20) — ONE SHOT with realistic example inputs/outputs
# -------------------------------------------------------------------------

METRIC_PROMPTS: Dict[str, Dict[str, Any]] = {
    # =========================
    # MLflow (6)
    # =========================

    "mlflow.experiment_completeness_band": {
        "system": _rubric_text(
            "Use together: pct_all, pct_params, pct_metrics, pct_tags, pct_artifacts.\n"
            "Band 5: ALL ≥ 0.90 (min ≥ 0.90)\n"
            "Band 4: ALL ≥ 0.80 AND ≥3 fields ≥ 0.85 (min ≥ 0.80)\n"
            "Band 3: ALL ≥ 0.70 AND ≥2 fields ≥ 0.80 (min ≥ 0.70)\n"
            "Band 2: ANY < 0.70 BUT ≥2 fields ≥ 0.60 AND pct_all ≥ 0.60\n"
            "Band 1: MOST < 0.60 or pct_all < 0.60 or evidence missing"
        ),
        "input_key_meanings": {
            "evidence.pct_all": "Share of runs with params+metrics+tags+artifacts all present",
            "evidence.pct_params": "Runs with parameter logging",
            "evidence.pct_metrics": "Runs with metric logging",
            "evidence.pct_tags": "Runs with tag metadata",
            "evidence.pct_artifacts": "Runs persisting artifacts (models/files)"
        },
        "example_input": {
            "metric_id": "mlflow.experiment_completeness_band",
            "evidence": {"pct_all": 0.82, "pct_params": 0.90, "pct_metrics": 0.82, "pct_tags": 0.81, "pct_artifacts": 0.75}
        },
        "example_output": {
            "metric_id": "mlflow.experiment_completeness_band",
            "band": 3,
            "rationale": "Params/metrics are strong, but artifacts at 0.75 are the main limiter.",
            "flags": ["artifacts_low"],
            "gaps": [
                "Artifacts at 0.75 cap the band → persist model binaries and eval files for every run → raise pct_artifacts to ≥0.80 (unlocks band 4).",
                "Not all fields consistently ≥0.85 → add tags auto-injection in training wrapper → lift pct_tags to ≥0.85 (stabilizes band 4)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "mlflow.lineage_coverage_band": {
        "system": _rubric_text(
            "Use: pct_git_sha, pct_data_ref, pct_env_files together.\n"
            "Band 5: ALL ≥ 0.95\n"
            "Band 4: ALL ≥ 0.85 AND ≥2 ≥ 0.90\n"
            "Band 3: ALL ≥ 0.70 AND ≥1 ≥ 0.85\n"
            "Band 2: ANY < 0.70 but at least one ≥ 0.60\n"
            "Band 1: MOST < 0.60 or multiple missing"
        ),
        "input_key_meanings": {
            "evidence.pct_git_sha": "Runs with committed Git SHA recorded",
            "evidence.pct_data_ref": "Runs with immutable data reference (path/version/hash)",
            "evidence.pct_env_files": "Runs with env files recorded (conda/requirements)"
        },
        "example_input": {
            "metric_id": "mlflow.lineage_coverage_band",
            "evidence": {"pct_git_sha": 0.93, "pct_data_ref": 0.84, "pct_env_files": 0.91}
        },
        "example_output": {
            "metric_id": "mlflow.lineage_coverage_band",
            "band": 3,
            "rationale": "Git/env references are ~0.90+; data_ref at 0.84 is the limiter.",
            "flags": ["data_ref_coverage"],
            "gaps": [
                "Data references at 0.84 block a higher band → log dataset version/hash via a pre-run hook → raise pct_data_ref to ≥0.85 (unlocks band 4).",
                "Uneven lineage across runs → enforce a common MLflow client wrapper → keep ALL lineage fields ≥0.90 (targets band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "mlflow.experiment_velocity_band": {
        "system": _rubric_text(
            "Use together: improvement_rate_mom, experiments_per_week.\n"
            "Band 5: rate ≥ 0.05 AND exp/wk ≥ 2.0\n"
            "Band 4: rate ≥ 0.03 AND exp/wk ≥ 1.5\n"
            "Band 3: BOTH ≥ 0.01\n"
            "Band 2: ONE ≥ 0.01 but the other lower\n"
            "Band 1: BOTH < 0.01"
        ),
        "input_key_meanings": {
            "evidence.improvement_rate_mom": "Monthly improvement rate of best run metric",
            "evidence.experiments_per_week": "Average experiments executed per week"
        },
        "example_input": {
            "metric_id": "mlflow.experiment_velocity_band",
            "evidence": {"improvement_rate_mom": 0.04, "experiments_per_week": 1.6}
        },
        "example_output": {
            "metric_id": "mlflow.experiment_velocity_band",
            "band": 4,
            "rationale": "Both dimensions exceed band-4 thresholds; consistent iteration cadence.",
            "flags": [],
            "gaps": [
                "Velocity shy of band-5 → schedule 2+ controlled experiments weekly → maintain exp/wk ≥2.0 and rate ≥0.05 (unlocks band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "mlflow.registry_hygiene_band": {
        "system": _rubric_text(
            "Use: pct_staged, pct_with_approver, median_stage_latency_h, rollback_count_30d.\n"
            "Band 5: staged ≥ 0.90 & approver ≥ 0.90 & latency < 48h & rollbacks == 0\n"
            "Band 4: ALL ≥ 0.80 & latency < 72h & rollbacks ≤ 1\n"
            "Band 3: ALL ≥ 0.70 & latency < 96h & rollbacks ≤ 2\n"
            "Band 2: ANY < 0.70 OR latency 96–119h OR rollbacks 3\n"
            "Band 1: latency ≥ 120h OR rollbacks > 3 OR evidence missing"
        ),
        "input_key_meanings": {
            "evidence.pct_staged": "Models in registry assigned a stage",
            "evidence.pct_with_approver": "Stage transitions with approver recorded",
            "evidence.median_stage_latency_h": "Median hours from staging to production",
            "evidence.rollback_count_30d": "Prod rollbacks in the last 30 days"
        },
        "example_input": {
            "metric_id": "mlflow.registry_hygiene_band",
            "evidence": {"pct_staged": 0.83, "pct_with_approver": 0.88, "median_stage_latency_h": 60, "rollback_count_30d": 1}
        },
        "example_output": {
            "metric_id": "mlflow.registry_hygiene_band",
            "band": 4,
            "rationale": "Approvals and latency meet targets; a single rollback prevents band 5.",
            "flags": ["rollback_present"],
            "gaps": [
                "One recent rollback limits confidence → add pre-deploy shadow tests and tighten rollback criteria → keep rollbacks_30d at 0 (unlocks band 5).",
                "Latency at 60h is acceptable but not elite → parallelize validation steps → reduce median_stage_latency_h to <48h (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "mlflow.validation_artifacts_band": {
        "system": _rubric_text(
            "Use together: pct_with_shap, pct_with_bias_report, pct_with_validation_json.\n"
            "Band 5: ALL ≥ 0.90\n"
            "Band 4: ALL ≥ 0.80 AND ≥2 ≥ 0.85\n"
            "Band 3: ALL ≥ 0.70 AND ≥1 ≥ 0.80\n"
            "Band 2: ANY < 0.70 (but at least one ≥ 0.60)\n"
            "Band 1: MOST < 0.60 or missing"
        ),
        "input_key_meanings": {
            "evidence.pct_with_shap": "Runs with SHAP/explainability files",
            "evidence.pct_with_bias_report": "Runs with bias/fairness report",
            "evidence.pct_with_validation_json": "Runs with validation summary JSON"
        },
        "example_input": {
            "metric_id": "mlflow.validation_artifacts_band",
            "evidence": {"pct_with_shap": 0.75, "pct_with_bias_report": 0.72, "pct_with_validation_json": 0.84}
        },
        "example_output": {
            "metric_id": "mlflow.validation_artifacts_band",
            "band": 3,
            "rationale": "Validation JSON is strong; SHAP and bias coverage below 0.80 limit the band.",
            "flags": ["bias_coverage_low", "shap_coverage_low"],
            "gaps": [
                "Explainability at 0.75 → add SHAP step to pipeline and store artifacts → raise pct_with_shap to ≥0.80 (unlocks band 4).",
                "Bias report at 0.72 → add fairness evaluation gate before register → raise pct_with_bias_report to ≥0.80 (unlocks band 4)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "mlflow.reproducibility_band": {
        "system": _rubric_text(
            "Use: match_rate and signature_conflicts[].\n"
            "Band 5: match_rate ≥ 0.95 & no conflicts\n"
            "Band 4: match_rate ≥ 0.85; minor conflicts allowed\n"
            "Band 3: match_rate ≥ 0.70; some conflicts present\n"
            "Band 2: match_rate ≥ 0.50; many/serious conflicts\n"
            "Band 1: match_rate < 0.50 OR repeated major conflicts"
        ),
        "input_key_meanings": {
            "evidence.match_rate": "Share of reruns matching previous metrics within tolerance",
            "evidence.signature_conflicts[]": "Conflicting model signatures with metric diffs"
        },
        "example_input": {
            "metric_id": "mlflow.reproducibility_band",
            "evidence": {"match_rate": 0.88, "signature_conflicts": [{"signature": "svc@1.0", "runs": ["r1","r8"], "metric_diff": 0.025}]}
        },
        "example_output": {
            "metric_id": "mlflow.reproducibility_band",
            "band": 4,
            "rationale": "High match rate with a minor signature conflict noted.",
            "flags": ["conflicts_present"],
            "gaps": [
                "Signature conflict on 'svc@1.0' → pin environment and seed; verify data hashes → remove conflict occurrences and lift match_rate ≥0.95 (unlocks band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    # =========================
    # Azure ML (5)
    # =========================

    "aml.endpoint_slo_band": {
        "system": _rubric_text(
            "Use declared_slo {availability, p95_ms, error_rate} and measured {availability_30d, p95_ms, error_rate}. Prefer the worst dimension.\n"
            "Band 5: availability_30d ≥ declared+0.002 AND p95 ≤ 0.80*declared AND error ≤ 0.50*declared\n"
            "Band 4: ALL declared met AND ≥2 exceed by margin (avail +0.001, p95 ≤ 0.90*declared, error ≤ 0.75*declared)\n"
            "Band 3: ≥2 declared met OR ALL barely met\n"
            "Band 2: Only one declared met OR conflicting trade-offs\n"
            "Band 1: None met OR evidence missing"
        ),
        "input_key_meanings": {
            "declared_slo.availability": "Target availability SLO",
            "declared_slo.p95_ms": "Target p95 latency (ms)",
            "declared_slo.error_rate": "Target error rate",
            "evidence.availability_30d": "Measured 30d availability",
            "evidence.p95_ms": "Measured p95 latency",
            "evidence.error_rate": "Measured error rate"
        },
        "example_input": {
            "metric_id": "aml.endpoint_slo_band",
            "declared_slo": {"availability": 0.995, "p95_ms": 300, "error_rate": 0.01},
            "evidence": {"availability_30d": 0.997, "p95_ms": 215, "error_rate": 0.003}
        },
        "example_output": {
            "metric_id": "aml.endpoint_slo_band",
            "band": 5,
            "rationale": "All measured dimensions exceed SLOs with healthy margins.",
            "flags": [],
            "gaps": []
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "aml.jobs_flow_band": {
        "system": _rubric_text(
            "Use together: success_rate, p95_duration_min, lead_time_hours.\n"
            "Band 5: success ≥ 0.98 & lead_time ≤ 4h & p95 ≤ 30\n"
            "Band 4: success ≥ 0.95 & lead_time ≤ 8h & p95 ≤ 45\n"
            "Band 3: success ≥ 0.90 & lead_time ≤ 24h & p95 ≤ 60\n"
            "Band 2: partial health (one clearly below)\n"
            "Band 1: generally failing"
        ),
        "input_key_meanings": {
            "evidence.success_rate": "Proportion of AML jobs that succeed",
            "evidence.p95_duration_min": "p95 job duration in minutes",
            "evidence.lead_time_hours": "Hours between commit and job start"
        },
        "example_input": {
            "metric_id": "aml.jobs_flow_band",
            "evidence": {"success_rate": 0.94, "p95_duration_min": 38, "lead_time_hours": 6.4}
        },
        "example_output": {
            "metric_id": "aml.jobs_flow_band",
            "band": 3,
            "rationale": "Success below 0.95 limits the band; p95 and lead-time acceptable.",
            "flags": [],
            "gaps": [
                "Success at 0.94 is the limiter → add retry-on-transient and resource quota checks → raise success_rate to ≥0.95 (unlocks band 4).",
                "Lead-time 6.4h acceptable but improvable → enable caching and artifact reuse → target ≤4h (pushes toward band 5 when success is ≥0.98)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "aml.monitoring_coverage_band": {
        "system": _rubric_text(
            "Use: monitors_enabled, median_time_to_ack_h, drift_alerts_30d.\n"
            "Band 5: monitors_enabled True & median_time_to_ack_h < 2h\n"
            "Band 4: monitors_enabled True & median_time_to_ack_h < 6h\n"
            "Band 3: monitors_enabled True BUT ack ≥ 6h OR no recent alerts to validate process\n"
            "Band 2: monitors disabled but some ad-hoc response evidence\n"
            "Band 1: monitors disabled and no response process"
        ),
        "input_key_meanings": {
            "evidence.monitors_enabled": "Whether data/quality/drift monitors are enabled",
            "evidence.median_time_to_ack_h": "Median hours to acknowledge alerts",
            "evidence.drift_alerts_30d": "Count of drift/quality alerts in last 30 days"
        },
        "example_input": {
            "metric_id": "aml.monitoring_coverage_band",
            "evidence": {"monitors_enabled": True, "median_time_to_ack_h": 3.2, "drift_alerts_30d": 1}
        },
        "example_output": {
            "metric_id": "aml.monitoring_coverage_band",
            "band": 4,
            "rationale": "Monitoring is enabled with timely acknowledgement under 6h.",
            "flags": [],
            "gaps": [
                "Ack at 3.2h misses elite threshold → add on-call rotation and pager duty routing → bring median_time_to_ack_h <2h (unlocks band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "aml.registry_governance_band": {
        "system": _rubric_text(
            "Use: pct_staged, pct_with_approvals, median_transition_h together.\n"
            "Band 5: staged ≥ 0.90 & approvals ≥ 0.90 & median_transition_h < 48\n"
            "Band 4: ALL ≥ 0.80 & median_transition_h < 72\n"
            "Band 3: ALL ≥ 0.70 & median_transition_h < 96\n"
            "Band 2: ANY < 0.70 OR median 96–119\n"
            "Band 1: median ≥ 120 OR widespread lack of approvals"
        ),
        "input_key_meanings": {
            "evidence.pct_staged": "Models with a registry stage",
            "evidence.pct_with_approvals": "Transitions with approvals",
            "evidence.median_transition_h": "Median hours for registry transitions"
        },
        "example_input": {
            "metric_id": "aml.registry_governance_band",
            "evidence": {"pct_staged": 0.83, "pct_with_approvals": 0.88, "median_transition_h": 60}
        },
        "example_output": {
            "metric_id": "aml.registry_governance_band",
            "band": 4,
            "rationale": "All controls meet band-4 thresholds; transition latency is moderate.",
            "flags": [],
            "gaps": [
                "Latency at 60h prevents band-5 → parallelize QA and security gates → reduce median_transition_h to <48h (unlocks band 5).",
                "Staging coverage 0.83 <0.90 → enforce stage on register policy → raise pct_staged to ≥0.90 (supports band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "aml.cost_correlation_band": {
        "system": _rubric_text(
            "Use: cost_join_rate, coverage (tags/resourceId/tags+resourceId), cost_per_1k_requests.\n"
            "Band 5: cost_join_rate ≥ 0.90 & coverage == 'tags+resourceId' & stable attribution\n"
            "Band 4: cost_join_rate ≥ 0.80 & coverage includes at least one of tags or resourceId\n"
            "Band 3: cost_join_rate ≥ 0.60 with partial coverage OR inconsistent attribution\n"
            "Band 2: cost_join_rate ≥ 0.40 with weak coverage\n"
            "Band 1: cost_join_rate < 0.40 or no usable attribution"
        ),
        "input_key_meanings": {
            "evidence.cost_join_rate": "Share of cost rows joinable to endpoints",
            "evidence.coverage": "Attribution depth used ('tags', 'resourceId', or 'tags+resourceId')",
            "evidence.cost_per_1k_requests": "USD per 1k endpoint requests"
        },
        "example_input": {
            "metric_id": "aml.cost_correlation_band",
            "evidence": {"cost_join_rate": 0.81, "coverage": "tags", "cost_per_1k_requests": 0.12}
        },
        "example_output": {
            "metric_id": "aml.cost_correlation_band",
            "band": 4,
            "rationale": "Join rate >0.80 with tag-based attribution; costs observable but not at the deepest granularity.",
            "flags": [],
            "gaps": [
                "Attribution limited to tags → add resourceId to billing ETL → move coverage to 'tags+resourceId' (unlocks band 5).",
                "Join rate near lower bound → enforce tag/resourceId on every deploy → raise cost_join_rate to ≥0.90 (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    # =========================
    # SageMaker (5)
    # =========================

    "sm.endpoint_slo_scaling_band": {
        "system": _rubric_text(
            "Use together: availability_30d, error_rate, p95_ms, median_reaction_s (autoscaling), max_rps_at_slo.\n"
            "Band 5: availability ≥ 0.999 & p95 ≤ 200 & error_rate ≤ 0.003 & reaction ≤ 60s & max_rps_at_slo ≥ 800\n"
            "Band 4: availability ≥ 0.997 & p95 ≤ 250 & error_rate ≤ 0.005 & reaction ≤ 120s & max_rps_at_slo ≥ 400\n"
            "Band 3: availability ≥ 0.995 & p95 ≤ 300 & error_rate ≤ 0.010\n"
            "Band 2: only 1–2 pass; reaction > 180s OR max_rps_at_slo < 200\n"
            "Band 1: fails most thresholds or evidence missing"
        ),
        "input_key_meanings": {
            "evidence.availability_30d": "Measured 30d availability",
            "evidence.error_rate": "Endpoint error rate",
            "evidence.p95_ms": "p95 latency (ms)",
            "evidence.median_reaction_s": "Autoscaling median reaction time (s)",
            "evidence.max_rps_at_slo": "Sustained RPS while meeting SLO"
        },
        "example_input": {
            "metric_id": "sm.endpoint_slo_scaling_band",
            "evidence": {"availability_30d": 0.997, "error_rate": 0.004, "p95_ms": 235, "median_reaction_s": 95, "max_rps_at_slo": 520}
        },
        "example_output": {
            "metric_id": "sm.endpoint_slo_scaling_band",
            "band": 4,
            "rationale": "All dimensions meet band-4 thresholds; headroom and scaling are healthy.",
            "flags": [],
            "gaps": [
                "p95 at 235ms above elite → warm pools & model compile optimizations → keep p95 ≤200ms (unlocks band 5).",
                "Reaction time 95s >60s → pre-scale based on schedule and faster cooldowns → reduce median_reaction_s ≤60 (unlocks band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "sm.pipeline_flow_band": {
        "system": _rubric_text(
            "Use: success_rate, p95_duration_min, retry_rate, promotion_time_h.\n"
            "Band 5: success ≥ 0.98 & promotion ≤ 8h & p95 ≤ 30 & retry_rate ≤ 0.03\n"
            "Band 4: success ≥ 0.95 & promotion ≤ 12h & p95 ≤ 45 & retry_rate ≤ 0.06\n"
            "Band 3: success ≥ 0.90 & promotion ≤ 24h & p95 ≤ 60\n"
            "Band 2: partial health\n"
            "Band 1: generally failing"
        ),
        "input_key_meanings": {
            "evidence.success_rate": "Share of pipeline executions that succeed",
            "evidence.p95_duration_min": "p95 pipeline duration (minutes)",
            "evidence.retry_rate": "Run retry share",
            "evidence.promotion_time_h": "Hours from success to promoted model"
        },
        "example_input": {
            "metric_id": "sm.pipeline_flow_band",
            "evidence": {"success_rate": 0.96, "p95_duration_min": 42, "retry_rate": 0.03, "promotion_time_h": 12.0}
        },
        "example_output": {
            "metric_id": "sm.pipeline_flow_band",
            "band": 4,
            "rationale": "High success with acceptable p95 and retries; promotion at 12h fits band-4.",
            "flags": [],
            "gaps": [
                "Promotion latency at 12h → automate risk sign-off and bake validation into CI → reduce promotion_time_h to ≤8h (unlocks band 5).",
                "p95 at 42min → parallelize feature gen and cache heavy steps → keep p95 ≤30min (reinforces band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "sm.experiments_lineage_band": {
        "system": _rubric_text(
            "Use: pct_code_ref, pct_data_ref, pct_env together.\n"
            "Band 5: ALL ≥ 0.95\n"
            "Band 4: ALL ≥ 0.85 & ≥2 ≥ 0.90\n"
            "Band 3: ALL ≥ 0.70 & ≥1 ≥ 0.85\n"
            "Band 2: ANY < 0.70 but ≥1 ≥ 0.60\n"
            "Band 1: MOST < 0.60 or missing"
        ),
        "input_key_meanings": {
            "evidence.pct_code_ref": "Experiments with code references",
            "evidence.pct_data_ref": "Experiments with data references",
            "evidence.pct_env": "Experiments with environment references"
        },
        "example_input": {
            "metric_id": "sm.experiments_lineage_band",
            "evidence": {"pct_code_ref": 0.90, "pct_data_ref": 0.86, "pct_env": 0.92}
        },
        "example_output": {
            "metric_id": "sm.experiments_lineage_band",
            "band": 4,
            "rationale": "All lineage ≥0.85 with two ≥0.90; data_ref limits band-5.",
            "flags": [],
            "gaps": [
                "Data ref at 0.86 blocks band-5 → enforce dataset version capture in training SDK → raise pct_data_ref to ≥0.90 (unlocks band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "sm.clarify_coverage_band": {
        "system": _rubric_text(
            "Use: pct_with_bias_report & pct_with_explainability.\n"
            "Band 5: both ≥ 0.90\n"
            "Band 4: both ≥ 0.80\n"
            "Band 3: both ≥ 0.70 OR one ≥ 0.85 while the other ≥ 0.70\n"
            "Band 2: one ≥ 0.60 but the other < 0.70\n"
            "Band 1: both < 0.60 or missing"
        ),
        "input_key_meanings": {
            "evidence.pct_with_bias_report": "Experiments/models with bias/fairness reports",
            "evidence.pct_with_explainability": "Experiments/models with explainability outputs"
        },
        "example_input": {
            "metric_id": "sm.clarify_coverage_band",
            "evidence": {"pct_with_bias_report": 0.78, "pct_with_explainability": 0.81}
        },
        "example_output": {
            "metric_id": "sm.clarify_coverage_band",
            "band": 3,
            "rationale": "Explainability ≥0.80; bias at 0.78 holds the band at 3.",
            "flags": ["bias_coverage_low"],
            "gaps": [
                "Bias reports at 0.78 → add Clarify step in pipeline and store JSON → raise pct_with_bias_report to ≥0.80 (unlocks band 4).",
                "Sustain explainability ≥0.80 → make SHAP computation a required stage → keep pct_with_explainability ≥0.80 (stabilizes band 4)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "sm.cost_efficiency_band": {
        "system": _rubric_text(
            "Use: per_1k_inferences_usd, per_training_hour_usd, gpu_mem_headroom_pct, idle_vs_active_ratio.\n"
            "Band 5: per_1k ≤ 0.08 & train_hour ≤ 4 & headroom in [10,40] & idle_ratio < 0.20\n"
            "Band 4: per_1k ≤ 0.10 & train_hour ≤ 6 & headroom in [8,45] & idle_ratio < 0.30\n"
            "Band 3: mixed signals (no severe waste) & idle_ratio < 0.45\n"
            "Band 2: per_1k > 0.12 OR train_hour > 8 OR headroom < 5 or > 55 OR idle_ratio ≥ 0.45\n"
            "Band 1: heavy waste across several dimensions"
        ),
        "input_key_meanings": {
            "evidence.per_1k_inferences_usd": "Serving cost per 1k inferences (USD)",
            "evidence.per_training_hour_usd": "Training cost per compute hour (USD)",
            "evidence.gpu_mem_headroom_pct": "Available GPU memory during peak (%)",
            "evidence.idle_vs_active_ratio": "Idle time ÷ active time over window"
        },
        "example_input": {
            "metric_id": "sm.cost_efficiency_band",
            "evidence": {"per_1k_inferences_usd": 0.11, "per_training_hour_usd": 5.2, "gpu_mem_headroom_pct": 52, "idle_vs_active_ratio": 0.26}
        },
        "example_output": {
            "metric_id": "sm.cost_efficiency_band",
            "band": 3,
            "rationale": "Training cost is fine; serving cost a bit high and GPU headroom is excessive.",
            "flags": ["serving_cost_high", "gpu_headroom_high"],
            "gaps": [
                "High GPU headroom at 52% → reduce instance size or increase batch size → bring headroom into 10–40% (unlocks band 4).",
                "Serving cost 0.11/1k → enable model quantization and autoscaling down → keep per_1k ≤ 0.10 (unlocks band 4)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    # =========================
    # CI/CD (4) — incl. Policy Gates
    # =========================

    "cicd.deploy_frequency_band": {
        "system": _rubric_text(
            "Use: freq_per_week and service_count; approx per-service rate = freq_per_week / max(service_count,1).\n"
            "Band 5: per-service ≳ 1/day (≥5 per week per service) OR freq_per_week ≥ 5 with ≤ 7 services\n"
            "Band 4: per-service ≥ 1/week OR freq_per_week ≥ 3\n"
            "Band 3: ~monthly per-service (≥0.25/week/service) OR freq_per_week ≥1\n"
            "Band 2: sporadic (< monthly per service) but some activity\n"
            "Band 1: rare or none"
        ),
        "input_key_meanings": {
            "evidence.freq_per_week": "Total deployments per week across ML services",
            "evidence.service_count": "Number of ML services"
        },
        "example_input": {
            "metric_id": "cicd.deploy_frequency_band",
            "evidence": {"freq_per_week": 5.2, "service_count": 7}
        },
        "example_output": {
            "metric_id": "cicd.deploy_frequency_band",
            "band": 5,
            "rationale": "≈daily overall with a moderate number of services.",
            "flags": [],
            "gaps": []
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "cicd.lead_time_band": {
        "system": _rubric_text(
            "Use: p50_hours and p95_hours; both must meet thresholds for higher bands.\n"
            "Band 5: p50 ≤ 4h & p95 ≤ 24h\n"
            "Band 4: p50 ≤ 8h & p95 ≤ 48h\n"
            "Band 3: p50 ≤ 24h & p95 ≤ 72h\n"
            "Band 2: partial (one passes but not the other) OR p95 ≤ 96h with weak p50\n"
            "Band 1: slower than above"
        ),
        "input_key_meanings": {
            "evidence.p50_hours": "Median (p50) lead time from commit to prod",
            "evidence.p95_hours": "p95 lead time from commit to prod"
        },
        "example_input": {
            "metric_id": "cicd.lead_time_band",
            "evidence": {"p50_hours": 6.8, "p95_hours": 18.2}
        },
        "example_output": {
            "metric_id": "cicd.lead_time_band",
            "band": 4,
            "rationale": "p50 < 8h and p95 < 24h meet band-4; p50 > 4h blocks band-5.",
            "flags": [],
            "gaps": [
                "p50 at 6.8h prevents band-5 → shard tests and cache dependencies → reduce p50 ≤4h (unlocks band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "cicd.change_failure_rate_band": {
        "system": _rubric_text(
            "Use together: cfr and rollbacks_30d; prefer the worse dimension.\n"
            "Band 5: cfr < 0.15 & rollbacks_30d ≤ 3\n"
            "Band 4: cfr < 0.20 & rollbacks_30d ≤ 5\n"
            "Band 3: cfr < 0.30 & rollbacks_30d ≤ 8\n"
            "Band 2: cfr < 0.40 OR rollbacks_30d ≤ 12\n"
            "Band 1: worse than those"
        ),
        "input_key_meanings": {
            "evidence.cfr": "Change failure rate for prod deployments",
            "evidence.rollbacks_30d": "Rollback count in the last 30 days"
        },
        "example_input": {
            "metric_id": "cicd.change_failure_rate_band",
            "evidence": {"cfr": 0.22, "rollbacks_30d": 4}
        },
        "example_output": {
            "metric_id": "cicd.change_failure_rate_band",
            "band": 3,
            "rationale": "CFR slightly high at 0.22; rollbacks within band-3 limits.",
            "flags": ["cfr_high"],
            "gaps": [
                "CFR at 0.22 limits reliability → add contract tests and canary deploys → bring cfr < 0.20 (unlocks band 4).",
                "Stabilize rollbacks via pre-prod soak tests → keep rollbacks_30d ≤3 (supports band 5 once CFR is <0.15)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "cicd.policy_gates_band": {
        "system": _rubric_text(
            "Inputs: required_checks[], workflow_yaml (text), logs_snippets[].\n"
            "Detect each required check in YAML and whether logs indicate pass/fail.\n"
            "Populate: present, missing, failing.\n"
            "Band 5: ALL required checks present AND passing pre-deploy\n"
            "Band 4: ALL present, but ≤1 failing/flaky in logs\n"
            "Band 3: ≥50% present/passing; some missing or failing\n"
            "Band 2: <50% present/passing; many missing/failing\n"
            "Band 1: Most missing with no enforcement"
        ),
        "input_key_meanings": {
            "required_checks[]": "Mandatory CI gates (pytest, integration-tests, bandit, trivy, bias_check, data_validation, etc.)",
            "workflow_yaml": "CI workflow yaml to infer which checks exist and when they run",
            "logs_snippets[]": "Log lines to infer pass/fail state for checks"
        },
        "example_input": {
            "metric_id": "cicd.policy_gates_band",
            "required_checks": ["pytest", "integration-tests", "bandit", "trivy", "bias_check", "data_validation"],
            "workflow_yaml": "jobs:\n  build:\n    steps:\n      - run: pytest\n      - run: bandit -r .\n      - run: trivy fs .\n      - run: make data_validation\n      - run: make bias_check\n  deploy:\n    needs: build\n    steps:\n      - run: ./deploy.sh",
            "logs_snippets": ["pytest passed", "bandit 0 issues", "trivy no HIGH|CRITICAL", "data_validation ok", "bias_check ok", "integration-tests flaky"]
        },
        "example_output": {
            "metric_id": "cicd.policy_gates_band",
            "band": 4,
            "rationale": "All checks are present; integration-tests show flakiness in logs.",
            "present": ["pytest", "bandit", "trivy", "bias_check", "data_validation", "integration-tests"],
            "missing": [],
            "failing": ["integration-tests"],
            "gaps": [
                "Flaky integration-tests reduce gate strength → quarantine flakies and make test non-optional pre-deploy → ensure passing before deploy (unlocks band 5)."
            ]
        },
        "response_format": POLICY_GATES_RESPONSE_FORMAT,
    },
}


# -----------------------
# Prompt builder and LLM
# -----------------------

def build_prompt(metric_id: str, task_input: dict) -> str:
    meta = METRIC_PROMPTS.get(metric_id)
    if not meta:
        raise ValueError(f"Unknown metric_id: {metric_id}")
    key_meanings = meta.get("input_key_meanings", {})
    key_lines = [f"- {k}: {v}" for k, v in key_meanings.items()]
    meanings_block = "INPUT KEY MEANINGS:\n" + "\n".join(key_lines) + "\n\n" if key_lines else ""
    improvement_block = (
        "IMPROVEMENT GUIDANCE EXAMPLES (how to raise the band):\n- "
        + "\n- ".join(IMPROVEMENT_GUIDANCE_EXAMPLES)
        + "\n\n"
    )
    return (
        f"{meta['system']}\n\n"
        f"{meanings_block}"
        f"RESPONSE FORMAT (JSON only):\n{meta['response_format']}\n\n"
        f"{improvement_block}"
        f"EVIDENCE (USER):\n{json.dumps(task_input, indent=2)}\n\n"
        f"EXAMPLE INPUT:\n{json.dumps(meta.get('example_input', {}), indent=2)}\n\n"
        f"EXAMPLE OUTPUT:\n{json.dumps(meta.get('example_output', {}), indent=2)}"
    )


# -------------------------
# LLM Engine class
# -------------------------

class MLOpsLLM(BaseMicroAgent):
    def grade_metric(self, metric_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        _ = METRIC_PROMPTS[metric_id]  # fail fast if unknown
        prompt = build_prompt(metric_id, evidence)
        return self._ask(metric_id=metric_id, user_prompt=prompt)

    def _ask(self, *, metric_id: str, user_prompt: str, max_tokens: int = 700) -> Dict[str, Any]:
        time.sleep(random.uniform(0.02, 0.07))
        raw = self._call_llm(system_prompt="", prompt=user_prompt, max_tokens=max_tokens)
        try:
            out = self._parse_json_response(raw) or {}
        except Exception:
            out = {}

        # Stamp metric and normalize band
        out["metric_id"] = metric_id
        try:
            band_val = int(out.get("band", out.get("score", 3)))
        except Exception:
            band_val = 3
        out["band"] = max(1, min(5, band_val))

        # Remove stray fields from other engines; KEEP gaps
        out.pop("score", None)
        out.pop("evidence", None)
        out.pop("actions", None)
        out.pop("confidence", None)

        # Ensure schema-specific fields
        if metric_id == "cicd.policy_gates_band":
            out.setdefault("rationale", "No rationale.")
            out.setdefault("present", [])
            out.setdefault("missing", [])
            out.setdefault("failing", [])
            out.setdefault("gaps", [])
            out.pop("flags", None)
        else:
            out.setdefault("rationale", "No rationale.")
            out.setdefault("flags", [])
            out.setdefault("gaps", [])

        return out

    # ---- Wrapper methods (1:1) ----
    # MLflow
    def grade_mlflow_experiment_completeness(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("mlflow.experiment_completeness_band", evidence)

    def grade_mlflow_lineage_coverage(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("mlflow.lineage_coverage_band", evidence)

    def grade_mlflow_experiment_velocity(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("mlflow.experiment_velocity_band", evidence)

    def grade_mlflow_registry_governance(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("mlflow.registry_hygiene_band", evidence)

    def grade_mlflow_validation_artifacts(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("mlflow.validation_artifacts_band", evidence)

    def grade_mlflow_reproducibility(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("mlflow.reproducibility_band", evidence)

    # Azure ML
    def grade_aml_endpoint_slo(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("aml.endpoint_slo_band", evidence)

    def grade_aml_jobs_flow(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("aml.jobs_flow_band", evidence)

    def grade_aml_monitoring_coverage(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("aml.monitoring_coverage_band", evidence)

    def grade_aml_registry_governance(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("aml.registry_governance_band", evidence)

    def grade_aml_cost_correlation(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("aml.cost_correlation_band", evidence)

    # SageMaker
    def grade_sm_endpoint_slo_scaling(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("sm.endpoint_slo_scaling_band", evidence)

    def grade_sm_pipeline_flow(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("sm.pipeline_flow_band", evidence)

    def grade_sm_experiments_lineage(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("sm.experiments_lineage_band", evidence)

    def grade_sm_clarify_coverage(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("sm.clarify_coverage_band", evidence)

    def grade_sm_cost_efficiency(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("sm.cost_efficiency_band", evidence)

    # CI/CD
    def grade_cicd_deploy_frequency(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("cicd.deploy_frequency_band", evidence)

    def grade_cicd_lead_time(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("cicd.lead_time_band", evidence)

    def grade_cicd_change_failure_rate(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("cicd.change_failure_rate_band", evidence)

    def check_cicd_policy_gates(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("cicd.policy_gates_band", evidence)

    # Parity with other engines
    def evaluate(self, code_snippets: List[str], context: Optional[Dict] = None) -> Dict[str, Any]:
        return {"status": "ok"}