"""Gráficos de mentira com o Pillow, com a mesma API do r36s_a11y.graphics.
Serve para gerar prévias das telas no PC, sem console e sem SDL:

    gfx = PilGfx("pasta/do/jogo"); desenhar(gfx); gfx.save("tela.png")
"""
import os

from PIL import Image as PImage, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def color(c):
    if c is None:
        return (255, 255, 255, 255)
    if isinstance(c, str):
        h = c.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    c = tuple(int(v) for v in c)
    return c if len(c) == 4 else c + (255,)


class Img:
    def __init__(self, pil):
        self.pil = pil
        self.width, self.height = pil.size


class Font:
    def __init__(self, size):
        self.size = size
        self.pil = ImageFont.truetype(FONT, size)


class PilGfx:
    available = True

    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.canvas = PImage.new("RGBA", (640, 480), (0, 0, 0, 255))
        self.default = Font(24)

    def _layer(self, fn):
        layer = PImage.new("RGBA", self.canvas.size, (0, 0, 0, 0))
        fn(ImageDraw.Draw(layer))
        self.canvas.alpha_composite(layer)

    def clear(self, c=(0, 0, 0)):
        self.canvas.paste(color(c), [0, 0, 640, 480])

    def rect(self, x, y, w, h, color=None, fill=True):
        c = globals()["color"](color)
        box = [x, y, x + w - 1, y + h - 1]
        self._layer(lambda d: d.rectangle(box, fill=c) if fill else d.rectangle(box, outline=c))

    def line(self, x1, y1, x2, y2, color=None, width=1):
        c = globals()["color"](color)
        self._layer(lambda d: d.line([x1, y1, x2, y2], fill=c, width=width))

    def circle(self, x, y, r, color=None, fill=True):
        c = globals()["color"](color)
        box = [x - r, y - r, x + r, y + r]
        self._layer(lambda d: d.ellipse(box, fill=c) if fill else d.ellipse(box, outline=c))

    def polygon(self, points, color=None, fill=True):
        c = globals()["color"](color)
        self._layer(lambda d: d.polygon(points, fill=c) if fill else d.polygon(points, outline=c))

    def image(self, path):
        return Img(PImage.open(os.path.join(self.base_dir, path)).convert("RGBA"))

    def draw(self, img, x, y, src=None, scale=1.0, **kw):
        part = img.pil.crop((src[0], src[1], src[0] + src[2], src[1] + src[3])) if src else img.pil
        if scale != 1.0:
            part = part.resize((int(part.width * scale), int(part.height * scale)), PImage.NEAREST)
        layer = PImage.new("RGBA", self.canvas.size, (0, 0, 0, 0))
        layer.paste(part, (int(x), int(y)))
        self.canvas.alpha_composite(layer)

    def font(self, path=None, size=24):
        return Font(size)

    def measure(self, text, font=None):
        font = font or self.default
        box = font.pil.getbbox(text)
        return (box[2], font.size)

    def text(self, text, x, y, font=None, color=None, align="left"):
        font = font or self.default
        w = self.measure(text, font)[0]
        if align == "center":
            x -= w / 2
        elif align == "right":
            x -= w
        c = globals()["color"](color)
        self._layer(lambda d: d.text((x, y), text, font=font.pil, fill=c))

    def save(self, path):
        self.canvas.convert("RGB").save(path)
