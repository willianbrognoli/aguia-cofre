import html
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from . import auth, config, db
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
    nomes = sorted(config.usuarios())
    if nomes:
        log.info("Usuários configurados: %s", ", ".join(nomes))
    else:
        log.warning("Nenhum usuário em USUARIOS: ninguém consegue entrar.")
    yield


app = FastAPI(title="Águia · Cofre de Questões", version=config.VERSAO, lifespan=ciclo,
              docs_url=None, redoc_url=None, openapi_url=None)
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
        "usuarios": sorted(config.usuarios().keys()),
        "guardar_enunciado": config.GUARDAR_ENUNCIADO,
    }


@app.get("/static/logo.png", include_in_schema=False)
def logo() -> FileResponse:
    return FileResponse(STATIC / "logo.png", headers={"Cache-Control": "public, max-age=86400"})


def _pagina_login(erro: str = "", usuario: str = "", proximo: str = "/", codigo: int = 200) -> HTMLResponse:
    pagina = (STATIC / "login.html").read_text(encoding="utf-8")
    pagina = pagina.replace("<!--ERRO-->", f'<p class="erro" role="alert">{html.escape(erro)}</p>' if erro else "")
    pagina = pagina.replace("<!--USUARIO-->", html.escape(usuario, quote=True))
    pagina = pagina.replace("<!--PROXIMO-->", html.escape(proximo, quote=True))
    return HTMLResponse(pagina, status_code=codigo, headers={"Cache-Control": "no-store"})


def _destino_seguro(proximo: str) -> str:
    return proximo if proximo.startswith("/") and not proximo.startswith("//") else "/"


@app.get("/login", include_in_schema=False)
def login_form(request: Request, proximo: str = "/"):
    if auth.usuario_da_sessao(request):
        return RedirectResponse(_destino_seguro(proximo), status_code=303)
    return _pagina_login(proximo=_destino_seguro(proximo))


@app.post("/login", include_in_schema=False)
def login_enviar(request: Request, usuario: str = Form(""), senha: str = Form(""), proximo: str = Form("/")):
    ip = auth.ip_de(request)
    destino = _destino_seguro(proximo)
    if auth.bloqueado(ip):
        return _pagina_login("Muitas tentativas. Aguarde 10 minutos e tente de novo.", usuario, destino, 429)
    cookie = auth.autenticar(usuario, senha, ip)
    if not cookie:
        log.info("Login recusado para '%s' (%s)", usuario.strip().lower(), ip)
        return _pagina_login("Usuário ou senha incorretos.", usuario, destino, 401)
    nome = usuario.strip().lower()
    db.registrar(nome, "login", {"ip": ip})
    resp = RedirectResponse(destino, status_code=303)
    resp.set_cookie(auth.COOKIE, cookie, max_age=auth.DURACAO, httponly=True,
                    secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
                    samesite="lax", path="/")
    return resp


@app.get("/sair", include_in_schema=False)
def sair(request: Request):
    nome = auth.usuario_da_sessao(request)
    if nome:
        db.registrar(nome, "logout")
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(auth.COOKIE, path="/", httponly=True, samesite="lax",
                       secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https")
    return resp


@app.get("/api/eu")
def eu(usuario: str = Depends(usuario_atual)) -> dict:
    return {"usuario": usuario, "versao": config.VERSAO}


@app.get("/", include_in_schema=False)
def inicio(request: Request):
    nome = auth.usuario_da_sessao(request)
    if not nome:
        return RedirectResponse("/login?proximo=" + quote("/"), status_code=303)
    db.registrar(nome, "acesso_painel")
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})
