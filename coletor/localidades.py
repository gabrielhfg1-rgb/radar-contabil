"""Identifica estados (UF) e municípios citados num texto.

A lista de municípios fica em localidades.json (na raiz do projeto) e pode ser
ampliada sem programar: basta acrescentar "Nome da cidade/UF".
"""
import json
import re
from pathlib import Path

from classificador import normalizar

RAIZ = Path(__file__).resolve().parent.parent

ESTADOS = {
    "AC": ("Acre", ["acre", "acreano", "acreana"]),
    "AL": ("Alagoas", ["alagoas", "alagoano", "alagoana"]),
    "AP": ("Amapá", ["amapa", "amapaense"]),
    "AM": ("Amazonas", ["amazonas", "amazonense"]),
    "BA": ("Bahia", ["bahia", "baiano", "baiana"]),
    "CE": ("Ceará", ["ceara", "cearense"]),
    "DF": ("Distrito Federal", ["distrito federal", "brasiliense"]),
    "ES": ("Espírito Santo", ["espirito santo", "capixaba"]),
    "GO": ("Goiás", ["goias", "goiano", "goiana"]),
    "MA": ("Maranhão", ["maranhao", "maranhense"]),
    "MT": ("Mato Grosso", ["mato grosso", "mato grossense"]),
    "MS": ("Mato Grosso do Sul", ["mato grosso do sul", "sul mato grossense"]),
    "MG": ("Minas Gerais", ["minas gerais"]),
    "PA": ("Pará", ["para", "paraense"]),
    "PB": ("Paraíba", ["paraiba", "paraibano", "paraibana"]),
    "PR": ("Paraná", ["parana", "paranaense"]),
    "PE": ("Pernambuco", ["pernambuco", "pernambucano", "pernambucana"]),
    "PI": ("Piauí", ["piaui", "piauiense"]),
    "RJ": ("Rio de Janeiro", ["estado do rio de janeiro", "fluminense"]),
    "RN": ("Rio Grande do Norte", ["rio grande do norte", "potiguar"]),
    "RS": ("Rio Grande do Sul", ["rio grande do sul", "gaucho", "gaucha"]),
    "RO": ("Rondônia", ["rondonia", "rondoniense"]),
    "RR": ("Roraima", ["roraima", "roraimense"]),
    "SC": ("Santa Catarina", ["santa catarina", "catarinense"]),
    "SP": ("São Paulo", ["estado de sao paulo", "paulista"]),
    "SE": ("Sergipe", ["sergipe", "sergipano", "sergipana"]),
    "TO": ("Tocantins", ["tocantins", "tocantinense"]),
}
# Nomes que também são palavras comuns: só contam com contexto ("estado do Pará")
AMBIGUOS_UF = {"para"}

# Sigla com contexto: "Sefaz-SP", "ICMS/RJ", "(MG)", "em SP", "no RS", "do PR"
_SIGLAS = "|".join(ESTADOS)
RE_SIGLA = re.compile(
    r"(?:[-/(]\s?|\b(?:em|de|do|da|no|na|para o|para a)\s+)(" + _SIGLAS + r")\b(?!-[a-z])"
)

RE_ESTADUAL = re.compile(
    r"\b(sefaz|secretaria (estadual )?da fazenda|assembleia legislativa|alesp|alerj|almg|alep|alesc|"
    r"governo (do estado|estadual)|governador|lei estadual|decreto estadual|icms|ipva|itcmd|fundo estadual)\b"
)
RE_MUNICIPAL = re.compile(
    r"\b(prefeitura|prefeito|camara municipal|vereador|vereadores|lei municipal|decreto municipal|"
    r"iss|issqn|iptu|itbi|nfs e municipal|codigo tributario municipal|refis municipal)\b"
)


def _carregar_municipios():
    arq = RAIZ / "localidades.json"
    with open(arq, encoding="utf-8") as f:
        dados = json.load(f)
    lista = []
    for entrada in dados["municipios"]:
        nome, uf = entrada.rsplit("/", 1)
        lista.append((nome.strip(), uf.strip().upper(), normalizar(nome)))
    ambiguos = {normalizar(x) for x in dados.get("ambiguos", [])}
    return lista, ambiguos


MUNICIPIOS, AMBIGUOS_MUN = _carregar_municipios()


def detectar(*textos):
    """Devolve (lista de UFs, lista de 'Município/UF') citados nos textos."""
    original = " ".join(t for t in textos if t)
    alvo = normalizar(original)
    ufs = set()
    municipios = set()

    for nome, uf, n in MUNICIPIOS:
        if n not in alvo:
            continue
        contexto = re.search(
            r"(prefeitura|municipio|cidade|capital) (de|do|da)" + re.escape(n.rstrip()) +
            r"|" + re.escape(n.rstrip()) + r" " + uf.lower() + r" ",
            alvo,
        )
        if n in AMBIGUOS_MUN and not contexto:
            continue
        # "São Paulo" e "Rio de Janeiro" sozinhos indicam o estado; a cidade precisa de contexto
        if n.strip() in ("sao paulo", "rio de janeiro") and not contexto:
            ufs.add(uf)
            continue
        municipios.add(f"{nome}/{uf}")
        ufs.add(uf)

    for uf, (_, termos) in ESTADOS.items():
        for t in termos:
            nt = " " + t + " "
            if nt in alvo:
                if t in AMBIGUOS_UF and not re.search(r"(estado|governo) do " + t + " ", alvo):
                    continue
                ufs.add(uf)
                break

    for m in RE_SIGLA.finditer(original):
        ufs.add(m.group(1))

    return sorted(ufs), sorted(municipios)


def esfera_pelo_texto(texto_normalizado):
    """'estadual', 'municipal' ou None, conforme o assunto do texto."""
    if RE_MUNICIPAL.search(texto_normalizado):
        return "municipal"
    if RE_ESTADUAL.search(texto_normalizado):
        return "estadual"
    return None
