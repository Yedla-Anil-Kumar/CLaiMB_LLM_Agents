# Data_Collection_Agents/dev_env_scanner/one_shot/code_quality_examples.py
from __future__ import annotations

CODE_QUALITY_EXAMPLES = {
    "CyclomaticComplexityAgent": {
        "input_key_meanings": {
            "code_snippets": "List of source-code snippets; each should be a reasonable slice (several functions/classes) from one file."
        },
        "example_input": {
            "code_snippets": [
                """\
def fetch_orders(client, user_id):
    if not user_id:
        return []
    orders = client.list_orders(user_id)
    results = []
    for o in orders:
        if o['status'] in ('NEW','PAID'):
            if o.get('amount', 0) > 0:
                results.append(o)
            else:
                continue
        elif o['status'] == 'CANCELLED':
            continue
        else:
            # manual verification path
            if client.has_flag(o['id'], 'manual'):
                results.append(o)
    return results

class OrderRouter:
    def route(self, order):
        if order.is_high_value():
            if order.is_international():
                return "intl_priority"
            return "domestic_priority"
        if order.requires_manual():
            return "manual_queue"
        return "standard"
""",
                """\
def transform(df):
    # simple but branching logic per column
    df = df.copy()
    df['amount_norm'] = (df['amount'] - df['amount'].mean()) / (df['amount'].std() or 1)
    df['country_group'] = df['country'].apply(lambda c: 'EU' if c in EU_LIST else ('US' if c=='US' else 'ROW'))
    if 'discount' in df.columns:
        df['net'] = df['amount'] - df['discount']
    else:
        df['net'] = df['amount']
    return df
"""
            ]
        },
        "example_output": {
            "avg_complexity": 3.6,
            "complexity_distribution": {"low": 1, "medium": 1, "high": 0, "very_high": 0},
            "recommendations": [
                "Flatten nested if/elif chains in fetch_orders via guard clauses.",
                "Move routing rules to a table/strategy pattern for clarity."
            ]
        }
    },

    "MaintainabilityAgent": {
        "input_key_meanings": {"code_snippets": "Representative code including class + function + some branching."},
        "example_input": {
            "code_snippets": [
                """\
class FeatureStore:
    def __init__(self, client):
        self._client = client

    def get_features(self, ids, ttl=3600):
        # mixed responsibilities: cache + fetch + transform in one method
        cache_key = f"feat:{hash(tuple(ids))}"
        data = self._client.cache_get(cache_key)
        if data:
            return data
        raw = self._client.batch_get(ids)
        out = []
        for r in raw:
            out.append({"id": r["id"], "score": (r["x"]*0.7 + r["y"]*0.3)})
        self._client.cache_put(cache_key, out, ttl=ttl)
        return out
"""
            ]
        },
        "example_output": {
            "maintainability_score": 0.72,
            "readability_score": 0.75,
            "design_quality": 0.68,
            "improvement_suggestions": [
                "Extract cache layer into a decorator or separate adapter.",
                "Split get_features into fetch() and transform() to reduce responsibilities.",
                "Document the scoring formula with rationale and units."
            ]
        }
    },

    "DocstringCoverageAgent": {
        "input_key_meanings": {"code_snippets": "Files with functions/classes; docstrings may be partial/inconsistent."},
        "example_input": {
            "code_snippets": [
                '''\
def load_model(path):
    """Load a LightGBM model from disk."""
    import joblib
    return joblib.load(path)

def predict(m, rows):
    # missing docstring
    return m.predict(rows)

class Scorer:
    """Compute domain-specific KPIs from predictions."""
    def score(self, y_true, y_pred):
        # missing parameter/return descriptions
        return {"mae": float(abs(y_true - y_pred).mean())}
'''
            ]
        },
        "example_output": {
            "docstring_coverage": 0.5,
            "docstring_quality": 0.6,
            "missing_documentation": ["predict", "Scorer.score params/returns"],
            "quality_improvements": [
                "Add parameter/return types to Scorer.score.",
                "Provide examples and edge cases for predict."
            ]
        }
    },

    "NestedLoopsAgent": {
        "input_key_meanings": {"code_snippets": "Single-file snippet; agent decides presence and depth of nested loops."},
        "example_input": {
            "code_snippets": [
                """\
for u in users:
    for o in u.orders:
        if o.status == "PAID":
            totals[u.id] = totals.get(u.id, 0) + o.amount
"""
            ]
        },
        "example_output": {
            "has_nested_loops": True,
            "max_nesting_depth": 2,
            "performance_concerns": ["O(U*O) aggregation risks hot paths on large tenants."],
            "optimization_suggestions": [
                "Pre-aggregate orders by user_id in SQL.",
                "Vectorize using pandas groupby or pushdown to warehouse."
            ]
        }
    },
}