CYCLO_COMPLEXITY_EXAMPLE = {
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
                            if o['status'] in ('NEW', 'PAID'):
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
                        df['country_group'] = df['country'].apply(
                            lambda c: 'EU' if c in EU_LIST else ('US' if c == 'US' else 'ROW')
                        )
                        if 'discount' in df.columns:
                            df['net'] = df['amount'] - df['discount']
                        else:
                            df['net'] = df['amount']
                        return df
                    """
            ]
        },
        "example_output": {
            "metric_id": "code.cyclomatic_complexity_band",
            "band": 4,
            "rationale": "Most functions are simple-to-moderate; a few nested conditional ladders raise complexity. Lack of deeply nested hotspots keeps risk contained.",
            "flags": ["nested_conditionals", "branching_hotspots"],
            "gaps": [
                "Nested conditional ladders drive decision points → refactor to guard clauses or a rule/strategy table → keep ≤20% functions in high/very_high and avg ≤7 (stabilizes band 4/targets band 5).",
                "Routing logic mixes thresholds and flow → extract policy objects for international/high-value cases → reduce max per-function complexity to ≤5 and ≤10% high/very_high (unlocks band 5)."
            ]
        }
    }
}