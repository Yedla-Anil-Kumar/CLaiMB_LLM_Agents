NESTED_LOOPS_EXAMPLE = {
    "NestedLoopsAgent": {
        "input_key_meanings": {
            "code_snippets": "Single-file snippet; agent decides presence and depth of nested loops."
        },
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
            "metric_id": "code.nested_loops_band",
            "band": 3,
            "rationale": "Nested loops identified with moderate depth (2). While acceptable for small datasets, scalability risks exist for larger inputs.",
            "flags": ["nested_depth_2", "scalability_risk"],
            "gaps": [
                "Loop nesting depth = 2 with direct aggregation → replace with SQL/pandas groupby aggregation → ensure hotspots have depth ≤1 (unlocks band 4).",
                "Performance risks on large tenants → benchmark with ≥10k records and refactor to vectorized operations → reduce O(U*O) risks (unlocks band 5)."
            ]
        }
    }
}