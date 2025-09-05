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
            "6. Provide actionable and great detail gap recommendations as a list of points (e.g., ['Add the missing field `created_at` of type `DATETIME` with a non-null constraint to the `users` table.', 'Implement automated schema drift detection to alert data engineers about schema changes as they occur, preventing future inconsistencies.', 'Establish a version control system for your schemas (e.g., using Git) to track changes and roll back to previous versions if needed.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"baseline_schema":{"users":["id","email","created_at"]},"actual_schema":{"users":["id","email"]}}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"schema.consistency","score":3,'
            '"rationale":"Missing field `created_at` in users; ~33% of required fields are absent.",'
            '"gap":["Add the missing field `created_at` of type `DATETIME` with a non-null constraint to the `users` table.", "Implement automated schema drift detection to alert data engineers about schema changes as they occur, preventing future inconsistencies.", "Establish a version control system for your schemas (e.g., using Git) to track changes and roll back to previous versions if needed."]}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"schema.consistency","score":5,'
            '"rationale":"All tables and fields match exactly between baseline and actual schema.",'
            '"gap":["No action required. The data platform is in a healthy and consistent state regarding its schema."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"schema.consistency","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "5. Gap should include actionable, highly specific, and detailed items as a list (e.g., ['Reschedule the `sales` ingestion pipeline to a new time slot to prevent overlap.', 'Investigate and debug the cause of late data arrivals, focusing on upstream API call failures or resource contention.', 'Implement an automated monitoring and alerting system for SLA breaches that notifies the data team via Slack or email when a table is more than 30 minutes past its expected update time.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"tables":[{"table":"sales","expected_frequency":"hourly","last_updated":"5h ago"}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"data.freshness","score":3,"rationale":"Table `sales` expected hourly, last updated 5h ago; indicates 4h SLA breach (~5h lag).",'
            '"gap":["Reschedule the `sales` ingestion pipeline to a new time slot to prevent overlap with other critical jobs.", "Debug the source of late arrivals by checking the upstream data source and pipeline logs for errors.", "Add an automated alert for the `sales` table that triggers when its `last_updated` timestamp is more than 60 minutes behind the current time."]}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"data.freshness","score":5,"rationale":"All tables updated within SLA. No significant freshness issues detected.",'
            '"gap":["No action needed. Continue to maintain a robust data pipeline and monitoring system to ensure consistent SLA compliance."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"data.freshness","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "4. Provide a gap: actionable, highly specific, and detailed recommendations as a list (e.g., ['Implement NOT NULL constraints on critical columns like `user_id` to ensure data completeness.', 'Enforce uniqueness on the `email` column by adding a unique key constraint to prevent duplicate user records.', 'Deploy a duplicate detection and cleansing pipeline that runs daily to identify and merge or remove duplicate records.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"table":"users","null_pct":0.07,"duplicate_pct":0.05,"outlier_pct":0.00}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"data.quality","score":3,'
            '"rationale":"Users table has ~12% issues (7% nulls, 5% duplicates). Outliers 0%.",'
            '"gap":["Implement NOT NULL constraints on critical columns such as `email` and `created_at` to improve data completeness.", "Enforce uniqueness on the `user_id` and `email` columns by adding unique key constraints.", "Deploy a scheduled data cleansing job to identify and handle duplicate records, possibly by merging them or removing older entries."]}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"data.quality","score":5,'
            '"rationale":"All quality dimensions (nulls, duplicates, outliers) <1%.",'
            '"gap":["No gaps. Continue to maintain automated data quality checks and monitoring to ensure sustained high data quality."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"data.quality","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "6. Gap must provide concrete, highly specific, and detailed recommendations as a list (e.g., ['Tighten IAM policies by implementing a strict principle of least privilege, restricting user access to only the data they absolutely need for their job function.', 'Conduct quarterly access audits to review and revoke unnecessary permissions, ensuring that former employees or users with changed roles no longer have access.', 'Enforce role-based access control (RBAC) across all data systems to standardize permissions and prevent ad-hoc access grants.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"valid_access":95,"violations":5}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"governance.compliance","score":4,'
            '"rationale":"Of 100 total requests, 5 were violations, representing a 5% rate. The platform is mostly compliant, but these minor breaches present a risk.",'
            '"gap":["Tighten IAM policies by implementing a strict principle of least privilege and regularly auditing user permissions.", "Conduct quarterly access audits to identify and remove stale or unnecessary access grants.", "Implement automated monitoring for failed access attempts and security events, with alerts sent to the security team."]}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"governance.compliance","score":5,'
            '"rationale":"100% of accesses were valid, with no governance violations observed.",'
            '"gap":["No governance gaps. Continue to maintain current access policies and automated monitoring to ensure ongoing compliance."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra commentary):\n"
            '{"metric_id":"governance.compliance","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "4. Gap: give actionable, highly specific, and detailed steps as a list (e.g., ['Implement automated lineage extraction tooling like OpenLineage or a commercial solution to automatically capture and map data flows from ingestion to consumption.', 'Enforce metadata catalog registration by integrating the data catalog into the CI/CD pipeline, making it mandatory for new data assets to have documented lineage before deployment.', 'Document missing data flows for the 15 tables that lack lineage, prioritizing critical business intelligence tables and high-impact dashboards.', 'Implement pipeline instrumentation and parsing for column-level lineage to provide a more granular view of data transformations.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"tables_total":100,"tables_with_lineage":85}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"data.lineage","score":3,'
            '"rationale":"85% lineage coverage (15 tables undocumented). Coverage is moderate but below enterprise-grade standards and hinders impact analysis.",'
            '"gap":["Deploy an automated lineage extraction tool to automatically map data flows across ETL/ELT pipelines.", "Document the data lineage for the 15 tables currently lacking coverage, prioritizing those used in critical business reports.", "Implement a policy to enforce column-level lineage tracking for new and updated data assets to provide a granular view of data transformations."]}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"data.lineage","score":5,'
            '"rationale":"Lineage documented for 100% of tables (complete coverage).",'
            '"gap":["No gaps. Maintain current automated lineage tracking and metadata management practices to ensure ongoing completeness and accuracy."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only):\n"
            '{"metric_id":"data.lineage","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "5. Rationale should be detailed: include the overall % documented, list which specific tables are missing metadata, and which fields are absent.\n"
            "6. Gap should recommend actionable, highly specific, and detailed actions as a list (e.g., ['Enforce metadata documentation standards for all new data assets, making it a mandatory step in the deployment process.', 'Assign specific data stewards responsible for filling in missing metadata for critical tables and data assets.', 'Implement an automated metadata validation check within the data catalog that flags entries with incomplete fields and sends notifications to the data owner.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"catalog_entries":[{"table":"orders","description":"Customer orders","owner":"data-team"},{"table":"customers","description":"","owner":"data-team"}],"required_fields":["description","owner"]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"metadata.coverage","score":3,'
            '"rationale":"50% of tables are fully documented. The `orders` table is complete, but the `customers` table is missing a required `description` field.",'
            '"gap":["Mandate metadata documentation standards for all new data assets and pipelines.", "Implement automated metadata validation checks that trigger alerts when a required field is left blank.", "Assign a dedicated data steward to each business domain to be responsible for filling in and maintaining metadata for their tables."]}\n\n'
            "EXAMPLE PERFECT MATCH OUTPUT:\n"
            '{"metric_id":"metadata.coverage","score":5,'
            '"rationale":"All catalog entries are fully documented with all required metadata fields completed, resulting in 100% coverage.",'
            '"gap":["No gaps. Continue to enforce current metadata stewardship and validation processes to ensure ongoing completeness and accuracy."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only):\n"
            '{"metric_id":"metadata.coverage","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "5. Provide a detailed rationale: indicate the overall tagging coverage percentage, list specific datasets and fields with missing tags, and highlight any critical untagged fields that pose a significant compliance risk (e.g., SSN, credit card numbers).\n"
            "6. Provide actionable, highly specific, and detailed recommendations as a list to improve tagging completeness (e.g., ['Deploy a machine-learning-based data classification tool to automatically scan and tag sensitive data at scale.', 'Enforce mandatory tagging policies by integrating them into the CI/CD pipeline, blocking deployments of new data assets that lack required tags.', 'Conduct regular, automated audits of the data catalog to identify and remediate untagged sensitive fields.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"datasets": [{"dataset": "users", "total_fields": 6, "fields": [{"name": "id", "sensitive": false, "tagged": false}, {"name": "email", "sensitive": true, "tagged": true}, {"name": "ssn", "sensitive": true, "tagged": false}, {"name": "phone", "sensitive": true, "tagged": true}, {"name": "address", "sensitive": true, "tagged": true}, {"name": "created_at", "sensitive": false, "tagged": false}]}, {"dataset": "orders", "total_fields": 5, "fields": [{"name": "order_id", "sensitive": false, "tagged": false}, {"name": "customer_id", "sensitive": true, "tagged": false}, {"name": "credit_card", "sensitive": true, "tagged": false}, {"name": "amount", "sensitive": false, "tagged": false}, {"name": "order_date", "sensitive": false, "tagged": false}]}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id": "sensitive.tagging", "score": 2, "rationale": "Across all datasets, 3 out of 6 sensitive fields are tagged, resulting in a 50% coverage rate. The `users` dataset is missing a tag for `ssn`, and the `orders` dataset is missing tags for `customer_id` and `credit_card`. The untagged `ssn` and `credit_card` fields represent a significant privacy and compliance risk.", "gap": ["Deploy an automated data classification tool to scan for and tag sensitive data types like PII and PCI across all tables.", "Implement a mandatory data governance policy that requires all new tables containing sensitive data to be tagged before they are put into production.", "Conduct a full manual audit of existing data sources to identify and tag all previously missed sensitive fields."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id": "sensitive.tagging", "score": <1-5>, "rationale": "...", "gap": ["...","..."]}'
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
            "4. Provide a detailed rationale: summarize the duplication levels for each domain, list the calculated percentages, and specifically highlight the domains with the most significant duplication issues.\n"
            "5. Provide actionable, highly specific, and detailed recommendations as a list (e.g., ['Implement domain-specific deduplication algorithms, such as fuzzy matching for customer records in the marketing domain.', 'Enforce a single source of truth for key business entities (e.g., customer, product) and deprecate redundant datasets.', 'Develop a data consolidation roadmap to systematically migrate duplicate data to a centralized, governed repository, prioritizing domains with the highest duplication rate.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"domains":[{"name":"finance","datasets_total":40,"duplicate_groups":4},{"name":"marketing","datasets_total":30,"duplicate_groups":8},{"name":"operations","datasets_total":50,"duplicate_groups":10}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"duplication","score":2,"rationale":"Finance has a moderate duplication rate of 10% (4/40). Marketing has a high duplication rate of 26.7% (8/30), which is the highest. Operations has a high duplication rate of 20% (10/50). The overall score is driven by the severe duplication in the marketing and operations domains.", "gap":["Implement a data deduplication process focusing on the marketing domain, starting with customer data.","Enforce a single source of truth for core datasets and deprecate redundant copies.","Develop a data consolidation roadmap for the operations domain to reduce its 20% duplication rate over the next two quarters."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"duplication","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "3. Provide a detailed rationale: describe each system's performance, explicitly stating its success rate, RPO, and RTO, and note any SLA breaches or risks. Start with critical systems first.\n"
            "4. Provide actionable, highly specific, and detailed gaps as a list, focusing on infrastructure upgrades, scheduling improvements, incremental backups, monitoring, and disaster recovery enhancements.\n\n"
            "EXAMPLE INPUT:\n"
            '{"backup_systems":[{"system_name":"primary_db_backup","criticality":"high","backup_success_rate":0.98,"avg_rpo_hours":0.8,"avg_rto_hours":0.9,"last_backup_timestamp":"2025-08-28T02:00:00Z"},{"system_name":"analytics_warehouse_backup","criticality":"medium","backup_success_rate":0.93,"avg_rpo_hours":3,"avg_rto_hours":2.5,"last_backup_timestamp":"2025-08-27T22:00:00Z"},{"system_name":"log_data_backup","criticality":"low","backup_success_rate":0.85,"avg_rpo_hours":10,"avg_rto_hours":7,"last_backup_timestamp":"2025-08-27T10:00:00Z"}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"backup.recovery","score":4,"rationale":"The `primary_db_backup` (critical) meets its SLAs with a 98% success rate, RPO of 0.8h, and RTO of 0.9h. The `analytics_warehouse_backup` (medium criticality) has a 93% success rate, an RPO of 3h, and an RTO of 2.5h. The `log_data_backup` (low criticality) has a success rate of 85%, an RPO of 10h, and an RTO of 7h, which are within acceptable bounds for its criticality. The overall score is driven by the strong performance of the critical system.","gap":["Improve backup success rates for the `log_data_backup` system by optimizing its storage target and implementing a more resilient scheduling mechanism.", "Introduce incremental backups for the `analytics_warehouse_backup` to reduce backup window size and minimize RPO/RTO values.", "Conduct quarterly disaster recovery drills to test the RTO and validate the recovery procedures for all critical and medium-critical systems."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"backup.recovery","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "5. Provide a detailed rationale: list each specific misconfiguration, noting the non-compliant setting and its corresponding rule, and mention which settings are in compliance to show a complete picture.\n"
            "6. Provide specific, actionable recommendations as a list to remediate detected issues. For each issue, propose a concrete step to fix it.\n\n"
            "EXAMPLE INPUT:\n"
            '{"security_settings":{"encryption":{"at_rest":"AES256","in_transit":"TLS1.0"},"iam_roles":[{"role":"admin","permissions":["full_access"],"assigned_users":3},{"role":"analyst","permissions":["read_only"],"assigned_users":15},{"role":"guest","permissions":["read_only"],"assigned_users":5}],"public_access":true,"firewall_enabled":false,"multi_factor_auth":true},"compliance_rules":{"encryption":{"at_rest":"AES256","in_transit":"TLS1.2"},"require_public_access":false,"require_firewall":true,"require_mfa":true,"iam_role_policies":{"admin":["full_access"],"analyst":["read_only"],"guest":["no_access"]}}}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id": "security.config", "score": 2, "rationale": "There are four misconfigurations out of six total checks. The system is non-compliant on: 1) Encryption in transit, using TLS1.0 instead of the required TLS1.2. 2) Public access, which is enabled when the rule specifies it should be false. 3) Firewall is disabled, but the policy requires it to be enabled. 4) The `guest` IAM role has `read_only` permissions, violating the `no_access` policy. At rest encryption and multi-factor authentication are compliant.", "gap": ["Upgrade the encryption protocol for data in transit to TLS1.2 or a higher version.", "Immediately disable public access to the data platform to comply with security policy.", "Enable and configure a firewall to restrict unauthorized network traffic.", "Revise the permissions for the `guest` IAM role to explicitly deny all access, aligning with the `no_access` policy."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"security.config","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "4. Provide a detailed rationale: show the overall success percentage, list specific failed pipelines by name, and highlight any notable runtime anomalies (e.g., jobs that run much longer than average).\n"
            "5. Recommend actionable and highly specific steps as a list (e.g., ['Implement robust retry mechanisms with exponential backoff for transient failures.', 'Investigate the root cause of failures for specific jobs by analyzing their logs.', 'Enhance monitoring and alerting to proactively notify the data engineering team of job failures or performance degradations.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"pipeline_runs":[{"id":1,"status":"success", "pipeline_name": "etl_orders"}, {"id":2,"status":"failure", "pipeline_name": "etl_sales"}, {"id":3,"status":"success", "pipeline_name": "etl_orders"}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"pipeline.success_rate","score":3,'
            '"rationale":"The overall success rate is 66.7% (2 out of 3 runs). The `etl_sales` pipeline failed, which is the primary cause for the low score.",'
            '"gap":["Implement robust retry mechanisms with exponential backoff for the `etl_sales` pipeline to handle transient failures.","Investigate the root cause of the `etl_sales` failure by reviewing its logs and dependency status.","Enhance monitoring and alerting to proactively notify the data engineering team of job failures or performance degradations."]}\n\n'
            f"TASK INPUT:\n{{task_input_json}}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"pipeline.success_rate","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "3. Provide a detailed rationale: summarize runtime, throughput, and queue wait time for each pipeline. Explicitly highlight long-running, low-throughput, or jobs with long queue times.\n"
            "4. Recommend actionable and specific optimization steps as a list (e.g., ['Parallelize ETL tasks and break down large jobs into smaller, more manageable ones.', 'Optimize SQL queries by adding indexes to frequently filtered columns and refactoring complex joins.', 'Improve cluster resources by adjusting worker counts or scaling up to more powerful instances.', 'Enhance scheduling to minimize resource contention and reduce queue wait times.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"pipelines":[{"pipeline_name":"marketing_data_etl", "avg_runtime_minutes":45,"rows_processed":600000,"queue_wait_minutes":10}, {"pipeline_name":"sales_agg_job", "avg_runtime_minutes":15,"rows_processed":1200000,"queue_wait_minutes":2}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"pipeline.latency_throughput","score":3,'
            '"rationale":"The `marketing_data_etl` pipeline has a moderate average runtime of 45 minutes and processes 600k rows with a 10-minute queue wait. The `sales_agg_job` performs well with a 15-minute runtime and 1.2M rows. The overall score is pulled down by the moderate performance of the marketing pipeline.",'
            '"gap":["Optimize the `marketing_data_etl` pipeline by parallelizing its ETL tasks to reduce runtime.","Investigate the 10-minute queue wait time for the `marketing_data_etl` and adjust scheduling to prevent resource contention.","Refactor the SQL queries within the `marketing_data_etl` job to improve its processing efficiency."]}\n\n'
            f"TASK INPUT:\n{{task_input_json}}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"pipeline.latency_throughput","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "5. Provide a detailed rationale: detail cluster-by-cluster utilization for CPU, memory, and storage. Highlight any clusters that are significantly underutilized or have high costs relative to their usage.\n"
            "6. Provide actionable, highly specific, and detailed gaps as a list (e.g., ['Right-size overprovisioned clusters by scaling down instances to better match workload demand.', 'Implement auto-scaling policies to dynamically adjust cluster size based on actual usage, preventing overspending during low periods.', 'Schedule regular FinOps reviews and cost analysis sessions to identify and eliminate wasteful spending on underutilized resources.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"clusters":[{"name":"etl_cluster_A", "resource_usage":{"cpu":55,"memory":40,"storage":60},"cost_data":{"monthly_cost_usd":12000}}, {"name":"reporting_cluster_B", "resource_usage":{"cpu":80,"memory":75,"storage":85},"cost_data":{"monthly_cost_usd":8000}}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"resource.utilization","score":4,'
            '"rationale":"The `etl_cluster_A` has an average utilization of 51.6% (CPU: 55%, Memory: 40%, Storage: 60%) with a monthly cost of $12k. The `reporting_cluster_B` has an excellent average utilization of 80% with a cost of $8k. The overall score is `good` but can be improved by optimizing the `etl_cluster_A`.",'
            '"gap":["Right-size the `etl_cluster_A` by scaling down its compute resources to better match its current average utilization.", "Implement auto-scaling on `etl_cluster_A` to prevent overprovisioning and reduce unnecessary costs.", "Conduct a FinOps review for the `etl_cluster_A` to identify opportunities for cost reduction and improve efficiency."]}\n\n'
            f"TASK INPUT:\n{{task_input_json}}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"resource.utilization","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "3. In your rationale, provide a detailed summary of the average runtime, list any specific very slow-running queries and their users, and identify any users or queries that failed.\n"
            "4. Provide highly specific and actionable recommendations as a list (e.g., ['Add appropriate indexes to frequently queried columns to speed up data retrieval.', 'Optimize query joins by ensuring they use appropriate keys and are structured efficiently.', 'Introduce a caching layer for frequently accessed dashboards and reports to reduce query load.', 'Provide training sessions for users on how to write more efficient and performant queries.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"query_logs":[{"id":"q1","runtime":4,"user":"alice","success":true},{"id":"q2","runtime":8,"user":"bob","success":true},{"id":"q3","runtime":25,"user":"charlie","success":true}, {"id":"q4","runtime":30,"user":"charlie","success":false}]}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"query.performance","score":3,"rationale":"The average runtime for successful queries is 12.3s. The `q1` and `q2` queries are fast, but `q3` has a slow runtime of 25s, and `q4` for user `charlie` failed, pulling down the overall performance.", "gap":["Review and optimize the `q3` query to reduce its 25-second runtime, potentially by adding an aindex or rewriting the query.", "Investigate the failure of `q4` for user `charlie` by checking error logs and permissions issues.", "Provide training for users on writing efficient queries and using proper filtering to improve overall platform performance."]}\n\n'
            f"TASK INPUT:\n{{task_input_json}}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"query.performance","score":<1-5>,"rationale":"...","gap":["...","..."]}'
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
            "3. In your rationale, provide a detailed summary of usage metrics. Highlight departments with high or low usage, call out top adopters, and clarify overall engagement trends.\n"
            "4. In your gap, provide highly specific and detailed recommendations as a list (e.g., ['Host targeted training sessions for the finance and operations departments to increase their understanding of the platform and its value.', 'Promote existing dashboards via internal newsletters and highlight success stories from high-adoption teams.', 'Implement a user enablement program to provide direct support and resources, such as office hours and documentation, to new users.']).\n\n"
            "EXAMPLE INPUT:\n"
            '{"active_users":35,"dashboard_views":500,"queries_executed":2000,"departments":[{"name":"sales","active_users":20},{"name":"marketing","active_users":10},{"name":"finance","active_users":5}]}}\n\n'
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"analytics.adoption","score":3,"rationale":"The platform has moderate adoption with 35 active users and 500 dashboard views. Sales is the top adopting department with 20 users, followed by marketing with 10. The finance department shows low engagement with only 5 active users.","gap":["Host targeted training sessions and workshops for the finance department to address their low usage and demonstrate the value of the platform.", "Promote high-value dashboards and success stories through internal communication channels to drive broader engagement.", "Establish a user support and enablement program to assist users with specific questions and encourage self-service analytics."]}\n\n'
            f"TASK INPUT:\n{{task_input_json}}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"analytics.adoption","score":<1-5>,"rationale":"...","gap":["...","..."]}'
        )