# CloudInfraAgent

**CloudInfraAgent** is a modular framework for assessing cloud infrastructure across **FinOps, security, scaling, availability, and utilization**.  
It ingests JSON inputs, an **LLM** for consistent scoring (1–5).  


---

## 📂 Project Structure

```
cloud_infra_agent/
├── main.py                  # Entry point for running agent
├── base_agents.py           # Base classes for agent orchestration     
├── call_llm_.py             # LLM call wrappers
├── compute_functions.py     # Functions for metric computation
├── config.py                # Configurations and constants
├── metric_input_loader.py   # Load JSON inputs for metrics
├── metrics.py               # Metric registry and prompts
├── utility_functions.py     # Shared helpers (aggregation, scoring, utils)
└── Data/
    └── Sample2/
        ├── inputs/          # Input JSONs per metric
        └── output.json      # Generated output
```

---

## 🚀 Features

- **Multi-domain Metric Coverage**  
  - Tagging coverage  
  - Compute utilization  
  - Database and load balancer metrics  
  - Kubernetes efficiency  
  - Scaling effectiveness  
  - Cost allocation, idle/waste tracking  
  - IAM risks, vulnerabilities, CSPM findings  

- **LLM Scoring**  
  **LLM-powered reasoning** for structured outputs.

- **Pluggable Design**  
  Add new metrics by extending `DEFAULT_METRICS` in `config.py` and mapping them in `metrics.py`.

- **Sample Datasets**  
  Ready-to-run JSONs included in `Data/Sample2/inputs`.

---

## ⚙️ Installation

```bash
git clone <your-repo-url>
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set environment variables (via `.env`):

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-google-key
OPENAI_KEY=your-openai-key
CLOUD_INFRA_DATA_DIR=cloud_infra_agent/Data
```

---

## ▶️ Usage

### Run with Sample Data

```bash
python -m cloud_infra_agent.main <sample_data_folder_name>
```

This will:
1. Load mappings from `Data/<sample_data_folder_name>/inputs/`
2. Ccall LLM for scoring
3. Generate structured output (`output.json`)


---

## 📊 Example Input → Output

### Input (`Data/Sample2/inputs/tagging_coverage.json`)

```json
{
  "resources": [
    {
      "id": "i-3",
      "tags": {
        "env": "prod",
        "owner": "search",
        "service": "api"
      }
    },
    {
      "id": "i-4",
      "tags": {
        "env": "stage",
        "owner": "search"
      }
    },
    {
      "id": "db-3",
      "tags": {
        "env": "prod"
      }
    }
  ],
  "required_tags": [
    "env",
    "owner",
    "cost-center",
    "service"
  ]
}
```

### LLM Evaluation Output

```json
{
      "metric_id": "tagging.coverage",
      "score": 2,
      "rationale": "Only 1 out of 3 resources (33%) are fully tagged with all required tags. Critical tags like 'owner' are missing on a production resource, and 'cost-center' is absent on all resources, posing material risks to cost tracking and accountability.",
      "evidence": {
        "coverage_pct": 0.33,
        "fully_tagged_ids": [
          "i-3"
        ],
        "missing_examples": [
          {
            "id": "i-4",
            "missing": [
              "cost-center",
              "service"
            ]
          },
          {
            "id": "db-3",
            "missing": [
              "owner",
              "cost-center",
              "service"
            ]
          }
        ],
        "prod_missing_critical": [
          {
            "id": "db-3",
            "missing": [
              "owner"
            ]
          }
        ]
      },
      "gaps": [
        "1. Add 'cost-center' and 'service' tags to all resources.",
        "2. Ensure 'owner' tag is present on all production resources.",
        "3. Implement automated checks to enforce required tags at provisioning."
      ],
      "confidence": 0.8
    }

```

