MAINTAINABILITY_EXAMPLE = {
    "MaintainabilityAgent": {
        "input_key_meanings": {
            "code_snippets": "Representative code including class + function + some branching."
        },
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
            "metric_id": "code.maintainability_band",
            "band": 3,
            "rationale": "Readable code with consistent naming; single method mixes caching, fetching, and transforming which reduces maintainability.",
            "flags": ["mixed_responsibilities", "low_cohesion"],
            "gaps": [
                "Mixed responsibilities in single method → extract cache/fetch/transform into separate functions → raise maintainability ≥0.75 across dimensions (unlocks band 4).",
                "No clear documentation of scoring formula → add comments + rationale with units → improve readability_score ≥0.80 (unlocks band 4)."
            ]
        }
    }
}