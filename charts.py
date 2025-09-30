import streamlit as st
import pandas as pd
from utils import fmt_int, fmt_pct2

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

# -----------------------------
# 전체 표 (후보, 득표율(소수2), 득표수(천단위))
# -----------------------------
def results_table(res_rows: pd.DataFrame):
    if res_rows.empty:
        st.info("24년 총선 결과 데이터가 없습니다.")
        return
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

    st.write("---")
    # KPI 배지
    k1 = fmt_pct2(kpi1_value)
    k2 = fmt_pct2(kpi2_value)
    st.markdown(f"- **{kpi1_name}**: {k1}")
    st.markdown(f"- **{kpi2_name}**: {k2}")

    # 부가 표기
    st.write("---")
    cols2 = st.columns(2)
    cols2[0].markdown(f"**인물경쟁력**<br>{row.get('인물경쟁력', '')}", unsafe_allow_html=True)
    cols2[1].markdown(f"**재출마가능성**<br>{row.get('재출마가능성', '')}", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
