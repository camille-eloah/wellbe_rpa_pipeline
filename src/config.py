from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppConfig:
    base_url: str
    movie_search_path: str
    default_query: str
    invoice_url: str
    invoice_table_id: str
    invoice_target_indices: tuple[int, ...]
    timeout_seconds: int
    headless: bool
    output_dir: Path
    data_dir: Path
    sql_dir: Path
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str


def _to_bool(raw_value: str, default: bool) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_indices(raw_value: str | None, default: tuple[int, ...]) -> tuple[int, ...]:
    if not raw_value:
        return default

    values: list[int] = []
    for token in raw_value.split(","):
        token = token.strip()
        if token.isdigit():
            values.append(int(token))

    return tuple(values) if values else default


def load_config() -> AppConfig:
    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)

    return AppConfig(
        base_url=os.getenv("BASE_URL", "https://rpachallenge.com/"),
        movie_search_path=os.getenv("MOVIE_SEARCH_PATH", "/movieSearch"),
        default_query=os.getenv("MOVIE_QUERY", "Avengers"),
        invoice_url=os.getenv("INVOICE_URL", "https://rpachallengeocr.azurewebsites.net/"),
        invoice_table_id=os.getenv("INVOICE_TABLE_ID", "tableSandbox"),
        invoice_target_indices=_parse_indices(os.getenv("INVOICE_TARGET_INDICES", "2,4"), default=(2, 4)),
        timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "15")),
        headless=_to_bool(os.getenv("HEADLESS", "true"), default=True),
        output_dir=ROOT_DIR / "outputs",
        data_dir=ROOT_DIR / "data",
        sql_dir=ROOT_DIR / "sql",
        mysql_host=os.getenv("MYSQL_HOST", "localhost"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_database=os.getenv("MYSQL_DATABASE", "wellbe_movies"),
        mysql_user=os.getenv("MYSQL_USER", "root"),
        mysql_password=os.getenv("MYSQL_PASSWORD", "root"),
    )
