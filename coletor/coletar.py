"""Radar Contabil — coletor principal.

Uso:  python coletor/coletar.py

Le fontes.json e categorias.json, busca os itens novos, classifica, junta com o
historico (sem duplicar) e grava em docs/dados/. Se uma fonte falhar, registra
o erro e segue com as outras.
"""
import hashlib
import os
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classificador import Classificador  # noqa: E402
from leitor_feeds import ler_data, ler_feed, resumir  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = Path(os.environ.get("RADAR_DADOS", RAIZ / "docs" / "dados"))
ARQ_FONTES = Path(os.environ.get("RADAR_FONTES", RAIZ / "fontes.json"))
USER_AGENT = "Mozilla/5.0 (compatible; RadarContabil/1.0; robo de leitura de feeds de escritorio contabil)"
PAUSA_ENTRE_REQUISICOES = 1.5  # segundos, para nao sobrecarregar as fontes
TEMPO_LIMITE = 30

PARAMETROS_RASTREIO = ("utm_", "fbclid", "gclid", "mc_", "ref")


def agora_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def baixar(url, tentativas=3, accept="application/rss+xml, application/xml, text/xml, */*"):
    erro = None
    for n in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": accept,
                "Accept-Language": "pt-BR,pt;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=TEMPO_LIMITE) as resp:
                return resp.read()
        except Exception as e:  # noqa: BLE001 — qualquer falha vira registro, nao derruba o robo
            erro = e
            if n + 1 < tentativas:
                time.sleep(5)
    raise erro


def normalizar_link(link):
    """Remove parametros de rastreio, '#...' e barra final para comparar links."""
    partes = urllib.parse.urlsplit(link.strip())
    consulta = [(k, v) for k, v in urllib.parse.parse_qsl(partes.query, keep_blank_values=True)
                if not k.lower().startswith(PARAMETROS_RASTREIO)]
    caminho = partes.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((
        "https",  # http e https contam como o mesmo link
        partes.netloc.lower().removeprefix("www."),
        caminho, urllib.parse.urlencode(consulta), "",
    ))


def id_do_link(link):
    return hashlib.sha1(normalizar_link(link).encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------- fontes

def coletar_feed(fonte):
    itens = []
    for bruto in ler_feed(baixar(fonte["url"])):
        itens.append({
            "titulo": bruto["titulo"],
            "link": bruto["link"],
            "resumo": bruto["resumo"],
            "data": bruto["data"],
            "categorias_fonte": bruto["categorias"][:6],
            "tipo": "noticia",
        })
    return itens


def coletar_camara(fonte):
    itens = []
    tipos = set(fonte.get("tipos") or [])
    for termo in fonte.get("termos", []):
        params = urllib.parse.urlencode({
            "keywords": termo, "ordem": "DESC", "ordenarPor": "id", "itens": 50,
        })
        dados = json.loads(baixar(f"{fonte['url']}?{params}", accept="application/json"))
        for p in dados.get("dados", []):
            if tipos and p.get("siglaTipo") not in tipos:
                continue
            ementa = (p.get("ementa") or "").strip()
            itens.append({
                "titulo": f"{p.get('siglaTipo')} {p.get('numero')}/{p.get('ano')}",
                "link": f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={p['id']}",
                "resumo": resumir(ementa),
                "data": _data_camara(p),
                "categorias_fonte": [termo],
                "tipo": "projeto",
            })
        time.sleep(PAUSA_ENTRE_REQUISICOES)
    return itens


def _data_camara(p):
    return ler_data(p.get("dataApresentacao") or "")


COLETORES = {"feed": coletar_feed, "camara": coletar_camara}


# ---------------------------------------------------------------- historico

def carregar_historico():
    itens = {}
    if PASTA_DADOS.exists():
        for arq in sorted(PASTA_DADOS.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].json")):
            with open(arq, encoding="utf-8") as f:
                for item in json.load(f):
                    itens[item["id"]] = item
    return itens


def salvar(itens, status, classif_config):
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    por_mes = {}
    for item in itens.values():
        por_mes.setdefault(item["data"][:7], []).append(item)
    for mes, lista in por_mes.items():
        lista.sort(key=lambda i: (i["data"], i["id"]), reverse=True)
        _gravar(PASTA_DADOS / f"{mes}.json", lista, compacto=True)
    indice = {
        "atualizado_em": agora_iso(),
        "meses": sorted(por_mes, reverse=True),
        "total": len(itens),
        "areas": classif_config["areas_painel"],
        "fontes": status,
    }
    _gravar(PASTA_DADOS / "indice.json", indice)


def _gravar(caminho, dados, compacto=False):
    tmp = caminho.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        if compacto:
            f.write("[\n" + ",\n".join(json.dumps(i, ensure_ascii=False, sort_keys=True) for i in dados) + "\n]\n")
        else:
            json.dump(dados, f, ensure_ascii=False, indent=1)
            f.write("\n")
    tmp.replace(caminho)


# ---------------------------------------------------------------- principal

def main():
    with open(ARQ_FONTES, encoding="utf-8") as f:
        fontes = [x for x in json.load(f)["fontes"] if x.get("ativo", True)]
    with open(RAIZ / "categorias.json", encoding="utf-8") as f:
        cat_config = json.load(f)
    classificador = Classificador(cat_config)
    areas_painel = [{"id": a["id"], "nome": a["nome"], "cor": a.get("cor", "#555")} for a in cat_config["areas"]]
    areas_painel.append(cat_config.get("outros", {"id": "outros", "nome": "Outros", "cor": "#7f8c8d"}))

    historico = carregar_historico()
    antes = len(historico)
    agora = agora_iso()
    status = []

    for fonte in fontes:
        registro = {"nome": fonte["nome"], "url": fonte["url"], "quando": agora}
        try:
            coletados = COLETORES[fonte.get("tipo", "feed")](fonte)
            novos = 0
            for item in coletados:
                item["areas"] = classificador.classificar(item["titulo"], item["resumo"], *item["categorias_fonte"])
                if fonte.get("somente_com_area") and item["areas"] == [classificador.id_outros]:
                    continue
                iid = id_do_link(item["link"])
                if iid in historico:
                    continue
                if not item["data"] or item["data"] > agora:
                    item["data"] = agora
                item.update({"id": iid, "fonte": fonte["nome"], "coletado_em": agora})
                historico[iid] = item
                novos += 1
            registro.update({"ok": True, "lidos": len(coletados), "novos": novos})
            print(f"[ok]   {fonte['nome']:<28} lidos={len(coletados):<4} novos={novos}  {fonte['url']}")
        except Exception as e:  # noqa: BLE001
            registro.update({"ok": False, "erro": f"{type(e).__name__}: {e}"[:300]})
            print(f"[ERRO] {fonte['nome']:<28} {registro['erro']}  {fonte['url']}")
        status.append(registro)
        time.sleep(PAUSA_ENTRE_REQUISICOES)

    # Reclassifica tudo: se voce mudar categorias.json, os itens antigos se ajustam tambem.
    for item in historico.values():
        item["resumo"] = resumir(item.get("resumo", ""))
        item["areas"] = classificador.classificar(item["titulo"], item["resumo"], *item.get("categorias_fonte", []))

    cat_config["areas_painel"] = areas_painel
    salvar(historico, status, cat_config)
    falhas = sum(1 for s in status if not s["ok"])
    print(f"\nTotal no historico: {len(historico)} (novos nesta rodada: {len(historico) - antes}). "
          f"Fontes com erro: {falhas} de {len(status)}.")
    # So falha o processo se TODAS as fontes falharem (ai provavelmente e problema de rede).
    return 1 if status and falhas == len(status) else 0


if __name__ == "__main__":
    sys.exit(main())
