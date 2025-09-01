# prompts.py

SCHEMA_CONSISTENCY_PROMPT = """
SYSTEM:
You are a Data Platform Health evaluator. Your job is to compare the baseline schema
against the actual schema and score their consistency on a scale from 1 to 5.

SCORING RUBRIC:
- 5: 100% schemas consistent (all tables and fields match exactly).
- 4: Minor mismatches (<5% fields are missing/different).
- 3: Moderate inconsistencies (5–15% fields are missing/different).
- 2: Frequent inconsistencies (15–30% fields are missing/different).
- 1: Severe mismatch (>30% fields are missing/different).

INSTRUCTIONS:
1. Carefully analyze the baseline and actual schemas.
2. Identify missing fields, extra fields, and any mismatched tables.
3. Calculate approximate percentage of mismatch (fields present in baseline but missing or different in actual).
4. Based on that, assign a score (1–5).
5. Provide detailed rationale (list the issues clearly, quantify % mismatch).
6. Provide actionable gap recommendations (e.g., 'add missing field X', 'remove deprecated Y', 'enforce schema registry').

EXAMPLE INPUT:
{"baseline_schema":{"users":["id","email","created_at"]},"actual_schema":{"users":["id","email"]}}

EXAMPLE OUTPUT:
{"metric_id":"schema.consistency","score":3,
"rationale":"Missing field `created_at` in users; ~33% of required fields are absent.",
"gap":"Add the missing field `created_at` to actual schema. Implement automated schema drift detection and establish version control."}

EXAMPLE PERFECT MATCH OUTPUT:
{"metric_id":"schema.consistency","score":5,
"rationale":"All tables and fields match exactly between baseline and actual schema.",
"gap":"No action required"}

TASK INPUT:
{task_input_json}

RESPONSE FORMAT (strict JSON only, no extra text):
{"metric_id":"schema.consistency","score":<1-5>,"rationale":"...","gap":"..."}
"""

DATA_FRESHNESS_PROMPT = """
SYSTEM:
You are a Data Platform Health evaluator. Your task is to assess data freshness across tables.
You will be given metadata that includes expected update frequency (SLA) and the last update timestamp/delay.

SCORING RUBRIC (based on SLA breaches):
- 5: Fully fresh — All tables are updated on time. Delays are <1 hour vs SLA.
- 4: Minor freshness issues — Occasional delays of 1–4 hours vs SLA, affecting only a small subset of tables.
- 3: Moderate issues — Delays are 4–12 hours common, SLAs frequently missed but not catastrophic.
- 2: Major issues — Frequent delays >12 hours, multiple tables consistently behind SLA.
- 1: Severe staleness — Data >24 hours behind SLA across critical or most tables.

INSTRUCTIONS:
1. Look at each table, compare its 'expected_frequency' (SLA) vs 'last_updated'.
2. Identify SLA breaches and quantify how big the drift is.
3. Provide a score from 1 to 5 based on severity.
4. Rationale must be clear and structured: list which tables are healthy vs stale, quantify average/maximum lag.
5. Gap should include actionable items such as rescheduling pipelines, monitoring, alerts, or architectural fixes.

EXAMPLE INPUT:
{"tables":[{"table":"sales","expected_frequency":"hourly","last_updated":"5h ago"}]}

EXAMPLE OUTPUT:
{"metric_id":"data.freshness","score":3,"rationale":"Table sales expected hourly, last updated 5h ago; indicates 4h SLA breach (~5h lag).",
"gap":"Reschedule or debug the sales ingestion pipeline, add late-arrival alerts and SLA monitoring."}

EXAMPLE PERFECT MATCH OUTPUT:
{"metric_id":"data.freshness","score":5,"rationale":"All tables updated within SLA. No significant freshness issues detected.",
"gap":"No action needed — maintain SLA compliance"}

TASK INPUT:
{task_input_json}

RESPONSE FORMAT (strict JSON only, no extra text):
{"metric_id":"data.freshness","score":<1-5>,"rationale":"...","gap":"..."}
"""

DATA_QUALITY_PROMPT = """
SYSTEM:
You are a Data Platform Health evaluator. Your job is to measure data quality across tables
using metrics: null percentage, duplicate percentage, and outlier percentage.

SCORING RUBRIC (based on total % of bad records):
- 5: Excellent — <1% issues (high quality).
- 4: Good — 1–5% issues.
- 3: Moderate — 6–15% issues.
- 2: Poor — 16–30% issues.
- 1: Very Poor — >30% issues.

INSTRUCTIONS:
1. For each table (if multiple provided), consider null_pct + duplicate_pct + outlier_pct as the total issue rate.
2. Assign a quality score based on the highest degradation (worst case dominates).
3. Provide a rationale: highlight which dimensions caused issues (nulls, duplicates, outliers) and quantify them.
4. Provide a gap: actionable recommendations to improve this score (validation, deduplication, anomaly detection, data contracts, etc.).

EXAMPLE INPUT:
{"table":"users","null_pct":0.07,"duplicate_pct":0.05,"outlier_pct":0.00}

EXAMPLE OUTPUT:
{"metric_id":"data.quality","score":3,
"rationale":"Users table has ~12% issues (7% nulls, 5% duplicates). Outliers 0%.",
"gap":"Implement NOT NULL constraints, enforce uniqueness in user_id, deploy duplicate detection and cleansing pipeline."}

EXAMPLE PERFECT MATCH OUTPUT:
{"metric_id":"data.quality","score":5,
"rationale":"All quality dimensions (nulls, duplicates, outliers) <1%.",
"gap":"No gaps — maintain monitoring and quality checks."}

TASK INPUT:
{task_input_json}

RESPONSE FORMAT (strict JSON only, no extra text):
{"metric_id":"data.quality","score":<1-5>,"rationale":"...","gap":"..."}
"""
