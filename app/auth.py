import secrets

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import usuarios

_basic = HTTPBasic(realm="Cofre de Questoes")
_HASH_FALSO = bcrypt.hashpw(b"nao-existe", bcrypt.gensalt()).decode()


def usuario_atual(cred: HTTPBasicCredentials = Depends(_basic)) -> str:
    """Autenticação básica com usuários definidos na variável USUARIOS."""
    h = usuarios().get(cred.username)
    try:
        # sempre roda o bcrypt, mesmo para usuário inexistente (tempo constante)
        ok = bcrypt.checkpw(cred.password.encode(), (h or _HASH_FALSO).encode())
    except ValueError:
        ok = False
    if not h or not ok:
        secrets.compare_digest("a", "b")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": 'Basic realm="Cofre de Questoes"'},
        )
    return cred.username
