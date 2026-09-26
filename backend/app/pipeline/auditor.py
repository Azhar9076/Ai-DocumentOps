"""AI Compliance Auditor agent generating standardized one-sentence compliance summaries."""

from __future__ import annotations

import logging
from typing import Any

from app.models import DocStatus, DocType
from app.pipeline.prompts_v2 import AUDIT_SUMMARY_PROMPT_TEMPLATE
from app.pipeline.validation import Issue, MathResult
from app.pipeline.watsonx import watsonx_client

logger = logging.getLogger(__name__)


def generate_audit_summary(
    doc_type: DocType,
    overall_confidence: float,
    status: DocStatus,
    math_result: MathResult,
    issues: list[Issue | dict[str, Any]],
) -> str:
    """Generate deterministic template-driven AI audit summary with Granite-generated anomaly clause.
    
    Format:
    Extracted at {avg_confidence}% avg confidence. Math {validated|mismatched|skipped} ({delta if any}).
    Routed to {status}. {anomaly_note}
    """
    avg_conf_pct = round(overall_confidence * 100, 1)

    # Format deterministic Math portion
    if math_result.status == "passed":
        math_str = "Math validated"
    elif math_result.status == "mismatched":
        math_str = f"Math mismatched (Δ ${math_result.delta:.2f})"
    else:
        math_str = "Math skipped (N/A)"

    # Determine anomaly note via IBM Granite or rule heuristic
    anomaly_note = "No anomalies detected."
    error_issues = [
        issue.message if isinstance(issue, Issue) else issue.get("message", "")
        for issue in issues
    ]

    if error_issues:
        issues_summary = "; ".join(error_issues)
        if watsonx_client.is_configured:
            try:
                prompt = AUDIT_SUMMARY_PROMPT_TEMPLATE.format(
                    doc_type=doc_type.value,
                    avg_confidence=avg_conf_pct,
                    math_status=math_result.status,
                    math_details=math_result.reason,
                    status=status.value,
                    issues_summary=issues_summary,
                )
                llm_note = watsonx_client.generate_text(prompt, max_tokens=100, retries=1).strip()
                if llm_note and len(llm_note) > 3:
                    anomaly_note = llm_note.strip("\"' \n")
            except Exception as exc:
                logger.warning("Granite audit summary generation failed: %s", exc)
                anomaly_note = f"Identified issues: {issues_summary}."
        else:
            anomaly_note = f"Flagged: {issues_summary}."

    # Assemble structured template
    summary = (
        f"Extracted at {avg_conf_pct}% avg confidence. {math_str}. "
        f"Routed to {status.value}. {anomaly_note}"
    )
    return summary
