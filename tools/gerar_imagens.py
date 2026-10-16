#!/usr/bin/env python3
"""Gera os ícones das comidas (images/comida.png) com a Pillow.

Cada ícone tem 32x32 e é desenhado em 128x128 e reduzido, para ficar macio.
A ordem dos ícones na folha é a de comes.tela.ICONS.

    python3 tools/gerar_imagens.py
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from comes.tela import ICON_SIZE, ICONS  # noqa: E402

S = 128
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "comida.png")

BREAD = (232, 184, 112)
CRUST = (176, 112, 52)
GOLD = (236, 168, 60)
GOLD_DARK = (190, 112, 34)
CHEESE = (255, 214, 64)
INK = (60, 36, 24)


def glass(d, fill, top=40):
    d.polygon([(34, 24), (94, 24), (86, 116), (42, 116)], fill=(220, 236, 244), outline=INK, width=4)
    d.polygon([(36 + (top - 24) * 0.09, top), (92 - (top - 24) * 0.09, top), (86, 112), (42, 112)],
              fill=fill)


def steam(d, x):
    for dx in (0, 18):
        d.arc((x + dx - 8, 2, x + dx + 8, 22), 90, 270, fill=(200, 200, 210), width=4)
        d.arc((x + dx - 8, 16, x + dx + 8, 36), 270, 90, fill=(200, 200, 210), width=4)


def draw(name, d):
    if name == "misto":
        d.rounded_rectangle((14, 30, 114, 108), 22, fill=CRUST)
        d.rounded_rectangle((20, 36, 108, 102), 18, fill=BREAD)
        d.rectangle((16, 62, 112, 70), fill=(236, 140, 150))
        d.polygon([(20, 70), (108, 70), (98, 84), (84, 74), (70, 88), (56, 74), (40, 86), (30, 74)],
                  fill=CHEESE)
        for x in (44, 64, 84):
            d.line((x, 40, x - 12, 58), fill=GOLD_DARK, width=5)
    elif name == "xburger":
        d.chord((14, 18, 114, 90), 180, 360, fill=(222, 140, 56), outline=INK, width=3)
        for x, y in ((40, 36), (64, 30), (88, 38), (52, 46), (76, 46)):
            d.ellipse((x - 3, y - 2, x + 3, y + 2), fill=(255, 240, 200))
        d.polygon([(14, 56), (114, 56), (100, 72), (84, 62), (64, 76), (44, 62), (28, 72)], fill=CHEESE)
        d.rounded_rectangle((12, 64, 116, 84), 10, fill=(110, 58, 30))
        d.rounded_rectangle((16, 86, 112, 108), 10, fill=(222, 140, 56), outline=INK, width=3)
    elif name == "fritas":
        for i, x in enumerate(range(34, 96, 10)):
            d.rectangle((x, 14 + (i % 3) * 8, x + 7, 80), fill=(255, 210, 70), outline=GOLD_DARK)
        d.polygon([(26, 54), (102, 54), (92, 118), (36, 118)], fill=(214, 46, 46), outline=INK, width=3)
        d.ellipse((54, 74, 74, 94), fill=(255, 220, 90))
    elif name == "pastel":
        d.chord((10, 30, 118, 138), 180, 360, fill=GOLD, outline=GOLD_DARK, width=4)
        d.line((14, 84, 114, 84), fill=GOLD_DARK, width=6)
        for x in range(20, 112, 12):
            d.line((x, 78, x, 90), fill=GOLD_DARK, width=3)
        for x, y in ((44, 56), (70, 48), (84, 64)):
            d.ellipse((x - 5, y - 4, x + 5, y + 4), fill=(250, 210, 120))
    elif name == "coxinha":
        d.polygon([(64, 10), (100, 80), (28, 80)], fill=(222, 130, 46))
        d.ellipse((24, 50, 104, 120), fill=(222, 130, 46), outline=GOLD_DARK, width=4)
        d.polygon([(64, 14), (96, 78), (32, 78)], fill=(234, 150, 62))
        for x, y in ((50, 80), (72, 92), (60, 104), (82, 74)):
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(180, 96, 30))
    elif name == "suco":
        glass(d, (255, 156, 30))
        d.line((70, 8, 78, 60), fill=(240, 80, 80), width=6)
        d.ellipse((76, 14, 112, 50), fill=(255, 166, 40), outline=(255, 220, 140), width=4)
    elif name == "suco_mexerica":
        glass(d, (250, 120, 20))
        d.chord((74, 14, 114, 54), 0, 360, fill=(255, 132, 30), outline=(255, 200, 120), width=4)
        d.polygon([(90, 10), (104, 4), (100, 18)], fill=(60, 150, 60))
    elif name == "pao_chapa":
        d.rounded_rectangle((16, 28, 112, 110), 26, fill=CRUST)
        d.rounded_rectangle((24, 36, 104, 102), 20, fill=(240, 196, 120))
        for x in (44, 64, 84):
            d.line((x, 44, x - 14, 94), fill=GOLD_DARK, width=5)
        d.rounded_rectangle((50, 56, 80, 80), 5, fill=(255, 236, 120), outline=(220, 180, 40), width=3)
    elif name == "queijo_quente":
        d.polygon([(12, 104), (64, 20), (116, 104)], fill=CRUST)
        d.polygon([(24, 96), (64, 32), (104, 96)], fill=BREAD)
        d.polygon([(16, 100), (112, 100), (100, 112), (86, 104), (70, 118), (56, 104), (40, 114),
                   (28, 104)], fill=CHEESE)
        for x in (52, 74):
            d.line((x, 52, x - 10, 80), fill=GOLD_DARK, width=5)
    elif name == "chocolate_quente":
        d.rounded_rectangle((22, 40, 92, 118), 14, fill=(214, 66, 66), outline=INK, width=4)
        d.arc((80, 56, 116, 98), 270, 90, fill=(214, 66, 66), width=10)
        d.ellipse((28, 34, 86, 54), fill=(120, 64, 32))
        d.ellipse((38, 26, 76, 46), fill=(250, 244, 236))
        steam(d, 48)
    elif name == "sanduiche_natural":
        d.polygon([(10, 100), (64, 20), (118, 100)], fill=(250, 236, 206), outline=CRUST, width=4)
        d.polygon([(14, 100), (114, 100), (104, 110), (90, 100), (76, 112), (62, 100), (46, 112),
                   (30, 100), (20, 110)], fill=(110, 196, 80))
        d.rectangle((18, 90, 110, 98), fill=(250, 250, 240))
        d.polygon([(14, 112), (114, 112), (110, 120), (18, 120)], fill=(250, 236, 206))
    elif name == "vitamina_morango":
        glass(d, (250, 150, 180), top=34)
        d.ellipse((40, 26, 90, 44), fill=(255, 230, 236))
        d.polygon([(82, 20), (106, 20), (94, 46)], fill=(222, 40, 60))
        d.polygon([(84, 18), (94, 10), (104, 18)], fill=(60, 160, 60))
    elif name == "cafezinho":
        d.ellipse((10, 92, 118, 118), fill=(240, 240, 236), outline=(160, 160, 170), width=3)
        d.chord((26, 40, 96, 120), 0, 180, fill=(250, 250, 248), outline=(140, 140, 150), width=4)
        d.rectangle((26, 60, 96, 80), fill=(250, 250, 248))
        d.line((26, 60, 26, 80), fill=(140, 140, 150), width=4)
        d.line((96, 60, 96, 80), fill=(140, 140, 150), width=4)
        d.ellipse((28, 52, 94, 68), fill=(92, 52, 26), outline=(140, 140, 150), width=3)
        d.arc((88, 62, 116, 92), 270, 90, fill=(140, 140, 150), width=7)
        steam(d, 50)
    elif name == "louca":
        for i, y in enumerate((94, 78, 62, 46)):
            d.ellipse((12, y, 116, y + 26), fill=(246, 246, 250), outline=(90, 110, 150), width=3)
            d.ellipse((40, y + 6, 88, y + 18), outline=(150, 170, 210), width=2)
        for x, y in ((30, 52), (90, 70), (60, 86)):
            d.ellipse((x - 6, y - 4, x + 6, y + 4), fill=(170, 130, 70))
    elif name == "queimado":
        d.ellipse((18, 54, 110, 112), fill=(40, 34, 32))
        d.ellipse((30, 60, 70, 82), fill=(70, 58, 52))
        for x in (40, 64, 88):
            d.ellipse((x - 12, 18, x + 12, 44), fill=(130, 130, 136))
    elif name == "carne":
        d.ellipse((14, 38, 114, 100), fill=(206, 70, 80), outline=(150, 40, 50), width=4)
        for x, y in ((40, 60), (70, 52), (84, 76), (54, 82)):
            d.ellipse((x - 6, y - 4, x + 6, y + 4), fill=(244, 170, 170))
    elif name == "hamburguer":
        d.ellipse((14, 38, 114, 100), fill=(110, 58, 30), outline=INK, width=4)
        for x in (44, 64, 84):
            d.line((x, 46, x - 14, 92), fill=(70, 34, 18), width=5)
    elif name == "batata":
        d.ellipse((16, 34, 112, 104), fill=(196, 150, 90), outline=(130, 92, 50), width=4)
        for x, y in ((40, 56), (78, 50), (62, 80), (92, 78)):
            d.ellipse((x - 4, y - 3, x + 4, y + 3), fill=(130, 92, 50))
    elif name == "laranja":
        d.ellipse((16, 24, 112, 120), fill=(255, 150, 20), outline=(210, 110, 10), width=4)
        d.ellipse((56, 14, 92, 34), fill=(70, 160, 60))
    elif name == "mexerica":
        d.ellipse((12, 40, 116, 116), fill=(255, 124, 20), outline=(206, 90, 10), width=4)
        for x in (40, 64, 88):
            d.line((x, 46, x, 110), fill=(236, 104, 14), width=3)
        d.ellipse((54, 26, 90, 46), fill=(70, 160, 60))
    elif name == "leite":
        d.polygon([(36, 34), (64, 14), (92, 34)], fill=(220, 230, 246), outline=(70, 110, 180), width=3)
        d.rectangle((36, 34, 92, 118), fill=(250, 252, 255), outline=(70, 110, 180), width=4)
        d.rectangle((36, 64, 92, 88), fill=(70, 130, 220))
    elif name == "morango":
        d.polygon([(22, 46), (106, 46), (64, 120)], fill=(222, 40, 60))
        d.ellipse((22, 30, 106, 80), fill=(222, 40, 60))
        for x, y in ((44, 56), (64, 66), (84, 56), (54, 86), (74, 86), (64, 102)):
            d.ellipse((x - 3, y - 4, x + 3, y + 4), fill=(255, 220, 120))
        d.polygon([(34, 36), (64, 18), (94, 36), (64, 44)], fill=(60, 160, 60))
    elif name == "graos":
        for x, y in ((40, 50), (74, 44), (56, 80), (88, 78)):
            d.ellipse((x - 18, y - 13, x + 18, y + 13), fill=(110, 62, 30), outline=INK, width=3)
            d.line((x - 12, y, x + 12, y), fill=INK, width=3)
    elif name == "massa":
        d.ellipse((10, 40, 118, 110), fill=(250, 232, 190), outline=(210, 180, 120), width=4)
        d.ellipse((24, 52, 104, 98), outline=(230, 206, 160), width=2)
    else:
        raise ValueError(name)


def main():
    sheet = Image.new("RGBA", (ICON_SIZE * len(ICONS), ICON_SIZE), (0, 0, 0, 0))
    for i, name in enumerate(ICONS):
        big = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        draw(name, ImageDraw.Draw(big))
        sheet.paste(big.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS), (i * ICON_SIZE, 0))
    sheet.save(OUT)
    print("%d ícones em %s" % (len(ICONS), os.path.normpath(OUT)))


if __name__ == "__main__":
    main()
