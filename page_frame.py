# streamlit_app.py
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

# ---------- 사이드바 (항상 보이는 지역 선택) ----------
st.sidebar.header("메뉴 선택")
menu = st.sidebar.radio("페이지", ["종합", "지역별 분석", "데이터 설명"], index=1)

regions = [
    "강서구병","관악구을","구로구갑","서대문구갑","은평구갑",
    "고양시을","부천시을","수원시을","평택시을","화성시을"
]
selected_region = st.sidebar.selectbox("지역을 선택하세요", regions, index=0)

# ---------- 데이터 로딩 & 집계 ----------
@st.cache_data(show_spinner=True)
def load_population(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # 필수 컬럼 존재 여부 체크 (부드럽게 경고)
    required = [
        "시/도","지역구","지역구코드","행정동","행정동코드",
        "전체 유권자","2030","4050","65세 이상","2030 남성","2030 여성","2030 1인가구"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.warning(f"population.csv에 다음 컬럼이 없습니다: {', '.join(missing)}")
    return df

def aggregate_by_region(df: pd.DataFrame) -> pd.DataFrame:
    # 숫자 컬럼만 합산: 행정동 → 지역구 수준 집계
    numeric_cols = [
        c for c in df.columns
        if c not in ["시/도","지역구","지역구코드","행정동","행정동코드"]
    ]
    # 숫자 변환 (문자 포함되어 있어도 NaN으로 안전 변환)
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    gb = df.groupby("지역구", as_index=False)[numeric_cols].sum(min_count=1)
    return gb

# population.csv 읽기
pop_path = Path("population.csv")
if not pop_path.exists():
    st.error("population.csv 파일을 프로젝트 폴더에 넣어주세요.")
    df_pop_raw = pd.DataFrame()
    df_by_region = pd.DataFrame()
else:
    df_pop_raw = load_population(pop_path)
    df_by_region = aggregate_by_region(df_pop_raw)

# ---------- 페이지 렌더링 ----------
if menu == "종합":
    st.subheader("📊 종합")
    if df_by_region.empty:
        st.info("집계된 인구 데이터가 없습니다.")
    else:
        st.write(f"현재 선택된 지역: **{selected_region}**")
        st.markdown("#### 10개 지역 2030 1인가구 비교")
        # 10개 관심지역만 필터링(선택하신 10개)
        df_focus = df_by_region[df_by_region["지역구"].isin(regions)].copy()
        bar_2030_single_household(df_focus, selected_region)

elif menu == "지역별 분석":
    st.subheader("📍 지역별 분석")
    if df_by_region.empty:
        st.info("집계된 인구 데이터가 없습니다.")
    else:
        st.write(f"선택 지역: **{selected_region}**")

        # 선택 지역 1행 (지역구 단위)
        sub = df_by_region[df_by_region["지역구"] == selected_region]
        if sub.empty:
            st.warning("선택된 지역 데이터가 없습니다.")
        else:
            row = sub.iloc[0]

            # 1) 파이: 2030 / 4050 / 65세 이상
            st.markdown("#### 연령대 구성 (2030 / 4050 / 65+)")
            pie_age_buckets(row)

            # 2) 파이: 2030 남성 vs 2030 여성
            st.markdown("#### 2030 성별 구성")
            pie_2030_gender(row)

            st.divider()

            # 3) 막대: 10개 지역의 2030 1인가구 (선택 지역 강조)
            st.markdown("#### 10개 지역 2030 1인가구 비교 (선택 지역 강조)")
            df_focus = df_by_region[df_by_region["지역구"].isin(regions)].copy()
            bar_2030_single_household(df_focus, selected_region)

elif menu == "데이터 설명":
    st.subheader("ℹ️ 데이터 설명")
    st.write("• 파일: population.csv")
    st.write("• 필수 컬럼: 시/도, 지역구, 지역구코드, 행정동, 행정동코드, 전체 유권자, 2030, 4050, 65세 이상, 2030 남성, 2030 여성, 2030 1인가구")
    if not df_pop_raw.empty:
        st.markdown("#### 원자료 (일부 미리보기)")
        st.dataframe(df_pop_raw.head(), use_container_width=True)
        st.markdown("#### 지역구 단위 집계 데이터 (일부 미리보기)")
        st.dataframe(df_by_region.head(), use_container_width=True)
