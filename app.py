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
# Page Config (요청 사양)
# -----------------------------
st.set_page_config(
    page_title="지역구 선정 1단계 조사 결과 대시보드",
    page_icon="🗳️",
    layout="wide",
)
st.title("🗳️ 지역구 선정 1단계 조사 결과")
st.caption("에스티아이")

# ---------- Sidebar Navigation ----------
st.sidebar.header("메뉴 선택")
menu = st.sidebar.radio(
    "페이지",
    ["종합", "지역별 분석", "데이터 설명"],
    index=0
)

DATA_DIR = Path("data")

# -----------------------------
# 공통 유틸
# -----------------------------
CODE_CANDIDATES = ["코드", "지역구코드", "선거구코드", "지역코드", "code", "CODE"]
NAME_CANDIDATES = ["지역구", "선거구명", "지역명", "district", "지역구명"]
SIDO_CANDIDATES = ["시/도", "시도", "광역", "sido", "province"]

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame() if df is None else df
    df2 = df.copy()
    df2.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in df2.columns]
    return df2

def _detect_col(df: pd.DataFrame, candidates: list) -> str or None:
    for c in candidates:
        if c in df.columns:
            return c
    # 공백·개행 변형 감안
    cols = [str(c).strip().replace("\n", "").replace("\r", "") for c in df.columns]
    for cand in candidates:
        if cand in cols:
            # 원래 이름으로 되돌려줌
            return df.columns[cols.index(cand)]
    return None

def ensure_code_col(df: pd.DataFrame) -> pd.DataFrame:
    """여러 이름의 코드 컬럼을 '코드'(str)로 표준화."""
    if df is None:
        return pd.DataFrame()
    if len(df) == 0:
        return df
    df2 = _normalize_columns(df)
    if "코드" not in df2.columns:
        found = _detect_col(df2, CODE_CANDIDATES)
        if found:
            df2 = df2.rename(columns={found: "코드"})
    if "코드" not in df2.columns:
        # 인덱스에 존재 가능성
        idx_name = df2.index.name
        if idx_name and idx_name in CODE_CANDIDATES + ["코드"]:
            df2 = df2.reset_index().rename(columns={idx_name: "코드"})
    if "코드" in df2.columns:
        df2["코드"] = df2["코드"].astype(str)
    else:
        df2["__NO_CODE__"] = True
    return df2

def get_by_code(df: pd.DataFrame, code: str) -> pd.DataFrame:
    """코드 컬럼 자동 탐지 후 해당 code 행만 반환(없으면 빈 DF)."""
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df2 = _normalize_columns(df)
    code_col = "코드" if "코드" in df2.columns else _detect_col(df2, CODE_CANDIDATES)
    if not code_col:
        return pd.DataFrame()
    try:
        return df2[df2[code_col].astype(str) == str(code)]
    except Exception:
        return pd.DataFrame()

def build_regions(df_pop: pd.DataFrame) -> pd.DataFrame:
    """사이드바 선택용 지역 목록: 코드 + 라벨(시/도 + 지역구)"""
    if df_pop is None or len(df_pop) == 0:
        return pd.DataFrame(columns=["코드", "라벨"])
    dfp = ensure_code_col(_normalize_columns(df_pop))
    name_col = _detect_col(dfp, NAME_CANDIDATES)
    if not name_col:
        return pd.DataFrame(columns=["코드", "라벨"])
    sido_col = _detect_col(dfp, SIDO_CANDIDATES)

    # 라벨 생성: '서울 강서구병' 형태 보장
    def _label(row):
        nm = str(row[name_col]).strip()
        if sido_col:
            sido = str(row[sido_col]).strip()
            return nm if nm.startswith(sido) else f"{sido} {nm}"
        return nm

    out = (
        dfp.assign(라벨=dfp.apply(_label, axis=1))
           .loc[:, ["코드", "라벨"]]
           .drop_duplicates()
           .sort_values("라벨")
           .reset_index(drop=True)
    )
    return out

# -----------------------------
# Load Data
# -----------------------------
with st.spinner("데이터 불러오는 중..."):
    df_pop = load_population_agg(DATA_DIR)            # population_agg.csv or population.csv
    df_prg = load_party_competence(DATA_DIR)          # progressive_party.csv
    df_trend = load_vote_trend(DATA_DIR)              # vote_trend.csv
    df_24 = load_results_2024(DATA_DIR)               # results_2024.csv
    df_curr = load_current_info(DATA_DIR)             # current_info.csv
    df_idx = load_index_sample(DATA_DIR)              # index_sample.csv (선택)

# 표준화
df_pop   = ensure_code_col(df_pop)
df_prg   = ensure_code_col(df_prg)
df_trend = ensure_code_col(df_trend)
df_24    = ensure_code_col(df_24)
df_curr  = ensure_code_col(df_curr)
df_idx   = ensure_code_col(df_idx)

# -----------------------------
# Page: 종합
# -----------------------------
if menu == "종합":
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("지역 수", f"{df_pop['코드'].nunique() if '코드' in df_pop.columns else 0:,}")
    with c2:
        st.metric("데이터 소스(표) 수", f"{sum([len(x) > 0 for x in [df_pop, df_24, df_curr, df_trend, df_prg, df_idx]])}/6")
    with c3:
        st.metric("최근 파일 로드 상태", "OK" if any(len(x) > 0 for x in [df_pop, df_24, df_curr]) else "확인 필요")

    st.divider()
    # 시/도 분포 (있으면)
    sido_col = _detect_col(df_pop, SIDO_CANDIDATES)
    name_col = _detect_col(df_pop, NAME_CANDIDATES)
    if sido_col and name_col:
        st.subheader("시/도별 지역구 개수")
        vc = (
            df_pop[[sido_col, "코드"]].dropna()
            .groupby(sido_col)["코드"].nunique()
            .sort_values(ascending=False)
            .rename("지역구수")
            .to_frame()
        )
        st.dataframe(vc)

# -----------------------------
# Page: 지역별 분석
# -----------------------------
elif menu == "지역별 분석":
    regions = build_regions(df_pop)
    if regions.empty:
        st.error("지역 목록을 만들 수 없습니다. (df_pop의 '코드' 또는 지역명 컬럼 확인)")
        st.stop()

    st.sidebar.header("지역 선택")
    sel_label = st.sidebar.selectbox("선거구를 선택하세요", regions["라벨"].tolist())
    sel_code = regions.loc[regions["라벨"] == sel_label, "코드"].iloc[0]

    # 상단: 좌(24년 결과) — 우(현직정보)
    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.subheader("24년 총선결과")
        res_row = get_by_code(df_24, sel_code)
        render_results_2024_card(res_row, df_24=df_24, code=sel_code)
    with col_right:
        st.subheader("현직정보")
        cur_row = get_by_code(df_curr, sel_code)
        render_incumbent_card(cur_row)

    st.divider()

    # 중단: 진보당 현황 + 정당성향별 득표추이
    col_a, col_b = st.columns([0.9, 1.1])
    with col_a:
        st.subheader("진보당 현황")
        prg_row = get_by_code(df_prg, sel_code)
        pop_row = get_by_code(df_pop, sel_code)
        render_prg_party_box(prg_row, pop_row)
    with col_b:
        st.subheader("정당성향별 득표추이")
        ts = compute_trend_series(df_trend, sel_code)
        render_vote_trend_chart(ts)

    # 요약지표 (유동성/경합도/진보득표력)
    summary = compute_summary_metrics(df_trend, df_24, df_idx, sel_code)
    prg_text  = f"{summary.get('PL_prg_str'):.2f}%" if isinstance(summary.get("PL_prg_str"), (int, float)) else "N/A"
    gap_text  = f"{summary.get('PL_gap_B'):.2f}p"    if isinstance(summary.get("PL_gap_B"), (int, float)) else "N/A"
    swing_txt = str(summary.get("PL_swing_B")) if summary.get("PL_swing_B") is not None else "N/A"
    st.caption(f"요약지표 · 진보정당득표력: {prg_text} · 유동성B: {swing_txt} · 경합도B: {gap_text}")

    st.divider()

    # 하단: 인구 정보
    st.subheader("인구 정보")
    render_population_box(get_by_code(df_pop, sel_code))

# -----------------------------
# Page: 데이터 설명
# -----------------------------
else:
    st.subheader("데이터 파일 설명")
    st.write("- population.csv: 지역구별 인구/유권자 구조")
    st.write("- results_2024.csv: 2024 총선 지역구별 1·2위 득표 정보")
    st.write("- current_info.csv: 현직 의원 기본 정보")
    st.write("- vote_trend.csv: 선거별 정당 성향 득표 추이")
    st.write("- progressive_party.csv: 진보당 관련 지표 (득표력, 조직 규모 등)")
    st.write("- index_sample.csv: 외부 지표(PL/EE 등) 선택적 제공")

    with st.expander("각 DataFrame 컬럼 미리보기"):
        def _cols(df, name):
            st.markdown(f"**{name}**")
            if df is None or len(df) == 0:
                st.write("없음/빈 데이터")
            else:
                st.code(", ".join(map(str, df.columns.tolist())))
        _cols(df_pop,  "df_pop (population)")
        _cols(df_24,   "df_24 (results_2024)")
        _cols(df_curr, "df_curr (current_info)")
        _cols(df_trend,"df_trend (vote_trend)")
        _cols(df_prg,  "df_prg (progressive_party)")
        _cols(df_idx,  "df_idx (index_sample)")

st.write("")
st.caption("© 2025 전략지역구 조사 · Streamlit 대시보드")
