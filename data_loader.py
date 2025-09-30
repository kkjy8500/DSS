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

