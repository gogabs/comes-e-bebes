"""Gráficos de mentira para os testes: guardam cada chamada e conferem que os
recortes das folhas cabem nos PNG de verdade. Não precisa do Pillow nem de SDL."""
import os
import struct


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", head[16:24])


class Img:
    def __init__(self, path, width, height):
        self.path, self.width, self.height = path, width, height


class Font:
    def __init__(self, size):
        self.size = size


class RecordingGfx:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.calls = []
        self.available = True
        self.opened = 0
        self.frames = 0
        self.fail = False

    # --- ciclo ---
    def open(self):
        self.opened += 1
        return True

    def begin(self):
        if self.fail:
            raise RuntimeError("vídeo caiu")
        self.calls = []

    def end(self):
        self.frames += 1

    def close(self):
        self.available = False

    # --- desenho ---
    def clear(self, color=(0, 0, 0)):
        self.calls.append(("clear", color))

    def rect(self, x, y, w, h, color=None, fill=True):
        self.calls.append(("rect", x, y, w, h, color))

    def line(self, x1, y1, x2, y2, color=None, width=1):
        self.calls.append(("line", x1, y1, x2, y2, color))

    def circle(self, x, y, radius, color=None, fill=True):
        self.calls.append(("circle", x, y, radius, color))

    def polygon(self, points, color=None, fill=True):
        self.calls.append(("polygon", points, color))

    def image(self, path):
        full = os.path.join(self.base_dir, path)
        return Img(full, *png_size(full))

    def draw(self, image, x, y, src=None, scale=1.0, rotation=0.0, **kw):
        if src is not None:
            sx, sy, sw, sh = src
            assert sx >= 0 and sy >= 0 and sx + sw <= image.width and sy + sh <= image.height, \
                "recorte %r fora de %s" % (src, image.path)
        self.calls.append(("draw", image.path, x, y, src))

    def font(self, path=None, size=24):
        return Font(size)

    def measure(self, text, font=None):
        size = font.size if font else 24
        return int(len(text) * size * 0.6), size

    def text(self, text, x, y, font=None, color=None, align="left"):
        self.calls.append(("text", text, x, y, color, align))

    # --- para os testes ---
    def texts(self):
        return [c[1] for c in self.calls if c[0] == "text"]

    def draws(self):
        return [c for c in self.calls if c[0] == "draw"]
