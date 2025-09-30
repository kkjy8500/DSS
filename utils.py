from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import re
from functools import lru_cache

# -----------------------------
# 캐싱 데코레이터 (Streamlit v1.29+)
# -----------------------------
def cache_data(func):
    return st.cache_data(show_spinner=False)(func)

# -----------------------------
# 파일 로더 (UTF-8 → CP949 폴백)
# -----------------------------
def load_csv_safe(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        st.error(f"파일이 존재하지 않습니다: {path}")
        st.stop()
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949")

# -----------------------------
# 포맷/파서
# -----------------------------
def parse_int(x) -> int | None:
    if pd.isna(x):
        return None
    s = str(x).strip()
    s = s.replace(",", "")
    if s == "" or s.lower() == "nan":
        return None
    try:
        return int(float(s))
    except Exception:
        return None

def parse_float_pct(x) -> float | None:
    """ '59.14%' or '59.14' or 59.14 -> 59.14 (float, %) """
    if pd.isna(x):
        return None
    s = str(x).strip()
    s = s.replace("%", "").replace(",", "")
    if s == "" or s.lower() == "nan":
        return None
    try:
        return float(s)
    except Exception:
        return None

def fmt_int(x: int | None) -> str:
    if x is None:
        return "데이터 없음"
    return f"{x:,}"

def fmt_pct2(x: float | None, suffix=" %") -> str:
    if x is None:
        return "데이터 없음"
    return f"{x:.2f}{suffix}"

# -----------------------------
# 후보 Wide → Long 변환
#  - 입력: 5_na_dis_results.csv (연도=2024로 이미 필터된 df)
#  - 출력: 각 후보 1행씩 (이름, 득표수, 득표율, 순위)
# -----------------------------
def candidates_long_from_wide(df_ge_2024: pd.DataFrame) -> pd.DataFrame:
    # 후보 1~7까지 존재 가능
    rows = []
    for _, r in df_ge_2024.iterrows():
        base = {
            "지역": r.get("지역"),
            "선거구": r.get("선거구"),
            "코드": r.get("코드"),
            "연도": r.get("연도"),
        }
        for k in range(1, 8):
            name_col = f"후보{k}_이름"
            votes_col = f"후보{k}_득표수"
            share_col = f"후보{k}_득표율"
            if name_col in df_ge_2024.columns and pd.notna(r.get(name_col)):
                name = str(r.get(name_col)).strip()
                votes_raw = r.get(votes_col) if votes_col in df_ge_2024.columns else None
                share_raw = r.get(share_col) if share_col in df_ge_2024.columns else None
                votes = parse_int(votes_raw)
                share = parse_float_pct(share_raw)  # 이미 % 없는 float일 수도 있음 → 안전 파서
                rows.append({**base, "후보": name, "득표수": votes, "득표율": share, "순위": k})
    out = pd.DataFrame(rows)
    # 정렬: 득표율 내림차순(동률 시 득표수, 그 다음 기존 k)
    out = out.sort_values(["코드", out["득표율"].fillna(-1)], ascending=[True, False]).reset_index(drop=True)
    return out

# -----------------------------
# 상위 1~3위 & 1-2위 격차 계산
# -----------------------------
def get_top3_and_gap(df_long_one: pd.DataFrame):
    """한 지역(코드 필터 완료)의 long df에서 상위 3과 격차(득표율 기준)"""
    tmp = df_long_one.copy()
    tmp = tmp.sort_values(tmp["득표율"].fillna(-1), ascending=False)
    top3 = tmp.head(3).copy()
    # 1-2위 격차(%p)
    if len(tmp) >= 2 and pd.notna(tmp.iloc[0]["득표율"]) and pd.notna(tmp.iloc[1]["득표율"]):
        gap = float(tmp.iloc[0]["득표율"]) - float(tmp.iloc[1]["득표율"])
    else:
        gap = None
    return top3, gap

# -----------------------------
# 교집합 지역 목록 (코드, 선거구)
# -----------------------------
def get_available_districts(df_comp: pd.DataFrame, df_ge: pd.DataFrame, df_inc: pd.DataFrame):
    codes = set(df_comp["코드"]).intersection(set(df_ge["코드"])).intersection(set(df_inc["코드"]))
    # 이름은 우선 comp 기준, 없으면 ge→inc 순으로 확보
    out = []
    for c in sorted(codes):
        name = None
        for df in (df_comp, df_ge, df_inc):
            tmp = df[df["코드"] == c]
            if not tmp.empty and "선거구" in tmp.columns and pd.notna(tmp.iloc[0]["선거구"]):
                name = str(tmp.iloc[0]["선거구"]).strip()
                break
        out.append((c, name if name else str(c)))
    return out

# -----------------------------
# 스타일 / 폰트
# -----------------------------
def inject_pretendard():
    st.markdown(
        """
        <style>
        @font-face {
          font-family: 'Pretendard';
          src: url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard-regular.woff2') format('woff2');
          font-weight: 400; font-style: normal; font-display: swap;
        }
        @font-face {
          font-family: 'Pretendard';
          src: url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard-bold.woff2') format('woff2');
          font-weight: 700; font-style: normal; font-display: swap;
        }
        html, body, [class*="css"] {
          font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
        }
        .metric-card {border:1px solid #eee; border-radius:16px; padding:16px; background:#fff;}
        .badge {display:inline-block; padding:2px 8px; border-radius:999px; background:#f2f4f8; color:#555; font-size:12px; margin-right:6px;}
        .inc-card {border:1px solid #eee; border-radius:16px; padding:16px; background:#fff;}
        </style>
        """,
        unsafe_allow_html=True
    )

def badge(title, text):
    return f'<span class="badge"><b>{title}</b> {text}</span>'
