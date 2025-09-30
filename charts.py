# =============================
# File: charts.py
# =============================
from __future__ import annotations

import pandas as pd
import streamlit as st
import altair as alt

from metrics import COLORS, compute_24_gap

# -----------------------------
# 유틸
# -----------------------------
def _safe_float(v, default=None):
    try:
        return float(v)
    except Exception:
        return default

def _fmt_pct(x):
    return f"{x:.2f}%" if isinstance(x, (int, float)) else "N/A"

def _fmt_gap(x):
    return f"{x:.2f}p" if isinstance(x, (int, float)) else "N/A"

# -----------------------------
# 카드: 24년 총선 결과 (좌측)
# -----------------------------
def render_results_2024_card(res_row: pd.DataFrame, df_24: pd.DataFrame | None = None, code: str | None = None):
    if res_row is None or res_row.empty:
        st.info("해당 선거구의 24년 결과 데이터가 없습니다.")
        return

    # 컬럼 후보들(데이터 상황에 따라 유연하게)
    col_1n = next((c for c in ["1위이름","1위 후보","1위_이름","1st_name"] if c in res_row.columns), None)
    col_1p = next((c for c in ["1위정당","1위 정당","1st_party"] if c in res_row.columns), None)
    col_1v = next((c for c in ["1위득표율","1위 득표율","1st_share"] if c in res_row.columns), None)

    col_2n = next((c for c in ["2위이름","2위 후보","2위_이름","2nd_name"] if c in res_row.columns), None)
    col_2p = next((c for c in ["2위정당","2위 정당","2nd_party"] if c in res_row.columns), None)
    col_2v = next((c for c in ["2위득표율","2위 득표율","2nd_share"] if c in res_row.columns), None)

    r = res_row.iloc[0]
    name1 = str(r[col_1n]) if col_1n else "1위"
    party1 = str(r[col_1p]) if col_1p else ""
    share1 = _safe_float(r[col_1v]) if col_1v else None

    name2 = str(r[col_2n]) if col_2n else "2위"
    party2 = str(r[col_2p]) if col_2p else ""
    share2 = _safe_float(r[col_2v]) if col_2v else None

    # 격차
    gap = None
    if share1 is not None and share2 is not None:
        gap = round(share1 - share2, 2)
    elif df_24 is not None and code is not None:
        gap = compute_24_gap(df_24, code)

    with st.container(border=True):
        st.markdown("**24년 총선결과**")
        c1, c2, c3 = st.columns([1.2, 1.2, 1])
        with c1:
            st.metric(label=f"{party1} {name1}", value=_fmt_pct(share1))
        with c2:
            st.metric(label=f"{party2} {name2}", value=_fmt_pct(share2))
        with c3:
            st.metric(label="1~2위 격차", value=_fmt_gap(gap))

# -----------------------------
# 카드: 현직 정보 (우측)
# -----------------------------
def render_incumbent_card(cur_row: pd.DataFrame):
    if cur_row is None or cur_row.empty:
        st.info("현직 정보 데이터가 없습니다.")
        return

    r = cur_row.iloc[0]
    # 후보 컬럼 추출
    name_col = next((c for c in ["의원명","이름","성명","incumbent_name"] if c in cur_row.columns), None)
    party_col = next((c for c in ["정당","소속정당","party"] if c in cur_row.columns), None)
    term_col  = next((c for c in ["선수","당선횟수","terms"] if c in cur_row.columns), None)
    age_col   = next((c for c in ["연령","나이","age"] if c in cur_row.columns), None)
    gender_col= next((c for c in ["성별","gender"] if c in cur_row.columns), None)
    status_col= next((c for c in ["상태","현직여부","status"] if c in cur_row.columns), None)

    with st.container(border=True):
        st.markdown("**현직정보**")
        st.write(
            f"- 의원: **{r.get(name_col, 'N/A')}**  "
            f" / 정당: **{r.get(party_col, 'N/A')}**"
        )
        st.write(
            f"- 선수: **{r.get(term_col, 'N/A')}**  "
            f"/ 성별: **{r.get(gender_col, 'N/A')}**  "
            f"/ 연령: **{r.get(age_col, 'N/A')}**"
        )
        if status_col:
            st.caption(f"상태: {r.get(status_col)}")

# -----------------------------
# 박스: 진보당 현황 (왼쪽 중단)
# -----------------------------
def render_prg_party_box(prg_row: pd.DataFrame, pop_row: pd.DataFrame):
    with st.container(border=True):
        st.markdown("**진보당 현황**")
        if prg_row is None or prg_row.empty:
            st.info("진보당 관련 데이터가 없습니다.")
            return

        r = prg_row.iloc[0]
        # 예상 가능한 컬럼들(유연)
        vote_col = next((c for c in ["진보당_득표율","진보_득표율","progressive_share"] if c in prg_row.columns), None)
        org_col  = next((c for c in ["당원수","조직수","branch_count"] if c in prg_row.columns), None)
        trend_col= next((c for c in ["최근_상승폭","trend_delta"] if c in prg_row.columns), None)

        c1, c2, c3 = st.columns(3)
        with c1:
            v = _safe_float(r.get(vote_col), None)
            st.metric("득표력", _fmt_pct(v))
        with c2:
            st.metric("조직 규모", f"{int(r.get(org_col)):,}" if org_col and pd.notna(r.get(org_col)) else "N/A")
        with c3:
            td = _safe_float(r.get(trend_col), None)
            st.metric("최근 추세(Δ)", f"{td:+.2f}p" if isinstance(td,(int,float)) else "N/A")

        # 보조 정보(인구)
        if pop_row is not None and not pop_row.empty:
            rp = pop_row.iloc[0]
            elder_col = next((c for c in ["고령층비율","65세이상비율","age65p"] if c in pop_row.columns), None)
            youth_col = next((c for c in ["청년층비율","39세이하비율","age39m"] if c in pop_row.columns), None)
            with st.expander("인구 맥락 보기", expanded=False):
                st.write(
                    f"- 고령층 비율: {_fmt_pct(_safe_float(rp.get(elder_col), None)) if elder_col else 'N/A'}  "
                    f"/ 청년층 비율: {_fmt_pct(_safe_float(rp.get(youth_col), None)) if youth_col else 'N/A'}"
                )

# -----------------------------
# 차트: 정당성향별 득표 추이 (오른쪽 중단)
# -----------------------------
def render_vote_trend_chart(ts: pd.DataFrame):
    if ts is None or ts.empty:
        st.info("득표 추이 데이터가 없습니다.")
        return

    # 연도/선거 구분 컬럼 후보
    year_col = next((c for c in ["연도","year"] if c in ts.columns), None)
    if year_col is None:
        st.dataframe(ts)
        return

    value_cols = [c for c in ts.columns if c not in ["코드","선거구명",year_col,"선거명","election"]]
    if not value_cols:
        st.dataframe(ts)
        return

    # 와이드 -> 롱
    plot_df = ts[[year_col] + value_cols].melt(id_vars=[year_col], var_name="계열", value_name="득표율")
    plot_df["득표율"] = pd.to_numeric(plot_df["득표율"], errors="coerce")

    # 색상 매핑(기본값 포함)
    color_scale = alt.Scale(
