# =============================
# File: data_loader.py
# =============================
from __future__ import annotations

import pandas as pd
from pathlib import Path

# 공통: CSV 로드(없으면 빈 DF)
def _read_csv_safe(path: Path, encoding: str = "utf-8") -> pd.DataFrame:
    try:
        if path.exists():
            return pd.read_csv(path, encoding=encoding)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949")
    except Exception:
        pass
    return pd.DataFrame()

def load_population_agg(data_dir: Path) -> pd.DataFrame:
    # 예시 파일명: population_agg.csv
    return _read_csv_safe(data_dir / "population_agg.csv")

def load_party_competence(data_dir: Path) -> pd.DataFrame:
    # 예시 파일명: progressive_party.csv
    return _read_csv_safe(data_dir / "progressive_party.csv")

def load_vote_trend(data_dir: Path) -> pd.DataFrame:
    # 예시 파일명: vote_trend.csv
    return _read_csv_safe(data_dir / "vote_trend.csv")

def load_results_2024(data_dir: Path) -> pd.DataFrame:
    # 예시 파일명: results_2024.csv
    return _read_csv_safe(data_dir / "results_2024.csv")

def load_current_info(data_dir: Path) -> pd.DataFrame:
    # 예시 파일명: current_info.csv
    return _read_csv_safe(data_dir / "current_info.csv")

def load_index_sample(data_dir: Path) -> pd.DataFrame:
    # 예시 파일명: index_sample.csv (EE_/PL_* 외부 지표)
    return _read_csv_safe(data_dir / "index_sample.csv")
