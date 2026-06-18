"""
Narration Script Generator — converts findings into ordered script segments.
Order: insights → problems → suggestions
Target total: 150-250 words.
"""
from __future__ import annotations

from typing import Any

# Approximate TTS speed in words per second
WPS = 2.5

TEMPLATES: dict[str, dict[str, str]] = {
    "trend_up": (
        "Strong business momentum: {num_col} surged {pct_change:.1f}% to {last_value:,.0f}. "
        "The pro is direct revenue growth; the con is potential scaling strain. Capitalize immediately."
    ),
    "trend_down": (
        "Critical risk alert: {num_col} dropped {pct_change:.1f}% to {last_value:,.0f}. "
        "This signals a clear negative trajectory. Immediate operational review needed to mitigate losses."
    ),
    "concentration_insight": (
        "Heavy reliance on {dominant_cat} ({dominant_pct:.1f}% of {col}). "
        "Pro: highly focused market. Con: immense dependency risk if conditions shift."
    ),
    "missing_problem": (
        "Data integrity warning: {col} is missing {missing_pct:.1f}% values. "
        "This gap directly undermines actionable business intelligence and predictive modeling accuracy."
    ),
    "duplicates_problem": (
        "Pipeline inefficiency: {dup_pct:.1f}% duplicate records detected. "
        "This inflates key metrics, creating false positives that misguide strategic business decisions."
    ),
    "outliers_problem": (
        "Anomaly detected: {outlier_count:,} outliers in {col}. "
        "Are these lucrative edge-cases or critical system errors? Requires immediate analyst triage."
    ),
    "correlation_insight": (
        "High-value relationship: {col1} and {col2} show a {r:.2f} {direction} correlation. "
        "As one moves, the other follows. Leverage this predictability for targeted business strategy."
    ),
    # Suggestions
    "trend_up_suggestion": (
        "Maximize ROI on {num_col} growth. Scale marketing spend and optimize fulfillment bottlenecks now."
    ),
    "trend_down_suggestion": (
        "Execute a turnaround on {num_col}. Audit pricing structures and initiate aggressive retention campaigns."
    ),
    "concentration_suggestion": (
        "Hedge {col} risk by diversifying beyond {dominant_cat} while extracting maximum yield from the current base."
    ),
    "missing_suggestion": (
        "Enforce strict validation on {col} at collection points to ensure clean downstream analytics."
    ),
    "duplicates_suggestion": (
        "Deploy deterministic deduplication logic. Protect your core metrics from artificial inflation."
    ),
    "outliers_suggestion": (
        "Isolate {col} anomalies. Treat them as either VIP opportunities or critical system warnings."
    ),
    "correlation_suggestion": (
        "Operationalize the {col1}-{col2} link. Feed this relationship directly into algorithmic forecasting."
    ),
}

TEMPLATES_21S: dict[str, dict[str, str]] = {
    "trend_up": "Bullish trend: {num_col} jumped {pct_change:.1f}% to {last_value:,.0f}. Strong ROI potential but watch scaling risks.",
    "trend_down": "Bearish signal: {num_col} fell {pct_change:.1f}%. Immediate operational audit required to stem losses.",
    "concentration_insight": "Market skew: {col} heavily tied to {dominant_cat} ({dominant_pct:.1f}%). Great for focus, highly risky if disrupted.",
    "missing_problem": "Analytics blocker: {missing_pct:.1f}% missing data in {col}. This directly sabotages executive decision-making.",
    "duplicates_problem": "Data bloat: {dup_pct:.1f}% duplicates. This artificially inflates KPIs and risks bad strategy.",
    "outliers_problem": "Critical anomalies: {outlier_count:,} outliers in {col}. High-priority triage needed: bug or massive opportunity?",
    "correlation_insight": "Strategic link: {col1} and {col2} are correlated (r={r:.2f}). Leverage this direct relationship to drive predictive action.",
    # If a suggestion somehow gets passed in 21s
    "trend_up_suggestion": "Capitalize on {num_col} now.",
    "trend_down_suggestion": "Audit and fix {num_col} immediately.",
    "concentration_suggestion": "Diversify away from {dominant_cat}.",
    "missing_suggestion": "Fix data capture for {col}.",
    "duplicates_suggestion": "Cleanse duplicates to fix KPIs.",
    "outliers_suggestion": "Triage {col} outliers ASAP.",
    "correlation_suggestion": "Use {col1}-{col2} link for modeling."
}


def _fill(template_key: str, meta: dict, explanation_level: str) -> str:
    # Use shorter templates for 21s cut
    target_templates = TEMPLATES_21S if "21s" in explanation_level else TEMPLATES
    template = target_templates.get(template_key, "{text}")
    try:
        # Inject move direction for correlation
        if "col1" in meta:
            meta = dict(meta, move="increase" if meta.get("direction") == "positive" else "decrease")
        return template.format(**meta)
    except (KeyError, ValueError):
        return template


def _duration(text: str) -> float:
    word_count = len(text.split())
    return round(word_count / WPS, 1)


def generate_script(findings: list[dict[str, Any]], explanation_level: str = "concise_21s") -> list[dict[str, Any]]:
    """
    Generate one script segment per finding.
    Returns list of {finding_id, text, estimated_duration_seconds}.
    """
    segments = []
    for f in findings:
        source = f.get("source", "")
        f_type = f.get("type", "insight")
        meta = f.get("meta", {})

        # Resolve template key
        key = None
        if source == "trend":
            direction = meta.get("direction", "up")
            if f_type == "insight":
                key = f"trend_{direction}"
            else:
                key = f"trend_{direction}_suggestion"
        elif source == "concentration":
            key = "concentration_insight" if f_type == "insight" else "concentration_suggestion"
        elif source == "missing":
            key = "missing_problem" if f_type == "problem" else "missing_suggestion"
        elif source == "duplicates":
            key = "duplicates_problem" if f_type == "problem" else "duplicates_suggestion"
        elif source == "outliers":
            key = "outliers_problem" if f_type == "problem" else "outliers_suggestion"
        elif source == "correlation":
            key = "correlation_insight" if f_type == "insight" else "correlation_suggestion"

        if key and key in (TEMPLATES_21S if "21s" in explanation_level else TEMPLATES):
            text = _fill(key, meta, explanation_level)
        else:
            text = f.get("text", "")

        segments.append(
            {
                "finding_id": f.get("id", ""),
                "finding_type": f_type,
                "text": text,
                "estimated_duration_seconds": _duration(text),
                "word_count": len(text.split()),
            }
        )

    return segments
