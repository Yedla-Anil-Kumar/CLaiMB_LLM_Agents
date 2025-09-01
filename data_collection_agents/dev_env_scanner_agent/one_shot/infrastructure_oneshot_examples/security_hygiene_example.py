from __future__ import annotations

INFRA_SECURITY_HYGIENE_EXAMPLE = {
    "SecurityAgent": {
        "input_key_meanings": {"code_snippets": "Any code with potential secrets or security risks."},
        "example_input": {
            "code_snippets": [
                """\
                    SENTRY_DSN = "https://key:secret@sentry.io/12345"  # hardcoded!
                    def login(user, pwd):
                        if len(pwd) < 6:
                            return False
                        return True
                """
            ]
        },
        "example_output": {
            "metric_id": "infra.security_hygiene",
            "band": 2,
            "rationale": "Hardcoded secret-like value and weak password checks indicate material security risk.",
            "flags": ["hardcoded_secret", "weak_password_policy"],
            "gaps": [
                "Move secrets to a secret manager/env with rotation → eliminate hardcoded credentials (unlocks band 4).",
                "Enforce strong policy + rate limiting/lockout → reduce account takeover risk (supports band 4–5)."
            ]
        }
    }
}