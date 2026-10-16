import unittest

from helpers import bench, focus, new_service, run

from comes import config as C
from comes.expediente import COZINHA, STATIONS

CHAPA = STATIONS.index("chapa")
FRITADEIRA = STATIONS.index("fritadeira")
LIQUIDIFICADOR = STATIONS.index("liquidificador")
LIXEIRA = STATIONS.index("lixeira")


class BancadaTest(unittest.TestCase):
    def test_misto_montado_gasta_estoque(self):
        s, ui, casa, _, _ = new_service()
        before = casa.count("pao")
        self.assertTrue(bench(s, "ing:pao", "ing:presunto", "ing:queijo"))
        self.assertEqual([i.kind for i in s.hands], ["misto_montado"])
        self.assertEqual(casa.count("pao"), before - 1)
        self.assertIn("misto montado", ui.last())

    def test_combinacao_errada_nao_gasta_nada(self):
        s, ui, casa, _, _ = new_service()
        before = casa.count("pao")
        self.assertFalse(bench(s, "ing:pao", "ing:laranja"))
        self.assertEqual(s.hands, [])
        self.assertEqual(casa.count("pao"), before)
        self.assertIn("não vira nenhuma receita", ui.last())

    def test_opcoes_descontam_o_que_ja_foi_escolhido(self):
        s, _, casa, _, _ = new_service()
        casa.stock["sal"] = [[1, 999]]
        s.bench = ["ing:sal"]
        keys = [k for k, _ in s.bench_options()]
        self.assertNotIn("ing:sal", keys)

    def test_mao_entra_na_montagem(self):
        s, _, _, _, _ = new_service()
        from comes.expediente import Item
        s.hands = [Item("hamburguer", quality=0.6)]
        self.assertTrue(bench(s, "ing:pao", "mao:0", "ing:queijo"))
        self.assertEqual(len(s.hands), 1)
        self.assertEqual(s.hands[0].kind, "xburger")
        self.assertAlmostEqual(s.hands[0].quality, 0.6)

    def test_maos_cheias(self):
        s, ui, _, _, _ = new_service()
        bench(s, "ing:carne")
        bench(s, "ing:carne")
        self.assertFalse(bench(s, "ing:carne"))
        self.assertIn("cheias", ui.last())


class ChapaTest(unittest.TestCase):
    def setUp(self):
        self.s, self.ui, self.casa, _, _ = new_service()
        bench(self.s, "ing:carne")
        focus(self.s, COZINHA, CHAPA)
        self.s.action_down()            # põe na chapa
        self.tp = C.COOK["hamburguer_cru"][0]

    def test_no_ponto(self):
        self.assertEqual(len(self.s.cookers["chapa"].slots), 1)
        self.assertIn("chapa", self.ui.loops)
        run(self.s, self.tp + 0.5)
        self.assertIn("ponto", self.ui.played)
        self.s.action_down()
        self.assertEqual(self.s.hands[0].kind, "hamburguer")
        self.assertEqual(self.s.hands[0].quality, 1.0)
        self.assertNotIn("chapa", self.ui.loops)

    def test_passando_do_ponto(self):
        tp, win, _, _ = C.COOK["hamburguer_cru"]
        run(self.s, tp + win + 0.5)
        self.s.action_down()
        self.assertEqual(self.s.hands[0].quality, C.PASSING_QUALITY)

    def test_queima_e_pega_fogo(self):
        total = sum(C.COOK["hamburguer_cru"])
        run(self.s, total + 0.5)
        chapa = self.s.cookers["chapa"]
        self.assertTrue(chapa.fire)
        self.assertEqual(self.ui.loops["chapa"][0], "fogo")
        self.assertEqual(self.s.stats["fires"], 1)
        self.s.action_down()            # extintor
        run(self.s, C.EXTINGUISH_TIME + 0.2)
        self.assertFalse(chapa.fire)
        self.assertGreaterEqual(self.casa.dirt["chapa"], 3)

    def test_fogo_passa_para_a_fritadeira(self):
        run(self.s, sum(C.COOK["hamburguer_cru"]) + C.FIRE_SPREAD + 0.5)
        self.assertTrue(self.s.cookers["fritadeira"].fire)

    def test_queimado_vai_para_a_lixeira(self):
        tp, win, passing, _ = C.COOK["hamburguer_cru"]
        run(self.s, tp + win + passing + 0.5)
        self.s.action_down()
        self.assertEqual(self.s.hands[0].kind, "queimado")
        focus(self.s, COZINHA, LIXEIRA)
        self.s.action_down()
        self.assertEqual(self.s.hands, [])
        self.assertEqual(self.casa.dirt["lixo"], 1)


class VirarTest(unittest.TestCase):
    def test_misto_virado_fica_perfeito(self):
        s, ui, _, _, _ = new_service()
        bench(s, "ing:pao", "ing:presunto", "ing:queijo")
        focus(s, COZINHA, CHAPA)
        s.action_down()
        tp = C.COOK["misto_montado"][0]
        run(s, tp * C.TURN_WINDOW[0] + 0.2)
        self.assertIn("aviso_virar", ui.played)
        s.action_down()
        self.assertIn("Virou", ui.last())
        run(s, tp)
        s.action_down()
        self.assertEqual(s.hands[0].kind, "misto")
        self.assertEqual(s.hands[0].quality, 1.0)

    def test_misto_sem_virar_perde_qualidade(self):
        s, _, _, _, _ = new_service()
        bench(s, "ing:pao", "ing:presunto", "ing:queijo")
        focus(s, COZINHA, CHAPA)
        s.action_down()
        run(s, C.COOK["misto_montado"][0] + 0.2)
        s.action_down()
        self.assertAlmostEqual(s.hands[0].quality, C.MISSED_TURN_QUALITY)

    def test_batata_sacudida_e_salgada(self):
        s, _, _, _, _ = new_service()
        bench(s, "ing:batata")
        focus(s, COZINHA, FRITADEIRA)
        s.action_down()
        tp = C.COOK["batata_crua"][0]
        run(s, tp * 0.5)
        s.action_down()                 # sacode
        run(s, tp * 0.5 + 0.2)
        s.action_down()                 # tira
        self.assertEqual(s.hands[0].kind, "fritas_sem_sal")
        self.assertTrue(bench(s, "mao:0", "ing:sal"))
        self.assertEqual(s.hands[0].kind, "fritas")
        self.assertEqual(s.hands[0].quality, 1.0)


class LiquidificadorTest(unittest.TestCase):
    def setUp(self):
        self.s, self.ui, _, _, _ = new_service()
        bench(self.s, "ing:laranja")
        focus(self.s, COZINHA, LIQUIDIFICADOR)
        self.s.action_down()            # põe as laranjas

    def hold(self, seconds):
        self.s.action_down()
        run(self.s, seconds)
        self.s.action_up()

    def test_bater_no_tempo(self):
        self.hold(C.BLEND_MIN + 0.5)
        self.assertEqual(self.s.hands[0].kind, "suco")
        self.assertEqual(self.s.hands[0].quality, 1.0)

    def test_soltar_cedo_pode_continuar(self):
        self.hold(1.0)
        self.assertIn("pedaço", self.ui.last())
        self.hold(C.BLEND_MIN)
        self.assertEqual(self.s.hands[0].kind, "suco")

    def test_bater_demais_esquenta(self):
        self.hold(C.BLEND_MAX + 1)
        self.assertEqual(self.s.hands[0].quality, C.WARM_JUICE_QUALITY)


if __name__ == "__main__":
    unittest.main()
