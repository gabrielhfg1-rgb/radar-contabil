"""Classifica textos nas areas contabeis definidas em categorias.json.

A comparacao ignora acentos, maiusculas/minusculas e pontuacao, e so aceita
palavras inteiras (assim "ISS" nao casa com "comissao").
"""
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def normalizar(texto):
    """'Reforma Tributária: NF-e' -> ' reforma tributaria nf e '"""
    if not texto:
        return " "
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return " " + texto.strip() + " "


class Classificador:
    def __init__(self, config):
        self.areas = []
        for area in config["areas"]:
            termos = []
            for palavra in area.get("palavras", []):
                n = normalizar(palavra)
                if n.strip():
                    termos.append(n)
            self.areas.append((area["id"], termos))
        self.id_outros = config.get("outros", {}).get("id", "outros")

    @classmethod
    def do_arquivo(cls, caminho=None):
        caminho = Path(caminho or RAIZ / "categorias.json")
        with open(caminho, encoding="utf-8") as f:
            return cls(json.load(f))

    def classificar(self, *textos):
        """Devolve a lista de ids de area. Se nada casar, devolve ['outros']."""
        alvo = normalizar(" ".join(t for t in textos if t))
        achadas = [area_id for area_id, termos in self.areas if any(t in alvo for t in termos)]
        return achadas or [self.id_outros]
