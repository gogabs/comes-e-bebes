"""A limpeza depois de fechar: cada sujeira tem seu lugar, seu som e seu jeito.

Mesmo `ui` do expediente (say, play, loop, stop). O tempo anda por update(dt).
"""
from . import config as C
from .expediente import join

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
       "raspar": "Segure B para raspar.",
       "lavar": "Aperte B para lavar cada prato.",
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
    def __init__(self, casa, ui, on_done=None):
        self.casa = casa
        self.ui = ui
        self.on_done = on_done
        self.layout = (list(SPOTS[0]), list(SPOTS[1]))
        self.layer = COZINHA
        self.index = [0, 3]          # começa na pia
        self.scrubbing = None        # (camada, índice) sendo esfregado
        self.last_side = None
        self.strokes = 0
        self.scraping = False
        self.scrape_t = 0.0
        self.wash_wait = 0.0
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
        if self.wash_wait > 0:
            self.wash_wait -= dt
        if self.scraping:
            self._scrape(dt)
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
        self.scraping = False
        self.ui.stop("raspar")
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
        if self.scrubbing:
            return
        if layer == self.layer:
            self.ui.play("borda", self._spot(layer, self.index[layer]))
            return
        self.layer = layer
        self.announce_focus(with_layer=True)

    def jump(self, delta):
        if self.scrubbing:
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
            self.scraping = True
            self.ui.loop("raspar", "raspar", pos)
        elif how == "lavar":
            if self.wash_wait > 0:
                return
            self.wash_wait = C.WASH_TIME
            self.casa.dirt["louca"] -= 1
            n = self.casa.dirt["louca"]
            self.ui.play("lavar", pos, pitch=1.0 + 0.4 / (1 + n))
            if n == 0:
                self.ui.say("Última louça lavada.")
        else:
            self.busy = C.TRASH_TIME
            self.ui.play("passos", pos)
            self.ui.say("Levando o lixo para fora.")

    def action_up(self):
        if self.scraping:
            self.scraping = False
            self.ui.stop("raspar")
            spot = self._here()
            if self._dirt(spot) > 0:
                self.ui.say("%s: %s." % (spot[1], dirt_words(spot[0], self._dirt(spot))))

    def back(self):
        """A: para de esfregar; fora disso, diz como limpar o que está em foco."""
        if self.scrubbing:
            self._stop_scrub("Parou de esfregar.")
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

    def _scrape(self, dt):
        spot = self._here()
        self.scrape_t += dt
        if self.scrape_t >= C.SCRAPE_TIME:
            self.scrape_t = 0.0
            self.casa.dirt[spot[0]] = max(0, self.casa.dirt[spot[0]] - 1)
            if self.casa.dirt[spot[0]] == 0:
                self.scraping = False
                self.ui.stop("raspar")
                self.ui.play("brilho", self._spot(self.layer, self.index[self.layer]))
                self.ui.say("%s limpinha." % spot[1])
