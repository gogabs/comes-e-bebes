import math
import random
import unittest

from helpers import FakeUI, run

from comes import config as C
from comes.casa import Casa
from comes.limpeza import COZINHA, SALAO, Cleaning


def new_cleaning():
    casa = Casa()
    ui = FakeUI()
    done = []
    c = Cleaning(casa, ui, on_done=lambda: done.append(True), rng=random.Random(2))
    return c, ui, casa, done


class LimpezaTest(unittest.TestCase):
    def test_lavar_louca_girando_o_analogico(self):
        c, ui, casa, _ = new_cleaning()
        casa.dirt["louca"] = 2
        c.action_down()
        self.assertEqual(c.spinning, "lavar")
        self.assertIn("na mão", ui.last())
        turns = 0
        while casa.dirt["louca"] and turns < 20:
            for a in range(0, 360, 30):          # uma volta, de 30 em 30 graus
                c.stick("lx", math.cos(math.radians(a)))
                c.stick("ly", -math.sin(math.radians(a)))
            turns += 1
        self.assertEqual(casa.dirt["louca"], 0)
        self.assertIsNone(c.spinning)
        self.assertIn("última louça", ui.last())
        self.assertIn("esponja", ui.played)
        self.assertIn("prato_limpo", ui.played)

    def test_lavar_com_o_direcional(self):
        c, ui, casa, _ = new_cleaning()
        casa.dirt["louca"] = 1
        c.action_down()
        need = 4 * c.plate[1]
        c.go_layer(0)                            # cima
        for d in ("right", "down", "left", "up", "right", "down", "left", "up")[:need]:
            if d in ("up", "down"):
                c.go_layer(0 if d == "up" else 1)
            else:
                c.step(-1 if d == "left" else 1)
        self.assertEqual(casa.dirt["louca"], 0)

    def test_analogico_parado_no_centro_nao_conta(self):
        c, _, casa, _ = new_cleaning()
        casa.dirt["louca"] = 1
        c.action_down()
        for a in range(0, 720, 30):
            c.stick("lx", 0.2 * math.cos(math.radians(a)))
            c.stick("ly", 0.2 * math.sin(math.radians(a)))
        self.assertEqual(casa.dirt["louca"], 1)

    def test_a_para_de_lavar(self):
        c, ui, casa, _ = new_cleaning()
        casa.dirt["louca"] = 3
        c.action_down()
        c.back()
        self.assertIsNone(c.spinning)
        self.assertIn("Parou de lavar", ui.last())

    def test_esfregar_mesa(self):
        c, ui, casa, _ = new_cleaning()
        casa.dirt["mesa2"] = 1
        c.layer = SALAO
        c.index[SALAO] = 1
        c.action_down()
        self.assertIsNotNone(c.scrubbing)
        c.step(-1)
        c.step(-1)                       # mesmo lado não conta
        self.assertEqual(c.strokes, 1)
        for side in (1, -1, 1):
            c.step(side)
        self.assertEqual(casa.dirt["mesa2"], 0)
        self.assertIsNone(c.scrubbing)
        self.assertIn("limpinho", ui.last())

    def test_raspar_chapa_girando(self):
        c, ui, casa, _ = new_cleaning()
        casa.dirt["chapa"] = 2
        c.index[COZINHA] = 1
        c.action_down()
        self.assertEqual(c.spinning, "raspar")
        for _ in range(2 * C.SCRAPE_TURNS + 1):
            for a in range(0, 360, 30):
                c.stick("lx", math.cos(math.radians(a)))
                c.stick("ly", math.sin(math.radians(a)))
        self.assertEqual(casa.dirt["chapa"], 0)
        self.assertIsNone(c.spinning)
        self.assertIn("limpinha", ui.last())

    def test_lixo(self):
        c, _, casa, _ = new_cleaning()
        casa.dirt["lixo"] = 4
        c.index[COZINHA] = 4
        c.action_down()
        run(c, C.TRASH_TIME + 0.2)
        self.assertEqual(casa.dirt["lixo"], 0)

    def test_sons_de_ambiente_e_pulo(self):
        c, ui, casa, _ = new_cleaning()
        casa.dirt["mesa1"] = 1
        run(c, C.AMBIENT_EVERY + 0.1)
        self.assertIn("mosca", ui.played)
        c.jump(1)
        self.assertEqual((c.layer, c.index[SALAO]), (SALAO, 0))

    def test_ir_para_casa(self):
        c, _, _, done = new_cleaning()
        c.go_home()
        self.assertEqual(done, [True])

    def test_falta_limpar(self):
        c, _, casa, _ = new_cleaning()
        self.assertIn("tudo limpo", c.left_text())
        casa.dirt["louca"] = 3
        self.assertIn("Pia: 3 pratos", c.left_text())


if __name__ == "__main__":
    unittest.main()
