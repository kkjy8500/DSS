from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path

from utils import load_csv_safe, parse_int, parse_float_pct, fmt_int, fmt_pct2, candidates_long_from_wide, get_top3_and_gap, get_available_districts, inject_pretendard, cache_data
from charts import top3_cards, results_table, incumbent_card

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="지역구 선정 1단계 조사 결과 대시보드",
    page_icon="🗳️",
    layout="wide",
)

inject_pretendard()

# -----------------------------
# 상단 타이틀(대문)
# -----------------------------
st.title("🗳️ 지역구 선정 1단계 조사 결과")
st.caption("에스티아이")

# -----------------------------
# 데이터 파일 경로
# -----------------------------
DATA_DIR = Path("data")
FILE_COMP = DATA_DIR / "(sample)party_competence.csv"  # 진보당 당원수/지방선거후보수
FILE_GE24 = DATA_DIR / "5_na_dis_results.csv"          # 24년 총선결과(지역구)
FILE_INC  = DATA_DIR / "current_info.csv"              # 현직정보

# -----------------------------
# 데이터 로드(캐시)
# -----------------------------
@cache_data
def load_all():
    df_comp = load_csv_safe(FILE_COMP)
    df_ge   = load_csv_safe(FILE_GE24)
    df_inc  = load_csv_safe(FILE_INC)
    return df_comp, df_ge, df_inc

df_comp, df_ge, df_inc = load_all()

# 필수 컬럼 체크
required_comp_cols = {"코드", "선거구", "진보당 당원수", "진보당 지방선거후보"}
required_ge_cols   = {"코드", "선거구", "연도"}
required_inc_cols  = {"코드", "선거구", "이름", "정당", "성별", "연령", "선수", "24년득표", "24년득표율", "인물경쟁력", "재출마가능성"}

for need, df, name in [
    (required_comp_cols, df_comp, "(sample)party_competence.csv"),
    (required_ge_cols, df_ge, "5_na_dis_results.csv"),
    (required_inc_cols, df_inc, "current_info.csv"),
]:
    missing = need - set(df.columns)
    if missing:
        st.error(f"❌ `{name}`에 필요한 열이 없습니다: {sorted(missing)}")
        st.stop()

# 교집합 지역 목록 (코드, 선거구)
district_opts = get_available_districts(df_comp, df_ge, df_inc)
if not district_opts:
    st.warning("표시 가능한 지역이 없습니다.")
    st.stop()

# -----------------------------
# 사이드바 메뉴 & 지역 선택
# -----------------------------
st.sidebar.header("메뉴 선택")
menu = st.sidebar.radio("페이지", ["종합", "지역별 분석", "데이터 설명"], index=0)

# 데이터 기반 지역 목록 (라벨은 이름만)
opt_labels = [name for code, name in district_opts]
opt_map = {name: (code, name) for code, name in district_opts}
choice = st.sidebar.selectbox("지역을 선택하세요", opt_labels, index=0)
sel_code, sel_name = opt_map[choice]

# -----------------------------
# 공통 전처리 (24년 총선 결과)
# -----------------------------
df_ge_2024 = df_ge[df_ge["연도"].astype(str) == "2024"].copy()
df_long = candidates_long_from_wide(df_ge_2024)

# 선택 지역별 슬라이스
comp_row = df_comp[df_comp["코드"] == sel_code].head(1)
inc_row  = df_inc[df_inc["코드"] == sel_code].head(1)
res_rows = df_long[df_long["코드"] == sel_code].copy()

# -----------------------------
# 페이지 분기
# -----------------------------
if menu == "종합":
    st.subheader("개요")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("대시보드 대상 지역 수", f"{len(district_opts):,}개")
    with c2:
        st.metric("데이터 파일", "3개")
    with c3:
        st.metric("표시 기준", "정치지형1·24총선·현직")

    st.write("---")
    st.markdown("#### 바로 가기")
    st.info("좌측 사이드바에서 **지역을 선택**하고, 상단 라디오에서 **'지역별 분석'**을 선택하면 상세 페이지가 표시됩니다.")

elif menu == "지역별 분석":
    # 선택 지역 데이터 유효성 점검
    if comp_row.empty or inc_row.empty or res_rows.empty:
        st.warning("선택한 지역의 표시 데이터가 충분하지 않습니다.")
        st.stop()

    # 숫자 파싱
    try:
        jinbo_members = parse_int(comp_row["진보당 당원수"].iloc[0])
    except Exception:
        jinbo_members = None
    try:
        jinbo_cands   = parse_int(comp_row["진보당 지방선거후보"].iloc[0])
    except Exception:
        jinbo_cands = None

    # 상위 1~3위 & 격차
    top3_df, gap_pct = get_top3_and_gap(res_rows)

    # 제목
    st.subheader(f"지역별 분석 · **{sel_name}**")

    # ─────────────────────────────
    # 진보당 현황 (2 메트릭)
    # ─────────────────────────────
    st.markdown("##### 진보당 현황")
    m1, m2 = st.columns(2)
    with m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(label="진보당 당원수(명)", value=fmt_int(jinbo_members) if jinbo_members is not None else "데이터 없음")
        st.markdown('</div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(label="진보당 지방선거 후보(명) · 기준: 2022", value=fmt_int(jinbo_cands) if jinbo_cands is not None else "데이터 없음")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ─────────────────────────────
    # 좌우 2단 레이아웃: 좌(24총선결과+격차), 우(현직 정보)
    # ─────────────────────────────
    left, right = st.columns([1.6, 1.0], gap="large")

    # 왼쪽: 24년 총선결과 + 격차
    with left:
        st.markdown("##### 24년 총선결과")
        # 1-2위 격차를 결과 제목 아래에 배치(작게)
        if gap_pct is not None:
            st.markdown(
                f'<div class="badge"><b>1-2위 격차</b> {fmt_pct2(gap_pct, suffix="")}%p</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown('<div class="badge"><b>1-2위 격차</b> 데이터 없음</div>', unsafe_allow_html=True)

        top3_cards(top3_df)
        results_table(res_rows)

    # 오른쪽: 현직 정보 카드
    with right:
        st.markdown("##### 현직 정보")
        incumbent_card(
            sel_name=sel_name,
            row=inc_row.iloc[0],
            kpi1_name="24년 득표율",
            kpi1_value=parse_float_pct(inc_row["24년득표율"].iloc[0]),
            kpi2_name="1-2위 격차",
            kpi2_value=gap_pct,
        )

elif menu == "데이터 설명":
    st.subheader("데이터 설명")
    with st.expander("정치지형1 · (sample)party_competence.csv — 컬럼/샘플 보기", expanded=False):
        st.write(sorted(df_comp.columns))
        st.dataframe(df_comp.head(10), use_container_width=True)
    with st.expander("24년 총선결과 · 5_na_dis_results.csv — 컬럼/샘플 보기", expanded=False):
        st.write(sorted(df_ge.columns))
        st.dataframe(df_ge.head(10), use_container_width=True)
    with st.expander("현직정보 · current_info.csv — 컬럼/샘플 보기", expanded=False):
        st.write(sorted(df_inc.columns))
        st.dataframe(df_inc.head(10), use_container_width=True)

else:
    st.info("좌측 메뉴에서 페이지를 선택하세요.")
