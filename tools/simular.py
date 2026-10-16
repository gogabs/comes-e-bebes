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
from comes.expediente import COZINHA, SALAO, Service  # noqa: E402


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
    at(s, COZINHA, s.layout[COZINHA].index(name))


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
    if s.coffee:
        have.append("cafezinho")
    if s.blender:
        have.append(D.BLENDS[s.blender][0] if s.blender in D.BLENDS else s.blender)
    chain = {"hamburguer": "xburger", "hamburguer_cru": "xburger", "misto_montado": "misto",
             "fritas_sem_sal": "fritas", "batata_crua": "fritas", "laranja_cortada": "suco",
             "mexerica_descascada": "suco_mexerica", "pao_manteiga": "pao_chapa",
             "queijo_montado": "queijo_quente", "leite_chocolate": "chocolate_quente",
             "morango_leite": "vitamina_morango", "pastel_cru": "pastel",
             "coxinha_crua": "coxinha"}
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
                      ("pao_manteiga", "chapa"), ("queijo_montado", "chapa"),
                      ("batata_crua", "fritadeira"), ("pastel_cru", "fritadeira"),
                      ("coxinha_crua", "fritadeira")):
        st = s.cookers[name]
        if raw in hand and len(st.slots) < st.cap:
            station(s, name)
            return s.action_down()
    if s.coffee == "pronto" and free:
        station(s, "cafeteira")
        return s.action_down()
    if s.coffee == "graos":
        station(s, "cafeteira")
        s.action_down()
        s.grind = 3.0             # segurou B o tempo certo
        return s.action_up()
    if s.blender and s.blender not in D.BLENDS and free:
        station(s, "liquidificador")
        return s.action_down()
    if any(k in D.BLENDS for k in hand) and s.blender is None:
        station(s, "liquidificador")
        return s.action_down()
    if s.blender in D.BLENDS:
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
            if k == "cafezinho":
                if s.coffee is None and s.casa.count("cafe"):
                    station(s, "cafeteira")
                    return s.action_down()
                continue
            parts = {"xburger": ["ing:carne"], "misto": ["ing:pao", "ing:presunto", "ing:queijo"],
                     "fritas": ["ing:batata"], "suco": ["ing:laranja"],
                     "pao_chapa": ["ing:pao", "ing:manteiga"],
                     "suco_mexerica": ["ing:mexerica"],
                     "queijo_quente": ["ing:pao", "ing:queijo"],
                     "chocolate_quente": ["ing:leite", "ing:chocolate"],
                     "sanduiche_natural": ["ing:pao", "ing:frango", "ing:alface"],
                     "vitamina_morango": ["ing:morango", "ing:leite"],
                     "pastel": ["ing:massa", "ing:queijo"],
                     "coxinha": ["ing:coxinha"]}[k]
            if all(s.casa.count(p[4:]) > 0 for p in parts):
                return make(s, parts)
        for t in s.tables:
            if t.state == "suja":
                at(s, SALAO, t.index)
                return s.action_down()


def restock(casa):
    for k in D.EQUIPMENT_ORDER:
        if k not in casa.equipment and casa.money >= D.EQUIPMENT[k][1] + 150:
            casa.buy_equipment(k)
    for k in casa.shop_keys():
        while casa.count(k) < D.INGREDIENTS[k][2] and casa.money > 40:
            casa.buy(k)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dias", type=int, default=7)
    p.add_argument("--ritmo", type=float, default=1.5, help="segundos entre ações")
    p.add_argument("--velocidade", default="Normal", choices=[n for n, _ in C.SPEEDS])
    p.add_argument("--semente", type=int, default=1)
    p.add_argument("--estacao", default="Verão", choices=list(D.SEASONS))
    args = p.parse_args()
    rng = random.Random(args.semente)
    casa = Casa(season=D.SEASONS.index(args.estacao))
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
