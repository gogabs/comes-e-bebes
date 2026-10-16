import json
import random
import unittest

from helpers import new_service, run

from comes import config as C
from comes.casa import Casa, stars


class CalendarioTest(unittest.TestCase):
    def test_comeca_no_verao(self):
        casa = Casa()
        lines = casa.start_day(random.Random(1))
        self.assertTrue(lines[0].startswith("Dia 1 do Verão, ano 1"))

    def test_estacao_vira_e_ano_vira(self):
        casa = Casa()
        casa.day = C.DAYS_PER_SEASON
        casa.end_day({})
        self.assertEqual((casa.day, casa.season), (1, 2))
        self.assertEqual(casa.checkpoint["season"], 2)
        casa.season, casa.day = 3, C.DAYS_PER_SEASON
        casa.end_day({})
        self.assertEqual((casa.day, casa.season, casa.year), (1, 0, 2))
        self.assertIn("da Primavera", casa.date_text())


class EstoqueTest(unittest.TestCase):
    def test_comprar_e_gastar_o_mais_velho(self):
        casa = Casa()
        casa.stock["pao"] = [[2, 1]]
        self.assertTrue(casa.buy("pao"))
        self.assertEqual(casa.count("pao"), 12)
        casa.take("pao", 3)
        self.assertEqual(sorted(casa.stock["pao"]), [[9, 3]])

    def test_sem_dinheiro(self):
        casa = Casa()
        casa.money = 1
        self.assertFalse(casa.buy("carne"))

    def test_estraga(self):
        casa = Casa()
        casa.stock["carne"] = [[4, 1], [6, 3]]
        casa.end_day({})
        lines = casa.start_day(random.Random(1))
        self.assertEqual(casa.count("carne"), 6)
        self.assertTrue(any("4 hambúrgueres" in l for l in lines))

    def test_precos(self):
        casa = Casa()
        casa.prices["xburger"] = 4
        self.assertEqual(casa.price("xburger"), 21)
        casa.prices["xburger"] = 0
        self.assertEqual(casa.price("xburger"), 8)


class HigieneTest(unittest.TestCase):
    def dirty_night(self, casa, rng):
        casa.start_day(rng)
        casa.dirt["louca"] = C.DIRT_DIRTY + 1
        casa.end_day({}, rng)

    def test_avisos_ate_a_carta(self):
        casa = Casa()
        rng = random.Random(2)
        self.dirty_night(casa, rng)
        self.dirty_night(casa, rng)
        lines = casa.start_day(rng)
        self.assertTrue(any("mosca" in l for l in lines))
        casa.end_day({}, rng)
        self.assertTrue(casa.letter)
        self.assertIsNotNone(casa.inspection_day)
        self.assertIn("vigilância", casa.report)

    def test_limpar_zera(self):
        casa = Casa()
        rng = random.Random(2)
        self.dirty_night(casa, rng)
        casa.dirt = {k: 0 for k in casa.dirt}
        casa.end_day({}, rng)
        self.assertEqual(casa.dirty_nights, 0)

    def test_visita_aprova_casa_limpa(self):
        casa = Casa()
        casa.inspection_day = casa.absolute_day
        casa.start_day(random.Random(1))
        s, ui, _, _, closed = new_service(casa=casa)
        run(s, C.DAY_SECONDS * C.INSPECTION_TIME[1] + 1, step=0.5)
        self.assertEqual(closed, [])
        self.assertIn("aprovou", " ".join(ui.said))
        self.assertIsNone(casa.inspection_day)

    def test_visita_interdita_e_volta_ao_dia_1(self):
        casa = Casa()
        start_money = casa.money
        rng = random.Random(1)
        for _ in range(3):
            casa.start_day(rng)
            casa.money += 50
            casa.end_day({}, rng)
        casa.dirt["lixo"] = C.DIRT_DIRTY + 5
        casa.inspection_day = casa.absolute_day
        casa.start_day(rng)
        s, _, _, _, closed = new_service(casa=casa)
        run(s, C.DAY_SECONDS * C.INSPECTION_TIME[1] + 1, step=0.5)
        self.assertEqual(closed, [True])
        self.assertTrue(s.over)
        casa.restore_checkpoint()
        self.assertEqual((casa.day, casa.money), (1, start_money))
        self.assertEqual(casa.total_dirt(), 0)
        self.assertIsNotNone(casa.checkpoint)


class SaveTest(unittest.TestCase):
    def test_ida_e_volta(self):
        casa = Casa()
        casa.money = 77
        casa.prices["suco"] = 1
        casa.dirt["mesa2"] = 3
        data = json.loads(json.dumps(casa.to_dict()))
        again = Casa.from_dict(data)
        self.assertEqual(again.money, 77)
        self.assertEqual(again.prices["suco"], 1)
        self.assertEqual(again.dirt["mesa2"], 3)
        self.assertEqual(again.checkpoint, casa.checkpoint)

    def test_versao_errada(self):
        with self.assertRaises(ValueError):
            Casa.from_dict({"versao": 99})


class EstrelasTest(unittest.TestCase):
    def test_falas(self):
        self.assertEqual(stars(2.5), "2 estrelas e meia")
        self.assertEqual(stars(1.0), "1 estrela")
        self.assertEqual(stars(0.4), "meia estrela")


if __name__ == "__main__":
    unittest.main()
