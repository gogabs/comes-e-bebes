"""Gráficos opcionais: a casa vista de frente, o salão em cima e a cozinha embaixo.

Nada aqui é necessário para jogar: tudo o que aparece na tela também é falado
(regra do contrato da plataforma). A legenda embaixo é sempre a última fala.
A tela segue a opção do sistema (SCREEN=0 desliga) e a economia de energia.

`draw_frame(gfx, ...)` só lê o estado do jogo e só usa a API de desenho do
SDK, então roda com o SDK de verdade, com o gráfico de mentira dos testes e
com o gerador de prévias (tools/previas.py).
"""
import math
import os
import time

from . import data as D

W, H = 640, 480
ICON_SIZE = 32
ICONS = ("misto", "xburger", "fritas", "pastel", "coxinha", "suco", "pao_chapa", "suco_mexerica",
         "queijo_quente", "chocolate_quente", "sanduiche_natural", "vitamina_morango",
         "cafezinho", "louca", "queimado", "carne", "hamburguer", "batata", "laranja",
         "mexerica", "leite", "morango", "graos", "massa")
SHEET = "images/comida.png"

# O que está na mão ou no fogo e ainda não está pronto: ícone e se é cru.
RAW = {"misto_montado": "misto", "hamburguer_cru": "carne", "batata_crua": "batata",
       "fritas_sem_sal": "fritas", "laranja_cortada": "laranja",
       "mexerica_descascada": "mexerica", "pao_manteiga": "pao_chapa",
       "queijo_montado": "queijo_quente", "leite_chocolate": "leite",
       "morango_leite": "morango", "pastel_cru": "pastel", "coxinha_crua": "coxinha"}
# Ingredientes do estoque, na bancada: ícone, ou uma bolinha com a cor.
INGREDIENT_ICONS = {"carne": "carne", "batata": "batata", "laranja": "laranja",
                    "mexerica": "mexerica", "leite": "leite", "morango": "morango",
                    "massa": "massa", "coxinha": "coxinha", "cafe": "graos"}
INGREDIENT_COLORS = {"pao": "#e8b870", "presunto": "#ec8c96", "queijo": "#ffd640",
                     "sal": "#f4f4f4", "manteiga": "#ffec78", "chocolate": "#6e3a1e",
                     "frango": "#f2e2c4", "alface": "#6ec450"}
BLEND_COLORS = {"laranja_cortada": "#ff9c1e", "mexerica_descascada": "#fa7814",
                "leite_chocolate": "#8a5030", "morango_leite": "#fa96b4",
                "suco": "#ff9c1e", "suco_mexerica": "#fa7814", "chocolate_quente": "#7a4426",
                "vitamina_morango": "#fa96b4"}

# --- cores: contraste alto, e a cor nunca é a única pista -------------------
BAR = "#2a1a12"
TEXT = "#fff6e6"
TEXT_DIM = "#e6cdb0"
FOCUS = "#ffd60a"
OUTLINE = "#000000"
WOOD = "#8a5a34"
WOOD_DARK = "#5c3a20"
WOOD_TOP = "#b07a48"
FLOOR = ("#c99a66", "#bb8c5a")
TILE = ("#f2efe8", "#e2ddd2")
KITCHEN_FLOOR = "#7d8a94"
STEEL = "#b7c0c8"
STEEL_DARK = "#56606a"
PANEL = (32, 20, 14, 235)
GOOD = "#3cc85a"
WARN = "#ffb020"
BAD = "#ff4a3c"
WALLS = ("#f3c6d2", "#ffe39a", "#e8a96a", "#9fb7d6")       # primavera, verão, outono, inverno
NIGHT_WALL = "#3a3550"
SKIN = ("#f1c7a0", "#d8a070", "#a8693c", "#7a4a2a", "#f6d8bc")
SHIRTS = ("#d6455a", "#3d7fd6", "#3bb07a", "#e0a020", "#8a5ad0", "#20a0b0")

TOP_BAR = 34
WALL_END = 96
SALAO_END = 236
COUNTER_END = 252
STATION_Y = 292
STATION_H = 88
KITCHEN_FLOOR_Y = 400
BOTTOM = 420
TABLE_X = (110, 320, 530)
TABLE_Y = 166


class Fonts:
    def __init__(self, gfx):
        self.small = gfx.font(size=13)
        self.normal = gfx.font(size=16)
        self.big = gfx.font(size=20)
        self.title = gfx.font(size=40)


class Scene:
    """O que desenhar: a fase, a casa, o expediente ou a limpeza, o menu aberto
    e a legenda."""

    def __init__(self, phase=None, casa=None, service=None, cleaning=None, menu=None,
                 caption="", t=0.0):
        self.phase = phase
        self.casa = casa
        self.service = service
        self.cleaning = cleaning
        self.menu = menu
        self.caption = caption
        self.t = t


# --- utilidades ------------------------------------------------------------------
def icon_src(name):
    return (ICONS.index(name) * ICON_SIZE, 0, ICON_SIZE, ICON_SIZE)


def draw_icon(gfx, sheet, kind, x, y, scale=1.0, raw=False):
    """Desenha a comida `kind` (receita, coisa na mão ou ingrediente)."""
    name = kind
    if kind in RAW:
        name, raw = RAW[kind], True
    elif kind in INGREDIENT_ICONS:
        name = INGREDIENT_ICONS[kind]
    if name in ICONS:
        gfx.draw(sheet, x, y, src=icon_src(name), scale=scale,
                 alpha=190 if raw else 255, tint=(255, 236, 214) if raw else None)
        return
    r = 12 * scale
    cx, cy = x + 16 * scale, y + 16 * scale
    gfx.circle(cx, cy, r + 2, OUTLINE)
    gfx.circle(cx, cy, r, INGREDIENT_COLORS.get(kind, "#cccccc"))


def outline_rect(gfx, x, y, w, h, color, width=3):
    for k in range(width):
        gfx.rect(x + k, y + k, w - 2 * k, h - 2 * k, color, fill=False)


def focus_box(gfx, x, y, w, h, t):
    pad = 4 + int(2 * (1 + math.sin(t * 6)) / 2)
    outline_rect(gfx, x - pad - 2, y - pad - 2, w + 2 * pad + 4, h + 2 * pad + 4, OUTLINE, 2)
    outline_rect(gfx, x - pad, y - pad, w + 2 * pad, h + 2 * pad, FOCUS, 3)


_fit_cache = {}


def fit(gfx, text, font, width):
    """O texto cortado com reticências para caber na largura."""
    key = (text, id(font), width)
    if key in _fit_cache:
        return _fit_cache[key]
    out = text
    if gfx.measure(text, font)[0] > width:
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if gfx.measure(text[:mid] + "…", font)[0] <= width:
                lo = mid
            else:
                hi = mid - 1
        out = text[:lo].rstrip() + "…"
    if len(_fit_cache) > 500:
        _fit_cache.clear()
    _fit_cache[key] = out
    return out


def wrap(gfx, text, font, width, lines):
    """Quebra em até `lines` linhas; se não couber, mostra o fim (a fala mais nova)."""
    key = ("wrap", text, id(font), width, lines)
    if key in _fit_cache:
        return _fit_cache[key]
    words = text.split()
    rows = []
    row = ""
    for word in words:
        test = (row + " " + word).strip()
        if row and gfx.measure(test, font)[0] > width:
            rows.append(row)
            row = word
        else:
            row = test
    if row:
        rows.append(row)
    if len(rows) > lines:
        rows = rows[-lines:]
        rows[0] = "…" + rows[0]
    _fit_cache[key] = rows
    return rows


def star(gfx, cx, cy, r, color):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    gfx.polygon(pts, color)


def bar(gfx, x, y, w, h, frac, color):
    gfx.rect(x - 1, y - 1, w + 2, h + 2, OUTLINE)
    gfx.rect(x, y, w, h, "#3a3a3a")
    gfx.rect(x, y, max(0, int(w * max(0.0, min(1.0, frac)))), h, color)


def frac_color(frac):
    return GOOD if frac > 0.5 else WARN if frac > 0.25 else BAD


# --- topo e rodapé -------------------------------------------------------------------
def draw_top(gfx, fonts, scene):
    gfx.rect(0, 0, W, TOP_BAR, BAR)
    casa = scene.casa
    if casa is None:
        return
    gfx.text(casa.date_text(), 10, 8, font=fonts.normal, color=TEXT)
    x = W - 10
    for k in range(5):
        cx = x - 8 - (4 - k) * 18
        whole = casa.reputation - k
        star(gfx, cx, 17, 8, OUTLINE)
        star(gfx, cx, 17, 7, FOCUS if whole >= 0.75 else "#a08040" if whole >= 0.25 else "#4a3a30")
    money = "R$ %d" % casa.money
    gfx.text(money, W - 110, 8, font=fonts.normal, color=TEXT, align="right")
    service = scene.service
    if service is not None:
        from .expediente import clock
        gfx.text(clock(service.minutes), 360, 8, font=fonts.normal, color=TEXT_DIM,
                 align="center")


def draw_bottom(gfx, sheet, fonts, scene):
    gfx.rect(0, BOTTOM, W, H - BOTTOM, BAR)
    hands = []
    if scene.service is not None:
        hands = scene.service.hands
    x0 = 8
    if scene.service is not None:
        for k in range(2):
            x = 8 + k * 44
            gfx.rect(x, BOTTOM + 10, 40, 40, "#4a3428")
            outline_rect(gfx, x, BOTTOM + 10, 40, 40, "#8a6a50", 1)
            if k < len(hands):
                draw_icon(gfx, sheet, hands[k].kind, x + 4, BOTTOM + 14)
        x0 = 100
    rows = wrap(gfx, scene.caption, fonts.normal, W - x0 - 10, 2)
    for k, row in enumerate(rows):
        gfx.text(row, x0, BOTTOM + 8 + k * 24, font=fonts.normal, color=TEXT)


# --- salão ---------------------------------------------------------------------------
def draw_window(gfx, scene, night):
    x, y, w, h = 250, 42, 140, 46
    casa = scene.casa
    weather = casa.weather if casa else "sol"
    sky = "#1c2448" if night else {"chuva": "#7d8ea0", "nublado": "#a9b8c8",
                                   "frio": "#b8d0e8", "calor": "#ffd27a"}.get(weather, "#8fd0ff")
    gfx.rect(x - 4, y - 4, w + 8, h + 8, WOOD_DARK)
    gfx.rect(x, y, w, h, sky)
    t = scene.t
    if night:
        gfx.circle(x + 110, y + 14, 8, "#fff4c0")
        gfx.circle(x + 114, y + 11, 7, sky)
        for sx, sy in ((x + 20, y + 10), (x + 50, y + 26), (x + 80, y + 8)):
            gfx.circle(sx, sy, 1, "#ffffff")
    elif weather in ("sol", "calor", "frio", "vento"):
        gfx.circle(x + 26, y + 16, 12 if weather == "calor" else 9, "#fff07a")
    if weather in ("nublado", "chuva") and not night:
        for cx in (x + 40, x + 90):
            gfx.circle(cx, y + 16, 10, "#eef2f6")
            gfx.circle(cx + 12, y + 14, 12, "#eef2f6")
            gfx.circle(cx + 24, y + 18, 9, "#eef2f6")
    if weather == "chuva" or (casa and D.SEASON_INFO[casa.season]["ambient"] == "inverno"
                              and weather in ("chuva", "frio", "nublado")):
        for k in range(10):
            rx = x + 6 + (k * 37 + int(t * 60)) % (w - 10)
            ry = y + (k * 13 + int(t * 90)) % (h - 10)
            gfx.line(rx, ry, rx - 3, ry + 8, "#dfe8ff")
    if weather == "vento":
        for k in range(3):
            lx = x + (k * 50 + int(t * 80)) % w
            ly = y + 10 + k * 12 + 4 * math.sin(t * 4 + k)
            gfx.circle(lx, ly, 3, "#d86a20")
    if casa is not None:
        draw_sill(gfx, casa.season, x, y + h + 4, w)
    gfx.line(x + w // 2, y, x + w // 2, y + h, WOOD_DARK, 3)


def draw_sill(gfx, season, x, y, w):
    gfx.rect(x - 8, y, w + 16, 5, WOOD)
    for k, px in enumerate((x + 12, x + w - 22)):
        gfx.rect(px, y - 10, 14, 10, "#c0603a")
        if season == 0:
            for dx, c in ((-3, "#ff6fa0"), (5, "#ffd23c"), (13, "#ff6fa0")):
                gfx.circle(px + dx + 2, y - 15, 4, c)
        elif season == 1:
            gfx.rect(px + 4, y - 24, 6, 14, "#3a9a4a")
        elif season == 2:
            for dx in (0, 7, 14):
                gfx.circle(px + dx, y - 14, 4, "#d86a20")
        else:
            gfx.line(px + 7, y - 10, px + 2, y - 24, WOOD_DARK, 2)
            gfx.line(px + 7, y - 14, px + 14, y - 22, WOOD_DARK, 2)


def draw_bunting(gfx, t):
    """Bandeirinhas nas datas especiais."""
    colors = ("#ff4a5a", "#ffd23c", "#3cb4ff", "#5ad06a", "#ff8a3c")
    for k in range(20):
        x = 8 + k * 32
        sag = 6 * math.sin(math.pi * (k % 10) / 10)
        gfx.polygon([(x, 38 + sag), (x + 24, 38 + sag), (x + 12, 54 + sag)], colors[k % 5])


def draw_salao_back(gfx, scene, night):
    casa = scene.casa
    wall = NIGHT_WALL if night else WALLS[casa.season if casa else 1]
    gfx.rect(0, TOP_BAR, W, WALL_END - TOP_BAR, wall)
    gfx.rect(0, WALL_END - 6, W, 6, WOOD_DARK)
    for k in range(0, W, 40):
        gfx.rect(k, WALL_END, 40, SALAO_END - WALL_END, FLOOR[(k // 40) % 2])
    if night:
        gfx.rect(0, WALL_END, W, SALAO_END - WALL_END, (16, 16, 48, 90))
    draw_window(gfx, scene, night)
    if casa is not None and casa.special() and not night:
        draw_bunting(gfx, scene.t)
    gfx.rect(0, SALAO_END, W, COUNTER_END - SALAO_END, WOOD_DARK)
    gfx.rect(0, SALAO_END, W, 4, WOOD_TOP)


def table_rect(i):
    return (TABLE_X[i] - 60, TABLE_Y - 62, 120, 130)


def draw_table(gfx, cx, top_items=()):
    gfx.rect(cx - 50, TABLE_Y + 22, 8, 26, WOOD_DARK)
    gfx.rect(cx + 42, TABLE_Y + 22, 8, 26, WOOD_DARK)
    gfx.rect(cx - 58, TABLE_Y, 116, 24, OUTLINE)
    gfx.rect(cx - 56, TABLE_Y + 2, 112, 20, WOOD)
    gfx.rect(cx - 56, TABLE_Y + 2, 112, 5, WOOD_TOP)


def draw_customer(gfx, cx, seed, mood, t, eating=False):
    skin = SKIN[seed % len(SKIN)]
    shirt = SHIRTS[(seed // 3) % len(SHIRTS)]
    bob = 2 * math.sin(t * 3 + seed) if eating else 0
    gfx.circle(cx, TABLE_Y + 6, 22, OUTLINE)
    gfx.circle(cx, TABLE_Y + 6, 20, shirt)
    hy = TABLE_Y - 30 + bob
    gfx.circle(cx, hy, 17, OUTLINE)
    gfx.circle(cx, hy, 15, skin)
    hair = ("#2a1a10", "#6a3a1a", "#d8b060", "#1a1a1a", "#a04020")[seed % 5]
    gfx.polygon([(cx - 15, hy - 2), (cx - 12, hy - 14), (cx, hy - 18), (cx + 12, hy - 14),
                 (cx + 15, hy - 2), (cx + 8, hy - 10), (cx - 8, hy - 10)], hair)
    if eating:
        gfx.line(cx - 8, hy - 2, cx - 3, hy - 2, OUTLINE, 2)
        gfx.line(cx + 3, hy - 2, cx + 8, hy - 2, OUTLINE, 2)
    else:
        gfx.circle(cx - 5, hy - 2, 2, OUTLINE)
        gfx.circle(cx + 5, hy - 2, 2, OUTLINE)
    if mood > 0.5 or eating:
        gfx.line(cx - 5, hy + 6, cx, hy + 8, OUTLINE, 2)
        gfx.line(cx, hy + 8, cx + 5, hy + 6, OUTLINE, 2)
    elif mood > 0.25:
        gfx.line(cx - 5, hy + 7, cx + 5, hy + 7, OUTLINE, 2)
    else:
        gfx.line(cx - 5, hy + 8, cx, hy + 5, OUTLINE, 2)
        gfx.line(cx, hy + 5, cx + 5, hy + 8, OUTLINE, 2)
        gfx.circle(cx - 9, hy + 4, 3, "#ff7a7a")
        gfx.circle(cx + 9, hy + 4, 3, "#ff7a7a")


def draw_bubble(gfx, x, y, w, h):
    gfx.rect(x - 2, y - 2, w + 4, h + 4, OUTLINE)
    gfx.rect(x, y, w, h, "#ffffff")
    gfx.polygon([(x + 6, y + h), (x + 18, y + h), (x + 2, y + h + 10)], OUTLINE)
    gfx.polygon([(x + 8, y + h - 1), (x + 16, y + h - 1), (x + 5, y + h + 6)], "#ffffff")


def customer_seed(table):
    return table.index * 7 + sum(len(k) for k in table.wanted)


def draw_tables(gfx, sheet, fonts, scene):
    service = scene.service
    for i, cx in enumerate(TABLE_X):
        t = service.tables[i] if service is not None else None
        seated = t is not None and t.state not in ("livre", "suja")
        if seated:
            frac = t.patience / t.patience_max if t.waiting else 1.0
            draw_customer(gfx, cx, customer_seed(t), frac, scene.t, eating=t.state == "comendo")
        draw_table(gfx, cx)
        gfx.text("Mesa %d" % (i + 1), cx, TABLE_Y + 50, font=fonts.small, color=OUTLINE,
                 align="center")
        if t is None:
            continue
        if t.state == "comendo":
            for k, (kind, _) in enumerate(t.served[:3]):
                draw_icon(gfx, sheet, kind, cx - 36 + k * 26, TABLE_Y - 12, scale=0.75)
        elif t.state == "suja":
            draw_icon(gfx, sheet, "louca", cx - 16, TABLE_Y - 18)
        if t.state == "pedir":
            draw_bubble(gfx, cx + 14, TABLE_Y - 92, 30, 30)
            gfx.text("!", cx + 29, TABLE_Y - 90, font=fonts.big, color=BAD, align="center")
        elif t.state == "esperando":
            n = min(3, len(t.order))
            draw_bubble(gfx, cx + 10, TABLE_Y - 96, 8 + 34 * n, 38)
            for k, kind in enumerate(t.order[:3]):
                draw_icon(gfx, sheet, kind, cx + 14 + k * 34, TABLE_Y - 93)
        elif t.state == "pagar":
            draw_bubble(gfx, cx + 14, TABLE_Y - 92, 30, 30)
            gfx.circle(cx + 29, TABLE_Y - 77, 11, "#e0a800")
            gfx.text("$", cx + 29, TABLE_Y - 88, font=fonts.normal, color=OUTLINE, align="center")
        if t.waiting:
            frac = max(0.0, t.patience / t.patience_max)
            bar(gfx, cx - 40, TABLE_Y + 34, 80, 6, frac, frac_color(frac))
    if scene.casa is not None and scene.casa.flies and service is not None:
        draw_flies(gfx, (TABLE_X[0], TABLE_Y - 40), scene.t, 2)


def draw_flies(gfx, center, t, n):
    for k in range(n):
        a = t * (3 + k) + k * 2
        x = center[0] + 22 * math.cos(a)
        y = center[1] + 10 * math.sin(a * 1.7)
        gfx.circle(x, y, 2, OUTLINE)
        gfx.circle(x - 2, y - 2, 2, "#d0e0ff")


# --- cozinha -------------------------------------------------------------------------
def kitchen_layout(scene):
    if scene.service is not None:
        return list(scene.service.layout[1])
    from .expediente import EXTRA_STATIONS, STATIONS
    casa = scene.casa
    return list(STATIONS) + [k for k in EXTRA_STATIONS if casa is not None and k in casa.equipment]


def station_rect(names, name):
    n = len(names)
    sw = W / n
    i = names.index(name)
    return (int(i * sw + 5), STATION_Y, int(sw - 10), STATION_H)


def station_focus(names, name):
    """A estação com o nome embaixo."""
    x, y, w, h = station_rect(names, name)
    return (x, y, w, h + 20)


def draw_kitchen_back(gfx):
    for k in range(0, W, 24):
        for j, y in enumerate(range(COUNTER_END, STATION_Y, 20)):
            gfx.rect(k, y, 24, 20, TILE[(k // 24 + j) % 2])
    gfx.rect(0, STATION_Y + STATION_H - 6, W, KITCHEN_FLOOR_Y - STATION_Y - STATION_H + 6,
             KITCHEN_FLOOR)
    gfx.rect(0, KITCHEN_FLOOR_Y, W, BOTTOM - KITCHEN_FLOOR_Y, "#6a7680")


def draw_station(gfx, sheet, fonts, scene, names, name):
    x, y, w, h = station_rect(names, name)
    cx = x + w / 2
    service = scene.service
    gfx.rect(x - 1, y - 1, w + 2, h + 2, OUTLINE)
    gfx.rect(x, y, w, h, STEEL)
    gfx.rect(x, y, w, 6, "#d8dee4")
    t = scene.t
    if name == "bancada":
        gfx.rect(x + 6, y + 16, w - 12, h - 30, "#d9a36a")
        gfx.rect(x + 6, y + 16, w - 12, 4, "#e8bc88")
        if service is not None and service.bench:
            for k, part in enumerate(service.bench[:3]):
                draw_icon(gfx, sheet, service._part_kind(part), x + 8 + k * 24, y + 26, 0.75)
    elif name in ("chapa", "fritadeira"):
        station = service.cookers[name] if service is not None else None
        if name == "chapa":
            gfx.rect(x + 6, y + 18, w - 12, h - 34, "#2e2e30")
        else:
            gfx.rect(x + 6, y + 18, w - 12, h - 34, "#6a5a30")
            gfx.rect(x + 9, y + 21, w - 18, h - 40, "#e8b830")
        if station is not None:
            for k, c in enumerate(station.slots):
                ix = x + 10 + k * (w - 20 - 32) if len(station.slots) > 1 else cx - 16
                iy = y + 22
                stage = c.stage
                if stage >= 3:
                    draw_icon(gfx, sheet, "queimado", ix, iy)
                else:
                    draw_icon(gfx, sheet, c.kind if stage == 0 else D.COOKED[c.kind], ix, iy)
                times = service._times(c.kind)
                frac = c.t / times[0]
                color = "#7ac8ff" if stage == 0 else GOOD if stage == 1 else WARN
                bar(gfx, ix, iy + 36, 32, 5, frac if stage == 0 else 1.0, color)
                if c.turn_cued and not c.turned and stage == 0:
                    gfx.text("!", ix + 30, iy - 6, font=fonts.big, color=FOCUS)
                for s in range(2):
                    sx = ix + 8 + s * 14
                    sy = iy - 4 - ((t * 20 + s * 7) % 10)
                    gfx.line(sx, sy, sx + 2, sy - 5, "#ffffff")
            if station.fire:
                draw_fire(gfx, cx, y + h - 16, w, t)
    elif name == "liquidificador":
        content = service.blender if service is not None else None
        shake = 2 * math.sin(t * 40) if service is not None and service.blending else 0
        jx = cx + shake
        gfx.rect(jx - 16, y + h - 22, 32, 12, "#3a3a40")
        gfx.polygon([(jx - 18, y + 12), (jx + 18, y + 12), (jx + 13, y + h - 22),
                     (jx - 13, y + h - 22)], "#e8f4fa")
        if content is not None:
            level = 0.55 if content in D.BLENDS else 0.8
            top = y + h - 22 - (h - 34) * level
            gfx.polygon([(jx - 18 + (top - y - 12) * 0.1, top), (jx + 18 - (top - y - 12) * 0.1, top),
                         (jx + 13, y + h - 22), (jx - 13, y + h - 22)],
                        BLEND_COLORS.get(content, "#ffffff"))
            if service.blending:
                frac = service.blend / 5.0
                bar(gfx, x + 6, y + h - 8, w - 12, 5, frac, GOOD if service.blend >= 2.5 else
                    "#7ac8ff")
        gfx.polygon([(jx - 18, y + 12), (jx + 18, y + 12), (jx + 13, y + h - 22),
                     (jx - 13, y + h - 22)], OUTLINE, fill=False)
    elif name == "pia":
        gfx.rect(x + 8, y + 22, w - 16, h - 36, "#5a7a96")
        gfx.rect(x + 12, y + 26, w - 24, h - 44, "#86aac8")
        gfx.rect(cx - 3, y + 8, 6, 16, STEEL_DARK)
        dishes = scene.casa.dirt["louca"] if scene.casa is not None else 0
        if dishes:
            draw_icon(gfx, sheet, "louca", cx - 16, y + 30)
            gfx.text(str(dishes), x + w - 10, y + 10, font=fonts.normal, color=OUTLINE,
                     align="right")
    elif name == "lixeira":
        full = scene.casa.dirt["lixo"] if scene.casa is not None else 0
        gfx.rect(cx - 20, y + 22, 40, h - 30, "#2f7a4a")
        gfx.rect(cx - 24, y + 16, 48, 8, "#3c9a5c")
        if full:
            gfx.circle(cx, y + 18, min(14, 4 + 2 * full), "#3a3a3a")
    elif name == "cafeteira":
        draw_coffee(gfx, sheet, service, x, y, w, h, t)
    label = D.ITEM_NAMES.get(name) or name
    from .expediente import STATION_NAMES
    gfx.text(fit(gfx, STATION_NAMES.get(name, label), fonts.small, w), cx, y + h + 2,
             font=fonts.small, color=TEXT, align="center")


def draw_coffee(gfx, sheet, service, x, y, w, h, t):
    cx = x + w / 2
    gfx.rect(cx - 22, y + 10, 44, h - 18, "#9a2a2a")
    gfx.polygon([(cx - 14, y + 4), (cx + 14, y + 4), (cx + 8, y + 18), (cx - 8, y + 18)],
                "#c8d8e0")
    gfx.rect(cx - 14, y + 44, 28, 4, "#3a3a3a")
    state = service.coffee if service is not None else None
    if state == "graos":
        draw_icon(gfx, sheet, "graos", cx - 12, y + 2, 0.75)
        if service.grinding:
            bar(gfx, x + 6, y + h - 8, w - 12, 5, service.grind / 4.0,
                GOOD if service.grind >= 2.0 else "#7ac8ff")
    elif state == "passando":
        dy = (t * 30) % 12
        gfx.circle(cx, y + 50 + dy, 2, "#5a3018")
    if state in ("passando", "pronto"):
        draw_icon(gfx, sheet, "cafezinho", cx - 16, y + 52)


def draw_fire(gfx, cx, base, w, t):
    for k in range(5):
        fx = cx - w / 2 + 10 + k * (w - 20) / 4
        hgt = 26 + 10 * math.sin(t * 9 + k * 1.7)
        gfx.polygon([(fx - 10, base), (fx + 10, base), (fx + 2, base - hgt)], "#ff5a1a")
        gfx.polygon([(fx - 5, base), (fx + 5, base), (fx + 1, base - hgt * 0.6)], "#ffd23c")


# --- sujeira (na limpeza) ----------------------------------------------------------
STAIN = "#6a4a2a"


def stains(gfx, x, y, w, h, n, seed, color=STAIN):
    for k in range(min(n, 8)):
        sx = x + ((seed * 37 + k * 53) % 100) / 100.0 * w
        sy = y + ((seed * 61 + k * 29) % 100) / 100.0 * h
        gfx.circle(sx, sy, 5 + (k * 3 + seed) % 5, color)


def draw_dirt(gfx, scene, names):
    dirt = scene.casa.dirt
    for i, cx in enumerate(TABLE_X):
        n = dirt["mesa%d" % (i + 1)]
        if n:
            stains(gfx, cx - 50, TABLE_Y + 6, 100, 12, n + 1, i + 1)
            draw_flies(gfx, (cx, TABLE_Y - 20), scene.t + i, min(3, n))
    stains(gfx, 20, WALL_END + 8, 600, 40, dirt["chao_salao"] * 2, 5)
    stains(gfx, 20, KITCHEN_FLOOR_Y + 2, 600, 14, dirt["chao_cozinha"] * 2, 9, "#4a3a2a")
    for name in ("chapa", "fritadeira"):
        n = dirt[name]
        if n and name in names:
            x, y, w, h = station_rect(names, name)
            stains(gfx, x + 8, y + 20, w - 16, h - 40, n * 2, len(name), "#a08a30")


def cleaning_focus_rect(cleaning, names):
    layer, index = cleaning.layer, cleaning.index[cleaning.layer]
    key = cleaning.layout[layer][index][0]
    if key.startswith("mesa"):
        return table_rect(int(key[4:]) - 1)
    if key == "chao_salao":
        return (6, WALL_END + 4, W - 12, 52)
    if key == "chao_cozinha":
        return (6, KITCHEN_FLOOR_Y - 2, W - 12, BOTTOM - KITCHEN_FLOOR_Y)
    station = {"louca": "pia", "lixo": "lixeira"}.get(key, key)
    return station_focus(names, station)


def draw_cleaning_hand(gfx, cleaning, rect, t):
    x, y, w, h = rect
    cx, cy = x + w / 2, y + h / 2
    if cleaning.spinning:
        a = cleaning.spinner.angle or 0.0
        sx, sy = cx + 26 * math.cos(a), cy - 18 * math.sin(a)
        gfx.rect(sx - 13, sy - 9, 26, 18, OUTLINE)
        gfx.rect(sx - 11, sy - 7, 22, 14, "#ffe04a" if cleaning.spinning == "lavar" else "#c0c8d0")
        gfx.rect(sx - 11, sy - 7, 22, 5, "#3cb45a" if cleaning.spinning == "lavar" else "#8a96a0")
    elif cleaning.scrubbing:
        sx = cx + (20 if cleaning.last_side == 1 else -20)
        gfx.rect(sx - 14, cy - 8, 28, 16, OUTLINE)
        gfx.rect(sx - 12, cy - 6, 24, 12, "#5ab4ff")


# --- menus ----------------------------------------------------------------------------
def draw_menu(gfx, fonts, menu, top=56, bottom=412):
    x, w = 48, W - 96
    bottom = min(bottom, top + 58 + 30 * len(menu.items))
    rows = max(3, (bottom - top - 50) // 30)
    gfx.rect(x - 3, top - 3, w + 6, bottom - top + 6, OUTLINE)
    gfx.rect(x, top, w, bottom - top, PANEL)
    gfx.text(fit(gfx, menu.title, fonts.big, w - 24), x + 12, top + 10, font=fonts.big, color=FOCUS)
    first = max(0, min(menu.index - rows // 2, len(menu.items) - rows))
    for k, item in enumerate(menu.items[first:first + rows]):
        i = first + k
        y = top + 46 + k * 30
        if i == menu.index:
            gfx.rect(x + 6, y - 3, w - 12, 28, FOCUS)
            color = OUTLINE
        else:
            color = TEXT
        gfx.text(fit(gfx, item, fonts.normal, w - 30), x + 14, y, font=fonts.normal, color=color)
    if first > 0:
        gfx.polygon([(x + w - 24, top + 44), (x + w - 14, top + 44), (x + w - 19, top + 36)], TEXT)
    if first + rows < len(menu.items):
        gfx.polygon([(x + w - 24, bottom - 14), (x + w - 14, bottom - 14),
                     (x + w - 19, bottom - 6)], TEXT)


def draw_storefront(gfx, sheet, fonts, t):
    """A tela de título: a fachada da lanchonete."""
    gfx.rect(0, 0, W, H, "#8fd0ff")
    gfx.circle(560, 60, 30, "#fff07a")
    for k, cx in enumerate((60, 610)):
        gfx.circle(cx + 10 * math.sin(t * 0.3 + k), 40 + k * 30, 16, "#ffffff")
        gfx.circle(cx + 18 + 10 * math.sin(t * 0.3 + k), 36 + k * 30, 20, "#ffffff")
    gfx.rect(0, 240, W, 240, "#7a7a80")
    gfx.rect(0, 236, W, 8, "#c8c8cc")
    gfx.rect(120, 60, 400, 180, "#f3c6d2")
    for k in range(10):
        gfx.rect(110 + k * 42, 96, 42, 26, "#d6455a" if k % 2 == 0 else "#ffffff")
    gfx.rect(150, 66, 340, 30, BAR)
    gfx.text("Comes e Bebes", 320, 68, font=fonts.big, color=FOCUS, align="center")
    gfx.rect(146, 126, 158, 88, WOOD_DARK)
    gfx.rect(150, 130, 150, 80, "#a8dcf0")
    gfx.rect(150, 196, 150, 14, WOOD)
    for k, kind in enumerate(("cafezinho", "xburger", "suco", "coxinha")):
        draw_icon(gfx, sheet, kind, 156 + k * 36, 164 - 3 * abs(math.sin(t * 2 + k)))
    gfx.rect(340, 130, 70, 110, WOOD)
    gfx.rect(348, 140, 54, 40, "#a8dcf0")
    gfx.circle(398, 196, 4, FOCUS)
    for px in (316, 424):
        gfx.rect(px, 214, 22, 24, "#c0603a")
        gfx.circle(px + 11, 206, 12, "#3a9a4a")
        gfx.circle(px + 6, 200, 4, "#ff6fa0")


# --- quadro ----------------------------------------------------------------------------
def draw_house(gfx, sheet, fonts, scene):
    night = scene.phase == "limpeza"
    draw_salao_back(gfx, scene, night)
    names = kitchen_layout(scene)
    draw_kitchen_back(gfx)
    if night and scene.cleaning is not None:
        for i, cx in enumerate(TABLE_X):
            draw_table(gfx, cx)
            gfx.text("Mesa %d" % (i + 1), cx, TABLE_Y + 50, font=fonts.small, color=TEXT,
                     align="center")
    else:
        draw_tables(gfx, sheet, fonts, scene)
    for name in names:
        draw_station(gfx, sheet, fonts, scene, names, name)
    if night and scene.casa is not None:
        draw_dirt(gfx, scene, names)
    service = scene.service
    if service is not None and scene.menu is None:
        if service.layer == 0:
            rect = table_rect(service.index[0])
        else:
            rect = station_focus(names, names[service.index[1]])
        focus_box(gfx, *rect, t=scene.t)
    if scene.cleaning is not None and scene.menu is None:
        rect = cleaning_focus_rect(scene.cleaning, names)
        focus_box(gfx, *rect, t=scene.t)
        draw_cleaning_hand(gfx, scene.cleaning, rect, scene.t)


def draw_frame(gfx, sheet, fonts, scene):
    if scene.casa is None:
        draw_storefront(gfx, sheet, fonts, scene.t)
        if scene.menu is not None:
            draw_menu(gfx, fonts, scene.menu, top=250, bottom=412)
    else:
        gfx.clear("#000000")
        draw_house(gfx, sheet, fonts, scene)
        draw_top(gfx, fonts, scene)
        if scene.menu is not None:
            draw_menu(gfx, fonts, scene.menu)
    draw_bottom(gfx, sheet, fonts, scene)


# --- ligação com o jogo ------------------------------------------------------------------
def read_setting(key):
    try:
        with open(os.environ.get("A11Y_SISTEMA_CONF", "/opt/a11y/etc/sistema.conf")) as f:
            for line in f:
                k, sep, value = line.strip().partition("=")
                if sep and k == key:
                    return value.strip("'\"")
    except OSError:
        pass
    return None


def screen_on():
    if os.environ.get("A11Y_GRAPHICS") == "0":
        return False
    return read_setting("SCREEN") != "0"


def frame_interval():
    """15 quadros por segundo; menos na economia de energia."""
    return {"moderate": 0.1, "aggressive": 0.2}.get(read_setting("ENERGY"), 1 / 15.0)


class Renderer:
    """Desenha em on_update, no ritmo de frame_interval. Uma falha de vídeo só
    desliga os gráficos: o jogo segue pelo som."""

    def __init__(self, game, get_scene, graphics=None):
        self.game = game
        self.get_scene = get_scene        # get_scene() -> Scene sem menu nem legenda
        self.graphics = graphics          # para os testes: fábrica de gráficos
        self.caption = ""
        self._say = game.say
        game.say = self.say               # a legenda é sempre a última fala
        self.gfx = None
        self.sheet = None
        self.fonts = None
        self.failed = False
        self.enabled = False
        self.interval = 1 / 15.0
        self.due = 0.0
        self.checked = -1.0
        self.started = time.monotonic()
        game.on_update(self.update)
        game.on_quit(self.close)

    def say(self, text, queue=False, on_done=None):
        self.caption = (self.caption + " " + text) if queue and self.caption else text
        self.caption = self.caption[-400:]
        return self._say(text, queue=queue, on_done=on_done)

    def menu(self):
        focus = getattr(self.game, "_focus", [])
        return focus[-1] if focus else None

    def open(self):
        if self.graphics is not None:
            gfx = self.graphics()
        else:
            from r36s_a11y.graphics import Graphics
            gfx = Graphics("Comes e Bebes", self.game.dir)
        if not gfx.open():
            self.failed = True
            return False
        self.gfx = gfx
        self.sheet = gfx.image(SHEET)
        self.fonts = Fonts(gfx)
        return True

    def close(self):
        if self.gfx is not None and self.gfx.available:
            self.gfx.close()
        self.gfx = None

    def update(self, dt):
        now = time.monotonic()
        if now - self.checked >= 0.5:
            self.checked = now
            self.enabled = screen_on()
            self.interval = frame_interval()
            if not self.enabled:
                self.close()
        if not self.enabled or self.failed:
            return
        self.due += dt
        if self.due < self.interval:
            return
        self.due = 0.0
        try:
            if self.gfx is None and not self.open():
                return
            scene = self.get_scene()
            scene.menu = self.menu()
            scene.caption = self.caption
            scene.t = now - self.started
            self.gfx.begin()
            draw_frame(self.gfx, self.sheet, self.fonts, scene)
            self.gfx.end()
        except Exception as exc:   # gráfico com defeito não pode derrubar o jogo
            print("[comes] gráficos desligados: %s" % exc)
            self.failed = True
            self.close()
