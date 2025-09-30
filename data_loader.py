# =============================
# File: data_loader.py
# =============================
from __future__ import annotations

import pandas as pd
from pathlib import Path

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
    """
    population_agg.csv 우선, 없으면 population.csv 대체 로딩
    """
    df = _read_csv_safe(data_dir / "population_agg.csv")
    if df is None or len(df) == 0:
        df = _read_csv_safe(data_dir / "population.csv")
    return df

def load_party_competence(data_dir: Path) -> pd.DataFrame:
    return _read_csv_safe(data_dir / "progressive_party.csv")

def load_vote_trend(data_dir: Path) -> pd.DataFrame:
    return _read_csv_safe(data_dir / "vote_trend.csv")

def load_results_2024(data_dir: Path) -> pd.DataFrame:
    return _read_csv_safe(data_dir / "results_2024.csv")

def load_current_info(data_dir: Path) -> pd.DataFrame:
    return _read_csv_safe(data_dir / "current_info.csv")

def load_index_sample(data_dir: Path) -> pd.DataFrame:
    return _read_csv_safe(data_dir / "index_sample.csv")
