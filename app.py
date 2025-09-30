# =============================
# File: app.py
# =============================
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path

from data_loader import (
    load_population_agg,
    load_party_competence,
    load_vote_trend,
    load_results_2024,
    load_current_info,
    load_index_sample
)
from metrics import (
    compute_trend_series,
    compute_summary_metrics,
    compute_24_gap,
)
from charts import (
    render_population_box,
    render_vote_trend_chart,
    render_results_2024_card,
    render_incumbent_card,
    render_prg_party_box,
)

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="전략지역구 조사 — 지역별 페이지", layout="wide")
st.title("전략지역구 조사 · 지역별 페이지")

DATA_DIR = Path("data")

# -----------------------------
# Load Data
# -----------------------------
with st.spinner("데이터 불러오는 중..."):
    df_pop = load_population_agg(DATA_DIR)               # 지역구 단위 합산
    df_prg = load_party_competence(DATA_DIR)
    df_trend = load_vote_trend(DATA_DIR)
    df_24 = load_results_2024(DATA_DIR)
    df_curr = load_current_info(DATA_DIR)
    df_idx = load_index_sample(DATA_DIR)  # 선택: EE_/PL_* A지표 등 외부 제공치

# 가용 지역 목록(코드/이름)
regions = (
    df_pop[["코드", "선거구명"]]
    .drop_duplicates()
    .sort_values("선거구명")
)

# 사이드바 — 지역 선택
st.sidebar.header("지역 선택")
sel_label = st.sidebar.selectbox(
    "선거구를 선택하세요",
    regions["선거구명"].tolist(),
)
sel_code = regions.loc[regions["선거구명"] == sel_label, "코드"].iloc[0]

# -----------------------------
# 상단 레이아웃: 좌(24년 결과) — 우(현직정보)
# -----------------------------
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("24년 총선결과")
    res_row = df_24[df_24["코드"] == sel_code]
    render_results_2024_card(res_row)

with col_right:
    st.subheader("현직정보")
    cur_row = df_curr[df_curr["코드"] == sel_code]
    render_incumbent_card(cur_row)

st.divider()

# -----------------------------
# 중단: 진보당 현황 + 정당성향별 득표추이
# -----------------------------
col_a, col_b = st.columns([0.9, 1.1])

with col_a:
    st.subheader("진보당 현황")
    prg_row = df_prg[df_prg["코드"] == sel_code]
    pop_row = df_pop[df_pop["코드"] == sel_code]
    render_prg_party_box(prg_row, pop_row)

with col_b:
    st.subheader("정당성향별 득표추이")
    # 2016~2025 전체 10개 선거 반영 (dataset에 존재하는 항목 기준)
    ts = compute_trend_series(df_trend, sel_code)
    render_vote_trend_chart(ts)

# 지표 요약(유동성/경합도 등) — 우측 아래 간략 배치
summary = compute_summary_metrics(df_trend, df_24, df_idx, sel_code)
st.caption(
    f"요약지표 · 진보정당득표력: {summary['PL_prg_str']:.2f}% · 유동성B: {summary['PL_swing_B']} · 경합도B: {summary['PL_gap_B']:.2f}p"
)

st.divider()

# -----------------------------
# 하단: 인구 정보(3-in-1 박스)
# -----------------------------
st.subheader("인구 정보")
render_population_box(df_pop[df_pop["코드"] == sel_code])

# 푸터
st.write("")
st.caption("© 2025 전략지역구 조사 · Streamlit 대시보드")


# =============================
# File: data_loader.py
# =============================
from __future__ import annotations

import pandas as pd
from pathlib import Path

# 공통 컬러 라벨 등은 charts.py에서 정의


def _std_code(series):
    # 코드 표준화: 문자열로 통일
    return series.astype(str).str.strip()


def load_population_agg(data_dir: Path) -> pd.DataFrame:
    """population.csv(행정동 단위)를 지역구(코드) 단위로 합산.
    출력 컬럼: 코드, 선거구명, 전체 유권자, 2030, 4050, 65세 이상, 2030 남성, 2030 여성, 2030 1인가구
    비율 계산은 charts/metrics에서 수행.
    """
    fp = data_dir / "population.csv"
    df = pd.read_csv(fp)
    # 표준화
    df["코드"] = _std_code(df["지역구코드"]) if "지역구코드" in df.columns else _std_code(df["코드"])  # 안전장치
    # 선거구명 생성: "시/도 + 지역구" 형태
    df["선거구명"] = df[["시/도", "지역구"]].astype(str).agg(" ".join, axis=1)

    # 합산 대상 숫자 컬럼 보정
    num_cols = [
        "전체 유권자", "2030", "4050", "65세 이상", "2030 남성", "2030 여성", "2030 1인가구",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = 0

    g = df.groupby(["코드", "선거구명"], as_index=False)[num_cols].sum()
    return g


def load_party_competence(data_dir: Path) -> pd.DataFrame:
    fp = data_dir / "(sample)party_competence.csv"
    df = pd.read_csv(fp)
    df["코드"] = _std_code(df["코드"]) if "코드" in df.columns else _std_code(df.iloc[:,0])
    # 열 보정
    rename = {
        "진보당 당원수": "진보당_당원수",
        "진보당 지방선거후보": "진보당_지방선거후보",
    }
    df = df.rename(columns=rename)
    for c in ["진보당_당원수", "진보당_지방선거후보"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[["코드", "선거구", "진보당_당원수", "진보당_지방선거후보"]]


def load_vote_trend(data_dir: Path) -> pd.DataFrame:
    fp = data_dir / "vote_trend_sample_all.csv"
    df = pd.read_csv(fp)
    df["코드"] = _std_code(df["code"]) if "code" in df.columns else _std_code(df["코드"])  # 안전장치
    df["label"] = df["label"].astype(str)
    df["election"] = df["election"].astype(str)
    df["prop"] = pd.to_numeric(df["prop"], errors="coerce")
    return df


def load_results_2024(data_dir: Path) -> pd.DataFrame:
    fp = data_dir / "5_na_dis_results.csv"
    df = pd.read_csv(fp)
    df["코드"] = _std_code(df["코드"]) if "코드" in df.columns else _std_code(df["code"])  # 안전장치
    # 득표율/수치 숫자화
    for c in df.columns:
        if ("득표율" in c) or (c in ["투표율", "선거인수", "투표수", "무효투표수", "기권수", "계"]):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_current_info(data_dir: Path) -> pd.DataFrame:
    fp = data_dir / "current_info.csv"
    df = pd.read_csv(fp)
    df["코드"] = _std_code(df["코드"]) if "코드" in df.columns else _std_code(df.iloc[:,0])
    # 숫자화
    for c in ["연령", "선수", "24년득표", "24년득표율", "인물경쟁력", "재출마가능성"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_index_sample(data_dir: Path) -> pd.DataFrame | None:
    """index_sample.csv가 있다면 cp949로 읽고 지표명을 컬럼으로 파싱.
    예상 컬럼 예: EE_voter_count, EE_newcomers, EE_65plus_ratio, EE_2030_ratio, EE_4050_ratio, EE_f2030_ratio,
                 PL_swing_A, PL_gap_A, PL_swing_B, PL_gap_B, PL_incum_str, PL_incum_rpl
    첫 열은 '선거구명,코드, ...' 형태의 한 줄 CSV로 들어올 수 있으므로 split 처리.
    """
    fp = data_dir / "index_sample.csv"
    if not fp.exists():
        return None
    try:
        raw = pd.read_csv(fp, header=None, encoding="cp949")
    except Exception:
        raw = pd.read_csv(fp, header=None, encoding="utf-8")

    # 각 행이 큰 문자열로 들어온 형태 → 쉼표 기반 split
    def parse_line(s: str) -> list[str]:
        s = str(s).strip().strip('"')
        parts = [p.strip() for p in s.split(',') if p is not None]
        return parts

    rows = [parse_line(x) for x in raw.iloc[:,0].tolist()]
    # 첫 행: 헤더, 이후 데이터
    header = rows[0]
    data = rows[1:]
    df = pd.DataFrame(data, columns=header)
    # 표준화
    if "코드" in df.columns:
        df["코드"] = _std_code(df["코드"])
    elif len(df.columns) >= 2:
        df.rename(columns={df.columns[1]: "코드"}, inplace=True)
        df["코드"] = _std_code(df["코드"])
    # 숫자 컬럼 변환
    for c in df.columns:
        if c not in ("코드", header[0]):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # 선거구명 컬럼명 통일
    if header[0] not in ("선거구명", "선거구"):
        df.rename(columns={header[0]: "선거구명"}, inplace=True)
    return df


# =============================
# File: metrics.py
# =============================
from __future__ import annotations

import pandas as pd
from typing import Dict

# 색상 팔레트 (차트에서 사용)
COLORS = {
    "민주": "#1976D2",
    "보수": "#D32F2F",
    "진보": "#F9A825",
    "기타": "#9E9E9E",
    "진보당": "#E91E63",
}

# 선거 정렬(가능한 10개: 2016~2025)
ELECTION_ORDER = [
    "2016_na_pro",
    "2017_president",
    "2018_loc_pro",
    "2020_na_pro",
    "2022_president",
    "2024_na_pro",
    "2025_president",
]
# 위 목록 외 추가 항목이 있으면 뒤에 정렬되도록 보조 키 제공


def _election_sort_key(x: str) -> tuple[int, str]:
    try:
        idx = ELECTION_ORDER.index(x)
        return (0, idx)
    except ValueError:
        return (1, x)


def compute_trend_series(df_trend: pd.DataFrame, code: str) -> pd.DataFrame:
    """선거코드별(시간축) label별 prop% 피벗. 소수점 2자리 반올림.
    반환: columns=['election','민주','보수','진보','기타']
    """
    t = df_trend[df_trend["코드"] == str(code)].copy()
    t = t[t["label"].isin(["민주", "보수", "진보", "기타"])]
    # 선거 필터: 2016~2025 전체 포함(데이터에 존재하는 한)
    t["_key"] = t["election"].apply(_election_sort_key)
    t = t.sort_values(["_key", "election", "label"]).drop(columns=["_key"])
    p = t.pivot_table(index="election", columns="label", values="prop", aggfunc="mean").reset_index()
    for c in ["민주", "보수", "진보", "기타"]:
        if c in p.columns:
            p[c] = p[c].round(2)
        else:
            p[c] = pd.NA
    return p


def compute_summary_metrics(df_trend: pd.DataFrame, df_24: pd.DataFrame, df_idx: pd.DataFrame | None, code: str) -> Dict[str, float]:
    """요약 지표 산출.
    - PL_prg_str: 2016 이후 비대선(총선/지선)에서 진보 평균 득표율
    - PL_swing_B, PL_gap_B: 2016 이후 10개 선거 기준 (데이터 가용한 범위)
    - A지표/EE_* 등은 index_sample이 있으면 해당 값을 사용(우선)
    """
    out = {"PL_prg_str": float("nan"), "PL_swing_B": float("nan"), "PL_gap_B": float("nan")}

    # index_sample 우선 사용
    if df_idx is not None and not df_idx.empty:
        row = df_idx[df_idx["코드"] == str(code)]
        if not row.empty:
            for k in ["PL_swing_B", "PL_gap_B"]:
                if k in row.columns:
                    out[k] = float(row.iloc[0][k]) if pd.notna(row.iloc[0][k]) else float("nan")

    # 진보정당득표력(비대선 평균)
    t = df_trend[(df_trend["코드"] == str(code)) & (~df_trend["election"].str.contains("president", na=False))]
    prg = t[t["label"] == "진보"]["prop"].dropna()
    if len(prg) > 0:
        out["PL_prg_str"] = round(prg.mean(), 2)

    # B지표 계산(데이터 기반): 1위 블록 변화 횟수, 평균 1-2위 격차
    # 선거별 블록 득표율 합이 아닌, label prop 자체가 100 합 가정.
    seq = (
        df_trend[df_trend["코드"] == str(code)]
        .groupby(["election", "label"], as_index=False)["prop"].mean()
    )
    if not seq.empty:
        # 정렬
        seq["_key"] = seq["election"].apply(_election_sort_key)
        seq = seq.sort_values(["_key", "election"]).drop(columns=["_key"])
        # 각 선거의 1~2위
        top = (
            seq.sort_values(["election", "prop"], ascending=[True, False])
            .groupby("election")
            .head(2)
        )
        # swing_B
        winners = top.groupby("election").first().reset_index()[["election", "label"]]
        winners["prev"] = winners["label"].shift(1)
        swing_b = int((winners["label"] != winners["prev"]) & winners["prev"].notna()).sum()
        out["PL_swing_B"] = float(swing_b) if pd.isna(out.get("PL_swing_B")) else out["PL_swing_B"]
        # gap_B (평균 1-2위 격차)
        gaps = (
            top.groupby("election")["prop"].apply(lambda s: s.max() - s.min()).dropna()
        )
        if len(gaps) > 0:
            out["PL_gap_B"] = round(float(gaps.mean()), 2) if pd.isna(out.get("PL_gap_B")) else out["PL_gap_B"]

    return out


def compute_24_gap(row_24: pd.DataFrame) -> float:
    """24년 1–2위 득표율 격차(%p) 계산."""
    if row_24 is None or row_24.empty:
        return float("nan")
    # 후보*_득표율 컬럼 수집
    cols = [c for c in row_24.columns if c.endswith("득표율") and c.startswith("후보")]
    vals = (
        row_24.iloc[0][cols].astype(float).dropna().sort_values(ascending=False).tolist()
        if len(row_24) > 0 else []
    )
    if len(vals) >= 2:
        return round(vals[0] - vals[1], 2)
    return float("nan")


# =============================
# File: charts.py
# =============================
from __future__ import annotations

import streamlit as st
import pandas as pd
import altair as alt
from typing import Optional

from metrics import COLORS, compute_24_gap


def _fmt_pct(x: Optional[float]) -> str:
    if pd.isna(x):
        return "–"
    return f"{x:.2f}%"


# -----------------------------
# 24년 총선결과 카드
# -----------------------------

def render_results_2024_card(res_row: pd.DataFrame):
    if res_row is None or res_row.empty:
        st.info("데이터 없음")
        return

    # 후보 리스트 구성
    cand_cols = []
    for i in range(1, 8):
        cand_cols.append({
            "name": f"후보{i}_이름",
            "vote": f"후보{i}_득표수",
            "pct": f"후보{i}_득표율",
        })

    data = []
    r = res_row.iloc[0]
    for c in cand_cols:
        if c["name"] in res_row.columns and pd.notna(r[c["name"]]):
            data.append({
                "이름": r[c["name"]],
                "득표수": pd.to_numeric(r.get(c["vote"], None), errors="coerce"),
                "득표율": pd.to_numeric(r.get(c["pct"], None), errors="coerce"),
            })

    df = pd.DataFrame(data).dropna(subset=["득표율"]).sort_values("득표율", ascending=False)
    gap = compute_24_gap(res_row)

    # 상단 배지
    st.markdown(
        f"**1–2위 격차**: <span style='background:#EEE;padding:3px 8px;border-radius:6px;'> {_fmt_pct(gap)} </span>",
        unsafe_allow_html=True,
    )

    # 표
    if not df.empty:
        df_display = df.copy()
        df_display["득표율"] = df_display["득표율"].map(lambda v: f"{v:.2f}%" if pd.notna(v) else "–")
        st.dataframe(
            df_display.reset_index(drop=True),
            hide_index=True,
            use_container_width=True,
        )

    # 하단 보조 지표
    meta = {
        "투표율": res_row.iloc[0].get("투표율"),
        "무효": res_row.iloc[0].get("무효투표수"),
        "기권": res_row.iloc[0].get("기권수"),
    }
    st.caption(
        " · ".join([f"{k}: {_fmt_pct(v) if k=='투표율' else (int(v) if pd.notna(v) else '–')}" for k, v in meta.items()])
    )


# -----------------------------
# 현직정보 카드
# -----------------------------

def render_incumbent_card(cur_row: pd.DataFrame):
    if cur_row is None or cur_row.empty:
        st.info("데이터 없음")
        return
    r = cur_row.iloc[0]
    left, right = st.columns([1, 1])
    with left:
        st.markdown(
            f"**{r.get('이름', '–')}** · {r.get('정당', '–')}\n\n"
            f"성별: {r.get('성별', '–')} · 연령: {int(r['연령']) if pd.notna(r.get('연령')) else '–'}세 · 선수: {int(r['선수']) if pd.notna(r.get('선수')) else '–'}선"
        )
        st.caption(
            f"24년 득표: {int(r['24년득표']) if pd.notna(r.get('24년득표')) else '–'}"
            f" · 24년 득표율: {_fmt_pct(r.get('24년득표율'))}"
        )
    with right:
        st.markdown(
            f"**인물경쟁력**: {r.get('인물경쟁력', '–')}\n\n**재출마가능성**: {r.get('재출마가능성', '–')}"
        )
        if pd.notna(r.get("최근경력")):
            st.caption(f"최근경력: {r['최근경력']}")


# -----------------------------
# 진보당 현황 박스
# -----------------------------

def render_prg_party_box(prg_row: pd.DataFrame, pop_row: pd.DataFrame):
    c1, c2 = st.columns(2)
    m1 = int(prg_row.iloc[0]["진보당_당원수"]) if (prg_row is not None and not prg_row.empty and pd.notna(prg_row.iloc[0].get("진보당_당원수"))) else None
    m2 = int(prg_row.iloc[0]["진보당_지방선거후보"]) if (prg_row is not None and not prg_row.empty and pd.notna(prg_row.iloc[0].get("진보당_지방선거후보"))) else None

    with c1:
        st.metric(label="진보당 당원수", value=f"{m1:,}" if m1 is not None else "–")
    with c2:
        st.metric(label="진보당 지방선거 후보 수(2022)", value=f"{m2:,}" if m2 is not None else "–")


# -----------------------------
# 정당성향별 득표추이 차트
# -----------------------------

def render_vote_trend_chart(pivot_ts: pd.DataFrame):
    if pivot_ts is None or pivot_ts.empty:
        st.info("데이터 없음")
        return

    df_long = pivot_ts.melt(id_vars=["election"], value_vars=["민주", "보수", "진보", "기타"], var_name="label", value_name="prop")

    line = (
        alt.Chart(df_long)
        .mark_line(point=True)
        .encode(
            x=alt.X("election:N", sort=None, title="선거"),
            y=alt.Y("prop:Q", title="득표율(%)"),
            color=alt.Color("label:N", scale=alt.Scale(domain=list(COLORS.keys()), range=list(COLORS.values()))),
            tooltip=["election", "label", alt.Tooltip("prop", format=".2f")],
        )
        .properties(height=280)
    )
    st.altair_chart(line, use_container_width=True)


# -----------------------------
# 인구 정보 3-in-1 박스
# -----------------------------

def render_population_box(pop_row: pd.DataFrame):
    if pop_row is None or pop_row.empty:
        st.info("데이터 없음")
        return
    r = pop_row.iloc[0]
    total = float(r.get("전체 유권자", 0) or 0)
    v2030 = float(r.get("2030", 0) or 0)
    v4050 = float(r.get("4050", 0) or 0)
    v65p  = float(r.get("65세 이상", 0) or 0)
    m2030 = float(r.get("2030 남성", 0) or 0)
    f2030 = float(r.get("2030 여성", 0) or 0)
    s2030 = float(r.get("2030 1인가구", 0) or 0)

    # 비율 계산 (소수점 2자리)
    pct = lambda a, b: round((a / b * 100.0), 2) if (b and b > 0) else float("nan")

    # (A) 2030/4050/65+
    a_df = pd.DataFrame({
        "구분": ["2030", "4050", "65+"],
        "비율(%)": [pct(v2030, total), pct(v4050, total), pct(v65p, total)],
    })
    # (B) 2030 성별
    b_df = pd.DataFrame({
        "구분": ["2030 남성", "2030 여성"],
        "비율(%)": [pct(m2030, v2030) if v2030 else float("nan"), pct(f2030, v2030) if v2030 else float("nan")],
    })
    # (C) 2030 1인가구
    c_df = pd.DataFrame({
        "구분": ["2030 1인가구"],
        "비율(%)": [pct(s2030, v2030) if v2030 else float("nan")],
    })

    box = st.container(border=True)
    c1, c2, c3 = box.columns(3)

    with c1:
        st.markdown("**연령대 구성(%)**")
        st.dataframe(a_df, hide_index=True, use_container_width=True)
    with c2:
        st.markdown("**2030 성별 구성(%)**")
        st.dataframe(b_df, hide_index=True, use_container_width=True)
    with c3:
        st.markdown("**2030 1인가구 비율(%)**")
        st.dataframe(c_df, hide_index=True, use_container_width=True)
