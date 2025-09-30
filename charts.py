# charts.py
from __future__ import annotations
import pandas as pd
import altair as alt
import streamlit as st
import pandas as pd
from utils import fmt_int, fmt_pct2

# ===== 파이차트: 2030 / 4050 / 65세 이상 =====
def pie_age_buckets(row: pd.Series) -> None:
    needed = ["2030", "4050", "65세 이상"]
    if not all(c in row.index for c in needed):
        st.warning("⚠️ population.csv에 2030, 4050, 65세 이상 컬럼이 필요합니다.")
        return
# -----------------------------
# 요약 메트릭 3개
# -----------------------------
def metric_triplet(title1, value1, title2, value2, title3, value3):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(label=title1, value=value1)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(label=title2, value=value2)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(label=title3, value=value3)
        st.markdown('</div>', unsafe_allow_html=True)

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
# -----------------------------
# 상위 1~3위 카드
# -----------------------------
def top3_cards(top3_df: pd.DataFrame):
    cols = st.columns(3)
    for i in range(min(3, len(top3_df))):
        row = top3_df.iloc[i]
        with cols[i]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f"**{i+1}위 | {row.get('후보', '')}**")
            st.markdown(f"- 득표율: **{fmt_pct2(row.get('득표율'))}**")
            st.markdown(f"- 득표수: **{fmt_int(row.get('득표수'))}**")
            st.markdown('</div>', unsafe_allow_html=True)

# ===== 파이차트: 2030 남성 / 2030 여성 =====
def pie_2030_gender(row: pd.Series) -> None:
    needed = ["2030 남성", "2030 여성"]
    if not all(c in row.index for c in needed):
        st.warning("⚠️ population.csv에 2030 남성, 2030 여성 컬럼이 필요합니다.")
# -----------------------------
# 전체 표 (후보, 득표율(소수2), 득표수(천단위))
# -----------------------------
def results_table(res_rows: pd.DataFrame):
    if res_rows.empty:
        st.info("24년 총선 결과 데이터가 없습니다.")
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
    df = res_rows.copy()
    # 표시용 포맷
    df_disp = df[["후보", "득표율", "득표수"]].copy()
    df_disp["득표율"] = df_disp["득표율"].apply(lambda x: fmt_pct2(x))
    df_disp["득표수"] = df_disp["득표수"].apply(lambda x: fmt_int(x))
    st.dataframe(
        df_disp.reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )
    st.altair_chart(chart, use_container_width=True)

# ===== 막대차트: 10개 지역 2030 1인가구 (선택 지역 강조) =====
def bar_2030_single_household(df_by_region: pd.DataFrame, selected_region: str) -> None:
    for col in ["지역구", "2030 1인가구"]:
        if col not in df_by_region.columns:
            st.warning("⚠️ population.csv에 '지역구', '2030 1인가구' 컬럼이 필요합니다.")
            return
# -----------------------------
# 현직 카드
# -----------------------------
def incumbent_card(sel_name: str, row, kpi1_name: str, kpi1_value, kpi2_name: str, kpi2_value):
    st.markdown('<div class="inc-card">', unsafe_allow_html=True)
    st.markdown(f"### {sel_name} 현직 정보")
    cols = st.columns([1.2, 1, 1, 1, 1, 1])
    cols[0].markdown(f"**이름**<br>{row.get('이름', '')}", unsafe_allow_html=True)
    cols[1].markdown(f"**정당**<br>{row.get('정당', '')}", unsafe_allow_html=True)
    cols[2].markdown(f"**성별**<br>{row.get('성별', '')}", unsafe_allow_html=True)
    cols[3].markdown(f"**연령**<br>{row.get('연령', '')}", unsafe_allow_html=True)  # 문자열 그대로
    cols[4].markdown(f"**선수**<br>{row.get('선수', '')}", unsafe_allow_html=True)
    cols[5].markdown(f"**24년 득표**<br>{row.get('24년득표', '')}", unsafe_allow_html=True)

    base = df_by_region.copy()
    base["선택"] = (base["지역구"] == selected_region)
    st.write("---")
    # KPI 배지
    k1 = fmt_pct2(kpi1_value)
    k2 = fmt_pct2(kpi2_value)
    st.markdown(f"- **{kpi1_name}**: {k1}")
    st.markdown(f"- **{kpi2_name}**: {k2}")

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
    # 부가 표기
    st.write("---")
    cols2 = st.columns(2)
    cols2[0].markdown(f"**인물경쟁력**<br>{row.get('인물경쟁력', '')}", unsafe_allow_html=True)
    cols2[1].markdown(f"**재출마가능성**<br>{row.get('재출마가능성', '')}", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
