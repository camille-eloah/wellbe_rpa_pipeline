from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .config import load_config
from .database import MySQLMovieRepository, build_dump_sql
from .scraper import RPAMovieScraper
from .utils import configure_logging, ensure_directories, normalize_movies_df, now_stamp, save_dataframe_outputs


LOGGER = logging.getLogger(__name__)


def run_pipeline(load_to_database: bool = True) -> dict[str, object]:
    config = load_config()
    configure_logging()
    ensure_directories([config.data_dir, config.output_dir, config.sql_dir])

    LOGGER.info("Iniciando etapa EXTRACT")
    with RPAMovieScraper(
        base_url=config.base_url,
        movie_search_path=config.movie_search_path,
        timeout_seconds=config.timeout_seconds,
        headless=config.headless,
    ) as scraper:
        raw_movies = scraper.run(query=config.default_query)

    raw_df = pd.DataFrame(raw_movies)
    raw_data_path = config.data_dir / "movies_raw.csv"
    raw_df.to_csv(raw_data_path, index=False, encoding="utf-8")

    LOGGER.info("Iniciando etapa TRANSFORM")
    transformed_df = normalize_movies_df(raw_df)
    stamp = now_stamp()
    output_files = save_dataframe_outputs(
        transformed_df,
        output_dir=config.output_dir,
        base_name=f"movies_avengers_{stamp}",
    )

    LOGGER.info("Iniciando etapa LOAD")
    inserted_rows = 0
    if load_to_database:
        with MySQLMovieRepository(
            host=config.mysql_host,
            port=config.mysql_port,
            database=config.mysql_database,
            user=config.mysql_user,
            password=config.mysql_password,
        ) as repo:
            repo.ensure_schema()
            inserted_rows = repo.upsert_movies(transformed_df.to_dict(orient="records"))

    dump_path = build_dump_sql(
        transformed_df.to_dict(orient="records"),
        output_file=config.sql_dir / f"movies_dump_{stamp}.sql",
    )

    summary = {
        "config": asdict(config),
        "raw_rows": int(raw_df.shape[0]),
        "transformed_rows": int(transformed_df.shape[0]),
        "inserted_rows": int(inserted_rows),
        "raw_data_path": str(raw_data_path),
        "output_files": {k: str(v) for k, v in output_files.items()},
        "dump_path": str(dump_path),
    }
    LOGGER.info("Pipeline finalizado")
    return summary


if __name__ == "__main__":
    result = run_pipeline(load_to_database=True)
    print(result)
