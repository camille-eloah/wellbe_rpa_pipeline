from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from .utils import sql_escape


LOGGER = logging.getLogger(__name__)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_movies_name (name)
);
""".strip()


class MySQLMovieRepository:
    def __init__(self, host: str, port: int, database: str, user: str, password: str) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None

    def connect(self) -> None:
        try:
            import mysql.connector
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Pacote mysql-connector-python nao instalado. Rode: pip install -r requirements.txt"
            ) from exc

        self.conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            autocommit=False,
        )
        LOGGER.info("Conexao MySQL estabelecida")

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            LOGGER.info("Conexao MySQL encerrada")

    def __enter__(self) -> "MySQLMovieRepository":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def ensure_schema(self) -> None:
        assert self.conn is not None
        with self.conn.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
        self.conn.commit()
        LOGGER.info("Tabela movies validada")

    def upsert_movies(self, movies: Iterable[dict[str, str]]) -> int:
        assert self.conn is not None
        sql = (
            "INSERT INTO movies (name, description) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE description = VALUES(description)"
        )
        payload = [(movie["name"], movie["description"]) for movie in movies]
        if not payload:
            return 0

        with self.conn.cursor() as cursor:
            cursor.executemany(sql, payload)
        self.conn.commit()
        LOGGER.info("Linhas processadas no banco: %s", len(payload))
        return len(payload)


def build_dump_sql(records: list[dict[str, str]], output_file: Path) -> Path:
    lines = [
        "-- Dump gerado automaticamente pelo pipeline wellbe_rpa_pipeline",
        "CREATE TABLE IF NOT EXISTS movies (",
        "    id INT AUTO_INCREMENT PRIMARY KEY,",
        "    name VARCHAR(255) NOT NULL,",
        "    description TEXT NOT NULL,",
        "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,",
        "    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,",
        "    UNIQUE KEY uq_movies_name (name)",
        ");",
        "",
    ]

    if records:
        lines.append("INSERT INTO movies (name, description) VALUES")
        values = []
        for row in records:
            name = sql_escape(row["name"])
            description = sql_escape(row["description"])
            values.append(f"('{name}', '{description}')")
        lines.append(",\n".join(values) + "\nON DUPLICATE KEY UPDATE description = VALUES(description);")
    else:
        lines.append("-- Nenhum registro para inserir.")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")
    LOGGER.info("Dump SQL salvo em: %s", output_file)
    return output_file
