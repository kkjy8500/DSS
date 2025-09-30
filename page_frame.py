from __future__ import annotations
import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

st.set_page_config(page_title="지역구 선정 1단계 조사 결과 대시보드", 
                   page_icon="🗳️", layout="wide")

st.title("🗳️ 지역구 선정 1단계 조사 결과")
st.caption("에스티아이")

# ---------- Sidebar Navigation ----------
st.sidebar.header("메뉴 선택")
menu = st.sidebar.radio(
    "페이지",
    ["종합", "지역별 분석", "데이터 설명"],
    index=0
)

# ---------- region list ----------
regions = [
    "강서구병",
    "관악구을",
    "구로구갑",
    "서대문구갑",
    "은평구갑",
    "고양시을",
    "부천시을",
    "수원시을",
    "평택시을",
    "화성시을"
]

# ---------- Pages ----------
if menu == "종합":
    st.subheader("📊 종합")
    st.write("전체 지표 요약")

elif menu == "지역별 분석":
    st.subheader("📍 지역별 분석")

    # 👉 사이드바에 10개 지역 리스트 표시
    st.sidebar.subheader("지역 선택")
    selected_region = st.sidebar.selectbox("지역 선택", regions)

    st.write(f"### {selected_region} 분석 결과")
    st.write("해당 지역의 데이터 시각화, 표, 설명 등")

elif menu == "데이터 설명":
    st.subheader("ℹ️ 데이터 설명")
    st.write("데이터 출처 및 변수 설명을 정리")

