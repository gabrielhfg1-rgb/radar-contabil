import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coletor"))
from classificador import Classificador, normalizar  # noqa: E402


class TestClassificador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Classificador.do_arquivo()

    def test_ignora_acentos_e_maiusculas(self):
        self.assertIn("fiscal", self.c.classificar("REFORMA TRIBUTARIA avança no Senado"))
        self.assertIn("fiscal", self.c.classificar("reforma tributária"))

    def test_palavra_inteira(self):
        # "ISS" nao pode casar com "comissão"; "MEI" nao pode casar com "meio"
        self.assertEqual(self.c.classificar("Comissão aprova meio ambiente"), ["outros"])

    def test_siglas_com_hifen(self):
        self.assertIn("fiscal", self.c.classificar("Nova versão da NF-e"))
        self.assertIn("fiscal", self.c.classificar("Prefeitura muda a NFS-e"))

    def test_mais_de_uma_area(self):
        areas = self.c.classificar("Holding familiar e ITCMD após a reforma tributária")
        self.assertIn("societario", areas)
        self.assertIn("fiscal", areas)

    def test_cada_area(self):
        casos = {
            "pessoal": "Governo muda prazo do eSocial e do FGTS Digital",
            "societario": "Distribuição de dividendos e JCP",
            "abertura": "MEI pode abrir CNPJ pela Redesim",
            "normas": "CFC publica nova NBC sobre demonstrações contábeis",
            "cambio": "IOF sobre câmbio sobe para remessa ao exterior",
            "fiscal": "Simples Nacional: prazo de opção",
        }
        for area, texto in casos.items():
            with self.subTest(area=area):
                self.assertIn(area, self.c.classificar(texto))

    def test_decimo_terceiro(self):
        self.assertIn("pessoal", self.c.classificar("Prazo do 13º salário"))

    def test_outros(self):
        self.assertEqual(self.c.classificar("Time vence campeonato"), ["outros"])

    def test_varios_textos(self):
        self.assertIn("normas", self.c.classificar("Título neutro", "", "Normas contábeis"))

    def test_normalizar(self):
        self.assertEqual(normalizar("Câmbio: NF-e!"), " cambio nf e ")


if __name__ == "__main__":
    unittest.main()
