from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


LOGGER_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=LOGGER_FORMAT)


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_movies_df(df: pd.DataFrame) -> pd.DataFrame:
    transformed = df.copy()
    transformed["name"] = transformed["name"].astype(str).str.strip()
    transformed["description"] = transformed["description"].astype(str).str.strip()
    transformed = transformed.dropna(subset=["name", "description"])
    transformed = transformed[transformed["name"] != ""]
    transformed = transformed[transformed["description"] != ""]
    transformed = transformed.drop_duplicates(subset=["name"], keep="first")
    transformed = transformed.sort_values(by="name").reset_index(drop=True)
    return transformed


def save_dataframe_outputs(df: pd.DataFrame, output_dir: Path, base_name: str) -> dict[str, Path]:
    ensure_directories([output_dir])
    csv_path = output_dir / f"{base_name}.csv"
    json_path = output_dir / f"{base_name}.json"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    records = df.to_dict(orient="records")
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"csv": csv_path, "json": json_path}


def sql_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "''")
