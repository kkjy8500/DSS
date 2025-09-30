from __future__ import annotations

import re
import numpy as np
import pandas as pd

# 내부적으로도 컬럼 후보를 사용
_CODE_CANDIDATES = ["코드", "지역구코드", "선거구코드", "지역코드", "code", "CODE"]
_NAME_CANDIDATES = ["지역구","선거구명","지역명","district","지역구명","region","지역"]

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
    try:
        return df2[df2[col].astype(str) == str(code)]
    except Exception:
        return pd.DataFrame()

def _extract_year_from_election(election: str) -> int | None:
    """
    '2016_na_pro' 같은 문자열에서 앞의 4자리 연도 추출.
    """
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

    # 컬럼 탐지
    election_col = "election" if "election" in sub.columns else ("연도" if "연도" in sub.columns else None)
    label_col    = "label" if "label" in sub.columns else _detect_col(sub, ["성향","정당성향","party_label"])
    value_col    = "prop"  if "prop"  in sub.columns else _detect_col(sub, ["득표율","비율","share","ratio","pct"])

    if not label_col or not value_col:
        # 최소 요건 불충족 시 원본 반환 (차트 쪽에서 테이블로 표출)
        return sub

    # 연도 파싱
    if election_col == "election":
        sub["year"] = sub["election"].apply(_extract_year_from_election)
    elif election_col == "연도":
        # 이미 연도라면 표준화
        sub["year"] = pd.to_numeric(sub["연도"], errors="coerce")
    else:
        sub["year"] = pd.NA

    # 피벗 (연도 x label -> prop)
    try:
        piv = (
            sub.dropna(subset=["year"])
               .pivot_table(index="year", columns=label_col, values=value_col, aggfunc="mean")
               .sort_index()
        )
        piv = piv.reset_index()  # 'year' 컬럼 보유
        return piv
    except Exception:
        # 피벗 실패 시 원본 반환
        return sub

def compute_24_gap(df_24: pd.DataFrame, code: str) -> float | None:
    """2024 총선에서 1위-2위 득표율 격차를 계산 (가능할 때만)."""
    try:
        row24 = _get_by_code_local(df_24, code)
        if not row24.empty:
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
