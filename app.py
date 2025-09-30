# =============================
# File: app.py
# =============================
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path

from data_loader import (
    load_population_agg,
    load_party_competence,
    load_vote_trend,
    load_results_2024,
    load_current_info,
    load_index_sample,
)
from metrics import (
    compute_trend_series,
    compute_summary_metrics,
    compute_24_gap,
)
from charts import (
    render_population_box,
    render_vote_trend_chart,
    render_results_2024_card,
    render_incumbent_card,
    render_prg_party_box,
)

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="전략지역구 조사 — 지역별 페이지", layout="wide")
st.title("전략지역구 조사 · 지역별 페이지")

DATA_DIR = Path("data")

# -----------------------------
# 코드 컬럼 표준화 유틸
# -----------------------------
CODE_CANDIDATES = ["코드", "code", "CODE", "선거구코드", "지역코드"]

def ensure_code_col(df: pd.DataFrame, src_name: str = "df") -> pd.DataFrame:
    """여러 형태로 들어올 수 있는 코드 컬럼을 '코드'(str)로 표준화."""
    if df is None:
        return pd.DataFrame()
    if len(df) == 0:
        return df

    df2 = df.copy()

    # 1) 컬럼 이름 매핑
    if "코드" not in df2.columns:
        for c in CODE_CANDIDATES:
            if c in df2.columns:
                df2 = df2.rename(columns={c: "코드"})
                break

    # 2) 인덱스에 코드가 들어있는 경우
    if "코드" not in df2.columns:
        idx_name = df2.index.name
        if idx_name in CODE_CANDIDATES or idx_name == "코드":
            df2 = df2.reset_index().rename(columns={idx_name if idx_name else "index": "코드"})

    # 3) 최종 타입 통일
    if "코드" in df2.columns:
        df2["코드"] = df2["코드"].astype(str)
    else:
        df2["__NO_CODE__"] = True

    return df2

# -----------------------------
# Load Data
# -----------------------------
with st.spinner("데이터 불러오는 중..."):
    df_pop = load_population_agg(DATA_DIR)               # 지역구 단위 합산(또는 이미 합산)
    df_prg = load_party_competence(DATA_DIR)
    df_trend = load_vote_trend(DATA_DIR)
    df_24 = load_results_2024(DATA_DIR)
    df_curr = load_current_info(DATA_DIR)
    df_idx = load_index_sample(DATA_DIR)  # 선택 외부지표(EE_/PL_* 등)

# --- 로드 직후 코드 표준화 (중요) ---
df_pop   = ensure_code_col(df_pop,   "df_pop")
df_prg   = ensure_code_col(df_prg,   "df_prg")
df_trend = ensure_code_col(df_trend, "df_trend")
df_24    = ensure_code_col(df_24,    "df_24")
df_curr  = ensure_code_col(df_curr,  "df_curr")
df_idx   = ensure_code_col(df_idx,   "df_idx")

# 가용 지역 목록(코드/이름)
if "지역구" not in df_pop.columns:
    st.error("df_pop에 '지역구' 컬럼이 없습니다. 데이터 파일을 확인하세요.")
    st.stop()

regions = (
    df_pop[["코드", "지역구"]]
    .drop_duplicates()
    .sort_values("지역구")
)

# 사이드바 — 지역 선택
st.sidebar.header("지역 선택")
sel_label = st.sidebar.selectbox(
    "선거구를 선택하세요",
    regions["지역구"].tolist() if not regions.empty else [],
)
if regions.empty:
    st.error("선택 가능한 지역이 없습니다. 데이터 소스를 확인하세요.")
    st.stop()

sel_code = regions.loc[regions["지역구"] == sel_label, "코드"].iloc[0]

# -----------------------------
# 상단 레이아웃: 좌(24년 결과) — 우(현직정보)
# -----------------------------
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("24년 총선결과")
    res_row = df_24[df_24["코드"] == sel_code]
    render_results_2024_card(res_row, df_24=df_24, code=sel_code)

with col_right:
    st.subheader("현직정보")
    cur_row = df_curr[df_curr["코드"] == sel_code]
    render_incumbent_card(cur_row)

st.divider()

# -----------------------------
# 중단: 진보당 현황 + 정당성향별 득표추이
# -----------------------------
col_a, col_b = st.columns([0.9, 1.1])

with col_a:
    st.subheader("진보당 현황")
    prg_row = df_prg[df_prg["코드"] == sel_code]
    pop_row = df_pop[df_pop["코드"] == sel_code]
    render_prg_party_box(prg_row, pop_row)

with col_b:
    st.subheader("정당성향별 득표추이")
    ts = compute_trend_series(df_trend, sel_code)
    render_vote_trend_chart(ts)

# 지표 요약
summary = compute_summary_metrics(df_trend, df_24, df_idx, sel_code)
pl_prg_str = summary.get("PL_prg_str")
pl_swing_b = summary.get("PL_swing_B")
pl_gap_b   = summary.get("PL_gap_B")

prg_text = f"{pl_prg_str:.2f}%" if isinstance(pl_prg_str, (int, float)) else "N/A"
gap_text = f"{pl_gap_b:.2f}p" if isinstance(pl_gap_b, (int, float)) else "N/A"
swing_text = str(pl_swing_b) if pl_swing_b is not None else "N/A"

st.caption(
    f"요약지표 · 진보정당득표력: {prg_text} · 유동성B: {swing_text} · 경합도B: {gap_text}"
)

st.divider()

# -----------------------------
# 하단: 인구 정보(3-in-1 박스)
# -----------------------------
st.subheader("인구 정보")
render_population_box(df_pop[df_pop["코드"] == sel_code])

# 푸터
st.write("")
st.caption("© 2025 전략지역구 조사 · Streamlit 대시보드")
