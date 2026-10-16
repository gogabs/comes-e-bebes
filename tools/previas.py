#!/usr/bin/env python3
"""Gera prévias das telas em docs/telas/, sem console e sem SDL (com a Pillow).

    python3 tools/previas.py
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from comes import tela as T  # noqa: E402
from comes.casa import Casa  # noqa: E402
from comes.expediente import COZINHA, SALAO, Item, Service  # noqa: E402
from comes.limpeza import Cleaning  # noqa: E402


class Quiet:
    def say(self, *a, **k): pass
    def play(self, *a, **k): pass
    def loop(self, *a, **k): pass
    def stop(self, *a, **k): pass
    def open_bancada(self): pass


class Menu:
    def __init__(self, title, items, index=0):
        self.title, self.items, self.index = title, items, index


def busy_service(season=1, special_day=None):
    casa = Casa(season=season)
    casa.money = 420
    casa.reputation = 3.5
    casa.buy_equipment("cafeteira")
    if special_day:
        casa.day = special_day
    casa.start_day(random.Random(3))
    s = Service(casa, Quiet(), rng=random.Random(5))
    s.next_arrival = 1e9
    t0, t1, t2 = s.tables
    s._seat(t0)
    s._wait(t0, "esperando", 110)
    t0.patience = 70
    s._seat(t1)
    s._wait(t1, "pedir", 60)
    t1.patience = 12
    s._seat(t2)
    t2.served = [(t2.order[0], 1.0)]
    t2.state = "comendo"
    s.hands = [Item("hamburguer_cru"), Item("suco")]
    s.bench = []
    s.cookers["chapa"].slots = []
    s.bench = ["ing:pao", "ing:queijo"]
    from comes.expediente import Cooking
    a, b = Cooking("misto_montado"), Cooking("hamburguer_cru")
    a.t, b.t = 6.0, 15.0
    b.stage = 1
    s.cookers["chapa"].slots = [a, b]
    c = Cooking("pastel_cru")
    c.t, c.turn_cued = 5.0, True
    s.cookers["fritadeira"].slots = [c]
    s.blender, s.blending, s.blend = "laranja_cortada", True, 2.0
    s.coffee = "passando"
    s.t = 140
    s.layer, s.index[COZINHA] = COZINHA, 1
    return s


def frame(path, scene):
    from pilgfx import PilGfx
    gfx = PilGfx(ROOT)
    T.draw_frame(gfx, gfx.image(T.SHEET), T.Fonts(gfx), scene)
    gfx.save(os.path.join(ROOT, "docs", "telas", path))


def main():
    frame("titulo.png", T.Scene(menu=Menu("Comes e Bebes", ["Jogar", "Como jogar", "Sair"]),
                                caption="Comes e Bebes. Jogar."))
    s = busy_service()
    frame("expediente.png", T.Scene("expediente", s.casa, s, caption="Hora de virar o pastel. "
                                    "Mesa 2 quer pedir."))
    s = busy_service(season=3, special_day=3)
    s.cookers["fritadeira"].fire = True
    s.layer, s.index[SALAO] = SALAO, 1
    frame("inverno-sao-joao.png", T.Scene("expediente", s.casa, s, caption="Fogo na fritadeira! "
                                          "Aperte B nela para usar o extintor."))
    casa = Casa(season=0)
    casa.start_day(random.Random(1))
    frame("abertura.png", T.Scene("abertura", casa, menu=Menu(
        "Abertura", ["Abrir a casa", "Compras", "Cardápio", "Preços", "Lojinha",
                     "Velocidade: Normal", "Dinheiro e estoque", "Resumo de ontem",
                     "Salvar e sair"], 4), caption="Lojinha."))
    casa = Casa(season=2)
    casa.dirt.update({"mesa1": 2, "mesa3": 1, "chao_salao": 2, "chao_cozinha": 2, "chapa": 3,
                      "louca": 6, "lixo": 3})
    c = Cleaning(casa, Quiet(), rng=random.Random(1))
    c.action_down()
    c.spinner.angle = 0.8
    frame("limpeza.png", T.Scene("limpeza", casa, cleaning=c,
                                 caption="Lavando. Prato de fritura na mão. Faltam 6 na pia."))
    print("prévias em docs/telas")


if __name__ == "__main__":
    main()
