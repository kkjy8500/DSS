# =============================
# File: metrics.py
# =============================
from __future__ import annotations

import numpy as np
import pandas as pd

# 내부적으로도 컬럼 후보를 사용
_CODE_CANDIDATES = ["코드", "지역구코드", "선거구코드", "지역코드", "code", "CODE"]

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame() if df is None else df
    df2 = df.copy()
    df2.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in df2.columns]
    return df2

def _detect_code_col(df: pd.DataFrame) -> str or None:
    for c in _CODE_CANDIDATES:
        if c in df.columns:
            return c
    cols = [str(c).strip().replace("\n", "").replace("\r", "") for c in df.columns]
    for cand in _CODE_CANDIDATES:
        if cand in cols:
            return df.columns[cols.index(cand)]
    return None

def _get_by_code_local(df: pd.DataFrame, code: str) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df2 = _normalize_columns(df)
    col = "코드" if "코드" in df2.columns else _detect_code_col(df2)
    if not col:
        return pd.DataFrame()
    try:
        return df2[df2[col].astype(str) == str(code)]
    except Exception:
        return pd.DataFrame()

def compute_trend_series(df_trend: pd.DataFrame, code: str) -> pd.DataFrame:
    """주어진 선거구(code)에 대한 정당성향별 득표 추이 시계열을 반환."""
    return _get_by_code_local(df_trend, code)

def compute_24_gap(df_24: pd.DataFrame, code: str) -> float or None:
    """2024 총선에서 1위-2위 득표율 격차를 계산 (가능할 때만)."""
    try:
        row24 = _get_by_code_local(df_24, code)
        if not row24.empty:
            # 후보 컬럼명 유연 인식
            c1v = next((c for c in ["1위득표율","1위 득표율","1st_share"] if c in row24.columns), None)
            c2v = next((c for c in ["2위득표율","2위 득표율","2nd_share"] if c in row24.columns), None)
            if c1v and c2v:
                gap = float(row24.iloc[0][c1v]) - float(row24.iloc[0][c2v])
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

    # 외부 지표가 없거나 코드 매칭 실패 시 24년 격차로 대체
    sub = _get_by_code_local(df_idx, code)
    if sub is None or sub.empty:
        gap = compute_24_gap(df_24, code)
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
            # 외부 값 파싱 실패 시 24년 격차로 보조
            gap = compute_24_gap(df_24, code)
            if gap is not None:
                out["PL_gap_B"] = gap
    else:
        # 필드 자체가 없으면 24년 격차 보조
        gap = compute_24_gap(df_24, code)
        if gap is not None:
            out["PL_gap_B"] = gap

    return out
