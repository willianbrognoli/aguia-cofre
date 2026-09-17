"""Login por página própria com cookie de sessão assinado.

- Usuários vêm da variável USUARIOS (usuario:senha ou usuario:hash_bcrypt).
- O cookie guarda usuário + validade + impressão da senha, assinados com HMAC.
  Trocar a senha no Easypanel derruba as sessões antigas daquele usuário.
- SESSION_SECRET (opcional): se não existir, uma chave aleatória é criada a cada
  reinício do serviço (todo mundo precisa entrar de novo após um deploy).
"""
import base64
import hashlib
import hmac
import os
import secrets
import time
from collections import defaultdict, deque

import bcrypt
from fastapi import HTTPException, Request, status

from .config import usuarios

COOKIE = "cofre_sessao"
DURACAO = 12 * 3600  # 12 horas
_SEGREDO = (os.getenv("SESSION_SECRET") or secrets.token_hex(32)).encode()

# limite simples de tentativas por IP: 8 erros a cada 10 minutos
_tentativas: dict[str, deque] = defaultdict(deque)
_JANELA, _MAX = 600, 8


def _confere(senha: str, guardada: str) -> bool:
    if guardada.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(senha.encode(), guardada.encode())
        except ValueError:
            return False
    return hmac.compare_digest(
        hashlib.sha256(senha.encode()).digest(),
        hashlib.sha256(guardada.encode()).digest(),
    )


def _impressao(guardada: str) -> str:
    return hashlib.sha256(guardada.encode()).hexdigest()[:12]


def _assinar(carga: str) -> str:
    return hmac.new(_SEGREDO, carga.encode(), hashlib.sha256).hexdigest()


def ip_de(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return (fwd.split(",")[0].strip() if fwd else "") or (request.client.host if request.client else "?")


def bloqueado(ip: str) -> bool:
    fila = _tentativas[ip]
    agora = time.time()
    while fila and agora - fila[0] > _JANELA:
        fila.popleft()
    return len(fila) >= _MAX


def autenticar(usuario: str, senha: str, ip: str) -> str | None:
    """Confere usuário e senha. Devolve o valor do cookie ou None."""
    nome = usuario.strip().lower()
    guardada = usuarios().get(nome)
    ok = _confere(senha, guardada or secrets.token_hex(16))
    if not guardada or not ok:
        _tentativas[ip].append(time.time())
        return None
    _tentativas.pop(ip, None)
    exp = int(time.time()) + DURACAO
    carga = f"{nome}|{exp}|{_impressao(guardada)}"
    return base64.urlsafe_b64encode(f"{carga}|{_assinar(carga)}".encode()).decode()


def usuario_da_sessao(request: Request) -> str | None:
    bruto = request.cookies.get(COOKIE)
    if not bruto:
        return None
    try:
        nome, exp, imp, assinatura = base64.urlsafe_b64decode(bruto.encode()).decode().split("|")
    except Exception:
        return None
    carga = f"{nome}|{exp}|{imp}"
    if not hmac.compare_digest(assinatura, _assinar(carga)):
        return None
    if int(exp) < time.time():
        return None
    guardada = usuarios().get(nome)
    if not guardada or not hmac.compare_digest(imp, _impressao(guardada)):
        return None
    return nome


def usuario_atual(request: Request) -> str:
    """Dependência das rotas protegidas (API): 401 sem sessão válida."""
    nome = usuario_da_sessao(request)
    if not nome:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada. Entre novamente.")
    return nome
