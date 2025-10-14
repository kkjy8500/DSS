# =============================
# File: charts.py
# =============================
from __future__ import annotations
from typing import Optional, Dict, Any
import re

import streamlit as st
import pandas as pd

# ---------------- plotting deps (matplotlib 우선, 없으면 Altair 대체) ----------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager, rcParams

    def _set_korean_font():
        """
        서버/OS별로 가능한 한글 폰트를 자동 적용.
        (우선순위: Malgun Gothic → AppleGothic → NanumGothic → Noto Sans CJK KR)
        """
        candidates = ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK KR Regular"]
        chosen = None
        try:
            installed = {f.name for f in font_manager.fontManager.ttflist}
            for name in candidates:
                if name in installed:
                    chosen = name
                    break
        except Exception:
            chosen = None
        rcParams["font.family"] = chosen or "DejaVu Sans"
        rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지

    _set_korean_font()
except Exception:
    plt = None
    rcParams = None

# Altair (파이/라인 대체 렌더용)
try:
    import altair as alt
except Exception:
    alt = None

# ---------------- metrics (필요 함수만) ----------------
from metrics import compute_24_gap

# ---------------- 유틸 함수 ----------------
def _to_pct_float(v, default=None):
    """'45.2%', '45,2', 0.452, ' 45.2 % ' -> 45.2 (percent)"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    s = str(v).strip().replace(",", "")
    m = re.match(r"^\s*([+-]?\d+(\.\d+)?)\s*%?\s*$", s)
    if not m:
        return default
    x = float(m.group(1))
    if "%" in s:
        return x
    return x * 100.0 if 0 <= x <= 1 else x

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

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame() if df is None else df
    out = df.copy()
    out.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in out.columns]
    return out

# ---------------- 내부: 파이차트 생성 (Altair) ----------------
def _pie_chart(title: str, labels: list[str], values: list[float], colors: list[str], width: int = 260, height: int = 260):
    if alt is None:
        st.info(f"{title} 시각화(Altair)를 사용할 수 없습니다.")
        return
    vals = [(v if isinstance(v, (int, float)) and v > 0 else 0.0) for v in values]
    total = sum(vals)
    if total <= 0:
        st.info(f"{title} 자료가 없습니다.")
        return
    vals = [v / total * 100.0 for v in vals]
    df = pd.DataFrame({"구성": labels, "비율": vals})

    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=60, stroke="white", strokeWidth=1)
        .encode(
            theta=alt.Theta("비율:Q"),
            color=alt.Color("구성:N",
                            scale=alt.Scale(domain=labels, range=colors),
                            legend=None),
            tooltip=[alt.Tooltip("구성:N"), alt.Tooltip("비율:Q", format=".1f")]
        )
        .properties(title=title, width=width, height=height)
    )
    st.altair_chart(chart, use_container_width=False)

# ---------------- 24년 결과 카드 (5_na_dis_results.csv) ----------------
def render_results_2024_card(res_row: pd.DataFrame, df_24: pd.DataFrame = None, code: str = None):
    """해당 선거구의 2024 (없으면 최신연도) 1~2위 득표율과 격차 표시."""
    if res_row is None or res_row.empty:
        st.info("해당 선거구의 24년 결과 데이터가 없습니다.")
        return

    res_row = _norm_cols(res_row)
    if "연도" in res_row.columns:
        try:
            cands = res_row.dropna(subset=["연도"]).copy()
            cands["__year__"] = pd.to_numeric(cands["연도"], errors="coerce")
            if (cands["__year__"] == 2024).any():
                r = cands[cands["__year__"] == 2024].iloc[0]
            else:
                r = cands.loc[cands["__year__"].idxmax()]
        except Exception:
            r = res_row.iloc[0]
    else:
        r = res_row.iloc[0]

    # 다양한 컬럼명 호환
    c1n = next((c for c in ["후보1_이름", "1위이름", "1위 후보", "1위_이름", "1st_name"] if c in res_row.columns), None)
    c1v = next((c for c in ["후보1_득표율", "1위득표율", "1위 득표율", "1st_share", "1위득표율(%)"] if c in res_row.columns), None)
    c2n = next((c for c in ["후보2_이름", "2위이름", "2위 후보", "2위_이름", "2nd_name"] if c in res_row.columns), None)
    c2v = next((c for c in ["후보2_득표율", "2위득표율", "2위 득표율", "2nd_share", "2위득표율(%)"] if c in res_row.columns), None)

    name1 = str(r.get(c1n)) if c1n else "1위"
    share1 = _to_pct_float(r.get(c1v))
    name2 = str(r.get(c2n)) if c2n else "2위"
    share2 = _to_pct_float(r.get(c2v))

    gap = None
    if isinstance(share1, (int, float)) and isinstance(share2, (int, float)):
        gap = round(share1 - share2, 2)
    elif df_24 is not None and code is not None:
        gap = compute_24_gap(df_24, code)

    box = st.container()
    with box:
        st.markdown("**24년 총선결과**")
        col1, col2, col3 = st.columns([1.2, 1.2, 1])
        with col1:
            st.metric(label=f"{name1}", value=_fmt_pct(share1))
        with col2:
            st.metric(label=f"{name2}", value=_fmt_pct(share2))
        with col3:
            st.metric(label="1~2위 격차", value=_fmt_gap(gap))

# ---------------- 현직 정보 카드 (current_info.csv) ----------------
def render_incumbent_card(cur_row: pd.DataFrame):
    if cur_row is None or cur_row.empty:
        st.info("현직 정보 데이터가 없습니다.")
        return

    cur_row = _norm_cols(cur_row)
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

# ---------------- 진보당 현황 박스 (party_labels.csv 기반) ----------------
def render_prg_party_box(prg_row: pd.DataFrame, pop_row: pd.DataFrame):
    """
    party_labels.csv가 해당 선거구 지표를 담고 있다면 유연하게 표출.
    """
    box = st.container()
    with box:
        st.markdown("**진보당 현황**")
        if prg_row is None or prg_row.empty:
            st.info("진보당 관련 데이터가 없습니다.")
            return

        prg_row = _norm_cols(prg_row)
        r = prg_row.iloc[0]

        strength_col = next((c for c in ["진보당 득표력","득표력","progressive_strength","PL_prg_str"] if c in prg_row.columns), None)
        org_col      = next((c for c in ["진보당 당원수","당원수","조직수","branch_count","members"] if c in prg_row.columns), None)
        cand_col     = next((c for c in ["진보당 지방선거후보","지방선거후보수","local_candidates"] if c in prg_row.columns), None)

        c1, c2 = st.columns(2)
        with c1:
            if strength_col and pd.notna(r.get(strength_col)):
                st.metric("진보득표력", _fmt_pct(_to_pct_float(r.get(strength_col))))
            else:
                st.metric("진보득표력", "지표 미제공")
        with c2:
            st.metric("조직 규모", f"{_to_int(r.get(org_col)):,}" if org_col and pd.notna(r.get(org_col)) else "N/A")

        if cand_col and pd.notna(r.get(cand_col)):
            st.caption(f"지방선거 후보 수: {_to_int(r.get(cand_col)):,}명")

        # 인구 맥락 간단 표시
        if pop_row is not None and not pop_row.empty:
            pop_row = _norm_cols(pop_row)
            rp = pop_row.iloc[0]
            elder_col = next((c for c in ["고령층비율", "65세이상비율", "age65p"] if c in pop_row.columns), None)
            youth_col = next((c for c in ["청년층비율", "39세이하비율", "age39m"] if c in pop_row.columns), None)
            with st.expander("인구 맥락 보기", expanded=False):
                elder = _fmt_pct(_to_pct_float(rp.get(elder_col))) if elder_col and pd.notna(rp.get(elder_col)) else "N/A"
                youth = _fmt_pct(_to_pct_float(rp.get(youth_col))) if youth_col and pd.notna(rp.get(youth_col)) else "N/A"
                st.write(f"- 고령층 비율: {elder} / 청년층 비율: {youth}")

# ---------------- 득표 추이 라인차트 (vote_trend.csv) ----------------
def render_vote_trend_chart(ts: pd.DataFrame):
    """
    득표 추이 라인차트.
    - matplotlib 가용 시: matplotlib 사용 (한글 폰트 적용 + x축 라벨 간격/회전)
    - 없으면 Altair로 자동 대체 (겹침 완화 옵션)
    - 입력 ts는 long(label/prop) 또는 wide(연도+계열) 모두 허용
    """
    if ts is None or ts.empty:
        st.info("득표 추이 데이터가 없습니다.")
        return

    df = _norm_cols(ts.copy())

    # long 포맷 감지 (label/prop)
    label_col = next((c for c in ["label", "성향", "정당성향", "party_label"] if c in df.columns), None)
    value_col = next((c for c in ["prop", "득표율", "비율", "share", "ratio", "pct"] if c in df.columns), None)

    # year/연도 & 선거명
    year_col = next((c for c in ["year", "연도", "년도"] if c in df.columns), None)
    elec_col = next((c for c in ["election", "선거명"] if c in df.columns), None)

    # ---- 공통: x축 라벨 생성
    def make_x_label(_df: pd.DataFrame) -> pd.DataFrame:
        d = _df.copy()
        if year_col and elec_col and (year_col in d.columns) and (elec_col in d.columns):
            d["__year_label__"] = d[year_col].astype(str) + " " + d[elec_col].astype(str)
        elif year_col and (year_col in d.columns):
            d["__year_label__"] = d[year_col].astype(str)
        elif elec_col and (elec_col in d.columns):
            d["__year_label__"] = d[elec_col].astype(str)
        else:
            if d.index.dtype.kind in ("i", "u"):
                d = d.reset_index().rename(columns={"index": "연도"})
                d["__year_label__"] = d["연도"].astype(str)
            else:
                d["__year_label__"] = d.index.astype(str)
        # 정렬
        if year_col and (year_col in d.columns):
            d = d.sort_values(by=year_col, ascending=True)
        return d

    # ---- long → wide
    if label_col and value_col:
        # 값이 0~1이면 %로 변환
        if pd.api.types.is_numeric_dtype(df[value_col]) and (df[value_col].dropna() <= 1).all():
            df[value_col] = df[value_col] * 100.0
        else:
            df[value_col] = df[value_col].apply(lambda x: _to_pct_float(x, default=None))
        df = make_x_label(df)
        wide = df.pivot_table(index="__year_label__", columns=label_col, values=value_col, aggfunc="mean").reset_index()
    else:
        df = make_x_label(df)
        wide = df

    # 시리즈 및 색상
    party_order = ["진보", "중도", "보수", "기타"]
    colors = {"진보": "#450693", "중도": "#152484", "보수": "#E61E2B", "기타": "#798897"}
    series_cols = [p for p in party_order if p in wide.columns]
    if not series_cols:
        # 숫자형 컬럼 자동 탐색 (최대 6개)
        series_cols = [c for c in wide.columns if c not in ["__year_label__", year_col, elec_col] and pd.api.types.is_numeric_dtype(wide[c])]
        series_cols = series_cols[:6]

    if not series_cols:
        st.info("그릴 수 있는 수치형 시리즈가 없습니다.")
        return

    # ---------------- 경로 A: matplotlib 사용 가능 ----------------
    if plt is not None:
        x_labels = list(wide["__year_label__"])
        x_pos = list(range(len(x_labels)))  # 문자열 라벨을 위치값으로

        fig, ax = plt.subplots(figsize=(10, 5))
        for col in series_cols:
            ax.plot(x_pos, wide[col], marker="o", label=col, color=colors.get(col, None))

        # x축 틱 간격 자동 축약 (최대 10개 표시)
        n = len(x_labels)
        if n <= 10:
            tick_idx = list(range(n))
        else:
            step = max(1, n // 10)
            tick_idx = list(range(0, n, step))
            if tick_idx[-1] != n - 1:
                tick_idx.append(n - 1)

        ax.set_xticks(tick_idx)
        ax.set_xticklabels([x_labels[i] for i in tick_idx], rotation=30, ha="right")

        ax.set_title("정당성향별 득표 추이", fontsize=13, pad=15)
        ax.set_xlabel("연도 / 선거명")
        ax.set_ylabel("득표율(%)")
        ax.legend(title="정당 성향", loc="upper left")
        ax.grid(True, linestyle="--", alpha=0.5)

        fig.tight_layout()
        st.pyplot(fig)
        return

    # ---------------- 경로 B: Altair 대체 ----------------
    try:
        import altair as alt  # 안전 재시도
        tidy = wide.melt(id_vars="__year_label__", value_vars=series_cols, var_name="성향", value_name="득표율")
        tidy = tidy.dropna(subset=["득표율"])

        domain = [c for c in party_order if c in series_cols] + [c for c in series_cols if c not in party_order]
        rng = [colors.get(c, None) for c in domain]

        chart = (
            alt.Chart(tidy)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "__year_label__:N",
                    title="연도 / 선거명",
                    sort=None,
                    axis=alt.Axis(labelAngle=-30, labelOverlap="greedy")  # 겹침 완화
                ),
                y=alt.Y("득표율:Q", title="득표율(%)"),
                color=alt.Color("성향:N", scale=alt.Scale(domain=domain, range=rng), title="정당 성향"),
                tooltip=[
                    alt.Tooltip("__year_label__:N", title="라벨"),
                    alt.Tooltip("성향:N"),
                    alt.Tooltip("득표율:Q", format=".2f")
                ]
            )
            .properties(width=780, height=340, title="정당성향별 득표 추이")
        )
        st.altair_chart(chart, use_container_width=True)
    except Exception:
        # 최후의 보루: Streamlit 기본 라인차트
        try:
            st.line_chart(wide.set_index("__year_label__")[series_cols])
        except Exception:
            st.error("시각화 모듈(matplotlib/altair) 사용 불가 및 기본 라인차트도 실패했습니다. 환경 설정을 확인하세요.")

# ---------------- 인구 정보 박스 (population.csv) ----------------
def render_population_box(pop_df: pd.DataFrame):
    box = st.container()
    with box:
        st.markdown("**인구 정보**")

        if pop_df is None or pop_df.empty:
            st.info("인구 데이터가 없습니다.")
            return

        pop_df = _norm_cols(pop_df)
        r = pop_df.iloc[0]

        # 1) 비율 컬럼 우선
        elder_col  = next((c for c in ["고령층비율", "65세이상비율", "age65p"] if c in pop_df.columns), None)
        youth_col  = next((c for c in ["청년층비율", "39세이하비율", "age39m"] if c in pop_df.columns), None)
        mid_col    = next((c for c in ["40_59비율", "40-59비율", "age40_59p", "4050비율"] if c in pop_df.columns), None)

        male_col   = next((c for c in ["남성비율", "남", "male_p", "2030 남성비율"] if c in pop_df.columns), None)
        female_col = next((c for c in ["여성비율", "여", "female_p", "2030 여성비율"] if c in pop_df.columns), None)

        elder_pct = _to_pct_float(r.get(elder_col)) if elder_col else None
        youth_pct = _to_pct_float(r.get(youth_col)) if youth_col else None
        mid_pct   = _to_pct_float(r.get(mid_col))   if mid_col   else None
        male_pct  = _to_pct_float(r.get(male_col))  if male_col  else None
        female_pct= _to_pct_float(r.get(female_col))if female_col else None

        # 2) 인원수 기반 비율
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

        # 60-64 추가(남는 비율로 추정)
        s_pct = None
        if all(isinstance(x, (int, float)) for x in [youth_pct, mid_pct, elder_pct]) and isinstance(total, (int, float)):
            used = (youth_pct or 0) + (mid_pct or 0) + (elder_pct or 0)
            s_pct = max(0.0, 100.0 - used)

        # 2030 남/여
        male_share_2030 = None
        female_share_2030 = None
        has_2030_m = "2030 남성" in pop_df.columns and pd.notna(r.get("2030 남성"))
        has_2030_f = "2030 여성" in pop_df.columns and pd.notna(r.get("2030 여성"))
        if (has_2030_m or has_2030_f) and v2030:
            m_cnt = _to_int(r.get("2030 남성")) if has_2030_m else 0
            f_cnt = _to_int(r.get("2030 여성")) if has_2030_f else 0
            denom = (m_cnt + f_cnt) if (m_cnt + f_cnt) > 0 else v2030
            male_share_2030 = (m_cnt / denom * 100.0) if denom else None
            female_share_2030 = (f_cnt / denom * 100.0) if denom else None
        else:
            male_share_2030 = male_pct
            female_share_2030 = female_pct

        # --- 상단: 유권자 수 ---
        st.metric("유권자 수", f"{total:,}" if isinstance(total, (int, float)) else "N/A")

        # --- 파이차트 2개 ---
        col1, col2 = st.columns(2)

        y = youth_pct or 0.0
        m = mid_pct   or 0.0
        s = s_pct     or 0.0
        e = elder_pct or 0.0
        with col1:
            age_colors = ["#deebf7", "#9ecae1", "#6baed6", "#08519c"]
            _pie_chart("연령 구성", ["청년층(≤39)", "40-59", "60-64", "65+"], [y, m, s, e], colors=age_colors)

        mm = male_share_2030 or 0.0
        ff = female_share_2030 or 0.0
        with col2:
            if mm == 0 and ff == 0:
                st.info("2030 남/여 자료가 없습니다.")
            else:
                gender_colors = ["#bdd7e7", "#08519c"]
                _pie_chart("2030 성별 구성", ["남성", "여성"], [mm, ff], colors=gender_colors)
