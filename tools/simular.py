#!/usr/bin/env python3
"""Joga dias inteiros com um jogador automático, para conferir o equilíbrio.

O jogador faz uma ação a cada `--ritmo` segundos (um humano faz bem menos que um
robô) e sempre faz a coisa mais urgente. Limpa tudo no fim do dia e compra o
que acabou. Mostra o dinheiro, a reputação e quantos clientes foram embora.

    python3 tools/simular.py --dias 7 --ritmo 1.5 --velocidade Normal
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from comes import config as C  # noqa: E402
from comes import data as D  # noqa: E402
from comes.casa import Casa  # noqa: E402
from comes.expediente import COZINHA, SALAO, STATIONS, Service  # noqa: E402


class Quiet:
    def say(self, *a, **k): pass
    def play(self, *a, **k): pass
    def loop(self, *a, **k): pass
    def stop(self, *a, **k): pass
    def open_bancada(self): pass


def at(s, layer, index):
    s.layer = layer
    s.index[layer] = index


def station(s, name):
    at(s, COZINHA, STATIONS.index(name))


def kinds(s):
    return [i.kind for i in s.hands]


def make(s, parts):
    s.bench = list(parts)
    return s.bench_done()


def pending(s):
    """Pratos pedidos que ainda não estão em preparo nem na mão."""
    want = []
    for t in s.tables:
        if t.state == "esperando":
            want.extend(t.order)
    have = kinds(s)
    for st in s.cookers.values():
        have += [D.COOKED[c.kind] for c in st.slots]
    if s.blender:
        have.append("suco")
    chain = {"hamburguer": "xburger", "hamburguer_cru": "xburger", "misto_montado": "misto",
             "fritas_sem_sal": "fritas", "batata_crua": "fritas", "laranja_cortada": "suco"}
    have = [chain.get(k, k) for k in have]
    for k in have:
        if k in want:
            want.remove(k)
    return want


def act(s):
    """Uma ação: a mais urgente."""
    free = len(s.hands) < C.HANDS
    for name, st in s.cookers.items():
        if st.fire:
            station(s, name)
            return s.action_down()
    for name, st in s.cookers.items():
        if any(c.stage >= 1 for c in st.slots) and free:
            station(s, name)
            return s.action_down()
        if any(c.turn_cued and not c.turned for c in st.slots):
            station(s, name)
            return s.action_down()
    for t in s.tables:
        if t.state == "pagar":
            at(s, SALAO, t.index)
            return s.action_down()
        if t.state == "esperando" and any(k in t.order for k in kinds(s)):
            at(s, SALAO, t.index)
            return s.action_down()
    if "queimado" in kinds(s):
        station(s, "lixeira")
        return s.action_down()
    if "louca" in kinds(s):
        station(s, "pia")
        return s.action_down()
    hand = kinds(s)
    if "hamburguer" in hand:
        return make(s, ["ing:pao", "mao:%d" % hand.index("hamburguer"), "ing:queijo"])
    if "fritas_sem_sal" in hand:
        return make(s, ["mao:%d" % hand.index("fritas_sem_sal"), "ing:sal"])
    for raw, name in (("hamburguer_cru", "chapa"), ("misto_montado", "chapa"),
                      ("batata_crua", "fritadeira")):
        st = s.cookers[name]
        if raw in hand and len(st.slots) < st.cap:
            station(s, name)
            return s.action_down()
    if s.blender == "suco" and free:
        station(s, "liquidificador")
        return s.action_down()
    if "laranja_cortada" in hand and s.blender is None:
        station(s, "liquidificador")
        return s.action_down()
    if s.blender == "laranja_cortada":
        station(s, "liquidificador")
        s.action_down()
        s.blend = 3.5             # segurou B o tempo certo
        return s.action_up()
    for t in s.tables:
        if t.state in ("pedir",):
            at(s, SALAO, t.index)
            return s.action_down()
    if free:
        for k in pending(s):
            parts = {"xburger": ["ing:carne"], "misto": ["ing:pao", "ing:presunto", "ing:queijo"],
                     "fritas": ["ing:batata"], "suco": ["ing:laranja"]}[k]
            if all(s.casa.count(p[4:]) > 0 for p in parts):
                return make(s, parts)
        for t in s.tables:
            if t.state == "suja":
                at(s, SALAO, t.index)
                return s.action_down()


def restock(casa):
    for k in D.INGREDIENT_ORDER:
        while casa.count(k) < D.INGREDIENTS[k][2] and casa.money > 40:
            casa.buy(k)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dias", type=int, default=7)
    p.add_argument("--ritmo", type=float, default=1.5, help="segundos entre ações")
    p.add_argument("--velocidade", default="Normal", choices=[n for n, _ in C.SPEEDS])
    p.add_argument("--semente", type=int, default=1)
    args = p.parse_args()
    rng = random.Random(args.semente)
    casa = Casa()
    for _ in range(args.dias):
        casa.start_day(rng)
        restock(casa)
        result = {}
        s = Service(casa, Quiet(), rng=rng, speed=dict(C.SPEEDS)[args.velocidade],
                    on_done=result.update)
        wait = 0.0
        while not s.finished and s.t < C.DAY_SECONDS * 3:
            s.update(0.1)
            wait -= 0.1
            if wait <= 0:
                act(s)
                wait = args.ritmo
        dirt = casa.total_dirt()
        if os.environ.get("DETALHE"):
            print({k: v for k, v in casa.dirt.items() if v})
        casa.dirt = {k: 0 for k in casa.dirt}
        casa.end_day(result, rng)
        print("%-22s clientes %2d  foram embora %d  fogo %d  vendas %4d  gorjetas %3d  "
              "dinheiro %4d  reputação %.1f  sujeira %d" % (
                  casa.short_date(), result.get("served", 0), result.get("left", 0),
                  result.get("fires", 0), result.get("sales", 0), result.get("tips", 0),
                  casa.money, casa.reputation, dirt))


if __name__ == "__main__":
    main()
