# =============================
# File: metrics.py
# =============================
from __future__ import annotations

import numpy as np
import pandas as pd

# 색상 팔레트(차트 공통 사용)
COLORS = {
    "progressive": "#E45756",
    "conservative": "#4C78A8",
    "centrist": "#72B7B2",
    "others": "#A0A0A0",
}

def compute_trend_series(df_trend: pd.DataFrame, code: str) -> pd.DataFrame:
    """주어진 선거구(code)에 대한 정당성향별 득표 추이 시계열을 반환."""
    if df_trend is None or len(df_trend) == 0:
        return pd.DataFrame()
    code_str = str(code)
    if "코드" in df_trend.columns:
        out = df_trend[df_trend["코드"].astype(str) == code_str].copy()
    else:
        out = df_trend.iloc[0:0].copy()
    return out

def compute_24_gap(df_24: pd.DataFrame, code: str) -> float or None:
    """2024 총선에서 1위-2위 득표율 격차를 계산 (가능할 때만)."""
    try:
        row24 = df_24[df_24["코드"].astype(str) == str(code)]
        if not row24.empty and {"1위득표율", "2위득표율"}.issubset(row24.columns):
            gap = float(row24.iloc[0]["1위득표율"]) - float(row24.iloc[0]["2위득표율"])
            return round(gap, 2)
    except Exception:
        pass
    return None

def compute_summary_metrics(
    df_trend: pd.DataFrame,
    df_24: pd.DataFrame,
    df_idx: pd.DataFrame,
    code: str,
) -> dict:
    """
    요약 지표 반환:
    - PL_prg_str: 진보정당 득표력(%) [외부지표 있으면 사용, 없으면 NaN]
    - PL_swing_B: 유동성 등급(문자) [외부지표 없으면 'N/A']
    - PL_gap_B:  경합도 수치(혹은 등급 수치화) [외부지표 없으면 24년 1-2위 격차 사용]
    """
    out = {
        "PL_prg_str": np.nan,
        "PL_swing_B": "N/A",
        "PL_gap_B": np.nan,
    }

    code_str = str(code)

    # 외부 지표가 없거나 '코드'가 없으면 24년 격차만 계산
    if df_idx is None or len(df_idx) == 0 or ("코드" not in df_idx.columns):
        gap = compute_24_gap(df_24, code_str)
        if gap is not None:
            out["PL_gap_B"] = gap
        return out

    # 대상 행 추출
    sub = df_idx[df_idx["코드"].astype(str) == code_str]
    if sub.empty:
        gap = compute_24_gap(df_24, code_str)
        if gap is not None:
            out["PL_gap_B"] = gap
        return out

    row = sub.iloc[0]

    # 외부 지표 필드 사용 (있을 때만)
    if "PL_prg_str" in row.index:
        try:
            out["PL_prg_str"] = float(row["PL_prg_str"])
        except Exception:
            pass

    if "PL_swing_B" in row.index:
        try:
            out["PL_swing_B"] = str(row["PL_swing_B"])
        except Exception:
            pass

    if "PL_gap_B" in row.index:
        try:
            out["PL_gap_B"] = float(row["PL_gap_B"])
        except Exception:
            gap = compute_24_gap(df_24, code_str)
            if gap is not None:
                out["PL_gap_B"] = gap
    else:
        gap = compute_24_gap(df_24, code_str)
        if gap is not None:
            out["PL_gap_B"] = gap

    return out
