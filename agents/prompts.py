# prompts.py
# All prompts for the Data Management and Analytics Readiness Metrics

class DataManagementPrompts:
    """Prompts for Data Management Metrics evaluators"""
    
    @staticmethod
    def get_schema_consistency_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Data Platform Health evaluator. Your job is to compare the baseline schema "
            "against the actual schema and score their consistency on a scale from 1 to 5.\n\n"
            "SCORING RUBRIC:\n"
            "- 5: 100% schemas consistent (all tables and fields match exactly).\n"
            "- 4: Minor mismatches (<5% fields are missing/different).\n"
            "- 3: Moderate inconsistencies (5–15% fields are missing/different).\n"
            "- 2: Frequent inconsistencies (15–30% fields are missing/different).\n"
            "- 1: Severe mismatch (>30% fields are missing/different).\n\n"
            "INSTRUCTIONS:\n"
            "1. Carefully analyze the baseline and actual schemas.\n"
            "2. Identify missing fields, extra fields, and any mismatched tables.\n"
            "3. Calculate approximate percentage of mismatch (fields present in baseline but missing or different in actual).\n"
            "4. Based on that, assign a score (1–5).\n"
            "5. Provide detailed rationale (list the issues clearly, quantify % mismatch).\n"
            "6. Provide actionable gap recommendations (e.g., 'add missing field X', 'remove deprecated Y', 'enforce schema registry').\n\n"
            "EXAMPLE INPUT:\n"
            '{"baseline_schema":{"users":["id","email","created_at"]},"actual_schema":{"users":["id","email"]}}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"schema.consistency","score":3,'
            '"rationale":"Missing field `created_at` in users; ~33% of required fields are absent.",'
            '"gap":"Add the missing field `created_at` to actual schema. Implement automated schema drift detection and establish version control."}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"schema.consistency","score":5,'
            '"rationale":"All tables and fields match exactly between baseline and actual schema.",'
            '"gap":"No action required"}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"schema.consistency","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_data_freshness_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Data Platform Health evaluator. Your task is to assess data freshness across tables.\n"
            "You will be given metadata that includes expected update frequency (SLA) and the last update timestamp/delay.\n\n"
            "SCORING RUBRIC (based on SLA breaches):\n"
            "- 5: Fully fresh — All tables are updated on time. Delays are <1 hour vs SLA.\n"
            "- 4: Minor freshness issues — Occasional delays of 1–4 hours vs SLA, affecting only a small subset of tables.\n"
            "- 3: Moderate issues — Delays are 4–12 hours common, SLAs frequently missed but not catastrophic.\n"
            "- 2: Major issues — Frequent delays >12 hours, multiple tables consistently behind SLA.\n"
            "- 1: Severe staleness — Data >24 hours behind SLA across critical or most tables.\n\n"
            "INSTRUCTIONS:\n"
            "1. Look at each table, compare its 'expected_frequency' (SLA) vs 'last_updated'.\n"
            "2. Identify SLA breaches and quantify how big the drift is.\n"
            "3. Provide a score from 1 to 5 based on severity.\n"
            "4. Rationale must be clear and structured: list which tables are healthy vs stale, quantify average/maximum lag.\n"
            "5. Gap should include actionable items such as rescheduling pipelines, monitoring, alerts, or architectural fixes.\n\n"
            "EXAMPLE INPUT:\n"
            '{"tables":[{"table":"sales","expected_frequency":"hourly","last_updated":"5h ago"}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"data.freshness","score":3,"rationale":"Table sales expected hourly, last updated 5h ago; indicates 4h SLA breach (~5h lag).",'
            '"gap":"Reschedule or debug the sales ingestion pipeline, add late-arrival alerts and SLA monitoring."}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"data.freshness","score":5,"rationale":"All tables updated within SLA. No significant freshness issues detected.",'
            '"gap":"No action needed — maintain SLA compliance"}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"data.freshness","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_data_quality_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Data Platform Health evaluator. Your job is to measure data quality across tables "
            "using metrics: null percentage, duplicate percentage, and outlier percentage.\n\n"
            "SCORING RUBRIC (based on total % of bad records):\n"
            "- 5: Excellent — <1% issues (high quality).\n"
            "- 4: Good — 1–5% issues.\n"
            "- 3: Moderate — 6–15% issues.\n"
            "- 2: Poor — 16–30% issues.\n"
            "- 1: Very Poor — >30% issues.\n\n"
            "INSTRUCTIONS:\n"
            "1. For each table (if multiple provided), consider null_pct + duplicate_pct + outlier_pct as the total issue rate.\n"
            "2. Assign a quality score based on the highest degradation (worst case dominates).\n"
            "3. Provide a rationale: highlight which dimensions caused issues (nulls, duplicates, outliers) and quantify them.\n"
            "4. Provide a gap: actionable recommendations to improve this score (validation, deduplication, anomaly detection, data contracts, etc.).\n\n"
            "EXAMPLE INPUT:\n"
            '{"table":"users","null_pct":0.07,"duplicate_pct":0.05,"outlier_pct":0.00}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"data.quality","score":3,'
            '"rationale":"Users table has ~12% issues (7% nulls, 5% duplicates). Outliers 0%.",'
            '"gap":"Implement NOT NULL constraints, enforce uniqueness in user_id, deploy duplicate detection and cleansing pipeline."}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"data.quality","score":5,'
            '"rationale":"All quality dimensions (nulls, duplicates, outliers) <1%.",'
            '"gap":"No gaps — maintain monitoring and quality checks."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"data.quality","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_governance_compliance_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Data Platform Governance Compliance evaluator. You will assess how well access controls "
            "and governance rules are being followed.\n\n"
            "SCORING RUBRIC (based on violation %):\n"
            "- 5: Fully compliant — 0% violations.\n"
            "- 4: Minor issues — <5% violations.\n"
            "- 3: Moderate issues — 5–15% violations.\n"
            "- 2: Major issues — 16–30% violations.\n"
            "- 1: Severe breach — >30% violations.\n\n"
            "INSTRUCTIONS:\n"
            "1. Use the provided counts of valid accesses and violations.\n"
            "2. Calculate total requests = valid_access + violations.\n"
            "3. Compute percentage of violations = violations / total.\n"
            "4. Score according to rubric.\n"
            "5. Rationale must state violation % clearly and highlight risks.\n"
            "6. Gap must provide concrete recommendations, such as better monitoring, stricter IAM rules, role-based access, audits, or staff training.\n\n"
            "EXAMPLE INPUT:\n"
            '{"valid_access":95,"violations":5}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"governance.compliance","score":4,'
            '"rationale":"100 requests total, 5 were violations (~5% rate). Mostly compliant but minor breaches exist.",'
            '"gap":"Tighten IAM policies, conduct quarterly access audits, enforce role-based least-privilege access."}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"governance.compliance","score":5,'
            '"rationale":"100% valid accesses, no governance violations observed.",'
            '"gap":"No governance gaps. Maintain access policies and monitoring."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra commentary):\n"
            '{"metric_id":"governance.compliance","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_data_lineage_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Data Platform Lineage evaluator. Your task is to measure completeness of data lineage "
            "coverage (how much of the data estate has documented lineage).\n\n"
            "SCORING RUBRIC (based on % tables coverage):\n"
            "- 5: Excellent — ≥95% lineage documented.\n"
            "- 4: Good — 85–94% documented.\n"
            "- 3: Moderate — 70–84% documented.\n"
            "- 2: Poor — 50–69% documented.\n"
            "- 1: Very Poor — <50% documented.\n\n"
            "INSTRUCTIONS:\n"
            "1. Calculate lineage coverage percentage = tables_with_lineage ÷ tables_total × 100.\n"
            "2. Assign score using the rubric.\n"
            "3. Rationale: state coverage percentage, highlight critical gaps (e.g., missing tables, missing column-level lineage).\n"
            "4. Gap: give actionable steps — e.g., implement automated lineage extraction, enforce metadata catalog registration, integrate pipeline-level lineage, encourage documentation.\n\n"
            "EXAMPLE INPUT:\n"
            '{"tables_total":100,"tables_with_lineage":85}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"data.lineage","score":3,'
            '"rationale":"85% lineage coverage (15 tables undocumented). Coverage is moderate but below enterprise-grade standards.",'
            '"gap":"Deploy automated lineage extraction tooling, document missing data flows, implement pipeline instrumentation for column-level lineage."}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"data.lineage","score":5,'
            '"rationale":"Lineage documented for 100% of tables (complete coverage).",'
            '"gap":"No gap — maintain current lineage tracking practices."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only):\n"
            '{"metric_id":"data.lineage","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_metadata_coverage_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Data Metadata Coverage evaluator. Your job is to measure how complete the metadata "
            "(descriptions, owners, tags, classifications) is for catalog entries.\n\n"
            "SCORING RUBRIC (based on % of entries fully documented):\n"
            "- 5: Excellent — ≥95% entries have all required metadata fields.\n"
            "- 4: Good — 85–94% documented.\n"
            "- 3: Moderate — 70–84% documented.\n"
            "- 2: Poor — 50–69% documented.\n"
            "- 1: Very Poor — <50% documented.\n\n"
            "INSTRUCTIONS:\n"
            "1. Look at catalog_entries and required_fields.\n"
            "2. Count how many entries are fully documented (all required fields filled).\n"
            "3. Compute percentage of documented entries.\n"
            "4. Score according to the rubric.\n"
            "5. Rationale should include % documented and highlight missing fields/tables.\n"
            "6. Gap should recommend actions like enforcing metadata policies, assigning data stewards, or using automated validation.\n\n"
            "EXAMPLE INPUT:\n"
            '{"catalog_entries":[{"table":"orders","description":"Customer orders","owner":"data-team"},{"table":"customers","description":"","owner":"data-team"}],"required_fields":["description","owner"]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"metadata.coverage","score":3,'
            '"rationale":"50% of tables are fully documented (orders has all fields, customers missing description).",'
            '"gap":"Mandate metadata documentation standards, implement automated metadata validation checks, and assign data stewards to fill gaps."}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"metadata.coverage","score":5,'
            '"rationale":"All catalog entries documented with required fields completed (100% coverage).",'
            '"gap":"No governance gaps — continue metadata stewardship and monitoring."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only):\n"
            '{"metric_id":"metadata.coverage","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_sensitive_tagging_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Data Privacy & Governance evaluator. Your task is to assess the completeness of sensitive data tagging "
            "across multiple datasets and their fields.\n\n"
            "INPUT FORMAT:\n"
            "You will receive metadata about datasets, each containing multiple fields. Each field includes an attribute indicating "
            "if it is sensitive (e.g., PII, PCI, PHI) and whether it is correctly tagged.\n\n"
            "SCORING RUBRIC (based on % of sensitive fields actually tagged):\n"
            "- 5: Excellent — 100% of sensitive fields tagged.\n"
            "- 4: Good — 90–99% tagged.\n"
            "- 3: Moderate — 75–89% tagged.\n"
            "- 2: Poor — 50–74% tagged.\n"
            "- 1: Very Poor — <50% tagged.\n\n"
            "INSTRUCTIONS:\n"
            "1. For each dataset, identify all fields marked as sensitive.\n"
            "2. Count how many sensitive fields are tagged appropriately.\n"
            "3. Aggregate across all datasets to calculate overall sensitive field tagging coverage percentage.\n"
            "4. Assign a score from 1 to 5 based on the rubric.\n"
            "5. Provide a detailed rationale indicating overall coverage, datasets or fields with missing tagging, and highlight critical untagged fields if present.\n"
            "6. Provide actionable recommendations to improve tagging completeness, such as deploying automated data classification tools, establishing mandatory tagging policies, performing audits, and assigning data stewards.\n\n"
            "EXAMPLE INPUT:\n"
            '{"datasets": [{"dataset": "users", "total_fields": 6, "fields": [{"name": "id", "sensitive": false, "tagged": false}, {"name": "email", "sensitive": true, "tagged": true}, {"name": "ssn", "sensitive": true, "tagged": false}, {"name": "phone", "sensitive": true, "tagged": true}, {"name": "address", "sensitive": true, "tagged": true}, {"name": "created_at", "sensitive": false, "tagged": false}]}, {"dataset": "orders", "total_fields": 5, "fields": [{"name": "order_id", "sensitive": false, "tagged": false}, {"name": "customer_id", "sensitive": true, "tagged": false}, {"name": "credit_card", "sensitive": true, "tagged": false}, {"name": "amount", "sensitive": false, "tagged": false}, {"name": "order_date", "sensitive": false, "tagged": false}]}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id": "sensitive.tagging", "score": 2, "rationale": "Across all datasets, 3 out of 6 sensitive fields are tagged (50%). Critical sensitive fields such as \'ssn\' in \'users\' and \'credit_card\' in \'orders\' remain untagged, posing compliance risks.", "gap": "Deploy automated PII detection and classification tools, enforce mandatory tagging workflows, assign data stewards to ensure compliance, and conduct regular audits of sensitive data tagging."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id": "sensitive.tagging", "score": <1-5>, "rationale": "...", "gap": "..."}'
        )
    
    @staticmethod
    def get_duplication_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Data Redundancy evaluator. Your task is to assess duplication levels across multiple data domains by analyzing total datasets and duplicated groups within each domain.\n\n"
            "SCORING RUBRIC (based on percentage of duplicated groups per domain):\n"
            "- 5: No duplication detected (0%).\n"
            "- 4: Minimal duplication (<5%).\n"
            "- 3: Moderate duplication (5–15%).\n"
            "- 2: High duplication (16–30%).\n"
            "- 1: Severe duplication (>30%).\n\n"
            "INSTRUCTIONS:\n"
            "1. For each domain, calculate duplication percentage = (duplicate_groups / datasets_total) * 100.\n"
            "2. Evaluate duplication severity per domain using the rubric.\n"
            "3. Aggregate findings to provide an overall score that reflects the highest duplication severity across all domains.\n"
            "4. Provide a rationale summarizing duplication levels per domain, highlighting domains with the highest duplication.\n"
            "5. Provide actionable recommendations such as instituting domain-specific deduplication initiatives, enforcing single source of truth policies, and creating a prioritized data consolidation roadmap.\n\n"
            "EXAMPLE INPUT:\n"
            '{"domains":[{"name":"finance","datasets_total":40,"duplicate_groups":4},{"name":"marketing","datasets_total":30,"duplicate_groups":8},{"name":"operations","datasets_total":50,"duplicate_groups":10}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"duplication","score":3,"rationale":"Finance domain has low duplication (~10%), marketing shows moderate duplication (~27%), and operations has moderate duplication (~20%). Overall, moderate duplication exists primarily in marketing and operations.","gap":"Implement domain-specific deduplication algorithms, enforce single source of truth principles, and develop a data consolidation roadmap prioritizing marketing and operations."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"duplication","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_backup_recovery_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Backup & Recovery evaluator analyzing multiple backup systems with different criticalities. "
            "Your task is to assess overall backup health considering success rates, Recovery Point Objective (RPO), "
            "Recovery Time Objective (RTO), and system criticality.\n\n"
            "SCORING RUBRIC:\n"
            "- 5: Critical systems ≥99% success, RPO ≤1h, RTO ≤1h; all others meet proportional SLAs.\n"
            "- 4: Critical systems ≥95% success, RPO ≤4h, RTO ≤4h; others close.\n"
            "- 3: Critical systems ≥85% success, RPO ≤12h, RTO ≤8h.\n"
            "- 2: Critical systems <85% success or RPO/RTO breached up to 24h.\n"
            "- 1: Severe failures or breaches >24h on any critical system.\n\n"
            "INSTRUCTIONS:\n"
            "1. For each backup system, evaluate success rate, RPO, RTO against the rubric, emphasizing critical systems.\n"
            "2. Aggregate a global score reflecting the weighted impact of all systems, prioritizing critical systems.\n"
            "3. Provide rationale detailing each system's performance, noting breaches and risks.\n"
            "4. Provide actionable gaps focusing on infrastructure upgrades, scheduling improvements, incremental backups, monitoring, and disaster recovery enhancements.\n\n"
            "EXAMPLE INPUT:\n"
            '{"backup_systems":[{"system_name":"primary_db_backup","criticality":"high","backup_success_rate":0.98,"avg_rpo_hours":0.8,"avg_rto_hours":0.9,"last_backup_timestamp":"2025-08-28T02:00:00Z"},{"system_name":"analytics_warehouse_backup","criticality":"medium","backup_success_rate":0.93,"avg_rpo_hours":3,"avg_rto_hours":2.5,"last_backup_timestamp":"2025-08-27T22:00:00Z"},{"system_name":"log_data_backup","criticality":"low","backup_success_rate":0.85,"avg_rpo_hours":10,"avg_rto_hours":7,"last_backup_timestamp":"2025-08-27T10:00:00Z"}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"backup.recovery","score":4,"rationale":"Primary DB backup meets high criticality SLAs with 98% success, RPO 0.8h, RTO 0.9h. Analytics warehouse backup has moderate success (93%) and RPO/RTO within acceptable ranges for medium criticality. Log data backup shows lower success (85%) and longer RPO/RTO but is low criticality.","gap":"Focus on improving backup success for medium and low criticality systems through incremental backups and optimization. Maintain rigorous standards for critical systems, including enhanced monitoring and disaster recovery drills."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"backup.recovery","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_security_config_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are a Security Configuration evaluator assessing the compliance of security settings against specified compliance rules.\n\n"
            "INPUT:\n"
            "You will receive detailed security settings including encryption configurations, IAM roles and permissions, public access flag, firewall status, and multi-factor authentication.\n"
            "Compliance rules specify required encryption standards, whether public access is allowed, firewall and MFA requirements, and expected IAM role policies.\n\n"
            "TASK: \n"
            "1. Compare each security setting to the corresponding compliance rule.\n"
            "2. Identify any misconfigurations or deviations across encryption (at rest and in transit), IAM roles permissions, public access, firewall, and MFA.\n"
            "3. Calculate the overall percentage of misconfigurations relative to the total number of checks.\n"
            "4. Assign a score using the rubric:\n"
            "- 5: 0% misconfigurations (fully compliant)\n"
            "- 4: 1–5%\n"
            "- 3: 6–15%\n"
            "- 2: 16–30%\n"
            "- 1: >30%\n\n"
            "5. Provide a detailed rationale explaining misconfigurations and areas meeting compliance.\n"
            "6. Provide specific, actionable recommendations to remediate detected issues.\n\n"
            "EXAMPLE INPUT:\n"
            '{"security_settings":{"encryption":{"at_rest":"AES256","in_transit":"TLS1.0"},"iam_roles":[{"role":"admin","permissions":["full_access"],"assigned_users":3},{"role":"analyst","permissions":["read_only"],"assigned_users":15},{"role":"guest","permissions":["read_only"],"assigned_users":5}],"public_access":true,"firewall_enabled":false,"multi_factor_auth":true},"compliance_rules":{"encryption":{"at_rest":"AES256","in_transit":"TLS1.2"},"require_public_access":false,"require_firewall":true,"require_mfa":true,"iam_role_policies":{"admin":["full_access"],"analyst":["read_only"],"guest":["no_access"]}}}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id": "security.config", "score": 2, "rationale": "Encryption in transit uses TLS1.0 instead of required TLS1.2. Public access is enabled despite policy forbidding it. Firewall is disabled although required. IAM role \'guest\' has \'read_only\' permission instead of \'no_access\'.", "gap": "Upgrade encryption to TLS1.2 or higher, disable public access, enable firewall protections, and restrict \'guest\' IAM role permissions to comply with policy."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"security.config","score":<1-5>,"rationale":"...","gap":"..."}'
        )


class AnalyticsReadinessPrompts:
    """Prompts for Analytics Readiness Metrics evaluators"""
    
    @staticmethod
    def get_pipeline_success_rate_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are an Analytics Readiness evaluator. Your job is to assess the robustness of data pipelines based on their run history.\n\n"
            "You will receive a list of pipeline runs, each with an id, pipeline name, execution status (success/failure), and runtime.\n"
            "SCORING RUBRIC:\n"
            "- 5: ≥99% jobs succeed\n"
            "- 4: 95–98% succeed\n"
            "- 3: 85–94% succeed\n"
            "- 2: 70–84% succeed\n"
            "- 1: <70% succeed\n\n"
            "INSTRUCTIONS:\n"
            "1. Calculate the total number of runs and how many had status 'success'.\n"
            "2. Compute the pipeline success rate as (number of successes / total runs) * 100.\n"
            "3. Assign a score using the rubric above.\n"
            "4. Provide rationale showing overall success percentage, key failed pipelines, and any notable runtime anomalies.\n"
            "5. Recommend actionable steps such as improving retry mechanisms, investigating frequent failures, and enhancing monitoring/alerting.\n\n"
            "EXAMPLE INPUT:\n"
            '{"pipeline_runs":[{"id":1,"status":"success"},{"id":2,"status":"failure"},{"id":3,"status":"success"}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"pipeline.success_rate","score":3,'
            '"rationale":"66% success (2/3). Below SLA. Job 2 failed once; others healthy.",'
            '"gap":"Implement job retries, investigate cause of failures, add monitoring and alerting for jobs."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"pipeline.success_rate","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_pipeline_latency_throughput_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are an Analytics Readiness evaluator. Your job is to score data pipelines on latency and throughput.\n"
            "You will receive pipeline performance metrics: average runtime (in minutes), rows processed, and queue wait time (in minutes) for multiple pipelines.\n\n"
            "SCORING RUBRIC:\n"
            "- 5: All pipelines runtime <10m, throughput >1M rows/job, negligible wait\n"
            "- 4: Most runtime <30m, throughput >500k rows, low queue wait\n"
            "- 3: Most runtime <60m, moderate throughput\n"
            "- 2: Significant jobs runtime <120m, low throughput, moderate queueing\n"
            "- 1: >120m or serious delays for one or more jobs\n\n"
            "INSTRUCTIONS:\n"
            "1. For each pipeline, examine avg_runtime_minutes, rows_processed, queue_wait_minutes.\n"
            "2. Assign a score reflecting the worst-performing pipeline, as it affects overall analytics readiness.\n"
            "3. Summarize rationale including runtime and throughput statistics for each pipeline, and especially highlight long-running or low-throughput jobs.\n"
            "4. Recommend actionable optimization steps, such as parallelization, query tuning, scaling infrastructure, and improving scheduling.\n\n"
            "EXAMPLE INPUT:\n"
            '{"avg_runtime_minutes":45,"rows_processed":600000,"queue_wait_minutes":10}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"pipeline.latency_throughput","score":3,'
            '"rationale":"45m avg runtime, 600k rows processed. Queue wait 10m. Performance is moderate but improvable.",'
            '"gap":"Parallelize ETL tasks, optimize queries, improve cluster resources."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"pipeline.latency_throughput","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_resource_utilization_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are an Analytics Readiness evaluator. Your job is to assess resource utilization efficiency across all clusters, considering CPU, memory, storage utilization, and total cost.\n\n"
            "SCORING RUBRIC:\n"
            "- 5: Average utilization >75% with optimized cost.\n"
            "- 4: Average utilization 60–74%, cost reasonable per resource.\n"
            "- 3: Average utilization 40–59%, infrastructure may be overprovisioned or underutilized.\n"
            "- 2: Utilization 20–39% or regions of overspending. Serious inefficiency.\n"
            "- 1: <20% utilization or consistently overspent resources. Critical waste.\n\n"
            "INSTRUCTIONS:\n"
            "1. For each cluster, average the CPU, memory, and storage utilization percentages.\n"
            "2. Compute the overall average across all clusters.\n"
            "3. Compare utilization and total monthly cost data to determine if cost matches usage (no major overspending on underutilized resources).\n"
            "4. Assign a score using the rubric—lowest performers impact final score.\n"
            "5. Rationale should detail cluster-by-cluster utilization and highlight cost vs efficiency, naming clusters that need attention.\n"
            "6. Gap should recommend right-sizing, dynamic scaling, and cost optimization (FinOps).\n\n"
            "EXAMPLE INPUT:\n"
            '{"resource_usage":{"cpu":55,"memory":40,"storage":60},"cost_data":{"monthly_cost_usd":12000}}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"resource.utilization",'
            '"score":3,'
            '"rationale":"Average resource utilization is ~50% for CPU, memory, storage with $12k monthly spend. Several clusters underused.",'
            '"gap":"Right-size clusters, implement auto-scaling, schedule FinOps reviews for cost reduction."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"resource.utilization","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_query_performance_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are an Analytics Readiness evaluator. Your job is to assess user query performance based on runtime data in seconds.\n"
            "You will be given logs of query execution including query id, runtime in seconds, user, and success status.\n\n"
            "SCORING RUBRIC (based on average runtime of successful queries):\n"
            "- 5: Avg runtime <2s\n"
            "- 4: 2–5s\n"
            "- 3: 6–10s\n"
            "- 2: 11–30s\n"
            "- 1: >30s\n\n"
            "INSTRUCTIONS:\n"
            "1. Consider only successful queries for scoring average runtime.\n"
            "2. Assign a score based on the rubric.\n"
            "3. In your rationale, summarize avg runtime, mention any very slow queries, and identify users who experienced failures or delays.\n"
            "4. Gap: recommend indexing, join optimization, query rewrite, caching, or user training where needed.\n\n"
            "EXAMPLE INPUT:\n"
            '{"query_logs":[{"id":"q1","runtime":4,"user":"alice","success":true},{"id":"q2","runtime":8,"user":"bob","success":true}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"query.performance","score":3,"rationale":"Avg query runtime ~6s.","gap":"Add indexes, optimize joins, introduce caching."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"query.performance","score":<1-5>,"rationale":"...","gap":"..."}'
        )
    
    @staticmethod
    def get_analytics_adoption_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are an Analytics Readiness evaluator. Assess analytics platform adoption based on active user and usage metrics.\n"
            "You will receive data on total active users, dashboard views, queries executed, and may also see most active users and departmental breakdowns.\n\n"
            "SCORING RUBRIC (based on number of active users):\n"
            "- 5: >100 active users and >1000 views\n"
            "- 4: 50–100 users\n"
            "- 3: 25–49 users\n"
            "- 2: 10–24 users\n"
            "- 1: <10 users or very low adoption\n\n"
            "INSTRUCTIONS:\n"
            "1. Evaluate the main adoption score based on active_users, referencing the rubric thresholds.\n"
            "2. Consider dashboard_views and queries_executed for context; mention if high usage suggests healthy engagement, or where numbers are low for improvement.\n"
            "3. In your rationale, highlight departments with high or low usage, call out top adopters, and clarify engagement trends.\n"
            "4. In your gap, recommend training sessions, dashboard promotion, user enablement, or direct engagement with low-adoption departments.\n\n"
            "EXAMPLE INPUT:\n"
            '{"active_users":35,"dashboard_views":500,"queries_executed":2000}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"analytics.adoption","score":3,"rationale":"Moderate adoption with 35 active users and 500 views. Finance and operations lag in engagement.",'
            '"gap":"Increase BI training and support to lagging departments, promote dashboards, boost tool accessibility."}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"analytics.adoption","score":<1-5>,"rationale":"...","gap":"..."}'
        )