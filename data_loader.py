# =============================
# File: data_loader.py
# =============================
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
    # 기존: population_agg.csv
    return _read_csv_safe(data_dir / "population.csv")

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
