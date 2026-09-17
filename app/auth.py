import hashlib
import secrets

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import usuarios

_basic = HTTPBasic(realm="Cofre de Questoes")


def _confere(senha: str, guardada: str) -> bool:
    """Aceita senha em hash bcrypt ($2b$...) ou em texto simples."""
    if guardada.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(senha.encode(), guardada.encode())
        except ValueError:
            return False
    a = hashlib.sha256(senha.encode()).digest()
    b = hashlib.sha256(guardada.encode()).digest()
    return secrets.compare_digest(a, b)


def usuario_atual(cred: HTTPBasicCredentials = Depends(_basic)) -> str:
    """Autenticação básica com usuários definidos na variável USUARIOS."""
    guardada = usuarios().get(cred.username)
    ok = _confere(cred.password, guardada or secrets.token_hex(16))
    if not guardada or not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": 'Basic realm="Cofre de Questoes"'},
        )
    return cred.username
