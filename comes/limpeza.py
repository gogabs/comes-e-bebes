"""A limpeza depois de fechar: cada sujeira tem seu lugar, seu som e seu jeito.

Mesmo `ui` do expediente (say, play, loop, stop). O tempo anda por update(dt).
"""
import random

from . import config as C
from .expediente import join
from .giro import Spinner

SALAO, COZINHA = 0, 1
# (chave da sujeira, nome falado, jeito de limpar, som de ambiente)
SPOTS = (
    (("mesa1", "Mesa 1", "esfregar", "mosca"),
     ("mesa2", "Mesa 2", "esfregar", "mosca"),
     ("mesa3", "Mesa 3", "esfregar", "mosca"),
     ("chao_salao", "Chão do salão", "esfregar", "passos_grudando")),
    (("chao_cozinha", "Chão da cozinha", "esfregar", "passos_grudando"),
     ("chapa", "Chapa", "raspar", "gordura"),
     ("fritadeira", "Fritadeira", "raspar", "gordura"),
     ("louca", "Pia", "lavar", "louca"),
     ("lixo", "Lixo", "levar", "lixo_cheio")),
)
HOW = {"esfregar": "Aperte B e esfregue com esquerda e direita.",
       "raspar": "Aperte B e gire o analógico, ou o direcional, em círculos.",
       "lavar": "Aperte B para pegar um prato e gire o analógico, ou o direcional, em "
                "círculos.",
       "levar": "Aperte B para levar o lixo para fora."}


def dirt_words(key, n):
    if key == "louca":
        return "%d %s" % (n, "prato" if n == 1 else "pratos")
    if key in ("chapa", "fritadeira"):
        return "gordura" if n < 3 else "muita gordura"
    if key == "lixo":
        return "lixo cheio" if n >= 3 else "lixo"
    return "sujo" if n < 3 else "muito sujo"


class Cleaning:
    def __init__(self, casa, ui, on_done=None, rng=None):
        self.casa = casa
        self.ui = ui
        self.rng = rng or random.Random()
        self.on_done = on_done
        self.layout = (list(SPOTS[0]), list(SPOTS[1]))
        self.layer = COZINHA
        self.index = [0, 3]          # começa na pia
        self.scrubbing = None        # (camada, índice) sendo esfregado
        self.last_side = None
        self.strokes = 0
        self.spinning = None         # "raspar" ou "lavar", na pia ou no fogo
        self.spinner = Spinner()
        self.quarters = 0
        self.plate = None            # (nome, voltas) do prato na mão
        self.busy = 0.0              # levando o lixo
        self.ambient_t = C.AMBIENT_EVERY
        self.ambient_next = 0
        self.paused = False
        self.done = False

    # --- utilidades ------------------------------------------------------
    def _spot(self, layer, index):
        return (layer, index, len(self.layout[layer]))

    def _here(self):
        return self.layout[self.layer][self.index[self.layer]]

    def _dirt(self, spot):
        return self.casa.dirt[spot[0]]

    def dirty_spots(self):
        return [(l, i) for l in (SALAO, COZINHA) for i, s in enumerate(self.layout[l])
                if self._dirt(s) > 0]

    def describe(self, layer, index):
        spot = self.layout[layer][index]
        n = self._dirt(spot)
        if n == 0:
            return "limpo" if spot[0] != "louca" else "pia vazia"
        return dirt_words(spot[0], n)

    def left_text(self):
        parts = ["%s: %s" % (s[1], dirt_words(s[0], self._dirt(s)))
                 for l in (SALAO, COZINHA) for s in self.layout[l] if self._dirt(s) > 0]
        if not parts:
            return "Está tudo limpo. Aperte Start e escolha Ir para casa."
        return "Falta limpar: %s." % join(parts)

    # --- fluxo -----------------------------------------------------------
    def start(self):
        self.ui.play("silencio")
        self.ui.say("Casa fechada, hora da limpeza. Você está na pia. " + self.left_text()
                    + " Quando quiser parar, Start e Ir para casa.")

    def update(self, dt):
        if self.paused or self.done:
            return
        if self.busy > 0:
            self.busy -= dt
            if self.busy <= 0:
                self.casa.dirt["lixo"] = 0
                self.ui.play("lixo_fora")
                self.ui.say("Lixo lá fora.")
        self.ambient_t -= dt
        if self.ambient_t <= 0:
            self.ambient_t = C.AMBIENT_EVERY
            self._ambient()

    def _ambient(self):
        dirty = self.dirty_spots()
        if not dirty:
            return
        self.ambient_next %= len(dirty)
        layer, index = dirty[self.ambient_next]
        self.ambient_next += 1
        spot = self.layout[layer][index]
        self.ui.play(spot[3], self._spot(layer, index), volume=0.5)

    def go_home(self):
        self.done = True
        self.spinning = None
        if self.on_done:
            self.on_done()

    # --- controles -------------------------------------------------------
    def announce_focus(self, with_layer=False):
        layer, index = self.layer, self.index[self.layer]
        spot = self.layout[layer][index]
        prefix = ("Salão. " if layer == SALAO else "Cozinha. ") if with_layer else ""
        self.ui.play("foco", self._spot(layer, index))
        self.ui.say("%s%s, %s." % (prefix, spot[1], self.describe(layer, index)))

    def step(self, delta):
        if self.spinning:
            self.spin_pad("left" if delta < 0 else "right")
            return
        if self.scrubbing:
            self._stroke(delta)
            return
        layer = self.layer
        new = self.index[layer] + delta
        if not 0 <= new < len(self.layout[layer]):
            self.ui.play("borda", self._spot(layer, self.index[layer]))
            return
        self.index[layer] = new
        self.announce_focus()

    def go_layer(self, layer):
        if self.spinning:
            self.spin_pad("up" if layer == 0 else "down")
            return
        if self.scrubbing:
            return
        if layer == self.layer:
            self.ui.play("borda", self._spot(layer, self.index[layer]))
            return
        self.layer = layer
        self.announce_focus(with_layer=True)

    def jump(self, delta):
        if self.scrubbing or self.spinning:
            return
        spots = [(l, i) for l in (SALAO, COZINHA) for i in range(len(self.layout[l]))]
        here = spots.index((self.layer, self.index[self.layer]))
        for k in range(1, len(spots) + 1):
            layer, index = spots[(here + delta * k) % len(spots)]
            if self._dirt(self.layout[layer][index]) > 0:
                changed = layer != self.layer
                self.layer = layer
                self.index[layer] = index
                self.announce_focus(with_layer=changed)
                return
        self.ui.play("borda")
        self.ui.say("Está tudo limpo.")

    def action_down(self):
        if self.busy > 0:
            self.ui.say("Levando o lixo.")
            return
        if self.scrubbing:
            self._stop_scrub("Parou de esfregar.")
            return
        if self.spinning:
            self._stop_spin("Parou de " + ("lavar." if self.spinning == "lavar" else "raspar."))
            return
        spot = self._here()
        pos = self._spot(self.layer, self.index[self.layer])
        if self._dirt(spot) == 0:
            self.ui.say("%s já está limpo." % spot[1] if spot[0] != "louca" else "Pia vazia.")
            return
        how = spot[2]
        if how == "esfregar":
            self.scrubbing = (self.layer, self.index[self.layer])
            self.last_side = None
            self.strokes = 0
            self.ui.play("pegar", pos)
            self.ui.say("Esfregando. Esquerda e direita, alternando. A ou B para parar.")
        elif how == "raspar":
            self._start_spin("raspar")
            self.ui.play("pegar", pos)
            self.ui.say("Raspando. Gire o analógico ou o direcional em círculos. A ou B para "
                        "parar.")
        elif how == "lavar":
            self._start_spin("lavar")
            self._next_plate("Lavando. Gire o analógico ou o direcional em círculos. A ou B "
                             "para parar. ")
        else:
            self.busy = C.TRASH_TIME
            self.ui.play("passos", pos)
            self.ui.say("Levando o lixo para fora.")

    def action_up(self):
        pass

    def back(self):
        """A: para de esfregar; fora disso, diz como limpar o que está em foco."""
        if self.scrubbing:
            self._stop_scrub("Parou de esfregar.")
            return
        if self.spinning:
            self._stop_spin("Parou de " + ("lavar." if self.spinning == "lavar" else "raspar."))
            return
        spot = self._here()
        if self._dirt(spot) == 0:
            self.ui.say("%s, limpo." % spot[1])
        else:
            self.ui.say("%s, %s. %s" % (spot[1], dirt_words(spot[0], self._dirt(spot)),
                                        HOW[spot[2]]))

    def _stroke(self, side):
        if side == self.last_side:
            return
        self.last_side = side
        layer, index = self.scrubbing
        spot = self.layout[layer][index]
        self.strokes += 1
        self.ui.play("pano", self._spot(layer, index), pitch=1.0 if side < 0 else 1.15)
        if self.strokes >= C.SCRUB_STROKES:
            self.strokes = 0
            self.casa.dirt[spot[0]] -= 1
            if self.casa.dirt[spot[0]] <= 0:
                self.casa.dirt[spot[0]] = 0
                self._stop_scrub("%s limpinho." % spot[1])

    def _stop_scrub(self, text):
        self.scrubbing = None
        self.ui.play("brilho" if "limpinho" in text else "pegar",
                     self._spot(self.layer, self.index[self.layer]))
        self.ui.say(text)

    # --- girar: raspar o fogo e lavar a louça ---------------------------
    def _start_spin(self, how):
        self.spinning = how
        self.spinner.reset()
        self.quarters = 0

    def _stop_spin(self, text, sound="pegar"):
        self.spinning = None
        self.plate = None
        self.ui.play(sound, self._spot(self.layer, self.index[self.layer]))
        self.ui.say(text)

    def stick(self, axis, value):
        """O analógico esquerdo mexeu."""
        if self.spinning and not self.paused:
            self._turned(self.spinner.stick(axis, value))

    def spin_pad(self, direction):
        self._turned(self.spinner.pad(direction))

    def _turned(self, quarters):
        for _ in range(quarters):
            if not self.spinning:
                return
            self._quarter()

    def _quarter(self):
        layer, index = self.layer, self.index[self.layer]
        spot = self.layout[layer][index]
        # o som sai do lado do círculo em que a mão está
        pos = (layer, index + 0.4 * self.spinner.side, len(self.layout[layer]))
        self.quarters += 1
        if self.spinning == "raspar":
            need = 4 * C.SCRAPE_TURNS
            self.ui.play("raspar_giro", pos, pitch=0.9 + 0.3 * self.quarters / need)
            if self.quarters >= need:
                self.quarters = 0
                self.casa.dirt[spot[0]] = max(0, self.casa.dirt[spot[0]] - 1)
                if self.casa.dirt[spot[0]] == 0:
                    self._stop_spin("%s limpinha." % spot[1], "brilho")
            return
        need = 4 * self.plate[1]
        self.ui.play("esponja", pos, pitch=0.85 + 0.35 * self.quarters / need)
        if self.quarters < need:
            return
        self.quarters = 0
        self.casa.dirt["louca"] = max(0, self.casa.dirt["louca"] - 1)
        self.ui.play("prato_limpo", self._spot(layer, index))
        name = self.plate[0]
        if self.casa.dirt["louca"] == 0:
            self._stop_spin("%s limpo. Era a última louça." % name.capitalize(), "brilho")
            return
        self._next_plate("%s limpo. " % name.capitalize())

    def _next_plate(self, prefix):
        names = [p[0] for p in C.PLATES]
        weights = [p[2] for p in C.PLATES]
        name = self.rng.choices(names, weights)[0]
        self.plate = next(p for p in C.PLATES if p[0] == name)
        n = self.casa.dirt["louca"]
        self.ui.play("louca", self._spot(self.layer, self.index[self.layer]), volume=0.6)
        self.ui.say("%s%s na mão. %s." % (prefix, name.capitalize(), "É o último" if n == 1
                                            else "Faltam %d na pia" % n))
