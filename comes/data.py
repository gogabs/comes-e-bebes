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
    "leite": ("leite", "copos de leite", 10, 7, 4),
    "chocolate": ("chocolate", "colheres de chocolate", 20, 9, 30),
    "frango": ("frango desfiado", "porções de frango desfiado", 8, 12, 3),
    "alface": ("alface", "folhas de alface", 12, 4, 3),
    "morango": ("morango", "porções de morango", 8, 8, 4),
    "massa": ("massa de pastel", "discos de massa", 10, 6, 5),
    "coxinha": ("coxinha congelada", "coxinhas congeladas", 10, 12, 20),
    "cafe": ("café em grão", "doses de café", 20, 10, 30),
}
INGREDIENT_ORDER = ("pao", "presunto", "queijo", "carne", "batata", "sal", "laranja",
                    "manteiga", "mexerica", "leite", "chocolate", "frango", "alface", "morango",
                    "massa", "coxinha", "cafe")
# Ingredientes que só aparecem nas compras em algumas estações (índices de SEASONS).
INGREDIENT_SEASONS = {"mexerica": (2,), "morango": (0,)}

# Estoque do começo do jogo: pacotes de cada ingrediente.
START_PACKS = {"pao": 1, "presunto": 1, "queijo": 1, "carne": 1, "batata": 1, "sal": 1,
               "laranja": 1, "massa": 1, "coxinha": 1}

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
    "queijo_montado": "queijo quente montado",
    "queijo_quente": "queijo quente",
    "leite_chocolate": "leite com chocolate",
    "chocolate_quente": "chocolate quente",
    "sanduiche_natural": "sanduíche natural",
    "morango_leite": "morango com leite",
    "vitamina_morango": "vitamina de morango",
    "pastel_cru": "pastel cru",
    "pastel": "pastel de queijo",
    "coxinha_crua": "coxinha para fritar",
    "coxinha": "coxinha",
    "cafezinho": "cafezinho",
    "queimado": "comida queimada",
    "louca": "louça suja",
}

# --- receitas do cardápio -----------------------------------------------------
# chave: (nome, preço justo, ingredientes que gasta)
RECIPES = {
    "misto": ("Misto quente", 8, ("pao", "presunto", "queijo")),
    "xburger": ("X-burger", 14, ("pao", "carne", "queijo")),
    "fritas": ("Batata frita", 10, ("batata", "sal")),
    "pastel": ("Pastel de queijo", 9, ("massa", "queijo")),
    "coxinha": ("Coxinha", 6, ("coxinha",)),
    "suco": ("Suco de laranja", 6, ("laranja",)),
    "pao_chapa": ("Pão na chapa", 5, ("pao", "manteiga")),
    "suco_mexerica": ("Suco de mexerica", 7, ("mexerica",)),
    "queijo_quente": ("Queijo quente", 7, ("pao", "queijo")),
    "chocolate_quente": ("Chocolate quente", 8, ("leite", "chocolate")),
    "sanduiche_natural": ("Sanduíche natural", 12, ("pao", "frango", "alface")),
    "vitamina_morango": ("Vitamina de morango", 9, ("morango", "leite")),
    "cafezinho": ("Cafezinho", 4, ("cafe",)),
}
RECIPE_ORDER = ("misto", "xburger", "fritas", "pastel", "coxinha", "suco", "pao_chapa",
                "suco_mexerica", "queijo_quente", "chocolate_quente", "sanduiche_natural",
                "vitamina_morango", "cafezinho")
BASE_RECIPES = ("misto", "xburger", "fritas", "pastel", "coxinha", "suco")
# Receitas que a casa aprende quando a estação chega pela primeira vez.
SEASON_RECIPES = {0: ("sanduiche_natural", "vitamina_morango"),
                  2: ("pao_chapa", "suco_mexerica"),
                  3: ("queijo_quente", "chocolate_quente")}
# Como é falado num pedido: (um ou uma, singular, plural).
ORDER_WORDS = {
    "misto": ("um", "misto quente", "mistos quentes"),
    "xburger": ("um", "X-burger", "X-burgers"),
    "fritas": ("uma", "batata frita", "batatas fritas"),
    "pastel": ("um", "pastel de queijo", "pastéis de queijo"),
    "coxinha": ("uma", "coxinha", "coxinhas"),
    "cafezinho": ("um", "cafezinho", "cafezinhos"),
    "suco": ("um", "suco de laranja", "sucos de laranja"),
    "pao_chapa": ("um", "pão na chapa", "pães na chapa"),
    "suco_mexerica": ("um", "suco de mexerica", "sucos de mexerica"),
    "queijo_quente": ("um", "queijo quente", "queijos quentes"),
    "chocolate_quente": ("um", "chocolate quente", "chocolates quentes"),
    "sanduiche_natural": ("um", "sanduíche natural", "sanduíches naturais"),
    "vitamina_morango": ("uma", "vitamina de morango", "vitaminas de morango"),
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
    (frozenset(("pao", "queijo")), "queijo_montado"),
    (frozenset(("leite", "chocolate")), "leite_chocolate"),
    (frozenset(("pao", "frango", "alface")), "sanduiche_natural"),
    (frozenset(("morango", "leite")), "morango_leite"),
    (frozenset(("massa", "queijo")), "pastel_cru"),
    (frozenset(("coxinha",)), "coxinha_crua"),
)

# Fogo: o que entra cru e sai pronto, e o nome curto usado nas falas.
COOKED = {"hamburguer_cru": "hamburguer", "misto_montado": "misto",
          "batata_crua": "fritas_sem_sal", "pao_manteiga": "pao_chapa",
          "queijo_montado": "queijo_quente", "pastel_cru": "pastel",
          "coxinha_crua": "coxinha"}
COOK_SHORT = {"hamburguer_cru": "hambúrguer", "misto_montado": "misto",
              "batata_crua": "batata", "pao_manteiga": "pão", "queijo_montado": "queijo quente",
              "pastel_cru": "pastel", "coxinha_crua": "coxinha"}
# Precisa virar (chapa) ou sacudir (fritadeira) no meio.
TURN = {"misto_montado": "virar", "batata_crua": "sacudir", "pao_manteiga": "virar",
        "queijo_montado": "virar", "pastel_cru": "virar"}
STATION_ACCEPTS = {"chapa": ("hamburguer_cru", "misto_montado", "pao_manteiga",
                             "queijo_montado"),
                   "fritadeira": ("batata_crua", "pastel_cru", "coxinha_crua")}

# Liquidificador: o que foi preparado na bancada -> (bebida, como é falado,
# o que acontece quando bate demais).
BLENDS = {"laranja_cortada": ("suco", "laranjas", "esquentou um pouco"),
          "mexerica_descascada": ("suco_mexerica", "mexericas", "esquentou um pouco"),
          "leite_chocolate": ("chocolate_quente", "leite com chocolate", "espumou demais"),
          "morango_leite": ("vitamina_morango", "morango com leite", "esquentou um pouco")}

# --- lojinha -----------------------------------------------------------------
# Equipamentos que a casa compra na abertura:
# chave: (nome, preço, descrição falada, receitas que libera, ingrediente de presente).
EQUIPMENT = {
    "cafeteira": ("Cafeteira", 250,
                  "Mói o grão e passa o cafezinho na hora. Fica no fim da cozinha, depois da "
                  "lixeira, e põe o cafezinho no cardápio.",
                  ("cafezinho",), "cafe"),
}
EQUIPMENT_ORDER = ("cafeteira",)

# --- estações -----------------------------------------------------------------
SEASONS = ("Primavera", "Verão", "Outono", "Inverno")

# Peso de cada receita nos pedidos, por estação. Acima de 1.4 é "da estação".
PREFERENCES = (
    {"misto": 1.0, "xburger": 1.0, "fritas": 1.0, "suco": 1.6, "pao_chapa": 0.8,
     "suco_mexerica": 0.8, "queijo_quente": 0.8, "chocolate_quente": 0.6,
     "sanduiche_natural": 2.0, "vitamina_morango": 2.0,
     "pastel": 1.2, "coxinha": 1.0, "cafezinho": 1.0},
    {"misto": 0.6, "xburger": 1.0, "fritas": 1.5, "suco": 2.5, "pao_chapa": 0.4,
     "suco_mexerica": 1.0, "queijo_quente": 0.5, "chocolate_quente": 0.2,
     "sanduiche_natural": 1.3, "vitamina_morango": 1.3,
     "pastel": 1.1, "coxinha": 0.9, "cafezinho": 0.6},
    {"misto": 1.5, "xburger": 1.1, "fritas": 0.9, "suco": 0.6, "pao_chapa": 2.0,
     "suco_mexerica": 2.0, "queijo_quente": 1.5, "chocolate_quente": 1.3,
     "sanduiche_natural": 0.8, "vitamina_morango": 0.8,
     "pastel": 1.0, "coxinha": 1.2, "cafezinho": 1.6},
    {"misto": 2.0, "xburger": 1.5, "fritas": 1.0, "suco": 0.4, "pao_chapa": 1.6,
     "suco_mexerica": 0.6, "queijo_quente": 2.0, "chocolate_quente": 2.5,
     "sanduiche_natural": 0.5, "vitamina_morango": 0.4,
     "pastel": 1.0, "coxinha": 1.3, "cafezinho": 2.2},
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
    {"arrival": "Chegou a primavera. Os passarinhos voltaram, o dia ficou mais leve e os "
                "fregueses querem coisa fresca. A casa aprendeu duas receitas: sanduíche "
                "natural, com pão, frango desfiado e alface na bancada, e vitamina de "
                "morango, com morango e leite na bancada, batida no liquidificador. O morango "
                "é a fruta da estação e só aparece nas compras na primavera.",
     "ambient": "primavera",
     "special": {21: ("Dia das Crianças", 1.5, 0.7, 1.3,
                      "Hoje é Dia das Crianças: a casa vai encher de famílias com a criançada, "
                      "que pede mais e deixa gorjetas maiores.")}},
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
    {"arrival": "Chegou o inverno. Faz frio, a garoa bate no toldo e os fregueses querem "
                "coisa bem quente. A casa aprendeu duas receitas: queijo quente, com pão e "
                "queijo na bancada e virando na chapa, e chocolate quente, com leite e "
                "chocolate na bancada, batido no liquidificador.",
     "ambient": "inverno",
     "special": {3: ("Dia de São João", 1.4, 0.6, 1.3,
                     "Hoje é Dia de São João: tem quadrilha na praça, e o povo passa na casa "
                     "para se esquentar antes e depois da festa.")}},
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
