import random
import unittest

from helpers import bench, focus, new_service, run

from comes import config as C
from comes import data as D
from comes.casa import Casa
from comes.expediente import COZINHA, STATIONS

PRIMAVERA, OUTONO, INVERNO = 0, 2, 3


def estacao(season, day=1):
    casa = Casa(season=season)
    casa.day = day
    lines = casa.start_day(random.Random(1))
    return casa, lines


def blend(s, ui, *parts, seconds=C.BLEND_MIN + 0.5):
    assert bench(s, *parts)
    focus(s, COZINHA, STATIONS.index("liquidificador"))
    s.action_down()
    s.action_down()
    run(s, seconds)
    s.action_up()


class InvernoTest(unittest.TestCase):
    def test_outono_vira_inverno(self):
        casa, _ = estacao(OUTONO)
        casa.day = C.DAYS_PER_SEASON
        casa.end_day({})
        lines = " ".join(casa.start_day(random.Random(1)))
        self.assertEqual(casa.season, INVERNO)
        self.assertIn("Chegou o inverno", lines)
        self.assertIn("pao_chapa", casa.known_recipes())
        self.assertIn("queijo_quente", casa.active_menu())
        self.assertIn("chocolate_quente", casa.active_menu())
        self.assertIn("um pacote de leite e um de chocolate", lines)

    def test_queijo_quente(self):
        casa, _ = estacao(INVERNO)
        s, ui, _, _, _ = new_service(casa=casa)
        self.assertTrue(bench(s, "ing:pao", "ing:queijo"))
        self.assertEqual(s.hands[0].kind, "queijo_montado")
        focus(s, COZINHA, STATIONS.index("chapa"))
        s.action_down()
        tp = C.COOK["queijo_montado"][0]
        run(s, tp * C.TURN_WINDOW[0] + 0.2)
        s.action_down()
        self.assertIn("Virou o queijo quente", ui.last())
        run(s, tp)
        s.action_down()
        self.assertEqual(s.hands[0].kind, "queijo_quente")
        self.assertEqual(s.hands[0].quality, 1.0)

    def test_chocolate_quente(self):
        casa, _ = estacao(INVERNO)
        s, ui, _, _, _ = new_service(casa=casa)
        blend(s, ui, "ing:leite", "ing:chocolate")
        self.assertEqual(s.hands[0].kind, "chocolate_quente")
        self.assertIn("Chocolate quente pronto", ui.last())

    def test_chocolate_batido_demais_espuma(self):
        casa, _ = estacao(INVERNO)
        s, ui, _, _, _ = new_service(casa=casa)
        blend(s, ui, "ing:leite", "ing:chocolate", seconds=C.BLEND_MAX + 0.5)
        self.assertIn("espumou demais", ui.last())

    def test_sao_joao(self):
        casa, lines = estacao(INVERNO, day=3)
        self.assertIn("São João", " ".join(lines))
        normal, _ = estacao(INVERNO, day=4)
        normal.weather = casa.weather
        self.assertGreater(casa.arrival_factor(), normal.arrival_factor())

    def test_pedidos_do_inverno(self):
        casa, _ = estacao(INVERNO)
        s, _, _, _, _ = new_service(casa=casa, seed=4)
        orders = []
        for _ in range(200):
            orders.extend(s._choose_order())
        self.assertGreater(orders.count("chocolate_quente"), orders.count("suco"))
        self.assertIn("queijo_quente", orders)

    def test_som_de_fundo(self):
        casa, _ = estacao(INVERNO)
        s, ui, _, _, _ = new_service(casa=casa)
        s.start()
        self.assertEqual(ui.loops["ambiente"][0], "inverno")


class PrimaveraTest(unittest.TestCase):
    def test_inverno_vira_primavera_do_ano_seguinte(self):
        casa, _ = estacao(INVERNO)
        casa.day = C.DAYS_PER_SEASON
        casa.end_day({})
        lines = " ".join(casa.start_day(random.Random(1)))
        self.assertEqual((casa.season, casa.year), (PRIMAVERA, 2))
        self.assertIn("Chegou a primavera", lines)
        self.assertIn("sanduiche_natural", casa.active_menu())
        self.assertIn("vitamina_morango", casa.active_menu())
        self.assertIn("queijo_quente", casa.known_recipes())
        # o leite sobrou do inverno ou foi comprado: só ganha o que falta
        self.assertIn("frango desfiado", lines)

    def test_presentes_de_quem_comeca_na_primavera(self):
        casa, lines = estacao(PRIMAVERA)
        self.assertIn("um pacote de frango desfiado, um de alface, um de morango e um de leite",
                      " ".join(lines))

    def test_morango_so_na_primavera(self):
        self.assertFalse(Casa(season=INVERNO).can_buy("morango"))
        casa, _ = estacao(PRIMAVERA)
        self.assertIn("morango", casa.shop_keys())
        self.assertIn("da estação", casa.stock_text("morango"))

    def test_sanduiche_natural_sai_da_bancada(self):
        casa, _ = estacao(PRIMAVERA)
        s, _, _, _, _ = new_service(casa=casa)
        self.assertTrue(bench(s, "ing:pao", "ing:frango", "ing:alface"))
        self.assertEqual(s.hands[0].kind, "sanduiche_natural")

    def test_vitamina_de_morango(self):
        casa, _ = estacao(PRIMAVERA)
        s, ui, _, _, _ = new_service(casa=casa)
        blend(s, ui, "ing:morango", "ing:leite")
        self.assertEqual(s.hands[0].kind, "vitamina_morango")
        self.assertIn("Vitamina de morango pronta", ui.last())

    def test_dia_das_criancas(self):
        casa, lines = estacao(PRIMAVERA, day=21)
        self.assertIn("Dia das Crianças", " ".join(lines))

    def test_pedidos_da_primavera(self):
        casa, _ = estacao(PRIMAVERA)
        s, _, _, _, _ = new_service(casa=casa, seed=4)
        orders = []
        for _ in range(200):
            orders.extend(s._choose_order())
        self.assertGreater(orders.count("sanduiche_natural"), orders.count("misto"))
        self.assertIn("vitamina_morango", orders)

    def test_som_de_fundo(self):
        casa, _ = estacao(PRIMAVERA)
        s, ui, _, _, _ = new_service(casa=casa)
        s.start()
        self.assertEqual(ui.loops["ambiente"][0], "primavera")

    def test_falas_do_pedido(self):
        self.assertEqual(D.order_text(["vitamina_morango", "vitamina_morango",
                                       "sanduiche_natural"]),
                         "duas vitaminas de morango e um sanduíche natural")


if __name__ == "__main__":
    unittest.main()
