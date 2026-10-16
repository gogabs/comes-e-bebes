"""Ingredientes, receitas, montagens e estações."""

# --- ingredientes -------------------------------------------------------------
# chave: (nome, nome no plural ou da unidade, tamanho do pacote, preço do pacote, dias até estragar)
INGREDIENTS = {
    "pao": ("pão", "pães", 10, 6, 3),
    "presunto": ("presunto", "fatias de presunto", 10, 7, 4),
    "queijo": ("queijo", "fatias de queijo", 10, 8, 5),
    "carne": ("carne", "hambúrgueres", 6, 15, 3),
    "batata": ("batata", "porções de batata", 8, 8, 10),
    "sal": ("sal", "pitadas de sal", 40, 2, 999),
    "laranja": ("laranja", "laranjas", 8, 6, 5),
    "manteiga": ("manteiga", "porções de manteiga", 20, 6, 10),
    "mexerica": ("mexerica", "mexericas", 8, 5, 5),
}
INGREDIENT_ORDER = ("pao", "presunto", "queijo", "carne", "batata", "sal", "laranja",
                    "manteiga", "mexerica")
# Ingredientes que só aparecem nas compras em algumas estações (índices de SEASONS).
INGREDIENT_SEASONS = {"mexerica": (2,)}

# Estoque do começo do jogo: pacotes de cada ingrediente.
START_PACKS = {"pao": 1, "presunto": 1, "queijo": 1, "carne": 1, "batata": 1, "sal": 1,
               "laranja": 1}

# --- o que vai nas mãos -------------------------------------------------------
ITEM_NAMES = {
    "misto_montado": "misto montado",
    "hamburguer_cru": "hambúrguer cru",
    "hamburguer": "hambúrguer grelhado",
    "batata_crua": "porção de batata crua",
    "fritas_sem_sal": "batata frita sem sal",
    "laranja_cortada": "laranjas cortadas",
    "misto": "misto quente",
    "xburger": "X-burger",
    "fritas": "batata frita",
    "suco": "suco de laranja",
    "pao_manteiga": "pão com manteiga",
    "pao_chapa": "pão na chapa",
    "mexerica_descascada": "mexericas descascadas",
    "suco_mexerica": "suco de mexerica",
    "queimado": "comida queimada",
    "louca": "louça suja",
}

# --- receitas do cardápio -----------------------------------------------------
# chave: (nome, preço justo, ingredientes que gasta)
RECIPES = {
    "misto": ("Misto quente", 8, ("pao", "presunto", "queijo")),
    "xburger": ("X-burger", 14, ("pao", "carne", "queijo")),
    "fritas": ("Batata frita", 10, ("batata", "sal")),
    "suco": ("Suco de laranja", 6, ("laranja",)),
    "pao_chapa": ("Pão na chapa", 5, ("pao", "manteiga")),
    "suco_mexerica": ("Suco de mexerica", 7, ("mexerica",)),
}
RECIPE_ORDER = ("misto", "xburger", "fritas", "suco", "pao_chapa", "suco_mexerica")
BASE_RECIPES = ("misto", "xburger", "fritas", "suco")
# Receitas que a casa aprende quando a estação chega pela primeira vez.
SEASON_RECIPES = {2: ("pao_chapa", "suco_mexerica")}
# Como é falado num pedido: (um ou uma, singular, plural).
ORDER_WORDS = {
    "misto": ("um", "misto quente", "mistos quentes"),
    "xburger": ("um", "X-burger", "X-burgers"),
    "fritas": ("uma", "batata frita", "batatas fritas"),
    "suco": ("um", "suco de laranja", "sucos de laranja"),
    "pao_chapa": ("um", "pão na chapa", "pães na chapa"),
    "suco_mexerica": ("um", "suco de mexerica", "sucos de mexerica"),
}

# Bancada: o que junta vira o quê. As partes podem ser ingredientes do estoque
# ou coisas que estão nas mãos.
ASSEMBLY = (
    (frozenset(("pao", "presunto", "queijo")), "misto_montado"),
    (frozenset(("carne",)), "hamburguer_cru"),
    (frozenset(("pao", "hamburguer", "queijo")), "xburger"),
    (frozenset(("batata",)), "batata_crua"),
    (frozenset(("fritas_sem_sal", "sal")), "fritas"),
    (frozenset(("laranja",)), "laranja_cortada"),
    (frozenset(("pao", "manteiga")), "pao_manteiga"),
    (frozenset(("mexerica",)), "mexerica_descascada"),
)

# Fogo: o que entra cru e sai pronto, e o nome curto usado nas falas.
COOKED = {"hamburguer_cru": "hamburguer", "misto_montado": "misto",
          "batata_crua": "fritas_sem_sal", "pao_manteiga": "pao_chapa"}
COOK_SHORT = {"hamburguer_cru": "hambúrguer", "misto_montado": "misto",
              "batata_crua": "batata", "pao_manteiga": "pão"}
# Precisa virar (chapa) ou sacudir (fritadeira) no meio.
TURN = {"misto_montado": "virar", "batata_crua": "sacudir", "pao_manteiga": "virar"}
STATION_ACCEPTS = {"chapa": ("hamburguer_cru", "misto_montado", "pao_manteiga"),
                   "fritadeira": ("batata_crua",)}

# Liquidificador: fruta preparada -> (suco, como a fruta é falada).
BLENDS = {"laranja_cortada": ("suco", "laranjas"),
          "mexerica_descascada": ("suco_mexerica", "mexericas")}

# --- estações -----------------------------------------------------------------
SEASONS = ("Primavera", "Verão", "Outono", "Inverno")

# Peso de cada receita nos pedidos, por estação. Acima de 1.4 é "da estação".
PREFERENCES = (
    {"misto": 1.0, "xburger": 1.0, "fritas": 1.0, "suco": 1.6, "pao_chapa": 0.8,
     "suco_mexerica": 1.0},
    {"misto": 0.6, "xburger": 1.0, "fritas": 1.5, "suco": 2.5, "pao_chapa": 0.4,
     "suco_mexerica": 1.0},
    {"misto": 1.5, "xburger": 1.1, "fritas": 0.9, "suco": 0.6, "pao_chapa": 2.0,
     "suco_mexerica": 2.0},
    {"misto": 2.0, "xburger": 1.5, "fritas": 1.0, "suco": 0.4, "pao_chapa": 1.6,
     "suco_mexerica": 0.6},
)
IN_SEASON = 1.4
IN_SEASON_TIP = 1.3

# Clima: (chave, como é falado, movimento, paciência, pesos por estação).
WEATHER = (
    ("sol", "sol", 1.0, 1.0, (5, 4, 4, 3)),
    ("calor", "calor forte", 1.1, 0.9, (1, 4, 0, 0)),
    ("nublado", "céu nublado", 0.95, 1.0, (3, 2, 4, 4)),
    ("chuva", "chuva", 0.7, 1.15, (2, 3, 3, 3)),
    ("frio", "frio", 0.9, 1.0, (0, 0, 1, 4)),
    ("vento", "vento frio, com folhas voando na calçada", 0.9, 1.05, (1, 0, 4, 1)),
)

# O que cada estação traz: a fala de chegada, o som de fundo do expediente e
# as datas especiais {dia: (nome, movimento, chance de pedir dois, gorjeta, fala)}.
SEASON_INFO = (
    {"arrival": "Chegou a primavera.", "ambient": None, "special": {}},
    {"arrival": "Chegou o verão: calor, suco gelado e batata frita.", "ambient": None,
     "special": {}},
    {"arrival": "Chegou o outono. O vento esfriou, as folhas caem na calçada e os "
                "fregueses querem coisa quentinha. A casa aprendeu duas receitas: pão na "
                "chapa, com pão e manteiga na bancada e virando na chapa, e suco de "
                "mexerica, a fruta da estação, que só aparece nas compras no outono.",
     "ambient": "outono",
     "special": {12: ("Dia das Mães", 1.5, 0.8, 1.5,
                      "Hoje é Dia das Mães: a casa vai encher de famílias, que pedem mais e "
                      "deixam gorjetas maiores.")}},
    {"arrival": "Chegou o inverno.", "ambient": None, "special": {}},
)


def weather(key):
    for w in WEATHER:
        if w[0] == key:
            return w
    return WEATHER[0]


def item_name(kind):
    return ITEM_NAMES.get(kind, kind)


def recipe_name(key):
    return RECIPES[key][0]


def order_text(keys):
    """["suco", "fritas", "suco"] -> "dois sucos de laranja e uma batata frita"."""
    counts = []
    for k in keys:
        if k not in [c for c, _ in counts]:
            counts.append((k, keys.count(k)))
    words = []
    for k, n in counts:
        article, one, many = ORDER_WORDS[k]
        if n == 1:
            words.append("%s %s" % (article, one))
        else:
            number = {2: "dois", 3: "três"}.get(n, str(n))
            if article == "uma" and n == 2:
                number = "duas"
            words.append("%s %s" % (number, many))
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " e " + words[-1]


def assemble(parts):
    """O que a bancada faz com essas partes, ou None."""
    found = frozenset(parts)
    for need, product in ASSEMBLY:
        if need == found:
            return product
    return None
