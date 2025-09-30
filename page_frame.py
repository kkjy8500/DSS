# app.py
from __future__ import annotations
import pandas as pd
import streamlit as st
from pathlib import Path

from charts import pie_age_buckets, pie_2030_gender, bar_2030_single_household

st.set_page_config(
    page_title="지역구 선정 1단계 조사 결과 대시보드",
    page_icon="🗳️",
    layout="wide",
)

st.title("🗳️ 지역구 선정 1단계 조사 결과")
st.caption("에스티아이")

# ---------- 사이드바 ----------
st.sidebar.header("메뉴 선택")
menu = st.sidebar.radio("페이지", ["종합", "지역별 분석", "데이터 설명"], index=1)

regions = [
    "강서구병","관악구을","구로구갑","서대문구갑","은평구갑",
    "고양시을","부천시을","수원시을","평택시을","화성시을"
]
selected_region = st.sidebar.selectbox("지역을 선택하세요", regions, index=0)

# ---------- 데이터 로딩 ----------
@st.cache_data(show_spinner=True)
def load_population(path: Path) -> pd.DataFrame:
    if not path.exists():
        st.error(f"❌ 파일을 찾을 수 없습니다: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp949")
    return df

def aggregate_by_region(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [
        c for c in df.columns
        if c not in ["시/도","지역구","지역구코드","행정동","행정동코드"]
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    gb = df.groupby("지역구", as_index=False)[numeric_cols].sum(min_count=1)
    return gb

pop_path = Path("data/population.csv")
df_pop_raw = load_population(pop_path)
df_by_region = aggregate_by_region(df_pop_raw) if not df_pop_raw.empty else pd.DataFrame()

# ---------- 페이지 ----------
if menu == "종합":
    st.subheader("📊 종합")
    if df_by_region.empty:
        st.info("집계된 인구 데이터가 없습니다.")
    else:
        st.write(f"현재 선택된 지역: **{selected_region}**")
        st.markdown("#### 10개 지역 2030 1인가구 비교")
        df_focus = df_by_region[df_by_region["지역구"].isin(regions)].copy()
        bar_2030_single_household(df_focus, selected_region)

elif menu == "지역별 분석":
    st.subheader("📍 지역별 분석")
    if df_by_region.empty:
        st.info("집계된 인구 데이터가 없습니다.")
    else:
        st.write(f"선택 지역: **{selected_region}**")
        sub = df_by_region[df_by_region["지역구"] == selected_region]
        if sub.empty:
            st.warning("선택된 지역 데이터가 없습니다.")
        else:
            row = sub.iloc[0]

            st.markdown("#### 연령대 구성 (2030 / 4050 / 65+)")
            pie_age_buckets(row)

            st.markdown("#### 2030 성별 구성")
            pie_2030_gender(row)

            st.divider()
            st.markdown("#### 10개 지역 2030 1인가구 비교 (선택 지역 강조)")
            df_focus = df_by_region[df_by_region["지역구"].isin(regions)].copy()
            bar_2030_single_household(df_focus, selected_region)

elif menu == "데이터 설명":
    st.subheader("ℹ️ 데이터 설명")
    st.write("• 파일: data/population.csv")
    if not df_pop_raw.empty:
        st.markdown("#### 원자료 미리보기")
        st.dataframe(df_pop_raw.head(), use_container_width=True)
        st.markdown("#### 지역구 단위 집계 데이터 미리보기")
        st.dataframe(df_by_region.head(), use_container_width=True)
