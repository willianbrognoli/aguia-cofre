import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse

from . import config, db
from .api_exemplo import router as router_exemplo
from .auth import usuario_atual

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cofre")
STATIC = Path(__file__).resolve().parent / "static"


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
app.include_router(router_exemplo)


@app.get("/health")
def health() -> dict:
    """Sem autenticação: usado pelo Easypanel e para checagem rápida."""
    banco = "ok"
    try:
        with db.conexao() as conn:
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


@app.get("/api/eu")
def eu(usuario: str = Depends(usuario_atual)) -> dict:
    return {"usuario": usuario, "versao": config.VERSAO}


@app.get("/static/logo.png", include_in_schema=False)
def logo() -> FileResponse:
    return FileResponse(STATIC / "logo.png", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/")
def inicio(usuario: str = Depends(usuario_atual)) -> FileResponse:
    db.registrar(usuario, "acesso_painel")
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})
