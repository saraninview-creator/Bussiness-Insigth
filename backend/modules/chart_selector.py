"""
Chart Type Selector — maps each finding to a chart type
and builds the chart_data dict for Remotion scene rendering.
"""
from __future__ import annotations

from typing import Any


def select_chart(finding: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Return {chart_type, chart_data} for a finding."""
    source = finding.get("source", "")
    meta = finding.get("meta", {})
    columns = profile.get("columns", {})

    # ── Time trend → line chart ─────────────────────────────────────────────
    if source == "trend":
        labels = meta.get("labels", [])
        values = meta.get("values", [])
        peak_week = meta.get("peak_week", "")
        highlight_idx = labels.index(peak_week) if peak_week in labels else len(labels) - 1
        return {
            "chart_type": "line",
            "chart_data": {
                "labels": labels,
                "series": values,
                "highlight_idx": highlight_idx,
                "y_label": meta.get("num_col", "Value"),
                "x_label": meta.get("date_col", "Date"),
                "pct_change": meta.get("pct_change", 0),
            },
        }

    # ── Category concentration → bar chart ─────────────────────────────────
    if source == "concentration":
        top_cats = meta.get("top_categories", [])
        labels = [c["value"] for c in top_cats]
        values = [c["pct"] for c in top_cats]
        dominant = meta.get("dominant_cat", "")
        return {
            "chart_type": "bar",
            "chart_data": {
                "labels": labels,
                "values": values,
                "highlight_label": dominant,
                "y_label": "Share (%)",
                "x_label": meta.get("col", "Category"),
            },
        }

    # ── Missing data → stat card ────────────────────────────────────────────
    if source == "missing":
        col = meta.get("col", "Column")
        col_info = columns.get(col, {})
        return {
            "chart_type": "stat_card",
            "chart_data": {
                "stat_label": "Missing Values",
                "stat_value": f"{meta.get('missing_pct', 0):.1f}%",
                "sub_label": "Affected Records",
                "sub_value": f"{meta.get('missing_count', 0):,}",
                "column": col,
                "total_rows": profile.get("n_rows", 0),
            },
        }

    # ── Duplicate rows → stat card ──────────────────────────────────────────
    if source == "duplicates":
        return {
            "chart_type": "stat_card",
            "chart_data": {
                "stat_label": "Duplicate Rows",
                "stat_value": f"{meta.get('dup_count', 0):,}",
                "sub_label": "Duplicate Rate",
                "sub_value": f"{meta.get('dup_pct', 0):.1f}%",
                "column": "Dataset",
                "total_rows": profile.get("n_rows", 0),
            },
        }

    # ── Outliers → histogram (use sample_values) ────────────────────────────
    if source == "outliers":
        col = meta.get("col", "")
        col_info = columns.get(col, {})
        sample = col_info.get("sample_values", [])
        sample = [v for v in sample if v is not None]
        # Build approximate histogram bins (10 bins)
        if sample:
            mn, mx = min(sample), max(sample)
            if mx > mn:
                bin_size = (mx - mn) / 10
                bins = [round(mn + i * bin_size, 2) for i in range(11)]
                counts = [0] * 10
                for v in sample:
                    idx = min(int((v - mn) / max(bin_size, 1e-9)), 9)
                    counts[idx] += 1
                outlier_lower = col_info.get("outlier_lower", mn)
                outlier_upper = col_info.get("outlier_upper", mx)
            else:
                bins = [mn, mx + 1]
                counts = [len(sample)]
                outlier_lower, outlier_upper = mn, mx
        else:
            bins, counts, outlier_lower, outlier_upper = [], [], 0, 0

        return {
            "chart_type": "histogram",
            "chart_data": {
                "bins": bins,
                "counts": counts,
                "outlier_lower": outlier_lower,
                "outlier_upper": outlier_upper,
                "column": col,
                "mean": col_info.get("mean"),
                "std": col_info.get("std"),
            },
        }

    # ── Correlation → scatter chart ─────────────────────────────────────────
    if source == "correlation":
        c1 = meta.get("col1", "")
        c2 = meta.get("col2", "")
        col1_info = columns.get(c1, {})
        col2_info = columns.get(c2, {})
        s1 = col1_info.get("sample_values", [])
        s2 = col2_info.get("sample_values", [])
        points = []
        for x, y in zip(s1[:30], s2[:30]):
            if x is not None and y is not None:
                points.append({"x": x, "y": y})
        return {
            "chart_type": "scatter",
            "chart_data": {
                "points": points,
                "x_label": c1,
                "y_label": c2,
                "r": meta.get("r", 0),
                "direction": meta.get("direction", "positive"),
            },
        }

    # ── Fallback → stat card ────────────────────────────────────────────────
    return {
        "chart_type": "stat_card",
        "chart_data": {
            "stat_label": finding.get("type", "Finding").title(),
            "stat_value": "–",
            "sub_label": finding.get("text", "")[:60],
            "sub_value": "",
            "column": "",
            "total_rows": profile.get("n_rows", 0),
        },
    }


def enrich_findings(findings: list[dict], profile: dict) -> list[dict]:
    """Add chart_type and chart_data to each finding in-place."""
    for f in findings:
        chart = select_chart(f, profile)
        f["chart_type"] = chart["chart_type"]
        f["chart_data"] = chart["chart_data"]
    return findings
