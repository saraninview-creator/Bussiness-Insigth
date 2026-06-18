"""
Data Profiling Module — profiles an uploaded CSV/Excel file
and returns a structured profile dict.
"""
import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def _detect_column_type(series: pd.Series) -> str:
    """Auto-detect column type: datetime, numeric, categorical, id_like, text."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        n_unique = series.nunique()
        if n_unique / max(len(series), 1) > 0.95 and n_unique > 100:
            return "id_like"
        return "numeric"
    # Try parsing as datetime
    sample = series.dropna().head(50)
    try:
        pd.to_datetime(sample, infer_datetime_format=True)
        return "datetime"
    except Exception:
        pass
    n_unique = series.nunique()
    total = len(series.dropna())
    if total == 0:
        return "text"
    ratio = n_unique / total
    avg_len = series.dropna().astype(str).str.len().mean() if total else 0
    if ratio < 0.05 or n_unique <= 20:
        return "categorical"
    if ratio > 0.95 and avg_len > 15:
        return "id_like"
    if avg_len > 40:
        return "text"
    return "categorical"


def _safe(val):
    """Make a value JSON-serializable."""
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val) if not np.isnan(val) else None
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, pd.Timestamp):
        return str(val)
    return val


def profile_data(filepath: str) -> dict[str, Any]:
    """Load and profile a CSV/Excel file. Returns a profile dict."""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(filepath, low_memory=False)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Try to parse date columns
    for col in df.columns:
        if df[col].dtype == object:
            try:
                parsed = pd.to_datetime(df[col], infer_datetime_format=True)
                if parsed.notna().sum() / max(len(df), 1) > 0.7:
                    df[col] = parsed
            except Exception:
                pass

    n_rows, n_cols = df.shape
    dup_count = int(df.duplicated().sum())

    columns = {}
    for col in df.columns:
        s = df[col]
        col_type = _detect_column_type(s)
        missing_count = int(s.isna().sum())
        missing_pct = round(missing_count / max(n_rows, 1) * 100, 2)
        n_unique = int(s.nunique())

        info: dict[str, Any] = {
            "type": col_type,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "unique_count": n_unique,
        }

        if col_type == "numeric":
            valid = s.dropna()
            if len(valid) > 0:
                q1 = float(valid.quantile(0.25))
                q3 = float(valid.quantile(0.75))
                iqr = q3 - q1
                lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                outlier_mask = (valid < lower) | (valid > upper)
                info.update(
                    {
                        "mean": _safe(valid.mean()),
                        "median": _safe(valid.median()),
                        "std": _safe(valid.std()),
                        "min": _safe(valid.min()),
                        "max": _safe(valid.max()),
                        "q1": q1,
                        "q3": q3,
                        "iqr": iqr,
                        "outlier_count": int(outlier_mask.sum()),
                        "outlier_pct": round(outlier_mask.sum() / max(len(valid), 1) * 100, 2),
                        "outlier_lower": lower,
                        "outlier_upper": upper,
                        "sample_values": [_safe(v) for v in valid.head(20).tolist()],
                    }
                )

        elif col_type == "datetime":
            valid = s.dropna()
            if len(valid) > 0:
                try:
                    valid_dt = pd.to_datetime(valid)
                    sorted_dt = valid_dt.sort_values()
                    # Build time series: group by week
                    if hasattr(df, "index"):
                        # find numeric column to pair with for time series
                        num_cols = [c for c in df.columns if _detect_column_type(df[c]) == "numeric"]
                        ts_data = {}
                        for nc in num_cols[:2]:
                            temp = pd.DataFrame({"dt": valid_dt, "val": df.loc[valid.index, nc]})
                            temp = temp.dropna()
                            temp = temp.set_index("dt").resample("W")["val"].sum().reset_index()
                            if len(temp) >= 2:
                                first = float(temp["val"].iloc[0])
                                last = float(temp["val"].iloc[-1])
                                pct_change = round((last - first) / max(abs(first), 1e-9) * 100, 2)
                                peak_idx = int(temp["val"].idxmax())
                                trough_idx = int(temp["val"].idxmin())
                                ts_data[nc] = {
                                    "labels": [str(d)[:10] for d in temp["dt"].tolist()],
                                    "values": [_safe(v) for v in temp["val"].tolist()],
                                    "pct_change": pct_change,
                                    "peak_week": str(temp["dt"].iloc[peak_idx])[:10],
                                    "trough_week": str(temp["dt"].iloc[trough_idx])[:10],
                                    "first_value": first,
                                    "last_value": last,
                                }
                        info["time_series"] = ts_data
                    info["min_date"] = str(sorted_dt.iloc[0])[:10]
                    info["max_date"] = str(sorted_dt.iloc[-1])[:10]
                except Exception:
                    pass

        elif col_type == "categorical":
            vc = s.value_counts()
            top = vc.head(10)
            total_non_null = s.notna().sum()
            info["top_categories"] = [
                {"value": str(k), "count": int(v), "pct": round(v / max(total_non_null, 1) * 100, 2)}
                for k, v in top.items()
            ]
            if len(vc) > 0:
                dominant = top.iloc[0]
                info["dominant_category"] = str(top.index[0])
                info["dominant_pct"] = round(dominant / max(total_non_null, 1) * 100, 2)
            # Check inconsistent formatting (mixed case)
            str_col = s.dropna().astype(str)
            lower_unique = str_col.str.lower().nunique()
            actual_unique = str_col.nunique()
            info["inconsistent_formatting"] = actual_unique > lower_unique

        columns[col] = info

    # Correlations between numeric columns
    num_cols = [c for c in df.columns if columns.get(c, {}).get("type") == "numeric"]
    correlations = []
    if len(num_cols) >= 2:
        corr_matrix = df[num_cols].corr(method="pearson")
        seen = set()
        for i, c1 in enumerate(num_cols):
            for j, c2 in enumerate(num_cols):
                if i >= j:
                    continue
                key = tuple(sorted([c1, c2]))
                if key in seen:
                    continue
                seen.add(key)
                r = corr_matrix.loc[c1, c2]
                if pd.notna(r) and abs(r) > 0.5:
                    correlations.append(
                        {
                            "col1": c1,
                            "col2": c2,
                            "r": round(float(r), 4),
                            "abs_r": round(abs(float(r)), 4),
                            "direction": "positive" if r > 0 else "negative",
                        }
                    )
        correlations.sort(key=lambda x: -x["abs_r"])

    # ── Advanced Analyst AI (Clustering & Predictive) ──────────────────────
    advanced = {}
    if len(num_cols) >= 2:
        try:
            from sklearn.cluster import KMeans
            from sklearn.linear_model import LinearRegression
            from sklearn.preprocessing import StandardScaler
            
            # Use top numeric columns with fewest NaNs
            selected_features = num_cols[:5]
            ml_df = df[selected_features].dropna()
            if len(ml_df) > 20:
                # 1. Clustering
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(ml_df)
                kmeans = KMeans(n_clusters=3, random_state=42, n_init="auto").fit(scaled_data)
                ml_df["cluster"] = kmeans.labels_
                
                cluster_sizes = ml_df["cluster"].value_counts().to_dict()
                advanced["clustering"] = {
                    "num_clusters": 3,
                    "features_used": selected_features,
                    "sizes": {str(k): int(v) for k, v in cluster_sizes.items()}
                }
                
                # 2. Predictive Models (Linear Regression on most correlated pair)
                if correlations:
                    top_corr = correlations[0]
                    c1, c2 = top_corr["col1"], top_corr["col2"]
                    X = ml_df[[c1]]
                    y = ml_df[c2]
                    lr = LinearRegression().fit(X, y)
                    r2 = lr.score(X, y)
                    coef = lr.coef_[0]
                    advanced["predictive"] = {
                        "target": c2,
                        "predictor": c1,
                        "r2": round(float(r2), 4),
                        "coefficient": round(float(coef), 4)
                    }
        except ImportError:
            pass
        except Exception as e:
            print("Advanced analytics exception:", e)

    return {
        "filename": path.name,
        "n_rows": n_rows,
        "n_cols": n_cols,
        "duplicate_rows": dup_count,
        "columns": columns,
        "correlations": correlations,
        "advanced_analytics": advanced,
    }


if __name__ == "__main__":
    import sys
    result = profile_data(sys.argv[1])
    print(json.dumps(result, indent=2, default=str))
