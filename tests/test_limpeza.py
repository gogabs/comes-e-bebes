import unittest

from helpers import FakeUI, run

from comes import config as C
from comes.casa import Casa
from comes.limpeza import COZINHA, SALAO, Cleaning


def new_cleaning():
    casa = Casa()
    ui = FakeUI()
    done = []
    c = Cleaning(casa, ui, on_done=lambda: done.append(True))
    return c, ui, casa, done


class LimpezaTest(unittest.TestCase):
    def test_lavar_louca(self):
        c, ui, casa, _ = new_cleaning()
        casa.dirt["louca"] = 2
        c.action_down()
        c.action_down()                  # cedo demais: ignora
        self.assertEqual(casa.dirt["louca"], 1)
        run(c, C.WASH_TIME + 0.1)
        c.action_down()
        self.assertEqual(casa.dirt["louca"], 0)
        self.assertIn("Última louça", ui.last())

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

    def test_raspar_chapa(self):
        c, ui, casa, _ = new_cleaning()
        casa.dirt["chapa"] = 2
        c.index[COZINHA] = 1
        c.action_down()
        self.assertIn("raspar", ui.loops)
        run(c, C.SCRAPE_TIME * 2 + 0.2)
        self.assertEqual(casa.dirt["chapa"], 0)
        self.assertNotIn("raspar", ui.loops)

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
