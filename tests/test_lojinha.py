import random
import unittest

from helpers import bench, focus, new_service, run

from comes import config as C
from comes import data as D
from comes.casa import Casa
from comes.expediente import COZINHA, STATIONS


def com_cafeteira():
    casa = Casa()
    casa.money = 1000
    casa.buy_equipment("cafeteira")
    return casa


class FritadeiraTest(unittest.TestCase):
    def test_pastel_vira_na_fritadeira(self):
        s, ui, _, _, _ = new_service()
        self.assertTrue(bench(s, "ing:massa", "ing:queijo"))
        self.assertEqual(s.hands[0].kind, "pastel_cru")
        focus(s, COZINHA, STATIONS.index("fritadeira"))
        s.action_down()
        tp = C.COOK["pastel_cru"][0]
        run(s, tp * C.TURN_WINDOW[0] + 0.2)
        self.assertIn("Hora de virar o pastel", " ".join(ui.said))
        s.action_down()
        self.assertIn("Virou o pastel", ui.last())
        run(s, tp)
        s.action_down()
        self.assertEqual(s.hands[0].kind, "pastel")
        self.assertEqual(s.hands[0].quality, 1.0)

    def test_coxinha_e_batata_juntas(self):
        s, ui, _, _, _ = new_service()
        bench(s, "ing:coxinha")
        bench(s, "ing:batata")
        focus(s, COZINHA, STATIONS.index("fritadeira"))
        s.action_down()
        s.action_down()
        self.assertEqual(len(s.cookers["fritadeira"].slots), 2)
        self.assertIn("Coxinha na fritadeira", " ".join(ui.said))
        run(s, C.COOK["coxinha_crua"][0] + 0.2)
        self.assertIn("Coxinha no ponto", " ".join(ui.said))

    def test_jogo_novo_ja_sabe(self):
        casa = Casa()
        self.assertIn("pastel", casa.active_menu())
        self.assertIn("coxinha", casa.active_menu())
        self.assertGreater(casa.count("massa"), 0)

    def test_falas_do_pedido(self):
        self.assertEqual(D.order_text(["coxinha", "coxinha", "pastel"]),
                         "duas coxinhas e um pastel de queijo")

    def test_save_antigo_ganha_pastel_e_coxinha(self):
        data = Casa().to_dict()
        for key in ("pastel", "coxinha", "cafezinho"):
            data["menu"].pop(key)
            data["prices"].pop(key)
            data["learned"].remove(key) if key in data["learned"] else None
        data.pop("equipment")
        casa = Casa.from_dict(data)
        self.assertIn("pastel", casa.active_menu())
        self.assertIn("coxinha", casa.active_menu())
        self.assertNotIn("cafezinho", casa.known_recipes())
        self.assertEqual(casa.equipment, [])


class LojinhaTest(unittest.TestCase):
    def test_comprar_cafeteira(self):
        casa = Casa()
        casa.money = 100
        self.assertIsNone(casa.buy_equipment("cafeteira"))
        casa.money = 1000
        text = casa.buy_equipment("cafeteira")
        self.assertIn("Cafezinho entrou no cardápio", text)
        self.assertEqual(casa.money, 1000 - D.EQUIPMENT["cafeteira"][1])
        self.assertIn("cafezinho", casa.active_menu())
        self.assertGreater(casa.count("cafe"), 0)
        self.assertIsNone(casa.buy_equipment("cafeteira"))   # não compra duas
        self.assertEqual(Casa.from_dict(casa.to_dict()).equipment, ["cafeteira"])

    def test_sem_cafeteira_a_cozinha_nao_muda(self):
        s, _, _, _, _ = new_service()
        self.assertEqual(s.layout[COZINHA], list(STATIONS))
        self.assertNotIn("cafezinho", s.casa.known_recipes())

    def test_cafeteira_no_fim_da_cozinha(self):
        s, _, _, _, _ = new_service(casa=com_cafeteira())
        self.assertEqual(s.layout[COZINHA][-1], "cafeteira")
        focus(s, COZINHA, len(STATIONS) - 1)
        s.step(1)
        self.assertEqual(s.spot_name(COZINHA, s.index[COZINHA]), "Cafeteira")

    def test_cafezinho(self):
        s, ui, casa, _, _ = new_service(casa=com_cafeteira())
        focus(s, COZINHA, s.layout[COZINHA].index("cafeteira"))
        before = casa.count("cafe")
        s.action_down()
        self.assertEqual(casa.count("cafe"), before - 1)
        s.action_down()
        self.assertIn("moedor", ui.loops)
        run(s, 1.0)
        s.action_up()
        self.assertIn("grosso", ui.last())
        s.action_down()
        run(s, C.GRIND_MIN)
        s.action_up()
        self.assertEqual(s.coffee, "passando")
        self.assertEqual(ui.loops["cafeteira"][0], "cafe_passando")
        run(s, C.COFFEE_BREW + 0.2)
        self.assertEqual(s.coffee, "pronto")
        self.assertTrue(s._needs_you(COZINHA, s.index[COZINHA]))
        s.action_down()
        self.assertEqual(s.hands[0].kind, "cafezinho")
        self.assertEqual(s.hands[0].quality, 1.0)

    def test_moer_demais_amarga_e_esperar_esfria(self):
        s, ui, _, _, _ = new_service(casa=com_cafeteira())
        focus(s, COZINHA, s.layout[COZINHA].index("cafeteira"))
        s.action_down()
        s.action_down()
        run(s, C.GRIND_MAX + 0.5)
        s.action_up()
        run(s, C.COFFEE_BREW + C.COFFEE_COOL + 1)
        self.assertIn("esfriando", " ".join(ui.said))
        s.action_down()
        self.assertLess(s.hands[0].quality, 1.0)

    def test_inverno_pede_cafezinho(self):
        casa = com_cafeteira()
        casa.season = 3
        casa.start_day(random.Random(1))
        s, _, _, _, _ = new_service(casa=casa, seed=4)
        orders = []
        for _ in range(200):
            orders.extend(s._choose_order())
        self.assertGreater(orders.count("cafezinho"), orders.count("suco"))


if __name__ == "__main__":
    unittest.main()
