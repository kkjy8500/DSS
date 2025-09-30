import streamlit as st
import pandas as pd
from pathlib import Path

from utils import (
    load_csv_safe, parse_int, parse_float_pct, fmt_int, fmt_pct2,
    candidates_long_from_wide, get_top3_and_gap, get_available_districts,
    inject_pretendard, badge, cache_data
)
from charts import (
    metric_triplet, top3_cards, results_table, incumbent_card
)

DATA_DIR = Path("data")
FILE_COMP = DATA_DIR / "(sample)party_competence.csv"
FILE_GE24 = DATA_DIR / "5_na_dis_results.csv"
FILE_INC  = DATA_DIR / "current_info.csv"

st.set_page_config(
    page_title="지역별 대시보드 (정치지형1 · 24총선 · 현직)",
    page_icon="📊",
    layout="wide"
)

inject_pretendard()  # 예쁜 폰트 적용 (Pretendard)

st.title("지역별 페이지")

# -----------------------------
# 데이터 로드 (캐시)
# -----------------------------
@cache_data
def load_all():
    df_comp = load_csv_safe(FILE_COMP)            # (sample)party_competence.csv
    df_ge   = load_csv_safe(FILE_GE24)            # 5_na_dis_results.csv
    df_inc  = load_csv_safe(FILE_INC)             # current_info.csv
    return df_comp, df_ge, df_inc

df_comp, df_ge, df_inc = load_all()

# 기본 유효성
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

# 지역 목록 (세 파일 교집합)
district_opts = get_available_districts(df_comp, df_ge, df_inc)  # [(코드, 선거구)]
if not district_opts:
    st.warning("표시 가능한 지역이 없습니다.")
    st.stop()

# 상단 Selectbox
opt_labels = [f"{name} ({code})" for code, name in district_opts]
opt_map = {f"{name} ({code})": (code, name) for code, name in district_opts}
choice = st.selectbox("지역구 선택", opt_labels, index=0)
sel_code, sel_name = opt_map[choice]

# -----------------------------
# 데이터 전처리 (선거결과 2024만)
# -----------------------------
df_ge_2024 = df_ge[df_ge["연도"].astype(str) == "2024"].copy()

# 후보 wide -> long
df_long = candidates_long_from_wide(df_ge_2024)

# 선택 지역 필터
comp_row = df_comp[df_comp["코드"] == sel_code].head(1)
inc_row  = df_inc[df_inc["코드"] == sel_code].head(1)
res_rows = df_long[df_long["코드"] == sel_code].copy()

if comp_row.empty or inc_row.empty or res_rows.empty:
    st.warning("선택한 지역의 표시 데이터가 충분하지 않습니다.")
    st.stop()

# 숫자 파싱/포맷 준비
try:
    jinbo_members = parse_int(comp_row["진보당 당원수"].iloc[0])
except Exception:
    jinbo_members = None
try:
    jinbo_cands   = parse_int(comp_row["진보당 지방선거후보"].iloc[0])
except Exception:
    jinbo_cands = None

# 상위 1~3위 & 격차 계산 (득표율 기준)
top3_df, gap_pct = get_top3_and_gap(res_rows)

# -----------------------------
# 요약 메트릭 (정치지형1 + 격차)
# -----------------------------
st.subheader("요약")
metric_triplet(
    title1="진보당 당원수(명)",
    value1=fmt_int(jinbo_members) if jinbo_members is not None else "데이터 없음",
    title2="진보당 지방선거 후보(명) · 기준: 2022",
    value2=fmt_int(jinbo_cands) if jinbo_cands is not None else "데이터 없음",
    title3="1-2위 격차(%p, 2024)",
    value3=fmt_pct2(gap_pct, suffix=""),
)

st.caption(
    badge("출처", "(sample)party_competence.csv / 5_na_dis_results.csv (연도=2024)") +
    " " +
    badge("표시", "절대값, 득표율 소수점 2자리")
)

# -----------------------------
# 24년 총선결과 (상위 1~3위 카드 + 전체 표)
# -----------------------------
st.subheader("24년 총선결과")
top3_cards(top3_df)
results_table(res_rows)

st.caption(
    badge("출처", "5_na_dis_results.csv (연도=2024)") + " " +
    badge("정책", "후보 이름/정당은 CSV 문자열 그대로, 정당 색상 미사용")
)

# -----------------------------
# 현직 정보 (KPI1=24년 득표율, KPI2=1-2위 격차)
# -----------------------------
st.subheader("현직 정보")
incumbent_card(
    sel_name=sel_name,
    row=inc_row.iloc[0],
    kpi1_name="24년 득표율",
    kpi1_value=parse_float_pct(inc_row["24년득표율"].iloc[0]),  # %문자 제거→float
    kpi2_name="1-2위 격차",
    kpi2_value=gap_pct,  # 위에서 계산한 격차(%p)
)

st.caption(
    badge("출처", "current_info.csv / 5_na_dis_results.csv") + " " +
    badge("표시", "연령·선수 문자열 그대로, 인물경쟁력/재출마가능성 표시")
)
