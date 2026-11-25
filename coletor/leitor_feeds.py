"""Leitor de feeds RSS 2.0, RSS 1.0 (RDF) e Atom usando so a biblioteca padrao."""
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

TAMANHO_RESUMO = 280


def _local(tag):
    """'{http://purl.org/rss/1.0/}item' -> 'item'"""
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""


def limpar_html(texto):
    if not texto:
        return ""
    texto = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", texto)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = html.unescape(html.unescape(texto))
    texto = re.sub(r"\s+", " ", texto).strip()
    return re.sub(r" ([.,;:!?)])", r"\1", texto)


def resumir(texto, limite=TAMANHO_RESUMO):
    texto = limpar_html(texto)
    if len(texto) <= limite:
        return texto
    corte = texto[:limite].rsplit(" ", 1)[0]
    return corte.rstrip(" ,.;:-") + "…"


def ler_data(texto):
    """Aceita datas RFC 822 (RSS) e ISO 8601 (Atom/RDF). Devolve ISO em UTC ou None."""
    if not texto:
        return None
    texto = texto.strip()
    dt = None
    try:
        dt = parsedate_to_datetime(texto)
    except (TypeError, ValueError, IndexError):
        pass
    if dt is None and re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        texto += "T12:00:00"  # so a data, sem hora: considera meio-dia
    if dt is None:
        iso = texto.replace("Z", "+00:00")
        iso = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", iso)
        try:
            dt = datetime.fromisoformat(iso)
        except ValueError:
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})", texto)
            if not m:
                m2 = re.match(r"(\d{2})/(\d{2})/(\d{4})", texto)
                if not m2:
                    return None
                dt = datetime(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)), 12)
            else:
                dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 12)
    if dt.tzinfo is None:
        # Sem fuso: as fontes sao brasileiras, assume horario de Brasilia (UTC-3)
        from datetime import timedelta
        dt = dt.replace(tzinfo=timezone(timedelta(hours=-3)))
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _texto(elem):
    return "".join(elem.itertext()).strip() if elem is not None else ""


def _item_de_elemento(el):
    campos = {"categorias": []}
    for filho in el:
        nome = _local(filho.tag)
        if nome == "title":
            campos["titulo"] = limpar_html(_texto(filho))
        elif nome == "link":
            href = filho.get("href")
            rel = filho.get("rel", "alternate")
            if href and rel == "alternate":
                campos.setdefault("link", href.strip())
            elif _texto(filho):
                campos.setdefault("link", _texto(filho))
        elif nome == "guid" and filho.get("isPermaLink", "true") != "false":
            campos.setdefault("guid", _texto(filho))
        elif nome in ("description", "summary"):
            campos.setdefault("resumo", _texto(filho))
        elif nome == "encoded" and "resumo" not in campos:
            campos["resumo_longo"] = _texto(filho)
        elif nome in ("pubdate", "date", "published", "updated", "issued", "created"):
            campos.setdefault("data", ler_data(_texto(filho)))
        elif nome in ("category", "subject"):
            cat = filho.get("term") or _texto(filho)
            if cat:
                campos["categorias"].append(limpar_html(cat))
    if "link" not in campos:
        sobre = el.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about") or campos.get("guid")
        if sobre and sobre.startswith("http"):
            campos["link"] = sobre
    return campos


def _por_regex(conteudo):
    """Plano B para feeds com XML quebrado (ex.: '&' solto)."""
    itens = []
    for bloco in re.findall(r"(?is)<(?:item|entry)\b[^>]*>(.*?)</(?:item|entry)>", conteudo):
        def pega(*tags):
            for t in tags:
                m = re.search(rf"(?is)<{t}\b[^>]*>(.*?)</{t}>", bloco)
                if m:
                    v = m.group(1)
                    v = re.sub(r"(?s)<!\[CDATA\[(.*?)\]\]>", r"\1", v)
                    return v.strip()
            return ""
        link = pega("link")
        if not link:
            m = re.search(r'(?i)<link\b[^>]*href="([^"]+)"', bloco)
            link = m.group(1) if m else ""
        itens.append({
            "titulo": limpar_html(pega("title")),
            "link": html.unescape(link),
            "resumo": pega("description", "summary"),
            "data": ler_data(pega("pubDate", "dc:date", "published", "updated")),
            "categorias": [limpar_html(re.sub(r"(?s)<!\[CDATA\[(.*?)\]\]>", r"\1", c))
                           for c in re.findall(r"(?is)<category\b[^>]*>(.*?)</category>", bloco)],
        })
    return itens


def ler_feed(conteudo):
    """Recebe o feed (bytes ou str) e devolve lista de dicionarios com
    titulo, link, resumo, data e categorias."""
    try:
        raiz = ET.fromstring(conteudo if isinstance(conteudo, bytes) else conteudo.encode("utf-8"))
        brutos = [_item_de_elemento(el) for el in raiz.iter() if _local(el.tag) in ("item", "entry")]
    except ET.ParseError:
        texto = conteudo.decode("utf-8", "replace") if isinstance(conteudo, bytes) else conteudo
        brutos = _por_regex(texto)

    itens = []
    for b in brutos:
        link = (b.get("link") or "").strip()
        titulo = (b.get("titulo") or "").strip()
        if not link or not titulo:
            continue
        itens.append({
            "titulo": titulo,
            "link": link,
            "resumo": resumir(b.get("resumo") or b.get("resumo_longo") or ""),
            "data": b.get("data"),
            "categorias": [c for c in b.get("categorias", []) if c],
        })
    return itens
