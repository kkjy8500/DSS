from __future__ import annotations
import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st


# ---------- Page & Title ----------
st.set_page_config(
page_title="지역구 선정 1단계 조사 결과 대시보드",
page_icon="🗳️",
layout="wide",
)


# Main title
st.title("🗳️ 지역구 선정 1단계 조사 결과")
st.caption(
"에스티아이"
)

# ---------- Tabs / Pages ----------

overview_tab, region_tab, notes_tab = st.tabs([
"종합",
"지역별 분석",
"데이터 설명",
])