import json
import logging
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL

log = logging.getLogger("cofre.db")
MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


@contextmanager
def conexao():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurada")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn


def migrar() -> list[str]:
    """Aplica, em ordem, os arquivos .sql de /migrations ainda não aplicados."""
    aplicadas: list[str] = []
    with conexao() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " arquivo text PRIMARY KEY,"
            " aplicada_em timestamptz NOT NULL DEFAULT now())"
        )
        feitas = {r["arquivo"] for r in conn.execute("SELECT arquivo FROM schema_migrations")}
        for arq in sorted(MIGRATIONS.glob("*.sql")):
            if arq.name in feitas:
                continue
            log.info("Aplicando migração %s", arq.name)
            with conn.transaction():
                conn.execute(arq.read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_migrations (arquivo) VALUES (%s)", (arq.name,))
            aplicadas.append(arq.name)
    return aplicadas


def registrar(usuario: str, acao: str, detalhe: dict | None = None) -> None:
    """Grava quem fez o quê (log de ações). Nunca derruba a requisição."""
    try:
        with conexao() as conn:
            conn.execute(
                "INSERT INTO log_acoes (usuario, acao, detalhe) VALUES (%s, %s, %s)",
                (usuario, acao, json.dumps(detalhe or {}, ensure_ascii=False)),
            )
    except Exception as e:
        log.warning("Não foi possível registrar ação %s: %s", acao, e)
