"""
Findings Generator — Converts a dataset into actionable findings using statistical heuristics.
No LLM used; Relies on pandas and scipy.stats for deterministic reasoning.
"""
from __future__ import annotations

import uuid
from typing import Any

import pandas as pd
import numpy as np
from scipy import stats

def _fid() -> str:
    return str(uuid.uuid4())[:8]


class FindingsEngine:
    def __init__(self, filepath: str, explanation_level: str):
        self.filepath = filepath
        self.explanation_level = explanation_level
        # Load the dataset intelligently
        if str(filepath).lower().endswith(".csv"):
            self.df = pd.read_csv(filepath)
        else:
            self.df = pd.read_excel(filepath)
            
        # Auto-parse datetime columns from objects using pandas heuristics
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                try:
                    # Attempt safe datetime conversion utilizing user-defined coerce logic
                    parsed = pd.to_datetime(self.df[col], errors='coerce')
                    if not parsed.isna().all():
                        self.df[col] = parsed.dt.tz_localize('UTC')
                except Exception:
                    pass

    def get_time_series_trends(self) -> list[dict]:
        """Calculate slopes to say 'Sales are trending up by X%'"""
        findings = []
        date_cols = self.df.select_dtypes(include=['datetime', 'datetimetz']).columns
        num_cols = self.df.select_dtypes(include=['number']).columns
        
        if len(date_cols) == 0 or len(num_cols) == 0:
            return findings
            
        date_col = date_cols[0] # Pick the first available date column
        df_sorted = self.df.sort_values(by=date_col).dropna(subset=[date_col])
        
        # Group by Month to smooth noise and enable robust linear regression
        df_grouped = df_sorted.groupby(df_sorted[date_col].dt.to_period('M')).sum(numeric_only=True)
        
        if len(df_grouped) < 3:
            return findings
            
        x = np.arange(len(df_grouped))
        
        for col in num_cols:
            if col not in df_grouped.columns:
                continue
            y = df_grouped[col].values
            if y.std() == 0:
                continue
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            if p_value < 0.15: # 85% confidence in trend existence
                start_val = intercept
                end_val = slope * x[-1] + intercept
                
                if abs(start_val) > 0.001:
                    pct_change = ((end_val - start_val) / abs(start_val)) * 100
                else:
                    pct_change = 0
                    
                if abs(pct_change) > 5:
                    direction = 'up' if slope > 0 else 'down'
                    findings.append({
                        "id": _fid(),
                        "type": "insight" if slope > 0 else "problem",
                        "score": 85 if slope > 0 else 90,
                        "source": "trend",
                        "text": (
                            f"Trend detected: '{col}' heavily trended {direction}ward by "
                            f"{abs(pct_change):.1f}% over the captured time period. "
                            f"Moving from ~{start_val:.0f} to ~{end_val:.0f}."
                        ),
                        "meta": {
                            "date_col": date_col,
                            "num_col": col,
                            "pct_change": pct_change,
                            "direction": direction,
                            "last_value": float(y[-1]) if len(y) > 0 else 0.0
                        }
                    })
        return findings

    def get_correlation_insights(self) -> list[dict]:
        """Matrix correlation analysis between numeric columns."""
        findings = []
        num_df = self.df.select_dtypes(include=['number'])
        if num_df.shape[1] < 2:
            return findings
            
        corr_matrix = num_df.corr()
        # Find high correlations (abs > 0.7)
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                r = corr_matrix.iloc[i, j]
                
                if abs(r) > 0.7:
                    findings.append({
                        "id": _fid(),
                        "type": "insight",
                        "score": int(abs(r) * 100),
                        "source": "correlation",
                        "text": f"High correlation found: '{col1}' and '{col2}' move together (r={r:.2f}). This indicates a strong statistical dependency.",
                        "meta": {"col1": col1, "col2": col2, "r": r}
                    })
        return findings

    def get_trend_suggestions(self) -> list[dict]:
        """Generate specific suggestions based on data profile."""
        suggestions = []
        num_cols = self.df.select_dtypes(include=['number']).columns
        
        for col in num_cols:
            avg = self.df[col].mean()
            std = self.df[col].std()
            
            # Suggest dynamic pricing or outlier trimming if volatility is high
            if avg != 0 and (std / avg) > 0.5:
                suggestions.append({
                    "id": _fid(),
                    "type": "suggestion",
                    "score": 70,
                    "source": "volatility",
                    "text": f"High volatility in '{col}': We suggest implementing dynamic pricing filters and establishing outlier trimming thresholds to stabilize reporting.",
                    "meta": {"col": col, "coefficient_of_variation": (std / avg)}
                })
        return suggestions

    def get_anomalies(self) -> list[dict]:
        """Anomaly detection using Z-scores > 2 to find outliers."""
        findings = []
        # Target specific columns requested by user if they exist
        target_cols = ['currentPrice', 'previousClose']
        num_cols = [c for c in target_cols if c in self.df.columns]
        if not num_cols:
            num_cols = self.df.select_dtypes(include=['number']).columns
        
        for col in num_cols:
            data = self.df[col].dropna()
            if len(data) < 5: continue
            
            z_scores = np.abs(stats.zscore(data))
            outliers = data[z_scores > 2.5] # Tighter threshold for 'Severe' tracking
            
            if len(outliers) > 0:
                findings.append({
                    "id": _fid(),
                    "type": "problem",
                    "score": 90,
                    "source": "outliers",
                    "text": f"Severe statistical outlier tracking: '{col}' contains {len(outliers)} dramatic spikes that deviate from mean bands by >2.5 standard deviations.",
                    "meta": {"col": col, "outlier_count": len(outliers)}
                })
        return findings

    def get_categorical_dominance(self) -> list[dict]:
        """Categorical dominance (finding if one category makes up >50% of the total)."""
        findings = []
        cat_cols = self.df.select_dtypes(exclude=['number', 'datetime', 'datetimetz']).columns
        
        total_rows = len(self.df)
        if total_rows == 0: return findings
            
        for col in cat_cols:
            if self.df[col].nunique() > 100: continue
                
            counts = self.df[col].value_counts()
            if len(counts) == 0: continue
                
            top_cat = counts.index[0]
            top_pct = (counts.iloc[0] / total_rows) * 100
            
            if top_pct > 50:
                findings.append({
                    "id": _fid(),
                    "type": "insight",
                    "score": 75,
                    "source": "concentration",
                    "text": f"Severe concentration detected: '{top_cat}' dominates the '{col}' category, accounting for {top_pct:.1f}% of all records.",
                    "meta": {"col": col, "dominant_cat": str(top_cat), "dominant_pct": top_pct}
                })
        return findings

    def generate(self) -> list[dict]:
        findings = []
        findings.extend(self.get_time_series_trends())
        findings.extend(self.get_anomalies())
        findings.extend(self.get_categorical_dominance())
        findings.extend(self.get_correlation_insights())
        findings.extend(self.get_trend_suggestions())
        
        findings.sort(key=lambda f: -f["score"])
        
        if "21s" in self.explanation_level:
            return findings[:2]
        if "65s" in self.explanation_level:
            return findings[:12]
            
        return findings[:6]


def generate_findings(filepath: str, profile: dict, explanation_level: str = "concise_21s") -> list[dict]:
    """Exposed method for the Pipeline Orchestrator."""
    engine = FindingsEngine(filepath, explanation_level)
    return engine.generate()


def generate_findings(filepath: str, profile: dict, explanation_level: str = "concise_21s") -> list[dict]:
    """Exposed method for the Pipeline Orchestrator."""
    engine = FindingsEngine(filepath, explanation_level)
    return engine.generate()
