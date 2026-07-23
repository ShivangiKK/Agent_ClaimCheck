"""
Lovelace Security Gate

This module screens user claims, dataset column names, and sample rows before
any content is passed to an LLM agent.

Purpose:
- detect prompt-injection attempts
- detect suspicious system-prompt language
- detect unsafe code-like patterns
- route risky inputs to human review
"""

from typing import Any, Dict, List


BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "developer message",
    "hidden prompt",
    "reveal your instructions",
    "show me your prompt",
    "bypass",
    "jailbreak",
    "drop table",
    "delete all",
    "<script",
    "</script>",
    "eval(",
    "exec(",
    "import os",
    "subprocess",
    "rm -rf",
    "send this data",
    "exfiltrate",
]


def _normalize_text(value: Any) -> str:
    """
    Convert any value into lowercase text for pattern scanning.
    """
    if value is None:
        return ""
    return str(value).lower()


def run_security_gate(
    claim: str,
    column_names: List[str],
    sample_rows: List[Dict[str, Any]],
    blocked_patterns: List[str] = None,
) -> Dict[str, Any]:
    """
    Deterministic security gate before LLM exposure.

    Parameters
    ----------
    claim:
        User-submitted business claim.
    column_names:
        Dataset column names.
    sample_rows:
        Small sample of dataset rows, represented as dictionaries.
    blocked_patterns:
        Optional custom list of blocked patterns.

    Returns
    -------
    Dict with:
    - security_passed
    - triggered_patterns
    - action
    - human_review_required
    - scanned_fields
    """
    patterns = blocked_patterns or BLOCKED_PATTERNS

    scan_parts = [_normalize_text(claim)]
    scan_parts.extend([_normalize_text(col) for col in column_names])

    for row in sample_rows:
        scan_parts.extend([_normalize_text(value) for value in row.values()])

    scan_text = " ".join(scan_parts)

    triggered_patterns = [
        pattern for pattern in patterns
        if pattern.lower() in scan_text
    ]

    security_passed = len(triggered_patterns) == 0

    return {
        "security_passed": security_passed,
        "triggered_patterns": triggered_patterns,
        "action": "continue" if security_passed else "halt_for_human_review",
        "human_review_required": not security_passed,
        "scanned_fields": {
            "claim": True,
            "column_names": True,
            "sample_rows": True,
        },
    }


def summarize_security_result(result: Dict[str, Any]) -> str:
    """
    Create a concise human-readable security summary.
    """
    if result.get("security_passed"):
        return "Security gate passed. No blocked patterns were detected."

    triggered = ", ".join(result.get("triggered_patterns", []))
    return f"Security gate failed. Human review required. Triggered patterns: {triggered}"
