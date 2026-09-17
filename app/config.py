import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "")
DADOS_DIR = Path(os.getenv("DADOS_DIR", "/data"))
GUARDAR_ENUNCIADO = os.getenv("GUARDAR_ENUNCIADO", "1") == "1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
VERSAO = "0.3.0"


def _sem_aspas(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1].strip()
    return v


def usuarios() -> dict[str, str]:
    """Lê USUARIOS=usuario:senha,usuario:senha (tolera aspas, espaços e maiúsculas no nome)."""
    out: dict[str, str] = {}
    for par in _sem_aspas(os.getenv("USUARIOS", "")).split(","):
        par = _sem_aspas(par)
        if not par or ":" not in par:
            continue
        nome, h = par.split(":", 1)
        out[_sem_aspas(nome).lower()] = _sem_aspas(h)
    return out
