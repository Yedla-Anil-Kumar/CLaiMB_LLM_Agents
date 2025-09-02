# Cloud Infrastructure Agent — Batch Runner Mode

This project runs Cloud Infrastructure Agent.  
A lightweight **scheduler** wakes up on a fixed interval, launches a **runner** to pick **one pending batch**, and the **engine** evaluates only the metrics present in that batch.
---

## 🚀 Quick Start

```bash
# 1) Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2) Cloud Infrastructure Agent ENV
CLOUD_INFRA_DATA_DIR=cloud_infra_agent/Data
LLM_PROVIDER=openai
# --- OpenAI ---
OPENAI_API_KEY=sk-proj-
OPENAI_MODEL=
# --- Google Gemini ---
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=
GOOGLE_MODEL=
BACKBONE_MODULE=cloud_infra_agent.agent_wrappers
DEFAULT_PLATFORM=aws

# 3) Start the scheduler (runs once immediately, then every 10 minutes by default)
python -m batch_runner.scheduler
```
- Drop a folder with JSON inputs under:  
  `cloud_infra_agent/Data/Inputs/<batch_name>/`
- On each tick the runner processes **one** pending batch and writes:  
  `cloud_infra_agent/Data/Outputs/<batch_name>/result.json`

---

## 📁 Repository Layout (relevant paths)

```
cloud_infra_agent/
  Data/
    Inputs/                 # put one subfolder per batch here
      Sample1/
        lb_performance.json
        availability_incidents.json
    Outputs/                # runner writes outputs here
      Sample1/result.json
    state/
      processed.json        # runner state (absolute paths of processed batches)

batch_runner/
  scheduler.py              # interval loop (run -> sleep -> run)
  runner.py                 # picks one pending batch and executes it
  engine_bridge.py          # runs engine (callable or external command)
  engine_adapter.py         # loads per-metric inputs, calls workflow
  config.yaml               # paths, patterns, engine wiring

workflows/
  monitor_workflow.py       # strict single-flow: run only metrics present

agent_layer/
  registry.py               # metric ids & category weights (dotted ids)
  tool_loader.py            # turns metric_id into callable
```

---

## ⚙️ Configuration

**`batch_runner/config.yaml`** (defaults shown):

```yaml
# === Batch Runner Config ===
inputs_root: "cloud_infra_agent/Data/Inputs"
outputs_root: "cloud_infra_agent/Data/Outputs"
state_file:  "cloud_infra_agent/Data/state/processed.json"

# A batch is processable if it has at least one file matching any glob here (at the batch root)
file_glob_patterns:
  - "*.json"

# Engine: call the Python adapter that loads per-metric JSONs and runs the workflow
engine_command: ""  # leave empty to use callable
engine_callable: "batch_runner.engine_adapter:run_engine"
```

**Scheduler interval:**  
The simple loop sleeps **600 seconds (10 minutes)** by default. Override:


---

## 🧱 Preparing a Batch

Create a **new subfolder** under `cloud_infra_agent/Data/Inputs/` and drop top-level JSON files:

```
cloud_infra_agent/Data/Inputs/Sample1/
  lb_performance.json
  availability_incidents.json
  compute_utilization.json
  ...
```

> **One folder = one batch.** The runner records processed folders by **absolute path** in `Data/state/processed.json`.  
> To re-run, create a **new folder name** (e.g., `Sample2/`).

### Canonical Metric IDs & Filenames

Metric identifiers are **dotted** (canonical), and the adapter reads files via a single map:

```python
# engine_adapter.py (excerpt)
Input_File_For_Metric_map = {
  "tagging.coverage":         "tagging_coverage.json",
  "compute.utilization":      "compute_utilization.json",
  "k8s.utilization":          "k8s_utilization.json",
  "scaling.effectiveness":    "scaling_effectiveness.json",
  "db.utilization":           "db_utilization.json",
  "lb.performance":           "lb_performance.json",
  "storage.efficiency":       "storage_efficiency.json",
  "iac.coverage_drift":       "iac_coverage_drift.json",
  "availability.incidents":   "availability_incidents.json",
  "cost.idle_underutilized":  "cost_idle_underutilized.json",
  "cost.commit_coverage":     "cost_commit_coverage.json",
  "cost.allocation_quality":  "cost_allocation_quality.json",
  "security.public_exposure": "security_public_exposure.json",
  "security.encryption":      "security_encryption.json",
  "security.iam_risk":        "security_iam_risk.json",
  "security.vuln_patch":      "security_vuln_patch.json"
}
```

Only metrics with a corresponding file present in the batch will run (**strict single flow**).

### Minimal JSON Examples

`lb_performance.json`
```json
{
  "load_balancers": [
    { "id": "alb-1", "lat_p95": 120, "lat_p99": 240, "r5xx": 0.002, "unhealthy_minutes": 1, "requests": 1800000 }
  ],
  "slo": { "p95_ms": 200, "p99_ms": 400, "5xx_rate_max": 0.005 }
}
```

`availability_incidents.json`
```json
{
  "incidents": [],
  "slo_breaches": [],
  "slo": { "objective": "availability", "target": 0.999 }
}
```

---

## 🔁 How the Scheduler/Runner Work

**On start:** scheduler immediately launches the runner once.  
**Every interval:** scheduler launches runner again.

**Runner steps each time:**
1. List batch folders under `Inputs/`.
2. Filter to **pending**:
   - has at least one file matching `file_glob_patterns` at the batch root,
   - **not** already in `state/processed.json`,
   - **no** `.lock` file present.
3. Pick **one** pending folder (newest by mtime), create a `.lock`, and run the engine.
4. Write output to `Outputs/<batch>/result.json`.
5. Mark batch as processed (absolute path) and remove `.lock`.

**One batch per tick** by design. If you drop multiple batches, they will be processed **one per interval** (e.g., every 10 minutes).

---

## 📄 Output

Per-batch result: `cloud_infra_agent/Data/Outputs/<batch_name>/result.json`

Shape:
```json
{
  "metrics": {
    "lb.performance":{ "metric_id": "lb.performance", "score": 4.0, "confidence": 0.9, "rationale": "...", "evidence": {}, "gaps": [] },
    "availability.incidents": { "metric_id": "availability.incidents", "score": 5.0, "confidence": 0.85, "rationale": "...", "evidence": {}, "gaps": [] }
  },
  "summary": {
    "overall_score": 4.1,
    "category_scores": { "reliability": 4.5, "cost": 3.7, "security": 4.0, "efficiency": 3.9 },
    "breakdown": [ /* category -> metrics & weights */ ],
    "scored_metrics": 12
  }
}
```

---


## ❗ Exit Codes (runner)

- `0` — Success (processed a batch **or** nothing pending)
- `1` — Engine failure (callable/command failed)
- `2` — Couldn’t write result file (I/O error)

The scheduler logs the runner’s exit code each tick.

---

## 🛠️ Troubleshooting

**“New batch not picked up”**
- Ensure it’s a **new folder** under `Data/Inputs/` (unique name).
- Ensure there is at least **one** `*.json` at the **batch root** (default globs are not recursive).
  - If you must put JSONs under a subfolder, add a glob in `config.yaml`:
    ```yaml
    file_glob_patterns:
      - "*.json"
      - "inputs/*.json"
    ```
- Check for a stale `.lock` inside the batch folder.
- Inspect logs; runner prints:
  - `[runner] subdirs: [...]`
  - `skip <name>: already processed | locked | no input files`
  - `pending candidates: [...]`

**“Missing mapped files” in engine logs**  
→ The adapter prints which metric files weren’t found. Add those files (or ignore those metrics for that batch).

---

## 📚 Notes

- **Re-runs:** Recommended approach is **new folder per batch** (e.g., timestamped dirs).
- **IDs:** Keep metric IDs **dotted** everywhere; only filenames map underscores.
- **Time:** Runner/scheduler timestamps are written in **UTC**.
