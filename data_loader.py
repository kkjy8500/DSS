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
    # population.csv
    return _read_csv_safe(data_dir / "population.csv")

def load_party_competence(data_dir: Path) -> pd.DataFrame:
    # (sample)party_competence.csv
    return _read_csv_safe(data_dir / "(sample)party_competence.csv")

def load_vote_trend(data_dir: Path) -> pd.DataFrame:
    # vote_trend_sample_all.csv
    return _read_csv_safe(data_dir / "vote_trend_sample_all.csv")

def load_results_2024(data_dir: Path) -> pd.DataFrame:
    # 5_na_dis_results.csv
    return _read_csv_safe(data_dir / "5_na_dis_results.csv")

def load_current_info(data_dir: Path) -> pd.DataFrame:
    # current_info.csv
    return _read_csv_safe(data_dir / "current_info.csv")

def load_index_sample(data_dir: Path) -> pd.DataFrame:
    # index_sample.csv (선택적)
    p = data_dir / "index_sample.csv"
    if p.exists():
        return _read_csv_safe(p)
    else:
        # 업로드 디렉토리 폴백
        return _read_csv_safe(Path("/mnt/data") / "index_sample.csv")
