# =============================
# File: charts.py
# =============================

import pandas as pd
import streamlit as st
from metrics import COLORS, compute_24_gap

# -------- 유틸 --------
def _safe_float(v, default=None):
    try:
        return float(v)
    except Exception:
        return default

def _fmt_pct(x):
    return f"{x:.2f}%" if isinstance(x, (int, float)) else "N/A"

def _fmt_gap(x):
    return f"{x:.2f}p" if isinstance(x, (int, float)) else "N/A"

# -------- 24년 결과 카드 --------
def render_results_2024_card(res_row: pd.DataFrame, df_24: pd.DataFrame = None, code: str = None):
    if res_row is None or res_row.empty:
        st.info("해당 선거구의 24년 결과 데이터가 없습니다.")
        return

    c1 = next((c for c in ["1위이름","1위 후보","1위_이름","1st_name"] if c in res_row.columns), None)
    c1p = next((c for c in ["1위정당","1위 정당","1st_party"] if c in res_row.columns), None)
    c1v = next((c for c in ["1위득표율","1위 득표율","1st_share"] if c in res_row.columns), None)

    c2 = next((c for c in ["2위이름","2위 후보","2위_이름","2nd_name"] if c in res_row.columns), None)
    c2p = next((c for c in ["2위정당","2위 정당","2nd_party"] if c in res_row.columns), None)
    c2v = next((c for c in ["2위득표율","2위 득표율","2nd_share"] if c in res_row.columns), None)

    r = res_row.iloc[0]
    name1 = str(r[c1]) if c1 else "1위"
    party1 = str(r[c1p]) if c1p else ""
    share1 = _safe_float(r[c1v]) if c1v else None

    name2 = str(r[c2]) if c2 else "2위"
    party2 = str(r[c2p]) if c2p else ""
    share2 = _safe_float(r[c2v]) if c2v else None

    gap = None
    if share1 is not None and share2 is not None:
        gap = round(share1 - share2, 2)
    elif df_24 is not None and code is not None:
        gap = compute_24_gap(df_24, code)

    box = st.container()
    with box:
        st.markdown("**24년 총선결과**")
        col1, col2, col3 = st.columns([1.2, 1.2, 1])
        with col1:
            st.metric(label=f"{party1} {name1}", value=_fmt_pct(share1))
        with col2:
            st.metric(label=f"{party2} {name2}", value=_fmt_pct(share2))
        with col3:
            st.metric(label="1~2위 격차", value=_fmt_gap(gap))

# -------- 현직 정보 카드 --------
def render_incumbent_card(cur_row: pd.DataFrame):
    if cur_row is None or cur_row.empty:
        st.info("현직 정보 데이터가 없습니다.")
        return

    r = cur_row.iloc[0]
    name_col   = next((c for c in ["의원명","이름","성명","incumbent_name"] if c in cur_row.columns), None)
    party_col  = next((c for c in ["정당","소속정당","party"] if c in cur_row.columns), None)
    term_col   = next((c for c in ["선수","당선횟수","terms"] if c in cur_row.columns), None)
    age_col    = next((c for c in ["연령","나이","age"] if c in cur_row.columns), None)
    gender_col = next((c for c in ["성별","gender"] if c in cur_row.columns), None)
    status_col = next((c for c in ["상태","현직여부","status"] if c in cur_row.columns), None)

    box = st.container()
    with box:
        st.markdown("**현직정보**")
        st.write(f"- 의원: **{r.get(name_col, 'N/A')}** / 정당: **{r.get(party_col, 'N/A')}**")
        st.write(
            f"- 선수: **{r.get(term_col, 'N/A')}** / 성별: **{r.get(gender_col, 'N/A')}** / 연령: **{r.get(age_col, 'N/A')}**"
        )
        if status_col:
            st.caption(f"상태: {r.get(status_col)}")

# -------- 진보당 현황 박스 --------
def render_prg_party_box(prg_row: pd.DataFrame, pop_row: pd.DataFrame):
    box = st.container()
    with box:
        st.markdown("**진보당 현황**")
        if prg_row is None or prg_row.empty:
            st.info("진보당 관련 데이터가 없습니다.")
            return

        r = prg_row.iloc[0]
        vote_col  = next((c for c in ["진보당_득표율","진보_득표율","progressive_share"] if c in prg_row.columns), None)
        org_col   = next((c for c in ["당원수","조직수","branch_count"] if c in prg_row.columns), None)
        trend_col = next((c for c in ["최근_상승폭","trend_delta"] if c in prg_row.columns), None)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("득표력", _fmt_pct(_safe_float(r.get(vote_col), None)) if vote_col else "N/A")
        with c2:
            st.metric("조직 규모", f"{int(r.get(org_col)):,}" if org_col and pd.notna(r.get(org_col)) else "N/A")
        with c3:
            td = _safe_float(r.get(trend_col), None) if trend_col else None
            st.metric("최근 추세(Δ)", f"{td:+.2f}p" if isinstance(td,(int,float)) else "N/A")

        if pop_row is not None and not pop_row.empty:
            rp = pop_row.iloc[0]
            elder_col = next((c for c in ["고령층비율","65세이상비율","age65p"] if c in pop_row.columns), None)
            youth_col = next((c for c in ["청년층비율","39세이하비율","age39m"] if c in pop_row.columns), None)
            with st.expander("인구 맥락 보기", expanded=False):
                elder = _fmt_pct(_safe_float(rp.get(elder_col), None)) if elder_col else "N/A"
                youth = _fmt_pct(_safe_float(rp.get(youth_col), None)) if youth_col else "N/A"
                st.write(f"- 고령층 비율: {elder} / 청년층 비율: {youth}")

# -------- 득표 추이 차트 --------
def render_vote_trend_chart(ts: pd.DataFrame):
    if ts is None or ts.empty:
        st.info("득표 추이 데이터가 없습니다.")
        return

    # 연도/선거 구분
    year_col = next((c for c in ["연도","year"] if c in ts.columns), None)
    if year_col is None:
        st.dataframe(ts)
        return

    value_cols = [c for c in ts.columns if c not in ["코드","선거구명",year_col,"선거명","election"]]
    if not value_cols:
        st.dataframe(ts)
        return

    plot_df = ts[[year_col] + value_cols].copy()
    plot_df = plot_df.set_index(year_col)
    # Streamlit 기본 라인차트 (의존성 최소화)
    st.line_chart(plot_df)

# -------- 인구 정보 박스 --------
def render_population_box(pop_df: pd.DataFrame):
    box = st.container()
    with box:
        st.markdown("**인구 정보**")

        if pop_df is None or pop_df.empty:
            st.info("인구 데이터가 없습니다.")
            return

        r = pop_df.iloc[0]
        elder_col  = next((c for c in ["고령층비율","65세이상비율","age65p"] if c in pop_df.columns), None)
        youth_col  = next((c for c in ["청년층비율","39세이하비율","age39m"] if c in pop_df.columns), None)
        mid_col    = next((c for c in ["40_59비율","40-59비율","age40_59p"] if c in pop_df.columns), None)
        male_col   = next((c for c in ["남성비율","남","male_p"] if c in pop_df.columns), None)
        female_col = next((c for c in ["여성비율","여","female_p"] if c in pop_df.columns), None)
        total_voter= next((c for c in ["유권자수","유권자 수","voters"] if c in pop_df.columns), None)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("고령층 비율(65+)", _fmt_pct(_safe_float(r.get(elder_col), None)) if elder_col else "N/A")
            st.metric("청년층 비율(≤39)", _fmt_pct(_safe_float(r.get(youth_col), None)) if youth_col else "N/A")
        with c2:
            st.metric("40-59세 비율", _fmt_pct(_safe_float(r.get(mid_col), None)) if mid_col else "N/A")
            v = _safe_float(r.get(total_voter), None) if total_voter else None
            st.metric("유권자 수", f"{int(v):,}" if isinstance(v,(int,float)) else "N/A")
        with c3:
            st.metric("남성 비율", _fmt_pct(_safe_float(r.get(male_col), None)) if male_col else "N/A")
            st.metric("여성 비율", _fmt_pct(_safe_float(r.get(female_col), None)) if female_col else "N/A")
