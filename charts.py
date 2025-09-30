# =============================
# File: charts.py
# =============================
import pandas as pd
import streamlit as st
from metrics import compute_24_gap

# -------- 유틸 --------
def _to_float(v, default=None):
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return default
        s = str(v).replace(",", "").strip()
        return float(s) if s not in ("", "nan", "None") else default
    except Exception:
        return default

def _to_int(v, default=None):
    f = _to_float(v, default=None)
    try:
        return int(f) if f is not None else default
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

    c1n = next((c for c in ["1위이름", "1위 후보", "1위_이름", "1st_name"] if c in res_row.columns), None)
    c1p = next((c for c in ["1위정당", "1위 정당", "1st_party"] if c in res_row.columns), None)
    c1v = next((c for c in ["1위득표율", "1위 득표율", "1st_share"] if c in res_row.columns), None)

    c2n = next((c for c in ["2위이름", "2위 후보", "2위_이름", "2nd_name"] if c in res_row.columns), None)
    c2p = next((c for c in ["2위정당", "2위 정당", "2nd_party"] if c in res_row.columns), None)
    c2v = next((c for c in ["2위득표율", "2위 득표율", "2nd_share"] if c in res_row.columns), None)

    r = res_row.iloc[0]
    name1 = str(r.get(c1n)) if c1n else "1위"
    party1 = str(r.get(c1p)) if c1p else ""
    share1 = _to_float(r.get(c1v))

    name2 = str(r.get(c2n)) if c2n else "2위"
    party2 = str(r.get(c2p)) if c2p else ""
    share2 = _to_float(r.get(c2v))

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
            st.metric(label=f"{(party1 + ' ' + name1).strip()}", value=_fmt_pct(share1))
        with col2:
            st.metric(label=f"{(party2 + ' ' + name2).strip()}", value=_fmt_pct(share2))
        with col3:
            st.metric(label="1~2위 격차", value=_fmt_gap(gap))


# -------- 현직 정보 카드 --------
def render_incumbent_card(cur_row: pd.DataFrame):
    if cur_row is None or cur_row.empty:
        st.info("현직 정보 데이터가 없습니다.")
        return

    r = cur_row.iloc[0]
    name_col   = next((c for c in ["의원명", "이름", "성명", "incumbent_name"] if c in cur_row.columns), None)
    party_col  = next((c for c in ["정당", "소속정당", "party"] if c in cur_row.columns), None)
    term_col   = next((c for c in ["선수", "당선횟수", "terms"] if c in cur_row.columns), None)
    age_col    = next((c for c in ["연령", "나이", "age"] if c in cur_row.columns), None)
    gender_col = next((c for c in ["성별", "gender"] if c in cur_row.columns), None)
    status_col = next((c for c in ["상태", "현직여부", "status"] if c in cur_row.columns), None)

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
        # (득표력) 업로드 파일에 없을 수 있음 → N/A 안전 처리
        vote_col = next((c for c in [
            "진보당_득표율", "진보_득표율", "progressive_share", "prg_share", "진보당 득표율"
        ] if c in prg_row.columns), None)

        # (조직 규모) 업로드 파일 반영: '진보당 당원수' 우선 인식
        org_col = next((c for c in [
            "진보당 당원수", "당원수", "조직수", "branch_count", "members"
        ] if c in prg_row.columns), None)

        # (지방선거 후보 수) 있으면 캡션으로 추가
        cand_col = next((c for c in [
            "진보당 지방선거후보", "지방선거후보수", "local_candidates"
        ] if c in prg_row.columns), None)

        trend_col = next((c for c in [
            "최근_상승폭", "trend_delta", "delta"
        ] if c in prg_row.columns), None)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("득표력", _fmt_pct(_to_float(r.get(vote_col))) if vote_col else "N/A")
        with c2:
            st.metric("조직 규모", f"{_to_int(r.get(org_col)):,}" if org_col and pd.notna(r.get(org_col)) else "N/A")
        with c3:
            td = _to_float(r.get(trend_col))
            st.metric("최근 추세(Δ)", f"{td:+.2f}p" if isinstance(td, (int, float)) else "N/A")

        if cand_col and pd.notna(r.get(cand_col)):
            st.caption(f"지방선거 후보 수: {_to_int(r.get(cand_col)):,}명")

        # 인구 맥락 (아래 render_population_box에서 비율 계산 지원)
        if pop_row is not None and not pop_row.empty:
            rp = pop_row.iloc[0]
            elder_col = next((c for c in ["고령층비율", "65세이상비율", "age65p"] if c in pop_row.columns), None)
            youth_col = next((c for c in ["청년층비율", "39세이하비율", "age39m"] if c in pop_row.columns), None)
            with st.expander("인구 맥락 보기", expanded=False):
                elder = _fmt_pct(_to_float(rp.get(elder_col))) if elder_col and pd.notna(rp.get(elder_col)) else "N/A"
                youth = _fmt_pct(_to_float(rp.get(youth_col))) if youth_col and pd.notna(rp.get(youth_col)) else "N/A"
                st.write(f"- 고령층 비율: {elder} / 청년층 비율: {youth}")


# -------- 득표 추이 차트 --------
def render_vote_trend_chart(ts: pd.DataFrame):
    """
    기대 입력형:
      index: year(int) 혹은 'year' 컬럼
      columns: 각 성향/정당 레이블
      values: 득표율 (0~100 기준)
    """
    if ts is None or ts.empty:
        st.info("득표 추이 데이터가 없습니다.")
        return

    plot_df = ts.copy()
    if "year" in plot_df.columns:
        plot_df = plot_df.set_index("year")
    elif "연도" in plot_df.columns:
        plot_df = plot_df.set_index("연도")
    # 이미 연도가 인덱스인 피벗 형태면 그대로 사용

    # 성향 컬럼만 남기기 (코드/지역명/선거명 제거)
    drop_cands = {"코드", "선거구명", "지역구", "district", "선거명", "election"}
    value_cols = [c for c in plot_df.columns if c not in drop_cands]
    if not value_cols:
        st.dataframe(ts)
        return

    st.line_chart(plot_df[value_cols])


# -------- 인구 정보 박스 --------
def render_population_box(pop_df: pd.DataFrame):
    box = st.container()
    with box:
        st.markdown("**인구 정보**")

        if pop_df is None or pop_df.empty:
            st.info("인구 데이터가 없습니다.")
            return

        r = pop_df.iloc[0]

        # 1) 비율 컬럼이 이미 있으면 우선 사용
        elder_col  = next((c for c in ["고령층비율", "65세이상비율", "age65p"] if c in pop_df.columns), None)
        youth_col  = next((c for c in ["청년층비율", "39세이하비율", "age39m"] if c in pop_df.columns), None)
        mid_col    = next((c for c in ["40_59비율", "40-59비율", "age40_59p", "4050비율"] if c in pop_df.columns), None)

        male_col   = next((c for c in ["남성비율", "남", "male_p", "2030 남성비율"] if c in pop_df.columns), None)
        female_col = next((c for c in ["여성비율", "여", "female_p", "2030 여성비율"] if c in pop_df.columns), None)

        elder_pct = _to_float(r.get(elder_col)) if elder_col else None
        youth_pct = _to_float(r.get(youth_col)) if youth_col else None
        mid_pct   = _to_float(r.get(mid_col))   if mid_col   else None
        male_pct  = _to_float(r.get(male_col))  if male_col  else None
        female_pct= _to_float(r.get(female_col))if female_col else None

        # 2) 없으면 인원수 → 비율 계산
        if any(v is None for v in [elder_pct, youth_pct, mid_pct, male_pct, female_pct]):
            total_col = next((c for c in ["유권자수", "유권자 수", "voters", "전체 유권자"] if c in pop_df.columns), None)
            c2030_col = "2030" if "2030" in pop_df.columns else None
            c4050_col = "4050" if "4050" in pop_df.columns else None
            c65p_col  = "65세 이상" if "65세 이상" in pop_df.columns else None

            total = _to_int(r.get(total_col)) if total_col else None
            v2030 = _to_int(r.get(c2030_col)) if c2030_col else None
            v4050 = _to_int(r.get(c4050_col)) if c4050_col else None
            v65p  = _to_int(r.get(c65p_col))  if c65p_col  else None

            def pct(val):
                return (val / total * 100.0) if (isinstance(val, (int, float)) and isinstance(total, (int, float)) and total) else None

            if elder_pct is None:
                elder_pct = pct(v65p)
            if youth_pct is None:
                youth_pct = pct(v2030)
            if mid_pct is None:
                mid_pct = pct(v4050)

            # 2030 남/여 인원만 있고 비율이 없을 때: 2030 내부 구성 비율로 계산
            if male_pct is None and "2030 남성" in pop_df.columns and v2030:
                male_pct = _to_int(r.get("2030 남성")) / v2030 * 100.0 if pd.notna(r.get("2030 남성")) else None
            if female_pct is None and "2030 여성" in pop_df.columns and v2030:
                female_pct = _to_int(r.get("2030 여성")) / v2030 * 100.0 if pd.notna(r.get("2030 여성")) else None

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("고령층 비율(65+)", _fmt_pct(elder_pct))
            st.metric("청년층 비율(≤39)", _fmt_pct(youth_pct))
        with c2:
            st.metric("40-59세 비율", _fmt_pct(mid_pct))
            # 총 유권자 수는 비율 계산에서 사용한 값 재활용(없으면 N/A)
            total_display = None
            for cand in ["유권자수", "유권자 수", "voters", "전체 유권자"]:
                if cand in pop_df.columns:
                    total_display = _to_int(r.get(cand))
                    break
            st.metric("유권자 수", f"{total_display:,}" if isinstance(total_display, (int, float)) else "N/A")
        with c3:
            st.metric("남성 비율", _fmt_pct(male_pct))
            st.metric("여성 비율", _fmt_pct(female_pct))
