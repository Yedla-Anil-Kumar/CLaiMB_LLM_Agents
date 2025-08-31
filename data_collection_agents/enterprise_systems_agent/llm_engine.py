# Data_Collection_Agents/enterprise_agent/llm_engine.py
from __future__ import annotations
import json
import random
import time
from typing import Any, Dict, List, Optional

from enterprise_systems_agent.base_agent import BaseMicroAgent


"""
Enterprise Systems Metric Grader — ONE-SHOT (per metric)

- Universal preamble + per-metric rubric
- Each metric includes: example_input AND example_output (true one-shot)
- build_prompt prints the RESPONSE FORMAT before EXAMPLES to reduce anchoring
- input_key_meanings documents expected evidence fields for every metric
- Public API: one wrapper method per metric (20 total)

Schema (LLM output):
  {"metric_id","band","rationale","flags","gaps"}

Rationale guidance:
  Name the strongest positive AND the main limiting factor (≤3 sentences).

Gaps guidance:
  Use action-plan phrasing:
  "<limiter> → <what to change> → <target threshold> (unlocks band X)".

Backward-compat shim:
  _ask() mirrors `band` -> `Score` and stamps `MetricID` so the current
  EnterpriseOrchestrator (which calls _s(metric["Score"])) keeps working.
"""

# -------- Universal grading contract --------

UNIVERSAL_PREAMBLE = (
    "You are an Enterprise Systems Assessor. Grade exactly one metric on a 1–5 band:\n"
    "5 = Excellent\n"
    "4 = Good\n"
    "3 = Fair\n"
    "2 = Poor\n"
    "1 = Critical\n\n"
    "Rules:\n"
    "- Use ONLY the provided JSON evidence/rubric. Do NOT invent data.\n"
    "- Evaluate ALL relevant evidence fields together; if signals conflict, choose the lower band and explain briefly.\n"
    "- Be conservative at borders. Keep the rationale ≤3 sentences and mention the strongest positive and the limiting factor.\n"
    "- 'gaps' must be practical action steps: '<limiter> → <what to change> → <target> (unlocks band X)'.\n"
    "- Return ONLY the specified JSON. No extra text."
)

UNIVERSAL_RESPONSE_FORMAT = (
    '{"metric_id":"<id>",'
    '"band":<1-5>,'
    '"rationale":"<1-3 sentences naming strongest positive and limiting factor>",'
    '"flags":[],'
    '"gaps":[]}'
)

def _rubric(text: str) -> str:
    return f"SYSTEM:\n{UNIVERSAL_PREAMBLE}\n\nRUBRIC:\n{text}"

# --- A tiny few-shot steering block to make 'gaps' more actionable ---
IMPROVEMENT_GUIDANCE_EXAMPLES = [
    "Tail risk unknown → add p95/p99 latency and failure %, per-system → keep p95 within SLA and failures <0.5% (unlocks band 5).",
    "Coverage uneven by platform → report coverage per platform and runs/week → achieve ≥0.85 coverage on ≥3 platforms (unlocks band 5).",
    "Root causes opaque → instrument pass/fail for unit/integration/security/data gates → show ≥95% pass pre-deploy (supports band 5).",
    "Stability unproven → include last 8–12 weeks trend for median and p90 → demonstrate non-declining trend (solidifies band 4–5).",
]

# -------- Metric definitions (20 one-shot graders) --------

METRIC_PROMPTS: Dict[str, Dict[str, Any]] = {
    # ---------- 1) Business Process & Workflow (1–10) ----------
    "process.automation.coverage": {
        "system": _rubric(
            "Coverage ratio of automated objects/workflows across Salesforce, SAP BPM, Workday, ServiceNow.\n"
            "Band 5: coverage_ratio ≥ 0.85 across ≥3 platforms with regular executions;\n"
            "Band 4: 0.70–0.84 across ≥2 platforms; Band 3: 0.50–0.69 (siloed/patchy);\n"
            "Band 2: 0.30–0.49 sporadic; Band 1: <0.30."
        ),
        "input_key_meanings": {
            "computed": "Namespace containing precomputed fields for automation footprint",
            "computed.sf_active_flows": "Count of active Salesforce Flows/Apex-triggered automations",
            "computed.sn_active_flows": "Count of active ServiceNow Flows/Workflows",
            "computed.wd_enabled_bps": "Number of enabled Workday business processes with automation steps",
            "computed.sap_bpm_runs_7d": "Execution count of SAP BPM jobs in last 7 days",
            "computed.estimated_automated_objects": "Estimated number of automated objects/entities",
            "computed.estimated_total_objects": "Estimated total automatable objects/entities",
            "computed.coverage_ratio": "Automated objects / total objects (0..1)",
        },
        "example_input": {
            "computed": {
                "sf_active_flows": 8,
                "sn_active_flows": 4,
                "wd_enabled_bps": 3,
                "sap_bpm_runs_7d": 300,
                "estimated_automated_objects": 22,
                "estimated_total_objects": 25,
                "coverage_ratio": 0.88
            }
        },
        "example_output": {
            "metric_id": "process.automation.coverage",
            "band": 5,
            "rationale": "High coverage across four platforms; minor manual tails remain in long-tail objects.",
            "flags": ["multi_platform_coverage"],
            "gaps": [
                "Execution regularity not verified → publish runs/week per platform for last 4 weeks → confirm consistent cadence (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "workflow.sla_adherence": {
        "system": _rubric(
            "On-time rate vs SLA for SF Cases, SN Incidents, SAP tickets, Workday tasks.\n"
            "Band 5: on_time_rate ≥ 0.95; 4: 0.90–0.94; 3: 0.80–0.89; 2: 0.60–0.79; 1: <0.60."
        ),
        "input_key_meanings": {
            "computed": "Namespace with SLA adherence calculations",
            "computed.on_time": "Count of items completed within SLA window",
            "computed.total": "Total completed items measured for SLA",
            "computed.by_system": "Per-system on-time ratio map (0..1) for SF/SN/SAP/WD",
            "computed.on_time_rate": "Optional precomputed on_time/total ratio (0..1)",
        },
        "example_input": {
            "computed": {
                "on_time": 190,
                "total": 200,
                "by_system": {"SF": 0.97, "SN": 0.96, "SAP": 0.93, "WD": 0.95}
            }
        },
        "example_output": {
            "metric_id": "workflow.sla_adherence",
            "band": 5,
            "rationale": "Aggregate on-time ≈0.95 with strong cross-system performance; SAP slightly lower limits risk buffer.",
            "flags": ["sap_trailing"],
            "gaps": [
                "Tail risk unknown → add p95/p99 lateness minutes per system → keep p95 within SLA for ≥95% items (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "sales.lead_to_oppty_cycle_time": {
        "system": _rubric(
            "Median hours from lead creation to opportunity creation/qualification (lower is better). Consider p90 tail.\n"
            "Band 5: ≤12h; 4: 13–24h; 3: 25–48h; 2: 49–96h; 1: >96h."
        ),
        "input_key_meanings": {
            "computed": "Namespace with conversion timing stats",
            "computed.median_hours": "Median hours from lead create → opportunity create/qualify",
            "computed.p90_hours": "90th percentile hours for the same path",
            "computed.sample": "Sample size (number of converted leads considered)",
        },
        "example_input": {"computed": {"median_hours": 10, "p90_hours": 20, "sample": 500}},
        "example_output": {
            "metric_id": "sales.lead_to_oppty_cycle_time",
            "band": 5,
            "rationale": "Median 10h is excellent with a tight p90 at 20h; seasonal variance unknown.",
            "flags": ["fast_conversion"],
            "gaps": [
                "Stability unproven → publish weekly medians/p90 for last 12 weeks → demonstrate non-declining trend (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "itsm.case_resolution_time": {
        "system": _rubric(
            "Median minutes to resolve incidents/requests in ServiceNow (lower is better). Consider p90 tail.\n"
            "Band 5: ≤45m; 4: 46–90m; 3: 91–180m; 2: 181–360m; 1: >360m."
        ),
        "input_key_meanings": {
            "computed": "Namespace with SN resolution timing stats",
            "computed.median_minutes": "Median minutes to resolve incident/request",
            "computed.p90_minutes": "90th percentile minutes to resolve",
            "computed.n_resolved": "Number of resolved tickets in window",
        },
        "example_input": {"computed": {"median_minutes": 40, "p90_minutes": 70, "n_resolved": 500}},
        "example_output": {
            "metric_id": "itsm.case_resolution_time",
            "band": 5,
            "rationale": "Median 40m with p90 70m shows fast resolution; impact of P1 incidents not shown.",
            "flags": ["low_tail_risk"],
            "gaps": [
                "Priority mix unclear → break out p50/p90 by P1/P2/P3 → ensure P1 p90 ≤90m (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "itsm.incident_reopen_rate": {
        "system": _rubric(
            "Share of incidents reopened within 7d of resolution (lower is better).\n"
            "Band 5: ≤2%; 4: 2–7%; 3: 8–12%; 2: 13–20%; 1: >20%."
        ),
        "input_key_meanings": {
            "computed": "Namespace with reopen quality metrics",
            "computed.rate": "Reopen ratio (reopened/resolved, 0..1)",
            "computed.reopened": "Number of reopened incidents in window",
            "computed.resolved": "Number of resolved incidents in window",
            "computed.by_priority": "Optional reopen rates by priority code",
        },
        "example_input": {
            "computed": {"rate": 0.015, "reopened": 9, "resolved": 600, "by_priority": {"1": 0.02, "2": 0.015, "3": 0.01}}
        },
        "example_output": {
            "metric_id": "itsm.incident_reopen_rate",
            "band": 5,
            "rationale": "Reopen rate ~1.5% indicates strong first-time fix; priority mix effects unknown.",
            "flags": ["excellent_ftfr"],
            "gaps": [
                "Root causes opaque → show reopen rate by resolver group and top 3 causes → reduce high-variance groups ≤2% (maintains band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "hr.onboarding_cycle_time": {
        "system": _rubric(
            "Workday Hire BP start→complete median hours (lower is better). Consider approval tail.\n"
            "Band 5: ≤24h; 4: 25–48h; 3: 49–72h; 2: 73–120h; 1: >120h."
        ),
        "input_key_meanings": {
            "computed": "Namespace with Workday onboarding timings",
            "computed.median_hours": "Median hours from BP start to completion",
            "computed.p90_hours": "90th percentile hours for onboarding",
            "computed.n_hires": "Number of hires completed in window",
        },
        "example_input": {"computed": {"median_hours": 20, "p90_hours": 36, "n_hires": 60}},
        "example_output": {
            "metric_id": "hr.onboarding_cycle_time",
            "band": 5,
            "rationale": "Median 20h with p90 36h is fast; dependency on specific approver chains not assessed.",
            "flags": ["fast_bp"],
            "gaps": [
                "Bottlenecks hidden → list top 3 longest approval steps with median/p90 → keep worst-step p90 ≤48h (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "sap.procure_to_pay_cycle": {
        "system": _rubric(
            "Total days from PO creation → approval → GR → invoice posted (lower is better). Consider sub-stage splits.\n"
            "Band 5: ≤5d; 4: 6–8d; 3: 9–12d; 2: 13–20d; 1: >20d."
        ),
        "input_key_meanings": {
            "computed": "Namespace with SAP P2P stage timings",
            "computed.total_days": "Total end-to-end days from PO create to invoice posted",
            "computed.approval_days": "Days from PO create to PO approval",
            "computed.gr_days": "Days from approval to Goods Receipt",
            "computed.invoice_days": "Days from GR to invoice posted",
        },
        "example_input": {"computed": {"total_days": 4.5, "approval_days": 0.5, "gr_days": 2.0, "invoice_days": 2.0}},
        "example_output": {
            "metric_id": "sap.procure_to_pay_cycle",
            "band": 5,
            "rationale": "End-to-end 4.5d is excellent; invoice posting variance not shown.",
            "flags": ["efficient_p2p"],
            "gaps": [
                "Tail variance unknown → provide p90 per sub-stage and by vendor tier → keep stage p90 ≤3d (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "q2c.throughput": {
        "system": _rubric(
            "Quote approval → Sales Order → Billing total hours (lower is better for time-to-cash). Consider sub-paths.\n"
            "Band 5: ≤12h; 4: 13–24h; 3: 25–48h; 2: 49–96h; 1: >96h."
        ),
        "input_key_meanings": {
            "computed": "Namespace with Q2C stage timings",
            "computed.total_hours": "Total hours from quote approval to billing posted",
            "computed.quote_to_so_hours": "Hours from quote approval to sales order",
            "computed.so_to_bill_hours": "Hours from SO to billing",
        },
        "example_input": {"computed": {"total_hours": 10, "quote_to_so_hours": 4, "so_to_bill_hours": 6}},
        "example_output": {
            "metric_id": "q2c.throughput",
            "band": 5,
            "rationale": "10h total is elite; dependence on specific approver windows could limit resilience.",
            "flags": ["fast_time_to_cash"],
            "gaps": [
                "Variability unknown → slice throughput by product family/region → keep p90 ≤18h across segments (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "backlog.aging": {
        "system": _rubric(
            "Median age of open work and tail risk across SN/WD/SAP (lower is better).\n"
            "Band 5: p50 ≤1d & p90 ≤3d; 4: p50 ≤2d & p90 ≤5d; 3: p50 ≤3d & p90 ≤7d; 2: p50 ≤5d or p90 ≤10d; 1: worse."
        ),
        "input_key_meanings": {
            "computed": "Namespace with open-work age stats",
            "computed.p50_days": "Median (p50) days of age for open items",
            "computed.p90_days": "90th percentile days of age",
            "computed.open_items": "Count of open items measured",
        },
        "example_input": {"computed": {"p50_days": 0.8, "p90_days": 2.5, "open_items": 200}},
        "example_output": {
            "metric_id": "backlog.aging",
            "band": 5,
            "rationale": "Backlog turns quickly (p50 0.8d, p90 2.5d); queue-specific hotspots unknown.",
            "flags": ["low_queue_age"],
            "gaps": [
                "Hidden pockets possible → publish per-queue age p95 and oldest 10 items → keep all queues p90 ≤3d (maintains band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "rpa.success_rate": {
        "system": _rubric(
            "Reliability of RPA runs overall and by system (higher is better). Consider volume and retries.\n"
            "Band 5: ≥98%; 4: 93–97%; 3: 85–92%; 2: 70–84%; 1: <70%."
        ),
        "input_key_meanings": {
            "computed": "Namespace with RPA run outcomes",
            "computed.rate": "Overall success ratio (success/(success+failed))",
            "computed.success": "Number of successful RPA runs in window",
            "computed.failed": "Number of failed RPA runs in window",
            "computed.by_system": "Optional per-system success ratios",
        },
        "example_input": {"computed": {"rate": 0.985, "success": 985, "failed": 15, "by_system": {"SAP": 0.98, "SF": 0.99}}},
        "example_output": {
            "metric_id": "rpa.success_rate",
            "band": 5,
            "rationale": "Overall 98.5% with strong per-system rates; impact of retries/auto-recovery not provided.",
            "flags": ["high_reliability"],
            "gaps": [
                "Retry dynamics unknown → add retry counts and auto-recovery share per system → keep retries ≤2% of runs (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    # ---------- 2) Integration & Data Health (11–15) ----------
    "integration.data_sync_latency": {
        "system": _rubric(
            "Latency between source and target delivery in iPaaS events (lower is better). Consider p95 tail and failure %.\n"
            "Band 5: median ≤30s & p95 ≤60s; 4: median ≤90s & p95 ≤180s; 3: median ≤300s; 2: median ≤900s; 1: worse."
        ),
        "input_key_meanings": {
            "computed": "Namespace with event delivery timings",
            "computed.median_sec": "Median seconds from source emit to target delivery",
            "computed.p95_sec": "95th percentile seconds for same",
            "computed.failed_pct": "Share of events failing delivery (0..1)",
        },
        "example_input": {"computed": {"median_sec": 25, "p95_sec": 55, "failed_pct": 0.0}},
        "example_output": {
            "metric_id": "integration.data_sync_latency",
            "band": 5,
            "rationale": "Median 25s and p95 55s are near-real-time; failure rate context is minimal.",
            "flags": ["near_real_time"],
            "gaps": [
                "Failure context missing → provide failure %, retry storms, and DLQ rate → keep failures ≤0.2% and DLQ ≈0 (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "api.reliability": {
        "system": _rubric(
            "API latency vs SLO and error rates across endpoints.\n"
            "Band 5: p95 within SLO & error_rate ≤0.5%; 4: slight SLO under-runs or 0.5–1%; 3: marginal misses or 1–2%; 2: frequent misses or 2–5%; 1: severe."
        ),
        "input_key_meanings": {
            "computed": "Namespace with API reliability stats",
            "computed.p95_ms": "95th percentile latency in milliseconds",
            "computed.error_rate_pct": "Error rate (%) across requests (0..100)",
            "computed.rps": "Average requests per second (traffic context)",
            "computed.slo_p95_ms": "Optional SLO threshold for p95 latency",
            "computed.slo_error_rate_pct": "Optional SLO threshold for error rate (%)",
        },
        "example_input": {"computed": {"p95_ms": 300, "error_rate_pct": 0.1, "rps": 120}},
        "example_output": {
            "metric_id": "api.reliability",
            "band": 5,
            "rationale": "Latency within SLO and ~0.1% errors shows strong reliability; per-endpoint variance unknown.",
            "flags": ["headroom_present"],
            "gaps": [
                "Endpoint variance unknown → provide top 5 endpoints by traffic with p95/error rates → ensure each meets SLO (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "integration.topology_health": {
        "system": _rubric(
            "Health of integration nodes/edges: uptime, retry storms, dead-letter rate.\n"
            "Band 5: ≥99.9% uptime across nodes, no critical errors; 4: minor instability in ≤1 node; 3: multiple nodes <99.5% or recurring errors; 2: frequent outages; 1: systemic failures."
        ),
        "input_key_meanings": {
            "computed": "Namespace with node/edge health indicators",
            "computed.avg_uptime": "Average node uptime percentage across estate",
            "computed.nodes_healthy": "Count of nodes within acceptable error/uptime thresholds",
            "computed.nodes_total": "Total number of nodes monitored",
            "computed.critical_errors": "Count of critical errors observed in window",
        },
        "example_input": {"computed": {"avg_uptime": 99.95, "nodes_healthy": 3, "nodes_total": 3, "critical_errors": 0}},
        "example_output": {
            "metric_id": "integration.topology_health",
            "band": 5,
            "rationale": "All nodes stable with ~99.95% uptime; DLQ volume not reported.",
            "flags": ["nodes_green"],
            "gaps": [
                "DLQ/retry visibility missing → add DLQ rate and retry storm counts per node → keep DLQ ~0 and storms rare (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "mdm.duplicate_rate": {
        "system": _rubric(
            "Duplicate rate across CRM/SAP/MDM matched entities (lower is better).\n"
            "Band 5: ≤2%; 4: 3–5%; 3: 6–10%; 2: 11–20%; 1: >20%."
        ),
        "input_key_meanings": {
            "computed": "Namespace with duplicate detection outcomes",
            "computed.rate": "Duplicate ratio among entities (0..1)",
            "computed.duplicate_groups": "Number of groups of duplicates detected",
            "computed.total_entities": "Total entities evaluated for duplication",
        },
        "example_input": {"computed": {"rate": 0.02, "duplicate_groups": 10, "total_entities": 500}},
        "example_output": {
            "metric_id": "mdm.duplicate_rate",
            "band": 5,
            "rationale": "~2% duplicates indicates strong matching/standardization; recent trend unknown.",
            "flags": ["low_dupes"],
            "gaps": [
                "Trend and source mix unknown → provide monthly duplicate trend and breakdown by source system → maintain ≤2% across sources (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "dq.exceptions_rate": {
        "system": _rubric(
            "Weighted exception rate by rule severity across systems (lower is better).\n"
            "Band 5: ≤1%; 4: 1–3%; 3: 3–6%; 2: 6–10%; 1: >10%. Consider severity mix."
        ),
        "input_key_meanings": {
            "computed": "Namespace with data quality control results",
            "computed.rate": "Overall exception rate (0..1) weighted by severity",
            "computed.failed_checks": "Count of failed rules/checks",
            "computed.total_checks": "Total rules/checks evaluated",
            "computed.weighted_severity": "Average weighted severity across failures",
        },
        "example_input": {"computed": {"rate": 0.008, "failed_checks": 20, "total_checks": 2500, "weighted_severity": 0.8}},
        "example_output": {
            "metric_id": "dq.exceptions_rate",
            "band": 5,
            "rationale": "~0.8% exceptions with low severity suggests strong DQ; coverage of critical rules not shown.",
            "flags": ["dq_strong"],
            "gaps": [
                "Coverage and impact unclear → list top 10 failing rules with severities and affected records → keep critical-rule failures near 0 (maintains band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    # ---------- 3) AI Integration & Outcomes (16–18) ----------
    "ai.penetration": {
        "system": _rubric(
            "Coverage of workflows using AI features and their execution share (higher is better).\n"
            "Band 5: ≥75% workflows & ≥75% executions; 4: 50–74%; 3: 30–49%; 2: 10–29%; 1: <10%."
        ),
        "input_key_meanings": {
            "computed": "Namespace with AI adoption coverage",
            "computed.workflows_with_ai": "Count of workflows that include AI features",
            "computed.workflows_total": "Total workflows in scope",
            "computed.executions_ai_pct": "Share of executions that invoke AI (0..1)",
        },
        "example_input": {"computed": {"workflows_with_ai": 80, "workflows_total": 100, "executions_ai_pct": 0.78}},
        "example_output": {
            "metric_id": "ai.penetration",
            "band": 5,
            "rationale": "AI present in 80% of workflows and 78% of runs; depth by use-case is unclear.",
            "flags": ["broad_adoption"],
            "gaps": [
                "Depth of usage unclear → list top AI use-cases and share of executions → ensure ≥3 material use-cases each ≥15% (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "ai.outcome_uplift": {
        "system": _rubric(
            "Before/after KPI improvement attributable to AI rollout (higher is better). Consider stability.\n"
            "Band 5: ≥20% uplift; 4: 10–19%; 3: 5–9%; 2: 1–4%; 1: <1% or negative."
        ),
        "input_key_meanings": {
            "computed": "Namespace with before/after KPI results",
            "computed.uplift_pct": "Estimated KPI improvement share (0..1)",
            "computed.baseline": "Baseline KPI value (pre-AI)",
            "computed.post": "Post-AI KPI value (same units as baseline)",
        },
        "example_input": {"computed": {"uplift_pct": 0.25, "baseline": 200, "post": 150}},
        "example_output": {
            "metric_id": "ai.outcome_uplift",
            "band": 5,
            "rationale": "Estimated 25% uplift is substantial; durability over multiple periods not proven.",
            "flags": ["strong_uplift"],
            "gaps": [
                "Durability unproven → add 8–12 week post-rollout trend and holdout/control if possible → maintain uplift ≥20% (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "ai.governance_coverage": {
        "system": _rubric(
            "Share of models with required governance controls; alert context.\n"
            "Band 5: ≥90%; 4: 75–89%; 3: 50–74%; 2: 25–49%; 1: <25%."
        ),
        "input_key_meanings": {
            "computed": "Namespace with model governance stats",
            "computed.coverage": "Share of models with all required controls (0..1)",
            "computed.models_with_all_controls": "Count of models that meet all governance controls",
            "computed.models_total": "Total models in registry/scope",
            "computed.alerts_30d": "Count of governance/monitoring alerts in last 30 days",
        },
        "example_input": {"computed": {"coverage": 0.92, "models_with_all_controls": 46, "models_total": 50, "alerts_30d": 1}},
        "example_output": {
            "metric_id": "ai.governance_coverage",
            "band": 5,
            "rationale": "Governance coverage ~92% with few alerts; control effectiveness tests not shown.",
            "flags": ["policies_covered"],
            "gaps": [
                "Effectiveness not validated → report % models with successful periodic control verification → keep verified ≥90% (maintains band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    # ---------- 4) Platform Health, Change & Risk (19–20) ----------
    "platform.customization_debt": {
        "system": _rubric(
            "Composite index from SF Apex/Flows, SN custom records, SAP transports, WD custom steps (lower is better).\n"
            "Band 5: low footprint & stable change; 4: moderate-low; 3: moderate; 2: high; 1: very high/brittle."
        ),
        "input_key_meanings": {
            "computed": "Namespace with platform customization surface",
            "computed.index": "Composite customization risk index (lower is better)",
            "computed.sf_apex": "Approximate count of Apex classes/triggers/custom flows",
            "computed.sn_custom_records": "Count of custom tables/records in ServiceNow",
            "computed.sap_transports_30d": "Count of SAP transports in last 30 days",
            "computed.wd_custom_steps": "Number of custom steps in Workday BPs",
        },
        "example_input": {"computed": {"index": 0.25, "sf_apex": 40, "sn_custom_records": 5, "sap_transports_30d": 3, "wd_custom_steps": 1}},
        "example_output": {
            "metric_id": "platform.customization_debt",
            "band": 5,
            "rationale": "Lean customization with disciplined transport cadence; dependency risk not detailed.",
            "flags": ["lean_footprint"],
            "gaps": [
                "Hidden risk unknown → add counts of unmanaged customizations and deprecated API usage → keep unmanaged/deprecated at 0 (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },

    "change.failure_rate": {
        "system": _rubric(
            "Proportion of failed or rolled-back changes across platforms (lower is better).\n"
            "Band 5: ≤3%; 4: 4–7%; 3: 8–12%; 2: 13–20%; 1: >20%."
        ),
        "input_key_meanings": {
            "computed": "Namespace with release reliability stats",
            "computed.rate": "Change failure rate (failed_or_rollback/deploys, 0..1)",
            "computed.deploys": "Total number of deploys in measurement window",
            "computed.failed_or_rollback": "Count of failed or rolled-back deploys",
        },
        "example_input": {"computed": {"rate": 0.02, "deploys": 200, "failed_or_rollback": 4}},
        "example_output": {
            "metric_id": "change.failure_rate",
            "band": 5,
            "rationale": "~2% CFR indicates robust gating; lack of policy-gate breakdown limits root-cause insight.",
            "flags": ["low_cfr"],
            "gaps": [
                "Gate effectiveness unknown → provide pass/fail counts for unit/integration/security/data gates pre-deploy → keep all gate pass rates ≥95% (solidifies band 5)."
            ]
        },
        "response_format": UNIVERSAL_RESPONSE_FORMAT,
    },
}


# -------- Prompt builder --------

def _build_prompt(metric_id: str, evidence: Dict[str, Any]) -> str:
    meta = METRIC_PROMPTS.get(metric_id)
    if not meta:
        raise ValueError(f"Unknown metric_id: {metric_id}")
    meanings = meta.get("input_key_meanings", {})
    key_meanings_str = "\n".join(
        [f"- {k}: {v}" for k, v in meanings.items()]
    ) if meanings else "N/A"

    improvement_block = (
        "IMPROVEMENT GUIDANCE EXAMPLES (how to raise the band):\n- "
        + "\n- ".join(IMPROVEMENT_GUIDANCE_EXAMPLES)
        + "\n\n"
    )

    return (
        f"{meta['system']}\n\n"
        f"INPUT JSON KEYS AND MEANINGS:\n{key_meanings_str}\n\n"
        f"RESPONSE FORMAT (JSON only):\n{meta['response_format']}\n\n"
        f"{improvement_block}"
        f"TASK INPUT (USER EVIDENCE):\n{json.dumps(evidence, indent=2)}\n\n"
        f"ONE-SHOT EXAMPLE INPUT:\n{json.dumps(meta['example_input'], indent=2)}\n\n"
        f"ONE-SHOT EXAMPLE OUTPUT:\n{json.dumps(meta['example_output'], indent=2)}"
    )


# -------- LLM wrapper --------

class EnterpriseLLM(BaseMicroAgent):
    """One-shot JSON-in/JSON-out grader with 20 wrapper methods (updated schema)."""

    def _ask(self, *, metric_id: str, user_prompt: str, max_tokens: int = 700) -> Dict[str, Any]:
        time.sleep(random.uniform(0.02, 0.06))
        raw = self._call_llm(system_prompt="", prompt=user_prompt, max_tokens=max_tokens)
        try:
            out = self._parse_json_response(raw) or {}
        except Exception:
            out = {}

        # Ensure required schema fields
        out.setdefault("metric_id", metric_id)
        try:
            band_val = int(out.get("band", 3))
        except Exception:
            band_val = 3
        out["band"] = max(1, min(5, band_val))
        out.setdefault("rationale", "Strong headline signal; limited by missing detail on tail/stability.")
        out.setdefault("flags", [])
        out.setdefault("gaps", [])

        # ---- Backward-compat shim for current orchestrator ----
        # Stamp legacy fields so EnterpriseOrchestrator._s(metric["Score"]) works.
        out["MetricID"] = out["metric_id"]
        out["Score"] = out["band"]
        # -------------------------------------------------------

        return out

    # ---- Public API ----
    def grade_metric(self, metric_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        _ = METRIC_PROMPTS[metric_id]  # fail fast if unknown
        prompt = _build_prompt(metric_id, evidence)
        return self._ask(metric_id=metric_id, user_prompt=prompt)

    # ---- 20 wrappers (1:1) ----
    # 1–10
    def grade_process_automation_coverage(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("process.automation.coverage", e)

    def grade_workflow_sla_adherence(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("workflow.sla_adherence", e)

    def grade_sales_lead_to_oppty_cycle_time(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("sales.lead_to_oppty_cycle_time", e)

    def grade_itsm_case_resolution_time(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("itsm.case_resolution_time", e)

    def grade_itsm_incident_reopen_rate(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("itsm.incident_reopen_rate", e)

    def grade_hr_onboarding_cycle_time(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("hr.onboarding_cycle_time", e)

    def grade_sap_procure_to_pay_cycle(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("sap.procure_to_pay_cycle", e)

    def grade_q2c_throughput(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("q2c.throughput", e)

    def grade_backlog_aging(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("backlog.aging", e)

    def grade_rpa_success_rate(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("rpa.success_rate", e)

    # 11–15
    def grade_integration_data_sync_latency(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("integration.data_sync_latency", e)

    def grade_api_reliability(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("api.reliability", e)

    def grade_integration_topology_health(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("integration.topology_health", e)

    def grade_mdm_duplicate_rate(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("mdm.duplicate_rate", e)

    def grade_dq_exceptions_rate(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("dq.exceptions_rate", e)

    # 16–18
    def grade_ai_penetration(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("ai.penetration", e)

    def grade_ai_outcome_uplift(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("ai.outcome_uplift", e)

    def grade_ai_governance_coverage(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("ai.governance_coverage", e)

    # 19–20
    def grade_platform_customization_debt(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("platform.customization_debt", e)

    def grade_change_failure_rate(self, e: Dict[str, Any]) -> Dict[str, Any]:
        return self.grade_metric("change.failure_rate", e)

    # parity with other agents
    def evaluate(self, code_snippets: List[str], context: Optional[Dict] = None) -> Dict[str, Any]:
        return {"status": "ok"}