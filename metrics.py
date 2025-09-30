# =============================
# File: metrics.py
# =============================
from __future__ import annotations

import pandas as pd
from typing import Dict

# 색상 팔레트 (차트에서 사용)
COLORS = {
    "민주": "#1976D2",
    "보수": "#D32F2F",
    "진보": "#F9A825",
    "기타": "#9E9E9E",
    "진보당": "#E91E63",
}

# 선거 정렬(가능한 10개: 2016~2025)
ELECTION_ORDER = [
    "2016_na_pro",
    "2017_president",
    "2018_loc_pro",
    "2020_na_pro",
    "2022_president",
    "2024_na_pro",
    "2025_president",
]
# 위 목록 외 추가 항목이 있으면 뒤에 정렬되도록 보조 키 제공


def _election_sort_key(x: str) -> tuple[int, str]:
    try:
        idx = ELECTION_ORDER.index(x)
        return (0, idx)
    except ValueError:
        return (1, x)


def compute_trend_series(df_trend: pd.DataFrame, code: str) -> pd.DataFrame:
    """선거코드별(시간축) label별 prop% 피벗. 소수점 2자리 반올림.
    반환: columns=['election','민주','보수','진보','기타']
    """
    t = df_trend[df_trend["코드"] == str(code)].copy()
    t = t[t["label"].isin(["민주", "보수", "진보", "기타"])]
    # 선거 필터: 2016~2025 전체 포함(데이터에 존재하는 한)
    t["_key"] = t["election"].apply(_election_sort_key)
    t = t.sort_values(["_key", "election", "label"]).drop(columns=["_key"])
    p = t.pivot_table(index="election", columns="label", values="prop", aggfunc="mean").reset_index()
    for c in ["민주", "보수", "진보", "기타"]:
        if c in p.columns:
            p[c] = p[c].round(2)
        else:
            p[c] = pd.NA
    return p


def compute_summary_metrics(df_trend: pd.DataFrame, df_24: pd.DataFrame, df_idx: pd.DataFrame | None, code: str) -> Dict[str, float]:
    """요약 지표 산출.
    - PL_prg_str: 2016 이후 비대선(총선/지선)에서 진보 평균 득표율
    - PL_swing_B, PL_gap_B: 2016 이후 10개 선거 기준 (데이터 가용한 범위)
    - A지표/EE_* 등은 index_sample이 있으면 해당 값을 사용(우선)
    """
    out = {"PL_prg_str": float("nan"), "PL_swing_B": float("nan"), "PL_gap_B": float("nan")}

    # index_sample 우선 사용
    if df_idx is not None and not df_idx.empty:
        row = df_idx[df_idx["코드"] == str(code)]
        if not row.empty:
            for k in ["PL_swing_B", "PL_gap_B"]:
                if k in row.columns:
                    out[k] = float(row.iloc[0][k]) if pd.notna(row.iloc[0][k]) else float("nan")

    # 진보정당득표력(비대선 평균)
    t = df_trend[(df_trend["코드"] == str(code)) & (~df_trend["election"].str.contains("president", na=False))]
    prg = t[t["label"] == "진보"]["prop"].dropna()
    if len(prg) > 0:
        out["PL_prg_str"] = round(prg.mean(), 2)

    # B지표 계산(데이터 기반): 1위 블록 변화 횟수, 평균 1-2위 격차
    # 선거별 블록 득표율 합이 아닌, label prop 자체가 100 합 가정.
    seq = (
        df_trend[df_trend["코드"] == str(code)]
        .groupby(["election", "label"], as_index=False)["prop"].mean()
    )
    if not seq.empty:
        # 정렬
        seq["_key"] = seq["election"].apply(_election_sort_key)
        seq = seq.sort_values(["_key", "election"]).drop(columns=["_key"])
        # 각 선거의 1~2위
        top = (
            seq.sort_values(["election", "prop"], ascending=[True, False])
            .groupby("election")
            .head(2)
        )
        # swing_B
        winners = top.groupby("election").first().reset_index()[["election", "label"]]
        winners["prev"] = winners["label"].shift(1)
        swing_b = int((winners["label"] != winners["prev"]) & winners["prev"].notna()).sum()
        out["PL_swing_B"] = float(swing_b) if pd.isna(out.get("PL_swing_B")) else out["PL_swing_B"]
        # gap_B (평균 1-2위 격차)
        gaps = (
            top.groupby("election")["prop"].apply(lambda s: s.max() - s.min()).dropna()
        )
        if len(gaps) > 0:
            out["PL_gap_B"] = round(float(gaps.mean()), 2) if pd.isna(out.get("PL_gap_B")) else out["PL_gap_B"]

    return out


def compute_24_gap(row_24: pd.DataFrame) -> float:
    """24년 1–2위 득표율 격차(%p) 계산."""
    if row_24 is None or row_24.empty:
        return float("nan")
    # 후보*_득표율 컬럼 수집
    cols = [c for c in row_24.columns if c.endswith("득표율") and c.startswith("후보")]
    vals = (
        row_24.iloc[0][cols].astype(float).dropna().sort_values(ascending=False).tolist()
        if len(row_24) > 0 else []
    )
    if len(vals) >= 2:
        return round(vals[0] - vals[1], 2)
    return float("nan")


