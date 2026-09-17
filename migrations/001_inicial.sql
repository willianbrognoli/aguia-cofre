-- Cofre de Questões · estrutura inicial
-- Requer Postgres com pgvector (imagem pgvector/pgvector:pg16)

CREATE EXTENSION IF NOT EXISTS vector;

-- Matérias (Administração, Português, ...)
CREATE TABLE materias (
  id          bigserial PRIMARY KEY,
  nome        text NOT NULL UNIQUE,
  criado_em   timestamptz NOT NULL DEFAULT now()
);

-- Versões da matriz de tópicos de cada matéria
CREATE TABLE matrizes (
  id           bigserial PRIMARY KEY,
  materia_id   bigint NOT NULL REFERENCES materias(id),
  versao       int NOT NULL,
  arquivo      text,
  ativa        boolean NOT NULL DEFAULT true,
  criado_por   text,
  criado_em    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (materia_id, versao)
);

-- Tópicos da matriz (independentes da origem da questão)
CREATE TABLE topicos (
  id           bigserial PRIMARY KEY,
  matriz_id    bigint NOT NULL REFERENCES matrizes(id),
  materia_id   bigint NOT NULL REFERENCES materias(id),
  codigo       text,                 -- ex.: "3.2"
  titulo       text NOT NULL,
  caminho      text,                 -- ex.: "Aula 3 > Controle > Tipos"
  ordem        int,
  embedding    vector(1536),         -- OpenAI text-embedding-3-small
  criado_em    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX topicos_materia_idx ON topicos (materia_id);

-- Envios feitos pelo painel (cadernos, matrizes, editais)
CREATE TABLE envios (
  id            bigserial PRIMARY KEY,
  tipo          text NOT NULL CHECK (tipo IN ('caderno', 'matriz', 'edital')),
  materia_id    bigint REFERENCES materias(id),
  nome_arquivo  text NOT NULL,
  caminho       text NOT NULL,
  ref_externa   text,                -- nº do caderno no Tec (opcional)
  status        text NOT NULL DEFAULT 'recebido'
                CHECK (status IN ('recebido', 'processando', 'pronto', 'erro')),
  total         int NOT NULL DEFAULT 0,
  novas         int NOT NULL DEFAULT 0,
  mensagens     jsonb NOT NULL DEFAULT '[]',
  criado_por    text,
  criado_em     timestamptz NOT NULL DEFAULT now(),
  concluido_em  timestamptz
);

-- Questões (qualquer origem). O código do Tec é um campo, não a identidade.
CREATE TABLE questoes (
  id              bigserial PRIMARY KEY,
  origem          text NOT NULL
                  CHECK (origem IN ('tec', 'prova_oficial', 'plataforma_professores', 'autoral')),
  codigo_origem   text,              -- código da questão no Tec
  materia_id      bigint REFERENCES materias(id),
  banca           text,
  orgao           text,
  cargo           text,
  ano             int,
  enunciado       text,              -- vazio se GUARDAR_ENUNCIADO=0
  alternativas    jsonb,             -- [{"letra":"A","texto":"..."}] ou null (Certo/Errado)
  tipo            text CHECK (tipo IN ('multipla', 'certo_errado')),
  gabarito        text,
  tabelas         jsonb NOT NULL DEFAULT '[]',
  imagens         jsonb NOT NULL DEFAULT '[]',
  tem_imagem      boolean NOT NULL DEFAULT false,
  situacao        text NOT NULL DEFAULT 'ativa'
                  CHECK (situacao IN ('ativa', 'anulada', 'desatualizada', 'gabarito_alterado')),
  hash_conteudo   text,              -- detecta mudança ao reenviar
  embedding       vector(1536),
  envio_id        bigint REFERENCES envios(id),
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (origem, codigo_origem)
);
CREATE INDEX questoes_materia_idx ON questoes (materia_id);
CREATE INDEX questoes_banca_ano_idx ON questoes (banca, ano);

-- Classificação questão × tópico (IA sugere, equipe confirma)
CREATE TABLE classificacoes (
  id            bigserial PRIMARY KEY,
  questao_id    bigint NOT NULL REFERENCES questoes(id) ON DELETE CASCADE,
  topico_id     bigint NOT NULL REFERENCES topicos(id),
  confianca     real,
  metodo        text NOT NULL CHECK (metodo IN ('ia', 'humano')),
  status        text NOT NULL DEFAULT 'sugerida'
                CHECK (status IN ('sugerida', 'confirmada', 'rejeitada')),
  revisado_por  text,
  revisado_em   timestamptz,
  criado_em     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (questao_id, topico_id)
);
CREATE INDEX classificacoes_topico_idx ON classificacoes (topico_id);
CREATE INDEX classificacoes_revisar_idx ON classificacoes (status, confianca);

-- Comentários (gerados uma vez, versionados)
CREATE TABLE comentarios (
  id             bigserial PRIMARY KEY,
  questao_id     bigint NOT NULL REFERENCES questoes(id) ON DELETE CASCADE,
  versao         int NOT NULL,
  texto          text NOT NULL,
  modelo         text,
  prompt_versao  text,
  criado_em      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (questao_id, versao)
);

-- Quem fez o quê
CREATE TABLE log_acoes (
  id         bigserial PRIMARY KEY,
  usuario    text NOT NULL,
  acao       text NOT NULL,
  detalhe    jsonb NOT NULL DEFAULT '{}',
  criado_em  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX log_acoes_data_idx ON log_acoes (criado_em DESC);
