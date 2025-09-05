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
                "You are a Data Platform Health evaluator. Your job is to measure overall data quality across:\n"
                "1. Table-level metrics (null percentage, duplicate percentage, outlier percentage).\n"
                "2. Dependency checks (e.g., schema consistency, data freshness).\n\n"
                "SCORING RUBRIC (based on worst-case degradation across all dimensions):\n"
                "- 5: Excellent — <1% table issues AND all dependencies scored 5.\n"
                "- 4: Good — 1–5% issues OR one dependency scored 4.\n"
                "- 3: Moderate — 6–15% issues OR one dependency scored 3.\n"
                "- 2: Poor — 16–30% issues OR one dependency scored 2.\n"
                "- 1: Very Poor — >30% issues OR one dependency scored 1.\n\n"
                "INSTRUCTIONS:\n"
                "1. For each table, compute issue_rate = null_pct + duplicate_pct + outlier_pct.\n"
                "   - Report the percentage for each dimension (nulls, duplicates, outliers) clearly.\n"
                "   - Report the total issue rate per table.\n"
                "2. Assign a table-level quality score using the rubric.\n"
                "3. Review all dependency checks and include their score + rationale explicitly.\n"
                "4. The final score is the lowest score across tables and dependencies (worst case dominates).\n"
                "5. Provide a rationale that includes:\n"
                "   - A breakdown of each table’s issues.\n"
                "   - A breakdown of each dependency’s score and rationale.\n"
                "   - A concluding statement explaining which factor drove the final score.\n"
                "6. Provide a gap: actionable, highly specific, and detailed recommendations **only for tables**. "
                "Do not include dependency recommendations here.\n\n"
                "EXAMPLE INPUT:\n"
                "{\n"
                '  "tables": [\n'
                '    {"table":"users","null_pct":0.07,"duplicate_pct":0.05,"outlier_pct":0.00},\n'
                '    {"table":"orders","null_pct":0.1,"duplicate_pct":0.03,"outlier_pct":0.05}\n'
                "  ],\n"
                '  "dependency_results": {\n'
                '    "check_schema_consistency": {\n'
                '      "metric_id": "schema.consistency",\n'
                '      "score": 2,\n'
                '      "rationale": "Missing fields in users and orders, extra field in reviews.",\n'
                '      "gap": ["Add missing fields.", "Remove undocumented extras."]\n'
                "    },\n"
                '    "evaluate_data_freshness": {\n'
                '      "metric_id": "data.freshness",\n'
                '      "score": 3,\n'
                '      "rationale": "Orders table is delayed by 5h beyond SLA.",\n'
                '      "gap": ["Fix ingestion pipeline for orders table."]\n'
                "    }\n"
                "  }\n"
                "}\n\n"
                "EXAMPLE OUTPUT:\n"
                '{"metric_id":"data.quality","score":2,'
                '"rationale":"Table breakdown: Users table has 7% nulls and 5% duplicates, totaling ~12% issues (score 3). Orders table has 10% nulls, 3% duplicates, and 5% outliers, totaling ~18% issues (score 2).\\n'
                'Dependency breakdown: Schema consistency scored 2 due to missing fields in users and orders plus an extra field in reviews. Data freshness scored 3 because the orders table was delayed by 5h beyond SLA.\\n'
                'Conclusion: The lowest score observed was 2 (from both orders table quality and schema consistency), so the overall data quality score is 2.",'
                '"gap":["Implement NOT NULL constraints on `email` and `created_at` in users.",'
                '"Enforce uniqueness on `user_id` in users.",'
                '"Deploy a cleansing job to handle duplicates in orders.",'
                '"Add anomaly detection logic to catch outlier values in orders."]}\n\n"'
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
            "You are an Analytics Readiness evaluator. Your job is to assess the robustness of data pipelines "
            "based on their run history and dependency health.\n\n"
            "You will receive:\n"
            "1. A list of pipeline runs (id, name, status, runtime).\n"
            "2. Dependency results (e.g., data lineage).\n\n"
            "SCORING RUBRIC (based on worst-case across runs + dependencies):\n"
            "- 5: ≥99% jobs succeed AND all dependencies scored 5.\n"
            "- 4: 95–98% jobs succeed OR one dependency scored 4.\n"
            "- 3: 85–94% jobs succeed OR one dependency scored 3.\n"
            "- 2: 70–84% jobs succeed OR one dependency scored 2.\n"
            "- 1: <70% jobs succeed OR one dependency scored 1.\n\n"
            "INSTRUCTIONS:\n"
            "1. Calculate the total number of runs and how many had status 'success'.\n"
            "2. Compute the pipeline success rate = (number of successes / total runs) * 100.\n"
            "3. Assign a success score using the rubric.\n"
            "4. Review dependency scores and rationales. The final score is the lowest across success rate and dependency scores (worst case dominates).\n"
            "5. Provide a detailed rationale that includes:\n"
            "   - Success rate percentage and counts (success vs. failures).\n"
            "   - A breakdown of which pipelines failed (by name and frequency).\n"
            "   - Notable runtime anomalies (e.g., jobs running much longer than others).\n"
            "   - Dependency breakdown: list each dependency metric, its score, and its rationale.\n"
            "   - A conclusion that explains why the final score was chosen.\n"
            "6. Provide a gap: actionable, highly specific, and detailed recommendations **only for pipelines** "
            "(retry logic, better logging, anomaly detection, etc.). Do not include dependency recommendations.\n\n"
            "EXAMPLE INPUT:\n"
            "{\n"
            '  "pipeline_runs":[\n'
            '    {"id":1,"name":"etl_orders","status":"success","runtime_sec":320},\n'
            '    {"id":2,"name":"etl_sales","status":"failure","runtime_sec":0},\n'
            '    {"id":3,"name":"etl_orders","status":"success","runtime_sec":310}\n'
            "  ],\n"
            '  "dependency_results": {\n'
            '    "evaluate_data_lineage": {\n'
            '      "metric_id": "data.lineage",\n'
            '      "score": 4,\n'
            '      "rationale": "80% lineage coverage with gaps in marketing domain.",\n'
            '      "gap": ["Implement automated lineage extraction tooling."]\n'
            "    }\n"
            "  }\n"
            "}\n\n"
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"pipeline.success_rate","score":2,'
            '"rationale":"Pipeline runs: 3 total, 2 successes and 1 failure. Success rate = 66.7%, which corresponds to score 1. '
            'The failed pipeline was `etl_sales` (runtime 0). Runtime distribution shows orders ETL averaging ~315s, while sales ETL failed entirely. '
            'Dependency results: Data lineage scored 4 due to incomplete documentation (80% coverage, gaps in marketing). '
            'Final score = 2 because the worst observed score was 1 (from pipeline success) and 4 (from lineage), leading to an overall poor robustness assessment.",'
            '"gap":["Implement robust retry mechanisms with exponential backoff for the `etl_sales` pipeline.",'
            '"Investigate root cause of `etl_sales` failure by reviewing logs and dependencies.",'
            '"Enhance pipeline monitoring to detect runtime anomalies and failures proactively."]}\n\n"'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"pipeline.success_rate","score":<1-5>,"rationale":"...","gap":["...","..."]}'
        )

    @staticmethod
    def get_pipeline_latency_throughput_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are an Analytics Readiness evaluator. Your job is to score data pipelines on latency and throughput, "
            "while also considering dependency health checks.\n\n"
            "You will receive:\n"
            "1. Pipeline performance metrics: avg_runtime_minutes, rows_processed, queue_wait_minutes.\n"
            "2. Dependency results (e.g., schema consistency, data freshness).\n\n"
            "SCORING RUBRIC (worst-case across all dimensions):\n"
            "- 5: All pipelines runtime <10m, throughput >1M rows/job, negligible wait, and all dependencies scored 5.\n"
            "- 4: Most runtime <30m, throughput >500k rows, low queue wait, or one dependency scored 4.\n"
            "- 3: Most runtime <60m, moderate throughput, or one dependency scored 3.\n"
            "- 2: Significant jobs runtime <120m, low throughput, moderate queueing, or one dependency scored 2.\n"
            "- 1: >120m or serious delays for one or more jobs, or one dependency scored 1.\n\n"
            "INSTRUCTIONS:\n"
            "1. For each pipeline, examine avg_runtime_minutes, rows_processed, queue_wait_minutes.\n"
            "   - Report runtime, throughput, and wait times explicitly.\n"
            "   - Highlight any long runtimes (>60m), low throughput (<500k), or queueing (>10m).\n"
            "2. Assign a score reflecting the worst-performing pipeline.\n"
            "3. Review dependency results and include their scores + rationales in the evaluation.\n"
            "4. The final score is the lowest across pipeline scores and dependency scores (worst case dominates).\n"
            "5. Provide a detailed rationale that includes:\n"
            "   - A per-pipeline breakdown (runtime, throughput, wait time).\n"
            "   - Dependency breakdown (metric, score, rationale).\n"
            "   - A conclusion explaining why the final score was chosen.\n"
            "6. Provide a gap: actionable, highly specific, and detailed recommendations **only for pipelines** "
            "(query tuning, scheduling improvements, scaling resources, etc.). Do not include dependency gaps.\n\n"
            "EXAMPLE INPUT:\n"
            "{\n"
            '  "pipelines": [\n'
            '    {"pipeline_name":"marketing_data_etl","avg_runtime_minutes":45,"rows_processed":600000,"queue_wait_minutes":10},\n'
            '    {"pipeline_name":"sales_agg_job","avg_runtime_minutes":15,"rows_processed":1200000,"queue_wait_minutes":2}\n'
            "  ],\n"
            '  "dependency_results": {\n'
            '    "check_schema_consistency": {\n'
            '      "metric_id": "schema.consistency",\n'
            '      "score": 2,\n'
            '      "rationale": "Missing fields in users and orders; extra field in reviews (~20% schema mismatch).",\n'
            '      "gap": ["Fix missing and extra fields."]\n'
            "    },\n"
            '    "evaluate_data_freshness": {\n'
            '      "metric_id": "data.freshness",\n'
            '      "score": 2,\n'
            '      "rationale": "Orders 5h late, inventory 26h late (major SLA breaches).",\n'
            '      "gap": ["Fix ingestion delays."]\n'
            "    }\n"
            "  }\n"
            "}\n\n"
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"pipeline.latency_throughput","score":2,'
            '"rationale":"Pipeline breakdown: marketing_data_etl has 45m runtime, 600k rows, and 10m queue wait (moderate performance). '
            'sales_agg_job performs well with 15m runtime, 1.2M rows, and minimal queueing. '
            'Dependency breakdown: Schema consistency scored 2 due to missing/extra fields (~20% mismatch). Data freshness scored 2 due to major SLA breaches (orders 5h late, inventory 26h late). '
            'Final score = 2 because both dependencies scored 2, which dominates overall readiness.",'
            '"gap":["Optimize marketing_data_etl by parallelizing ETL tasks to reduce its 45m runtime.",'
            '"Investigate queue scheduling for marketing_data_etl to reduce its 10m wait.",'
            '"Refactor queries in marketing_data_etl to improve efficiency."]}\n\n"'
            f"TASK INPUT:\n{task_input_json}\n\n"
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
            f"TASK INPUT:\n{task_input_json}\n\n"
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
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"query.performance","score":<1-5>,"rationale":"...","gap":["...","..."]}'
        )

    @staticmethod
    def get_analytics_adoption_prompt(task_input_json: str) -> str:
        return (
            "SYSTEM:\n"
            "You are an Analytics Readiness evaluator. Assess analytics platform adoption based on active user and usage metrics, "
            "while also considering dependency health checks.\n\n"
            "You will receive:\n"
            "1. Adoption metrics: active_users, dashboard_views, queries_executed, departmental breakdowns, most_active_users.\n"
            "2. Dependency results (e.g., metadata coverage, schema consistency, data freshness).\n\n"
            "SCORING RUBRIC (adoption-based):\n"
            "- 5: >100 active users and >1000 views\n"
            "- 4: 50–100 users\n"
            "- 3: 25–49 users\n"
            "- 2: 10–24 users\n"
            "- 1: <10 users or very low adoption\n\n"
            "FINAL SCORE RULE:\n"
            "The overall score = min(adoption score, dependency scores).\n\n"
            "INSTRUCTIONS:\n"
            "1. Calculate adoption score using active_users and rubric.\n"
            "2. Contextualize with dashboard_views, queries_executed, departmental usage, and most_active_users.\n"
            "   - Highlight top adopters, lagging departments, and usage distribution.\n"
            "3. Include dependency breakdown (list each dependency metric, score, and rationale).\n"
            "4. Choose the lowest score (adoption vs dependencies) as the final score.\n"
            "5. Rationale should:\n"
            "   - Summarize adoption (active_users, views, queries).\n"
            "   - Highlight departmental strengths/weaknesses and most active users.\n"
            "   - Summarize dependencies with their scores and issues.\n"
            "   - Conclude by explaining why the final score was chosen.\n"
            "6. Gap should provide actionable, adoption-specific recommendations only (e.g., training, enablement, comms). "
            "Do not include dependency gaps.\n\n"
            "EXAMPLE INPUT:\n"
            "{\n"
            '  "active_users": 35,\n'
            '  "dashboard_views": 500,\n'
            '  "queries_executed": 2000,\n'
            '  "departments": [{"name":"sales","active_users":20},{"name":"marketing","active_users":10},{"name":"finance","active_users":5}],\n'
            '  "dependency_results": {\n'
            '    "evaluate_metadata_coverage": {"metric_id":"metadata.coverage","score":2,"rationale":"~50% tables documented."},\n'
            '    "check_schema_consistency": {"metric_id":"schema.consistency","score":3,"rationale":"Minor schema drifts detected."}\n'
            "  }\n"
            "}\n\n"
            "EXAMPLE OUTPUT:\n"
            '{"metric_id":"analytics.adoption","score":2,'
            '"rationale":"Adoption score is 3 (35 active users, 500 views, 2000 queries). '
            'Sales leads adoption with 20 users, marketing has 10, finance lags with 5. '
            'Dependencies: metadata coverage scored 2 (~50% documented), schema consistency scored 3 (minor drifts). '
            'Final score = 2 because dependency metadata coverage pulled the overall readiness down.",'
            '"gap":["Host targeted training for finance to improve adoption.","Promote dashboards and success stories in sales to cross-pollinate adoption.","Establish office hours and enablement programs to onboard new users."]}\n\n'
            f"TASK INPUT:\n{task_input_json}\n\n"
            "RESPONSE FORMAT (strict JSON only, no extra text):\n"
            '{"metric_id":"analytics.adoption","score":<1-5>,"rationale":"...","gap":["...","..."]}'
        )
