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
    load_index_sample
)
from metrics import (
    compute_trend_series,
    metrics.py,
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
# Load Data
# -----------------------------
with st.spinner("데이터 불러오는 중..."):
    df_pop = load_population_agg(DATA_DIR)               # 지역구 단위 합산
    df_prg = load_party_competence(DATA_DIR)
    df_trend = load_vote_trend(DATA_DIR)
    df_24 = load_results_2024(DATA_DIR)
    df_curr = load_current_info(DATA_DIR)
    df_idx = load_index_sample(DATA_DIR)  # 선택: EE_/PL_* A지표 등 외부 제공치

# 가용 지역 목록(코드/이름)
regions = (
    df_pop[["코드", "선거구명"]]
    .drop_duplicates()
    .sort_values("선거구명")
)

# 사이드바 — 지역 선택
st.sidebar.header("지역 선택")
sel_label = st.sidebar.selectbox(
    "선거구를 선택하세요",
    regions["선거구명"].tolist(),
)
sel_code = regions.loc[regions["선거구명"] == sel_label, "코드"].iloc[0]

# -----------------------------
# 상단 레이아웃: 좌(24년 결과) — 우(현직정보)
# -----------------------------
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("24년 총선결과")
    res_row = df_24[df_24["코드"] == sel_code]
    render_results_2024_card(res_row)

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
    # 2016~2025 전체 10개 선거 반영 (dataset에 존재하는 항목 기준)
    ts = compute_trend_series(df_trend, sel_code)
    render_vote_trend_chart(ts)

# 지표 요약(유동성/경합도 등) — 우측 아래 간략 배치
summary = compute_summary_metrics(df_trend, df_24, df_idx, sel_code)
st.caption(
    f"요약지표 · 진보정당득표력: {summary['PL_prg_str']:.2f}% · 유동성B: {summary['PL_swing_B']} · 경합도B: {summary['PL_gap_B']:.2f}p"
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

