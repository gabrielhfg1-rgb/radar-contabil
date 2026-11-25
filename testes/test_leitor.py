import sys
import unittest
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "coletor"))
from coletar import id_do_link, normalizar_link  # noqa: E402
from leitor_feeds import ler_data, ler_feed, resumir  # noqa: E402


def amostra(nome):
    return (PASTA / "amostras" / nome).read_bytes()


class TestLeitor(unittest.TestCase):
    def test_rss2(self):
        itens = ler_feed(amostra("rss2.xml"))
        self.assertEqual(len(itens), 2)
        a = itens[0]
        self.assertEqual(a["titulo"], "Reforma Tributária: CBS e IBS começam em 2026")
        self.assertEqual(a["resumo"], "O Comitê Gestor publicou & detalhou regras novas.")
        self.assertEqual(a["categorias"], ["Tributário"])
        self.assertEqual(a["data"], "2026-11-24T13:30:00Z")

    def test_rdf_receita(self):
        itens = ler_feed(amostra("rdf.xml"))
        self.assertEqual(len(itens), 2)
        self.assertEqual(itens[0]["data"], "2026-11-24T17:05:00Z")
        self.assertEqual(itens[0]["categorias"], ["Imposto de Renda"])
        # sem <link>, usa o rdf:about
        self.assertTrue(itens[1]["link"].endswith("/novembro/b"))

    def test_atom(self):
        itens = ler_feed(amostra("atom.xml"))
        self.assertEqual(itens[0]["link"], "https://exemplo.org/cambio")
        self.assertEqual(itens[0]["categorias"], ["Economia"])

    def test_xml_quebrado(self):
        itens = ler_feed(amostra("quebrado.xml"))
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["link"], "https://exemplo.com/fgts")

    def test_resumo_curto(self):
        texto = "palavra " * 200
        self.assertLessEqual(len(resumir(texto)), 281)

    def test_datas(self):
        self.assertEqual(ler_data("2026-11-20"), "2026-11-20T15:00:00Z")
        self.assertEqual(ler_data("2026-11-20T10:00:00"), "2026-11-20T13:00:00Z")
        self.assertIsNone(ler_data("ontem"))

    def test_links_iguais(self):
        a = "http://www.exemplo.com/noticia/?utm_source=rss#topo"
        b = "https://exemplo.com/noticia"
        self.assertEqual(normalizar_link(a), normalizar_link(b))
        self.assertEqual(id_do_link(a), id_do_link(b))
        self.assertNotEqual(id_do_link("https://x.com/?id=1"), id_do_link("https://x.com/?id=2"))


if __name__ == "__main__":
    unittest.main()
