"""Números do equilíbrio do jogo, num lugar só.

Tempos em segundos reais, na velocidade Normal. A velocidade escolhida no
menu multiplica a paciência dos clientes, as janelas do fogo e o intervalo
entre clientes.
"""

# Velocidades: (nome, multiplicador das janelas de tempo).
SPEEDS = (("Tranquilo", 1.5), ("Normal", 1.0), ("Corrido", 0.7))
DEFAULT_SPEED = "Normal"

# --- calendário ---------------------------------------------------------------
DAYS_PER_SEASON = 28
FIRST_SEASON = 1              # o protótipo começa no Verão

# --- expediente ---------------------------------------------------------------
OPEN_HOUR = 10
CLOSE_HOUR = 18
DAY_SECONDS = 360             # do abrir ao fechar a porta, em segundos reais
TABLES = 3

FIRST_ARRIVAL = 6.0
ARRIVAL_INTERVAL = (22.0, 40.0)
CALL_DELAY = (2.0, 4.0)       # sentou -> chama para pedir
EAT_TIME = (14.0, 22.0)
TWO_ITEMS_CHANCE = 0.35

PATIENCE_ORDER = 60.0         # esperando para pedir
PATIENCE_FOOD = 110.0         # esperando a comida
PATIENCE_PAY = 45.0           # esperando para pagar
IMPATIENCE_STAGES = (0.5, 0.25, 0.1)   # fração da paciência que sobra
FIRE_PATIENCE_DRAIN = 2.0     # com fogo na cozinha, a paciência cai mais rápido
FLIES_PATIENCE = 0.85         # casa suja de ontem: clientes menos pacientes
HOT_PATIENCE = 0.9            # dia de calor

HANDS = 2

# Fogo e ponto: (até o ponto, janela no ponto, passando, queimado até pegar fogo).
COOK = {
    "hamburguer_cru": (14.0, 7.0, 8.0, 10.0),
    "misto_montado": (12.0, 7.0, 8.0, 10.0),
    "batata_crua": (16.0, 7.0, 8.0, 10.0),
    "pao_manteiga": (8.0, 6.0, 7.0, 10.0),
}
CHAPA_SLOTS = 2
FRITADEIRA_SLOTS = 1
# Virar o misto e sacudir a batata: janela em fração do tempo até o ponto.
TURN_WINDOW = (0.35, 1.0)
MISSED_TURN_QUALITY = 0.7     # misto que não foi virado
PASSING_QUALITY = 0.6         # tirado passando do ponto

BLEND_MIN = 2.5               # segurar B no liquidificador até ficar liso
BLEND_MAX = 5.0               # depois disso o suco esquenta
WARM_JUICE_QUALITY = 0.6

FIRE_SPREAD = 20.0            # fogo sem apagar passa para a estação vizinha
EXTINGUISH_TIME = 2.0

# --- dinheiro -----------------------------------------------------------------
START_MONEY = 60
START_REPUTATION = 2.5
# Faixas de preço: (nome, preço, movimento, paciência, gorjeta).
PRICE_TIERS = (
    ("Muito barato", 0.6, 1.4, 1.15, 1.2),
    ("Barato", 0.8, 1.2, 1.05, 1.1),
    ("Justo", 1.0, 1.0, 1.0, 1.0),
    ("Caro", 1.25, 0.8, 0.9, 0.85),
    ("Muito caro", 1.5, 0.6, 0.8, 0.7),
)
DEFAULT_TIER = 2
TIP_MAX = 0.3                 # gorjeta máxima, em fração da conta

# Reputação ganha ou perdida por cliente.
REP_HAPPY = 0.03
REP_OK = 0.01
REP_LEFT = -0.12
REP_FIRE = -0.1
REP_NOTHING = -0.03           # cliente que não achou nada para pedir
REP_INSPECTION_OK = 0.2

# --- limpeza e vigilância -----------------------------------------------------
DIRT_CLEAN = 2                # sobra de sujeira até aqui conta como casa limpa
DIRT_DIRTY = 8                # acima disso, a casa dormiu suja
COMMENTS_AFTER = 2            # noites sujas seguidas até os clientes comentarem
LETTER_AFTER = 3              # ... até a carta da vigilância
INSPECTION_WITHIN = (1, 3)    # a visita vem entre 1 e 3 dias depois da carta
INSPECTION_TIME = (0.2, 0.7)  # em que parte do expediente a visita chega

SCRUB_STROKES = 4             # esfregadas (esquerda e direita) por unidade de sujeira
SCRAPE_TIME = 1.2             # segundos segurando B por unidade de gordura
WASH_TIME = 0.4               # entre um prato lavado e outro
TRASH_TIME = 2.5              # levar o lixo para fora
AMBIENT_EVERY = 2.5           # um som de sujeira a cada tanto, na limpeza
AMBIENT_VOLUME = 0.25         # som de fundo da estação, no expediente

# Distância dos sons (metros): mesas à frente, cozinha atrás.
SALAO_Z = -3.0
COZINHA_Z = 2.0
SPREAD_X = 4.0                # largura do arco, da esquerda à direita
