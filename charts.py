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
