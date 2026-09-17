# Águia · Cofre de Questões

Banco de questões do Projeto Águia: lê cadernos do Tec Concursos (PDF), classifica cada questão nos tópicos da matriz, gera o comentário uma única vez e permite filtrar e exportar por tópico.

> O sistema **nunca acessa o Tec Concursos** de forma automatizada. Gerar o PDF e colar os códigos continuam manuais.

## Estado atual (v0.3.0)
- Serviço FastAPI com `/health` (aberto), página de login própria (`/login`, `/sair`) e painel em `/`.
- Painel com Painel, Enviar arquivo, Revisar e Montar caderno usando **dados de exemplo** (`app/api_exemplo.py`).
- Banco Postgres + pgvector com a estrutura completa, criada sozinha na primeira subida.
- Próximas etapas: leitura do PDF, classificação, revisão, comentários, exportação.

## Variáveis de ambiente
Veja `.env.example`.

| Variável | Para quê |
|---|---|
| `DATABASE_URL` | Conexão com o Postgres (pgvector) |
| `USUARIOS` | `usuario:senha,usuario:senha` (senha em texto ou hash bcrypt de `scripts/gerar_hash.py`) |
| `SESSION_SECRET` | Chave das sessões de login (texto longo aleatório) |
| `DADOS_DIR` | Pasta dos arquivos enviados (volume) |
| `GUARDAR_ENUNCIADO` | `1` guarda o texto das questões; `0` guarda só código, tópicos e comentário |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Usadas nas próximas etapas |

## Rodar localmente
```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql://...
export USUARIOS=gustavo:$(python -c "import bcrypt;print(bcrypt.hashpw(b'senha',bcrypt.gensalt()).decode())")
uvicorn app.main:app --reload
```

## Deploy (Easypanel)
1. **Banco:** serviço Postgres com a imagem `pgvector/pgvector:pg16`.
2. **App:** serviço App a partir deste repositório (Dockerfile), porta `8000`.
3. **Volume:** montar em `/data`.
4. **Variáveis:** as da tabela acima.
5. **Domínio com HTTPS** (obrigatório: a senha trafega na autenticação básica).
6. Conferir `https://SEU-DOMINIO/health` → `"banco": "ok"`.
