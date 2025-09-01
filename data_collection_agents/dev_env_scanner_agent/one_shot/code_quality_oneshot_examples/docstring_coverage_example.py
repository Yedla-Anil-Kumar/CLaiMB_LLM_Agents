DOCSTRING_EXAMPLE = {
    "DocstringCoverageAgent": {
        "input_key_meanings": {
            "code_snippets": "Files with functions/classes; docstrings may be partial/inconsistent."
        },
        "example_input": {
            "code_snippets": [
                """\
                    def load_model(path):
                        \"\"\"Load a LightGBM model from disk.\"\"\"
                        import joblib
                        return joblib.load(path)

                    def predict(m, rows):
                        # missing docstring
                        return m.predict(rows)

                    class Scorer:
                        \"\"\"Compute domain-specific KPIs from predictions.\"\"\"
                        def score(self, y_true, y_pred):
                            # missing parameter/return descriptions
                            return {"mae": float(abs(y_true - y_pred).mean())}
                    """
            ]
        },
        "example_output": {
            "metric_id": "code.docstring_coverage_band",
            "band": 2,
            "rationale": "Some key functions and classes have docstrings, but parameter/return details are inconsistent and missing in critical places.",
            "flags": ["missing_function_docs", "incomplete_params"],
            "gaps": [
                "Missing parameter/return docs → enforce complete function signatures with param/return tags → achieve ≥0.80 coverage and quality ≥0.75 (unlocks band 4).",
                "Sparse examples in usage → add input/output examples to core functions → increase docstring_quality ≥0.85 (unlocks band 5)."
            ]
        }
    }
}