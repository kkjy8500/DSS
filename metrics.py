# =============================
# File: metrics.py
# =============================
from __future__ import annotations

import re
import numpy as np
import pandas as pd

_CODE_CANDIDATES = ["코드", "지역구코드", "선거구코드", "지역코드", "code", "CODE"]
_NAME_CANDIDATES = ["지역구","선거구","선거구명","지역명","district","지역구명","region","지역"]

def _canon_code(x: object) -> str:
    s = str(x).strip()
    s = re.sub(r"[^0-9A-Za-z]", "", s)
    s = s.lstrip("0")
    return s.lower()

def _pct_float(v) -> float | None:
    """다양한 득표율 표기를 0~100 스케일로 변환."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip().replace(",", "")
    m = re.match(r"^\s*([+-]?\d+(\.\d+)?)\s*%?\s*$", s)
    if not m:
        return None
    x = float(m.group(1))
    if "%" in s:
        return x
    return x * 100.0 if 0 <= x <= 1 else x

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame() if df is None else df
    df2 = df.copy()
    df2.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in df2.columns]
    return df2

def _detect_col(df: pd.DataFrame, candidates: list) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    cols = [str(c).strip().replace("\n", "").replace("\r", "") for c in df.columns]
    for cand in candidates:
        if cand in cols:
            return df.columns[cols.index(cand)]
    return None

def _detect_code_col(df: pd.DataFrame) -> str | None:
    return _detect_col(df, _CODE_CANDIDATES)

def _get_by_code_local(df: pd.DataFrame, code: str) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df2 = _normalize_columns(df)
    col = "코드" if "코드" in df2.columns else _detect_code_col(df2)
    if not col:
        return pd.DataFrame()
    key = _canon_code(code)
    try:
        sub = df2[df2[col].astype(str).map(_canon_code) == key]
        return sub if len(sub) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def _extract_year_from_election(election: str) -> int | None:
    """'2016_na_pro' 같은 문자열에서 앞의 4자리 연도 추출."""
    if not isinstance(election, str):
        return None
    m = re.match(r"^(\d{4})", election.strip())
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None

def compute_trend_series(df_trend: pd.DataFrame, code: str) -> pd.DataFrame:
    """
    주어진 선거구(code)에 대한 정당성향별 득표 추이 시계열(피벗 완료)을 반환.
    기대 반환:
      columns: 각 성향(예: 민주, 보수, 진보, 기타)
      index/col: year(int) / 'year' 컬럼으로도 포함
    입력 df_trend의 최소 요구 컬럼: ['code' or '코드', 'election' or '연도', 'label' and 'prop']
    """
    sub = _get_by_code_local(df_trend, code)
    if sub.empty:
        return pd.DataFrame()

    sub = _normalize_columns(sub)

    election_col = "election" if "election" in sub.columns else ("연도" if "연도" in sub.columns else None)
    label_col    = "label" if "label" in sub.columns else _detect_col(sub, ["성향","정당성향","party_label"])
    value_col    = "prop"  if "prop"  in sub.columns else _detect_col(sub, ["득표율","비율","share","ratio","pct"])

    if not label_col or not value_col:
        return sub

    # 값이 문자열/퍼센트면 숫자(0~100)로 정규화
    try:
        if sub[value_col].dtype == "O":
            sub[value_col] = sub[value_col].apply(_pct_float)
        else:
            # 소수(0~1)일 가능성도 100배 보정
            if pd.api.types.is_numeric_dtype(sub[value_col]):
                if (sub[value_col].dropna() <= 1).all():
                    sub[value_col] = sub[value_col] * 100.0
    except Exception:
        pass

    if election_col == "election":
        sub["year"] = sub["election"].apply(_extract_year_from_election)
    elif election_col == "연도":
        sub["year"] = pd.to_numeric(sub["연도"], errors="coerce")
    else:
        sub["year"] = pd.NA

    try:
        piv = (
            sub.dropna(subset=["year"])
               .pivot_table(index="year", columns=label_col, values=value_col, aggfunc="mean")
               .sort_index()
        )
        piv = piv.reset_index()
        return piv
    except Exception:
        return sub

def compute_24_gap(df_24: pd.DataFrame, code: str) -> float | None:
    """1~2위 득표율 격차(단위 p). 다양한 열/표기 자동 인식."""
    try:
        row24 = _get_by_code_local(df_24, code)
        if row24.empty:
            return None

        c1v = next((c for c in ["1위득표율","1위 득표율","1st_share","득표율_1위","1위득표율(%)"] if c in row24.columns), None)
        c2v = next((c for c in ["2위득표율","2위 득표율","2nd_share","득표율_2위","2위득표율(%)"] if c in row24.columns), None)

        if not c1v:
            cands = [c for c in row24.columns if isinstance(c, str)]
            one_like = [c for c in cands if re.search(r"1.*득표|득표.*1", c)]
            c1v = one_like[0] if one_like else None
        if not c2v:
            cands = [c for c in row24.columns if isinstance(c, str)]
            two_like = [c for c in cands if re.search(r"2.*득표|득표.*2", c)]
            c2v = two_like[0] if two_like else None

        if not (c1v and c2v):
            return None

        v1 = _pct_float(row24.iloc[0][c1v])
        v2 = _pct_float(row24.iloc[0][c2v])
        if v1 is None or v2 is None:
            return None
        return round(v1 - v2, 2)
    except Exception:
        return None

def compute_summary_metrics(
    df_trend: pd.DataFrame,
    df_24: pd.DataFrame,
    df_idx: pd.DataFrame,
    code: str,
) -> dict:
    """
    요약 지표:
    - PL_prg_str: 진보정당 득표력(%)
    - PL_swing_B: 유동성 등급(문자)
    - PL_gap_B:  경합도 수치(없으면 24년 1-2위 격차로 대체)
    """
    out = {"PL_prg_str": np.nan, "PL_swing_B": "N/A", "PL_gap_B": np.nan}

    sub = _get_by_code_local(df_idx, code)
    if sub is None or sub.empty:
        gap = compute_24_gap(df_24, code)
        if gap is not None:
            out["PL_gap_B"] = gap
        return out

    row = sub.iloc[0]

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
            gap = compute_24_gap(df_24, code)
            if gap is not None:
                out["PL_gap_B"] = gap
    else:
        gap = compute_24_gap(df_24, code)
        if gap is not None:
            out["PL_gap_B"] = gap

    return out
