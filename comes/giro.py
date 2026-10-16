"""Girar em círculos, com o analógico ou com o direcional.

Conta quartos de volta. O analógico conta o ângulo percorrido (precisa sair do
centro); o direcional conta cada passo para uma direção vizinha, como
cima, direita, baixo, esquerda.
"""
import math

from . import config as C

QUARTER = math.pi / 2
DIRECTIONS = ("up", "right", "down", "left")


class Spinner:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.angle = None
        self.acc = 0.0
        self.sign = 0
        self.last_dir = None

    def reset(self):
        self.__init__()

    @property
    def side(self):
        """De -1 (esquerda) a 1 (direita): onde a mão está no círculo, para o som."""
        if self.angle is None:
            return 0.0
        return math.cos(self.angle)

    def stick(self, axis, value):
        """Valor novo de um eixo do analógico esquerdo. Devolve quantos quartos de volta."""
        if axis == "lx":
            self.x = value
        elif axis == "ly":
            self.y = -value              # no evdev, cima é negativo
        else:
            return 0
        if math.hypot(self.x, self.y) < C.SPIN_MIN:
            self.angle = None
            return 0
        a = math.atan2(self.y, self.x)
        if self.angle is None:
            self.angle = a
            return 0
        d = (a - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle = a
        sign = 1 if d > 0 else -1 if d < 0 else 0
        if sign and sign != self.sign:
            self.sign = sign
            self.acc = 0.0           # mudou de sentido: começa a contar de novo
        self.acc += abs(d)
        quarters = 0
        while self.acc >= QUARTER:
            self.acc -= QUARTER
            quarters += 1
        return quarters

    def pad(self, direction):
        """Um aperto no direcional. Devolve 1 se andou para uma direção vizinha."""
        if direction not in DIRECTIONS:
            return 0
        i = DIRECTIONS.index(direction)
        last, self.last_dir = self.last_dir, i
        self.angle = (math.pi / 2, 0.0, -math.pi / 2, math.pi)[i]
        if last is None:
            return 0
        return 1 if (i - last) % 4 in (1, 3) else 0
