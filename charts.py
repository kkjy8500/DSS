# charts.py
from __future__ import annotations
import pandas as pd
import altair as alt
import streamlit as st

# ===== 파이차트: 2030 / 4050 / 65세 이상 =====
def pie_age_buckets(row: pd.Series) -> None:
    needed = ["2030", "4050", "65세 이상"]
    if not all(c in row.index for c in needed):
        st.warning("⚠️ population.csv에 2030, 4050, 65세 이상 컬럼이 필요합니다.")
        return

    df = pd.DataFrame({
        "구성": needed,
        "인원": [float(row[c]) for c in needed]
    })
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta("인원:Q", stack=True),
            color=alt.Color("구성:N", legend=alt.Legend(title="연령대")),
            tooltip=["구성", "인원"]
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)

# ===== 파이차트: 2030 남성 / 2030 여성 =====
def pie_2030_gender(row: pd.Series) -> None:
    needed = ["2030 남성", "2030 여성"]
    if not all(c in row.index for c in needed):
        st.warning("⚠️ population.csv에 2030 남성, 2030 여성 컬럼이 필요합니다.")
        return

    df = pd.DataFrame({
        "구성": needed,
        "인원": [float(row[c]) for c in needed]
    })
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta("인원:Q", stack=True),
            color=alt.Color("구성:N", legend=alt.Legend(title="2030 성별")),
            tooltip=["구성", "인원"]
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)

# ===== 막대차트: 10개 지역 2030 1인가구 (선택 지역 강조) =====
def bar_2030_single_household(df_by_region: pd.DataFrame, selected_region: str) -> None:
    for col in ["지역구", "2030 1인가구"]:
        if col not in df_by_region.columns:
            st.warning("⚠️ population.csv에 '지역구', '2030 1인가구' 컬럼이 필요합니다.")
            return

    base = df_by_region.copy()
    base["선택"] = (base["지역구"] == selected_region)

    chart = (
        alt.Chart(base)
        .mark_bar()
        .encode(
            x=alt.X("2030 1인가구:Q", title="2030 1인가구(명)"),
            y=alt.Y("지역구:N", sort="-x", title="지역구"),
            color=alt.condition(
                alt.datum.선택, 
                alt.value("#1f77b4"),  # 선택 지역
                alt.value("#d3d3d3")   # 다른 지역
            ),
            tooltip=["지역구", "2030 1인가구"]
        )
        .properties(height=360)
    )
    st.altair_chart(chart, use_container_width=True)
