import html
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse

from . import config, db
from .auth import usuario_atual

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cofre")


@asynccontextmanager
async def ciclo(_app: FastAPI):
    config.DADOS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        aplicadas = db.migrar()
        log.info("Banco ok. Migrações aplicadas agora: %s", aplicadas or "nenhuma")
    except Exception as e:  # o app sobe mesmo sem banco; /health mostra o erro
        log.error("Falha ao migrar o banco: %s", e)
    if not config.usuarios():
        log.warning("Nenhum usuário em USUARIOS: o painel vai recusar todos os acessos.")
    yield


app = FastAPI(title="Águia · Cofre de Questões", version=config.VERSAO, lifespan=ciclo)


@app.get("/health")
def health() -> dict:
    """Sem autenticação: usado pelo Easypanel e para checagem rápida."""
    banco = "ok"
    try:
        with db.conexao() as conn:
            conn.execute("SELECT 1")
            conn.execute("SELECT 1 FROM questoes LIMIT 1")
    except Exception as e:
        banco = f"erro: {e.__class__.__name__}: {str(e)[:120]}"
    return {
        "status": "ok",
        "versao": config.VERSAO,
        "banco": banco,
        "usuarios_configurados": len(config.usuarios()),
        "guardar_enunciado": config.GUARDAR_ENUNCIADO,
    }


@app.get("/", response_class=HTMLResponse)
def inicio(usuario: str = Depends(usuario_atual)) -> str:
    db.registrar(usuario, "acesso_painel")
    u = html.escape(usuario)
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cofre de Questões</title>
<style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:60px auto;padding:0 20px;color:#1d2433}}
h1{{margin:0 0 8px}}.ok{{color:#15803d}}code{{background:#f1f3f7;padding:2px 6px;border-radius:4px}}</style>
</head><body>
<h1>Cofre de Questões</h1>
<p class="ok">Serviço no ar · versão {config.VERSAO}</p>
<p>Olá, <b>{u}</b>. O painel completo chega nas próximas etapas.</p>
<p>Checagem técnica: <code>/health</code></p>
</body></html>"""
