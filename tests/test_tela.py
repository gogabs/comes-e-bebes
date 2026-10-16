"""A tela, com gráficos de mentira: cada cena desenha sem erro, os recortes da
folha de ícones cabem no PNG, e a tela nunca derruba o jogo."""
import math
import os
import random
import sys
import unittest

from fakegfx import RecordingGfx, png_size
from helpers import FakeUI, new_service, run

from comes import data as D
from comes import tela as T
from comes.casa import Casa
from comes.expediente import COZINHA, SALAO, Cooking, Item
from comes.limpeza import Cleaning

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class Menu:
    def __init__(self, title, items, index=0):
        self.title, self.items, self.index = title, items, index


def frame(scene):
    gfx = RecordingGfx(ROOT)
    T.draw_frame(gfx, gfx.image(T.SHEET), T.Fonts(gfx), scene)
    return gfx


def busy(season=1):
    casa = Casa(season=season)
    casa.money = 1000
    casa.buy_equipment("cafeteira")
    casa.start_day(random.Random(1))
    s, ui, _, _, _ = new_service(casa=casa, seed=3)
    for t in s.tables:
        s._seat(t)
    s._wait(s.tables[0], "esperando", 100)
    s._wait(s.tables[1], "pagar", 40)
    s.tables[1].served = [("suco", 1.0)]
    s.hands = [Item("pastel_cru"), Item("louca", count=2)]
    a = Cooking("misto_montado")
    a.stage = 2
    s.cookers["chapa"].slots = [a, Cooking("queijo_montado")]
    s.cookers["fritadeira"].fire = True
    s.blender, s.blending, s.blend = "morango_leite", True, 1.0
    s.coffee, s.grinding = "graos", True
    s.bench = ["ing:pao", "ing:frango", "mao:0"]
    return s


class TelaTest(unittest.TestCase):
    def test_folha_tem_todos_os_icones(self):
        w, h = png_size(os.path.join(ROOT, T.SHEET))
        self.assertEqual((w, h), (T.ICON_SIZE * len(T.ICONS), T.ICON_SIZE))

    def test_toda_coisa_do_jogo_tem_desenho(self):
        kinds = set(D.ITEM_NAMES) | set(D.RECIPES) | set(D.INGREDIENTS)
        for kind in kinds:
            ok = (kind in T.ICONS or kind in T.RAW or kind in T.INGREDIENT_ICONS
                  or kind in T.INGREDIENT_COLORS)
            self.assertTrue(ok, kind)

    def test_titulo(self):
        gfx = frame(T.Scene(menu=Menu("Comes e Bebes", ["Jogar", "Sair"]), caption="Jogar."))
        self.assertIn("Comes e Bebes", gfx.texts())
        self.assertIn("Jogar.", gfx.texts())

    def test_expediente_em_todas_as_estacoes(self):
        for season in range(4):
            s = busy(season)
            for layer, n in ((SALAO, 3), (COZINHA, len(s.layout[COZINHA]))):
                for i in range(n):
                    s.layer, s.index[layer] = layer, i
                    gfx = frame(T.Scene("expediente", s.casa, s, caption="x", t=i * 0.7))
                    self.assertIn("Cafeteira", gfx.texts())
            self.assertIn(s.casa.date_text(), gfx.texts())

    def test_expediente_andando(self):
        s, ui, casa, _, _ = new_service(seed=2)
        s.next_arrival = 1.0
        for step in range(120):
            run(s, 2.0)
            frame(T.Scene("expediente", casa, s, t=step))

    def test_menu_por_cima(self):
        s = busy()
        menu = Menu("Pausa", ["Continuar", "Velocidade: Normal", "Sair para o menu"], 1)
        gfx = frame(T.Scene("expediente", s.casa, s, menu=menu))
        self.assertIn("Pausa", gfx.texts())

    def test_menu_comprido_cabe(self):
        casa = Casa()
        items = ["Item %d com um texto bem comprido que não cabe na linha do menu" % k
                 for k in range(30)]
        gfx = frame(T.Scene("abertura", casa, menu=Menu("Compras", items, 17)))
        shown = [t for t in gfx.texts() if t.startswith("Item")]
        self.assertTrue(any(t.startswith("Item 17") for t in shown))
        self.assertLess(len(shown), 15)

    def test_limpeza(self):
        casa = Casa(season=3)
        for k in casa.dirt:
            casa.dirt[k] = 3
        c = Cleaning(casa, FakeUI(), rng=random.Random(1))
        for layer in (0, 1):
            for i in range(len(c.layout[layer])):
                c.layer, c.index[layer] = layer, i
                frame(T.Scene("limpeza", casa, cleaning=c))
        c.layer, c.index[1] = 1, 3
        c.action_down()
        for a in range(0, 360, 45):
            c.stick("lx", math.cos(math.radians(a)))
            frame(T.Scene("limpeza", casa, cleaning=c, caption="Lavando."))
        self.assertEqual(c.spinning, "lavar")

    def test_legenda_mostra_o_fim(self):
        long = " ".join("palavra%d" % k for k in range(80))
        gfx = frame(T.Scene("abertura", Casa(), caption=long))
        caption = [t for t in gfx.texts() if "palavra" in t]
        self.assertLessEqual(len(caption), 2)
        self.assertTrue(caption[-1].endswith("palavra79"))


class FakeGame:
    def __init__(self):
        self.dir = ROOT
        self.said = []
        self._focus = []
        self.updates = []

    def say(self, text, queue=False, on_done=None):
        self.said.append(text)

    def on_update(self, fn):
        self.updates.append(fn)

    def on_quit(self, fn):
        pass


class RendererTest(unittest.TestCase):
    def setUp(self):
        os.environ["A11Y_SISTEMA_CONF"] = os.path.join(ROOT, "nao-existe.conf")
        os.environ.pop("A11Y_GRAPHICS", None)

    def make(self, get_scene=None):
        game = FakeGame()
        made = []

        def graphics():
            g = RecordingGfx(ROOT)
            made.append(g)
            return g
        r = T.Renderer(game, get_scene or (lambda: T.Scene()), graphics=graphics)
        return game, r, made

    def test_legenda_e_quadros(self):
        game, r, made = self.make()
        game.say("Mesa 1 quer pedir.")
        game.say("Mesa 2 também.", queue=True)
        self.assertEqual(game.said, ["Mesa 1 quer pedir.", "Mesa 2 também."])
        for _ in range(10):
            game.updates[0](0.1)
        self.assertGreater(made[0].frames, 3)
        self.assertIn("Mesa 1 quer pedir. Mesa 2 também.", made[0].texts())

    def test_defeito_desliga_so_a_tela(self):
        def broken():
            raise RuntimeError("tela quebrada")
        game, r, made = self.make(broken)
        stderr = sys.stdout
        try:
            sys.stdout = open(os.devnull, "w")
            for _ in range(5):
                game.updates[0](0.1)
        finally:
            sys.stdout.close()
            sys.stdout = stderr
        self.assertTrue(r.failed)

    def test_tela_desligada_no_sistema(self):
        os.environ["A11Y_GRAPHICS"] = "0"
        game, r, made = self.make()
        for _ in range(5):
            game.updates[0](0.1)
        self.assertEqual(made, [])
        os.environ.pop("A11Y_GRAPHICS")


if __name__ == "__main__":
    unittest.main()
