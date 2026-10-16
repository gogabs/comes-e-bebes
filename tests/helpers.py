import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from comes.casa import Casa  # noqa: E402
from comes.expediente import Service  # noqa: E402


class FakeUI:
    def __init__(self):
        self.said, self.played, self.loops, self.bench_opened = [], [], {}, 0

    def say(self, text, queue=False):
        self.said.append(text)

    def play(self, name, spot=None, pitch=1.0, volume=1.0):
        self.played.append(name)

    def loop(self, key, name, spot=None, pitch=1.0, volume=1.0):
        self.loops[key] = (name, pitch)

    def stop(self, key):
        self.loops.pop(key, None)

    def open_bancada(self):
        self.bench_opened += 1

    def last(self):
        return self.said[-1] if self.said else ""


def new_service(seed=1, casa=None, **kw):
    ui = FakeUI()
    casa = casa or Casa()
    done = []
    closed = []
    s = Service(casa, ui, rng=random.Random(seed), on_done=done.append,
                on_closed=lambda: closed.append(True), **kw)
    s.next_arrival = 1e9          # clientes só quando o teste quiser
    return s, ui, casa, done, closed


def run(service, seconds, step=0.1):
    t = 0.0
    while t < seconds:
        service.update(step)
        t += step


def focus(service, layer, index):
    service.layer = layer
    service.index[layer] = index


def bench(service, *keys):
    """Monta na bancada: chaves "ing:pao" ou "mao:0"."""
    service.bench = []
    for k in keys:
        service.bench_add(k)
    return service.bench_done()
