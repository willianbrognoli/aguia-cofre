"""Gera o hash bcrypt de uma senha para a variável USUARIOS.

Uso:  python scripts/gerar_hash.py
"""
import getpass

import bcrypt

usuario = input("Usuário: ").strip()
senha = getpass.getpass("Senha: ")
confirma = getpass.getpass("Repita a senha: ")
if senha != confirma:
    raise SystemExit("As senhas não conferem.")
h = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
print(f"\nCole em USUARIOS (separe vários com vírgula):\n{usuario}:{h}")
