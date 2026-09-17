import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "")
DADOS_DIR = Path(os.getenv("DADOS_DIR", "/data"))
GUARDAR_ENUNCIADO = os.getenv("GUARDAR_ENUNCIADO", "1") == "1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
VERSAO = "0.2.1"


def usuarios() -> dict[str, str]:
    """Lê USUARIOS=usuario:hash,usuario:hash."""
    out: dict[str, str] = {}
    for par in os.getenv("USUARIOS", "").split(","):
        par = par.strip()
        if not par or ":" not in par:
            continue
        nome, h = par.split(":", 1)
        out[nome.strip()] = h.strip()
    return out
