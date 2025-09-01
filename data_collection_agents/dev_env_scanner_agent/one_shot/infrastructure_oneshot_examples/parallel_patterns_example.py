from __future__ import annotations

INFRA_PARALLEL_PATTERNS_EXAMPLE = {
    "ParallelPatternsAgent": {
        "input_key_meanings": {
            "code_snippets": "Snippets that might use threading/multiprocessing/concurrent.futures/asyncio/Ray."
        },
        "example_input": {
            "code_snippets": [
                """\
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    import requests

                    session = requests.Session()

                    def fetch(url):
                        with session.get(url, timeout=5) as r:
                            return r.status_code

                    def crawl(urls):
                        results = []
                        with ThreadPoolExecutor(max_workers=16) as ex:
                            futures = [ex.submit(fetch, u) for u in urls]
                            for f in as_completed(futures):
                                results.append(f.result())
                        return results
                """
            ]
        },
        "example_output": {
            "metric_id": "infra.parallel_patterns",
            "band": 4,
            "rationale": "Thread-pool fan-out fits IO-bound workload; session reuse and timeouts present, but no back-pressure or bounded submission.",
            "flags": ["session_reused", "timeouts_present", "backpressure_missing"],
            "gaps": [
                "Unbounded submission → use a Queue/semaphore or chunked batches → prevent resource spikes (unlocks band 5).",
                "No graceful cancel → add timeouts/cancellation paths on executor → safer shutdown (supports band 5)."
            ]
        }
    }
}