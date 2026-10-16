import random
import unittest

from helpers import bench, focus, new_service, run

from comes import config as C
from comes import data as D
from comes.casa import Casa
from comes.expediente import COZINHA, STATIONS, Item

OUTONO = 2


def outono(day=1):
    casa = Casa(season=OUTONO)
    casa.day = day
    lines = casa.start_day(random.Random(1))
    return casa, lines


class ChegadaTest(unittest.TestCase):
    def test_aprende_as_receitas_no_primeiro_dia(self):
        casa, lines = outono()
        self.assertIn("Chegou o outono", " ".join(lines))
        self.assertIn("pao_chapa", casa.active_menu())
        self.assertIn("suco_mexerica", casa.active_menu())

    def test_verao_vira_outono(self):
        casa = Casa()
        self.assertNotIn("pao_chapa", casa.known_recipes())
        casa.day = C.DAYS_PER_SEASON
        casa.end_day({})
        lines = casa.start_day(random.Random(1))
        self.assertEqual(casa.season, OUTONO)
        self.assertIn("pao_chapa", casa.known_recipes())
        self.assertTrue(any("mexerica" in l for l in lines))

    def test_receitas_ficam_depois_do_outono(self):
        casa, _ = outono()
        casa.day = C.DAYS_PER_SEASON
        casa.end_day({})
        casa.start_day(random.Random(1))
        self.assertIn("pao_chapa", casa.known_recipes())


class ComprasTest(unittest.TestCase):
    def test_mexerica_so_no_outono(self):
        verao = Casa()
        self.assertNotIn("mexerica", verao.shop_keys())
        self.assertFalse(verao.buy("mexerica"))
        casa, _ = outono()
        self.assertIn("mexerica", casa.shop_keys())
        self.assertTrue(casa.buy("mexerica"))
        self.assertIn("da estação", casa.stock_text("mexerica"))

    def test_ganha_os_ingredientes_novos(self):
        casa, lines = outono()
        self.assertGreater(casa.count("mexerica"), 0)
        self.assertGreater(casa.count("manteiga"), 0)
        self.assertIn("manteiga e um de mexerica", " ".join(lines))
        self.assertEqual(Casa().count("manteiga"), 0)

    def test_compras_so_do_que_se_usa(self):
        self.assertNotIn("manteiga", Casa().shop_keys())
        casa, _ = outono()
        self.assertIn("manteiga", casa.shop_keys())


class DiaDasMaesTest(unittest.TestCase):
    def test_data_especial(self):
        casa, lines = outono(day=12)
        self.assertIn("Dia das Mães", " ".join(lines))
        normal, _ = outono(day=11)
        normal.weather = casa.weather
        self.assertGreater(casa.arrival_factor(), normal.arrival_factor())

    def test_gorjeta_maior(self):
        tips = []
        for day in (11, 12):
            casa, _ = outono(day=day)
            s, _, _, _, _ = new_service(casa=casa)
            t = s.tables[0]
            s._seat(t)
            t.served = [("xburger", 1.0)]
            t.order = []
            t.state = "pagar"
            t.patience = t.patience_max = 100
            focus(s, 0, 0)
            s.action_down()
            tips.append(s.stats["tips"])
        self.assertGreater(tips[1], tips[0])


class ReceitasTest(unittest.TestCase):
    def test_pao_na_chapa(self):
        casa, _ = outono()
        s, ui, _, _, _ = new_service(casa=casa)
        self.assertTrue(bench(s, "ing:pao", "ing:manteiga"))
        self.assertEqual(s.hands[0].kind, "pao_manteiga")
        focus(s, COZINHA, STATIONS.index("chapa"))
        s.action_down()
        tp = C.COOK["pao_manteiga"][0]
        run(s, tp * C.TURN_WINDOW[0] + 0.2)
        s.action_down()
        self.assertIn("Virou o pão", ui.last())
        run(s, tp)
        s.action_down()
        self.assertEqual(s.hands[0].kind, "pao_chapa")
        self.assertEqual(s.hands[0].quality, 1.0)

    def test_suco_de_mexerica(self):
        casa, _ = outono()
        s, ui, _, _, _ = new_service(casa=casa)
        self.assertTrue(bench(s, "ing:mexerica"))
        focus(s, COZINHA, STATIONS.index("liquidificador"))
        s.action_down()
        self.assertIn("Mexericas no liquidificador", ui.last())
        self.assertEqual(s.describe(COZINHA, STATIONS.index("liquidificador")), "com mexericas")
        s.action_down()
        run(s, C.BLEND_MIN + 0.5)
        s.action_up()
        self.assertEqual(s.hands[0].kind, "suco_mexerica")
        self.assertIn("Suco de mexerica pronto", ui.last())

    def test_pedidos_do_outono(self):
        casa, _ = outono()
        s, _, _, _, _ = new_service(casa=casa, seed=4)
        orders = []
        for _ in range(200):
            orders.extend(s._choose_order())
        self.assertGreater(orders.count("pao_chapa"), orders.count("suco"))
        self.assertIn("suco_mexerica", orders)

    def test_som_de_fundo(self):
        casa, _ = outono()
        s, ui, _, _, _ = new_service(casa=casa)
        s.start()
        self.assertEqual(ui.loops["ambiente"][0], "outono")
        verao, _, _, _, _ = new_service()
        verao.start()
        self.assertNotIn("ambiente", verao.ui.loops)

    def test_falas_do_pedido(self):
        self.assertEqual(D.order_text(["pao_chapa", "pao_chapa", "suco_mexerica"]),
                         "dois pães na chapa e um suco de mexerica")


class SaveAntigoTest(unittest.TestCase):
    def test_save_da_versao_anterior(self):
        data = Casa().to_dict()
        for key in ("pao_chapa", "suco_mexerica"):
            data["menu"].pop(key)
            data["prices"].pop(key)
        data["stock"].pop("mexerica")
        data["stock"].pop("manteiga")
        data.pop("learned")
        data["menu"]["fritas"] = False
        casa = Casa.from_dict(data)
        self.assertEqual(casa.known_recipes(), list(D.BASE_RECIPES))
        self.assertNotIn("fritas", casa.active_menu())
        self.assertEqual(casa.count("manteiga"), 0)
        self.assertEqual(casa.prices["pao_chapa"], C.DEFAULT_TIER)


if __name__ == "__main__":
    unittest.main()
