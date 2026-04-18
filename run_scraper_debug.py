from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from src.config import load_config
from src.scraper import RPAMovieScraper
from src.utils import configure_logging, ensure_directories


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Executa somente o scraper com logs de debug.")
    parser.add_argument("--query", default=None, help="Termo de busca. Ex: Avengers")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Executa em modo headless (sem abrir janela do navegador).",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Forca execucao com navegador visivel.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    configure_logging(logging.DEBUG)
    config = load_config()
    ensure_directories([config.data_dir, config.output_dir, config.sql_dir])

    query = args.query or config.default_query
    headless = config.headless
    if args.show_browser:
        headless = False
    elif args.headless:
        headless = True

    logging.getLogger(__name__).info("Iniciando scraper debug | query=%s | headless=%s", query, headless)

    with RPAMovieScraper(
        base_url=config.base_url,
        movie_search_path=config.movie_search_path,
        timeout_seconds=config.timeout_seconds,
        headless=headless,
    ) as scraper:
        records = scraper.run(query=query)

    df = pd.DataFrame(records)
    raw_path = config.data_dir / "movies_raw.csv"
    df.to_csv(raw_path, index=False, encoding="utf-8")

    logging.getLogger(__name__).info("Registros extraidos: %s", len(df))
    logging.getLogger(__name__).info("Arquivo salvo em: %s", raw_path)

    print("\nResumo:")
    print(df)

    return 0


if __name__ == "__main__":
    sys.exit(main())
