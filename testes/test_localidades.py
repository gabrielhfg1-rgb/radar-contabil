import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coletor"))
from classificador import normalizar  # noqa: E402
from localidades import detectar, esfera_pelo_texto  # noqa: E402


class TestLocalidades(unittest.TestCase):
    def test_sigla_com_contexto(self):
        self.assertEqual(detectar("Emitiu NF-e duplicada em SP? Sefaz proíbe")[0], ["SP"])
        self.assertEqual(detectar("Nova regra do ICMS-RJ")[0], ["RJ"])
        self.assertEqual(detectar("Refis ISS Natal (RN) permite quitar")[0], ["RN"])

    def test_sigla_sem_contexto_nao_conta(self):
        # "PA" e "MA" soltos, ou dentro de palavras, nao viram estado
        self.assertEqual(detectar("O PIS e a COFINS no regime MA PA")[0], [])

    def test_nome_do_estado(self):
        self.assertIn("RS", detectar("Governo do Rio Grande do Sul prorroga prazo")[0])
        self.assertIn("SC", detectar("Empresas catarinenses terão novo benefício")[0] or detectar("Empresa catarinense")[0])

    def test_para_ambiguo(self):
        self.assertEqual(detectar("Prazo para entrega da DCTF")[0], [])
        self.assertIn("PA", detectar("Governo do Pará reduz ICMS")[0])

    def test_municipio(self):
        ufs, muns = detectar("Prefeitura de Campinas lança Refis do ISS")
        self.assertEqual(muns, ["Campinas/SP"])
        self.assertEqual(ufs, ["SP"])

    def test_municipio_ambiguo(self):
        self.assertEqual(detectar("Feliz Natal e boas festas")[1], [])
        self.assertEqual(detectar("Refis ISS Natal/RN")[1], ["Natal/RN"])
        self.assertEqual(detectar("Prefeitura de Natal abre Refis")[1], ["Natal/RN"])

    def test_sao_paulo_estado_x_cidade(self):
        ufs, muns = detectar("São Paulo detalha crédito de ICMS")
        self.assertEqual((ufs, muns), (["SP"], []))
        self.assertEqual(detectar("Prefeitura de São Paulo muda o IPTU")[1], ["São Paulo/SP"])

    def test_esfera(self):
        self.assertEqual(esfera_pelo_texto(normalizar("Prefeitura de Natal abre Refis do ISS")), "municipal")
        self.assertEqual(esfera_pelo_texto(normalizar("Sefaz-SP orienta sobre crédito")), "estadual")
        self.assertIsNone(esfera_pelo_texto(normalizar("Receita libera lote do IRPF")))


if __name__ == "__main__":
    unittest.main()
