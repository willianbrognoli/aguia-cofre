"""API do painel com DADOS DE EXEMPLO.

Enquanto o parser do PDF não está pronto, estas rotas devolvem dados fictícios
no mesmo formato que as rotas reais vão devolver. Quando o parser e a
classificação ficarem prontos, cada função passa a ler do banco.
"""
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .auth import usuario_atual

router = APIRouter(prefix="/api", dependencies=[Depends(usuario_atual)])

_rng = random.Random(7)
AGORA = datetime.now()

MATERIAS = [
    {"id": 1, "nome": "Administração", "questoes": 3612, "classificadas": 3274, "revisar": 338, "comentadas": 0,
     "atualizado": (AGORA - timedelta(hours=3)).isoformat(), "situacao": "pendencias"},
    {"id": 2, "nome": "Língua Portuguesa", "questoes": 0, "classificadas": 0, "revisar": 0, "comentadas": 0,
     "atualizado": None, "situacao": "sem_caderno"},
    {"id": 3, "nome": "Direito Constitucional", "questoes": 0, "classificadas": 0, "revisar": 0, "comentadas": 0,
     "atualizado": None, "situacao": "sem_caderno"},
    {"id": 4, "nome": "Direito Penal", "questoes": 0, "classificadas": 0, "revisar": 0, "comentadas": 0,
     "atualizado": None, "situacao": "sem_caderno"},
]

TOPICOS_ADM = [
    ("1", "Aula 1 · Administração geral", [
        ("1.1", "Conceito e funções da administração", 214),
        ("1.2", "Evolução das teorias administrativas", 301),
        ("1.3", "Cultura e clima organizacional", 176),
    ]),
    ("2", "Aula 2 · Planejamento", [
        ("2.1", "Planejamento estratégico, tático e operacional", 268),
        ("2.2", "Análise SWOT e cenários", 143),
        ("2.3", "Balanced Scorecard", 97),
    ]),
    ("3", "Aula 3 · Organização e direção", [
        ("3.1", "Estrutura organizacional e departamentalização", 255),
        ("3.2", "Liderança e motivação", 389),
        ("3.3", "Comunicação e tomada de decisão", 162),
    ]),
    ("4", "Aula 4 · Controle e gestão pública", [
        ("4.1", "Controle: tipos e ferramentas", 188),
        ("4.2", "Gestão de processos", 211),
        ("4.3", "Gestão por resultados e indicadores", 154),
        ("4.4", "Governança e compliance no setor público", 132),
    ]),
    ("5", "Aula 5 · Gestão de pessoas", [
        ("5.1", "Recrutamento e seleção", 120),
        ("5.2", "Avaliação de desempenho", 146),
        ("5.3", "Treinamento e desenvolvimento", 98),
    ]),
]
BANCAS = ["CESPE/CEBRASPE", "FGV", "VUNESP", "FCC", "IBFC", "IDECAN", "AOCP"]

ENUNCIADOS = [
    ("A respeito das funções administrativas, julgue o item: o controle consiste em comparar o desempenho "
     "real com os padrões estabelecidos no planejamento e corrigir desvios.", "certo_errado",
     [("4.1", 0.58), ("1.1", 0.31)]),
    ("Um gestor que adapta seu estilo ao grau de maturidade da equipe, alternando entre orientar e delegar, "
     "está aplicando qual abordagem de liderança?", "multipla",
     [("3.2", 0.61), ("1.2", 0.22)]),
    ("Na análise do ambiente de uma organização pública, a identificação de mudanças na legislação que podem "
     "afetar os serviços prestados corresponde a qual elemento da matriz?", "multipla",
     [("2.2", 0.55), ("2.1", 0.36)]),
    ("Julgue o item: a departamentalização por processos agrupa as atividades segundo a sequência do fluxo "
     "de trabalho, favorecendo a visão horizontal da organização.", "certo_errado",
     [("3.1", 0.52), ("4.2", 0.44)]),
    ("Assinale a alternativa que apresenta um indicador de eficiência, e não de eficácia, na gestão de uma "
     "unidade de atendimento ao cidadão.", "multipla",
     [("4.3", 0.49), ("4.1", 0.40)]),
    ("Segundo a teoria dos dois fatores, as condições de trabalho e a remuneração são fatores que, quando "
     "adequados, apenas evitam a insatisfação.", "certo_errado",
     [("3.2", 0.63), ("5.2", 0.18)]),
]
ALTS = ["Situacional", "Transacional", "Carismática", "Autocrática", "Laissez-faire"]


def _titulo(codigo: str) -> str:
    for _, _, subs in TOPICOS_ADM:
        for c, t, _ in subs:
            if c == codigo:
                return t
    return codigo


def _fila():
    fila = []
    for i, (enun, tipo, sug) in enumerate(ENUNCIADOS):
        fila.append({
            "id": 1000 + i,
            "codigo": str(3150000 + _rng.randint(1000, 99999)),
            "banca": BANCAS[i % len(BANCAS)],
            "orgao": ["PC-PR", "PF", "PRF", "PM-SP", "TJ-RS", "SEFAZ-BA"][i],
            "ano": 2018 + (i * 2) % 7,
            "tipo": tipo,
            "enunciado": enun,
            "alternativas": [] if tipo == "certo_errado" else ALTS[:5],
            "gabarito": "C" if tipo == "certo_errado" else "A",
            "tem_imagem": i == 4,
            "sugestoes": [{"codigo": c, "titulo": _titulo(c), "confianca": p} for c, p in sug],
        })
    return fila


FILA = _fila()


@router.get("/resumo")
def resumo():
    total = sum(m["questoes"] for m in MATERIAS)
    return {
        "exemplo": True,
        "totais": {
            "questoes": total,
            "classificadas": sum(m["classificadas"] for m in MATERIAS),
            "revisar": sum(m["revisar"] for m in MATERIAS),
            "comentadas": sum(m["comentadas"] for m in MATERIAS),
        },
        "materias": MATERIAS,
        "envios": [
            {"id": 3, "tipo": "caderno", "materia": "Administração", "arquivo": "administracao-completo.pdf",
             "status": "pronto", "total": 3612, "novas": 3612, "por": "luiz",
             "quando": (AGORA - timedelta(hours=3)).isoformat()},
            {"id": 2, "tipo": "matriz", "materia": "Administração", "arquivo": "matriz-administracao-v1.xlsx",
             "status": "pronto", "total": 16, "novas": 16, "por": "luiz",
             "quando": (AGORA - timedelta(hours=4)).isoformat()},
            {"id": 1, "tipo": "caderno", "materia": "Administração", "arquivo": "adm-teste.pdf",
             "status": "erro", "total": 0, "novas": 0, "por": "willian",
             "quando": (AGORA - timedelta(days=1)).isoformat(),
             "mensagem": "O arquivo não parece ser um caderno do Tec Concursos."},
        ],
    }


@router.get("/materias/{materia_id}/topicos")
def topicos(materia_id: int):
    if materia_id != 1:
        return {"exemplo": True, "aulas": []}
    return {
        "exemplo": True,
        "aulas": [
            {"codigo": c, "titulo": t,
             "topicos": [{"codigo": sc, "titulo": st, "questoes": n} for sc, st, n in subs]}
            for c, t, subs in TOPICOS_ADM
        ],
    }


@router.get("/revisar")
def revisar():
    return {"exemplo": True, "total": 338, "itens": FILA}


class Decisao(BaseModel):
    topicos: list[str]


@router.post("/revisar/{questao_id}")
def decidir(questao_id: int, d: Decisao, usuario: str = Depends(usuario_atual)):
    return {"ok": True, "questao_id": questao_id, "topicos": d.topicos, "por": usuario}


class Filtro(BaseModel):
    materia_id: int
    topicos: list[str] = []
    bancas: list[str] = []
    ano_min: int | None = None
    ano_max: int | None = None
    so_revisadas: bool = False


@router.post("/filtrar")
def filtrar(f: Filtro):
    base = {sc: n for _, _, subs in TOPICOS_ADM for sc, _, n in subs}
    n = sum(base.get(t, 0) for t in f.topicos)
    if f.bancas:
        n = int(n * min(1, len(f.bancas) / 4))
    if f.ano_min or f.ano_max:
        n = int(n * 0.7)
    if f.so_revisadas:
        n = int(n * 0.9)
    r = random.Random(hash(tuple(sorted(f.topicos))) & 0xFFFF)
    codigos = sorted({str(r.randint(300000, 3299999)) for _ in range(n)})
    return {"exemplo": True, "total": len(codigos), "codigos": codigos}


@router.get("/bancas")
def bancas():
    return {"exemplo": True, "bancas": BANCAS}


class Envio(BaseModel):
    tipo: str
    materia_id: int | None = None
    arquivo: str
    ref_externa: str | None = None


@router.post("/envios/simular")
def simular_envio(e: Envio, usuario: str = Depends(usuario_atual)):
    return {"ok": True, "exemplo": True, "tipo": e.tipo, "arquivo": e.arquivo, "por": usuario}
