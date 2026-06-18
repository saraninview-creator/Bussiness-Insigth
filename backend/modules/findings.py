"""
Findings Generator — converts a data profile into a ranked list
of actionable findings (insight / problem / suggestion).
"""
from __future__ import annotations

import uuid
from typing import Any


def _fid() -> str:
    return str(uuid.uuid4())[:8]


def generate_findings(profile: dict[str, Any], explanation_level: str = "concise_21s") -> list[dict[str, Any]]:
    """Apply rule-based analysis to a profile dict and return ranked findings."""
    findings: list[dict[str, Any]] = []
    columns = profile.get("columns", {})
    correlations = profile.get("correlations", [])
    dup_count = profile.get("duplicate_rows", 0)
    n_rows = profile.get("n_rows", 1)

    # ── RULE: Duplicate rows ────────────────────────────────────────────────
    if dup_count > 0:
        dup_pct = round(dup_count / max(n_rows, 1) * 100, 1)
        findings.append(
            {
                "id": _fid(),
                "type": "problem",
                "score": 90,
                "text": (
                    f"Found {dup_count:,} duplicate rows ({dup_pct}% of the dataset). "
                    "Duplicates can skew calculations, inflate metrics, and produce misleading aggregations."
                ),
                "source": "duplicates",
                "meta": {"dup_count": dup_count, "dup_pct": dup_pct},
            }
        )
        findings.append(
            {
                "id": _fid(),
                "type": "suggestion",
                "score": 72,
                "text": (
                    f"Implement a deduplication step in your data pipeline to remove the {dup_count:,} duplicate rows. "
                    "Consider using a composite key of unique identifiers before aggregating."
                ),
                "source": "duplicates",
                "meta": {"dup_count": dup_count},
            }
        )

    # ── Column-level rules ──────────────────────────────────────────────────
    for col, info in columns.items():
        col_type = info.get("type")

        # RULE: Missing data > 5%
        missing_pct = info.get("missing_pct", 0)
        missing_count = info.get("missing_count", 0)
        if missing_pct > 5:
            score = min(95, 50 + int(missing_pct))
            findings.append(
                {
                    "id": _fid(),
                    "type": "problem",
                    "score": score,
                    "text": (
                        f"Column '{col}' has {missing_pct}% missing values ({missing_count:,} records). "
                        "This level of missing data can bias analysis and reduce model accuracy."
                    ),
                    "source": "missing",
                    "col": col,
                    "meta": {"missing_pct": missing_pct, "missing_count": missing_count, "col": col},
                }
            )
            findings.append(
                {
                    "id": _fid(),
                    "type": "suggestion",
                    "score": score - 15,
                    "text": (
                        f"Review data collection for '{col}' — {missing_pct}% gaps suggest a systemic capture issue. "
                        "Consider imputation with median/mode for non-critical fields, or flag rows for exclusion."
                    ),
                    "source": "missing",
                    "col": col,
                    "meta": {"missing_pct": missing_pct, "col": col},
                }
            )

        # RULE: Numeric — outliers
        if col_type == "numeric":
            outlier_pct = info.get("outlier_pct", 0)
            outlier_count = info.get("outlier_count", 0)
            if outlier_pct > 2:
                findings.append(
                    {
                        "id": _fid(),
                        "type": "problem",
                        "score": 70,
                        "text": (
                            f"Column '{col}' contains {outlier_count:,} statistical outliers ({outlier_pct}% of values), "
                            f"ranging outside [{info.get('outlier_lower', 0):.2f}, {info.get('outlier_upper', 0):.2f}]. "
                            "These may indicate data entry errors or genuine anomalies."
                        ),
                        "source": "outliers",
                        "col": col,
                        "meta": {
                            "col": col,
                            "outlier_count": outlier_count,
                            "outlier_pct": outlier_pct,
                            "mean": info.get("mean"),
                            "std": info.get("std"),
                            "min": info.get("min"),
                            "max": info.get("max"),
                            "sample_values": info.get("sample_values", []),
                        },
                    }
                )
                findings.append(
                    {
                        "id": _fid(),
                        "type": "suggestion",
                        "score": 55,
                        "text": (
                            f"Investigate the {outlier_count:,} outliers in '{col}'. "
                            "Validate if extreme values are legitimate (e.g., bulk orders) or errors. "
                            "Apply Winsorization or exclusion rules before modeling."
                        ),
                        "source": "outliers",
                        "col": col,
                        "meta": {"col": col, "outlier_count": outlier_count},
                    }
                )

        # RULE: Datetime — trends
        if col_type == "datetime":
            ts = info.get("time_series", {})
            for num_col, ts_info in ts.items():
                pct_change = ts_info.get("pct_change", 0)
                if abs(pct_change) >= 10 and len(ts_info.get("labels", [])) >= 3:
                    direction = "up" if pct_change > 0 else "down"
                    findings.append(
                        {
                            "id": _fid(),
                            "type": "insight",
                            "score": 85,
                            "text": (
                                f"'{num_col}' shows a {abs(pct_change):.1f}% {direction}ward trend over the analysis period "
                                f"(from {ts_info['first_value']:,.1f} to {ts_info['last_value']:,.1f}), "
                                f"peaking on {ts_info['peak_week']}."
                            ),
                            "source": "trend",
                            "col": col,
                            "meta": {
                                "num_col": num_col,
                                "date_col": col,
                                "pct_change": pct_change,
                                "direction": direction,
                                "labels": ts_info["labels"],
                                "values": ts_info["values"],
                                "peak_week": ts_info["peak_week"],
                                "trough_week": ts_info["trough_week"],
                            },
                        }
                    )
                    if direction == "up":
                        findings.append(
                            {
                                "id": _fid(),
                                "type": "suggestion",
                                "score": 70,
                                "text": (
                                    f"'{num_col}' grew {abs(pct_change):.1f}%. "
                                    "Capitalize on this momentum — increase investment, scale operations, "
                                    "and analyze what drove the peak to replicate it."
                                ),
                                "source": "trend",
                                "col": col,
                                "meta": {"num_col": num_col, "pct_change": pct_change},
                            }
                        )
                    else:
                        findings.append(
                            {
                                "id": _fid(),
                                "type": "suggestion",
                                "score": 70,
                                "text": (
                                    f"'{num_col}' declined {abs(pct_change):.1f}%. "
                                    "Investigate root causes — pricing pressure, churn, or seasonality — "
                                    "and implement corrective actions urgently."
                                ),
                                "source": "trend",
                                "col": col,
                                "meta": {"num_col": num_col, "pct_change": pct_change},
                            }
                        )

        # RULE: Categorical — dominant category > 30%
        if col_type == "categorical":
            dominant_pct = info.get("dominant_pct", 0)
            dominant_cat = info.get("dominant_category", "")
            top_cats = info.get("top_categories", [])
            if dominant_pct > 30 and dominant_cat:
                findings.append(
                    {
                        "id": _fid(),
                        "type": "insight",
                        "score": 75,
                        "text": (
                            f"'{col}' is highly concentrated: '{dominant_cat}' accounts for {dominant_pct:.1f}% of all records. "
                            f"The top 3 categories make up {sum(c['pct'] for c in top_cats[:3]):.1f}% of the data."
                        ),
                        "source": "concentration",
                        "col": col,
                        "meta": {
                            "col": col,
                            "dominant_cat": dominant_cat,
                            "dominant_pct": dominant_pct,
                            "top_categories": top_cats[:8],
                        },
                    }
                )
                findings.append(
                    {
                        "id": _fid(),
                        "type": "suggestion",
                        "score": 60,
                        "text": (
                            f"'{dominant_cat}' dominates '{col}' at {dominant_pct:.1f}%. "
                            "Evaluate whether to double down on this segment for efficiency, "
                            "or diversify to reduce concentration risk."
                        ),
                        "source": "concentration",
                        "col": col,
                        "meta": {"col": col, "dominant_cat": dominant_cat, "dominant_pct": dominant_pct},
                    }
                )

    # ── RULE: Strong correlations ───────────────────────────────────────────
    for corr in correlations[:3]:
        r = corr["r"]
        c1, c2 = corr["col1"], corr["col2"]
        direction = corr["direction"]
        findings.append(
            {
                "id": _fid(),
                "type": "insight",
                "score": 65,
                "text": (
                    f"Strong {direction} correlation detected between '{c1}' and '{c2}' (r = {r:.2f}). "
                    f"As '{c1}' increases, '{c2}' tends to {'increase' if direction == 'positive' else 'decrease'} proportionally."
                ),
                "source": "correlation",
                "meta": {
                    "col1": c1,
                    "col2": c2,
                    "r": r,
                    "direction": direction,
                },
            }
        )
        findings.append(
            {
                "id": _fid(),
                "type": "suggestion",
                "score": 50,
                "text": (
                    f"Leverage the {direction} link between '{c1}' and '{c2}' (r={r:.2f}). "
                    "Use this relationship for predictive modeling, forecasting, or bundling decisions."
                ),
                "source": "correlation",
                "meta": {"col1": c1, "col2": c2, "r": r},
            }
        )

    # ── RULE: Advanced Analyst AI (Clustering & Predictive Models) ───────────
    adv = profile.get("advanced_analytics", {})
    if adv.get("clustering"):
        cinfo = adv["clustering"]
        sizes = cinfo["sizes"]
        max_cluster_size = max(sizes.values())
        findings.append({
            "id": _fid(),
            "type": "insight",
            "score": 98,  # very high score to ensure it's picked for the pitch
            "text": (
                f"Analyst AI clustered the data into {cinfo['num_clusters']} distinct segments based on {len(cinfo['features_used'])} metrics. "
                f"The largest segment contains {max_cluster_size} records, revealing distinct behavioral tiers that a generic analysis would miss."
            ),
            "source": "clustering",
            "meta": cinfo
        })
        findings.append({
            "id": _fid(),
            "type": "suggestion",
            "score": 85,
            "text": (
                f"Tailor business strategies to the {cinfo['num_clusters']} identified clusters. "
                "Targeting these segments individually yields higher engagement and operational efficiency than a one-size-fits-all approach."
            ),
            "source": "clustering",
            "meta": cinfo
        })

    if adv.get("predictive"):
        pinfo = adv["predictive"]
        findings.append({
            "id": _fid(),
            "type": "insight",
            "score": 96,
            "text": (
                f"Our AI predictive model trained on '{pinfo['predictor']}' to forecast '{pinfo['target']}'. "
                f"It achieved an R² of {pinfo['r2']:.2f}, showing that every unit increase in {pinfo['predictor']} shifts the target by {pinfo['coefficient']:.2f}."
            ),
            "source": "predictive",
            "meta": pinfo
        })
        findings.append({
            "id": _fid(),
            "type": "suggestion",
            "score": 88,
            "text": (
                f"Leverage the predictive model on '{pinfo['target']}' to accurately forecast outcomes. "
                f"By optimizing '{pinfo['predictor']}', decision makers can directly manipulate and predict the '{pinfo['target']}' metric."
            ),
            "source": "predictive",
            "meta": pinfo
        })

    # ── Sort by score and filter findings based on explanation level ─────────
    # We want strong analyst pitch in the script. The script generator will handle the pitch.
    findings.sort(key=lambda f: -f["score"])

    selected: list[dict] = []
    
    if "21s" in explanation_level:
        # For a 21 second limit, we can only fit 1-2 findings
        # Pick the absolute highest scoring insight or problem.
        for t in ("insight", "problem"):
            hits = [f for f in findings if f["type"] == t]
            if hits:
                selected.append(hits[0])
                break
        
        # Add a strong analyst pitch summary recommendation if space allows
        suggestions = [f for f in findings if f["type"] == "suggestion"]
        if suggestions and len(selected) < 2:
            selected.append(suggestions[0])
    else:
        # Ensure we have at least one of each type for a balanced video
        for t in ("insight", "problem", "suggestion"):
            hits = [f for f in findings if f["type"] == t]
            for h in hits[:2]:
                if h not in selected:
                    selected.append(h)

        # Fill up to 6
        for f in findings:
            if f not in selected:
                selected.append(f)
            if len(selected) >= 6:
                break

    # Final ordering for script: insights -> problems -> suggestions
    order = {"insight": 0, "problem": 1, "suggestion": 2}
    selected.sort(key=lambda f: order[f["type"]])

    return selected
