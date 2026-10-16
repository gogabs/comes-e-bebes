"""A casa entre um dia e outro: dinheiro, estoque, cardápio, calendário e sujeira.

É o que vai para o jogo salvo. Não toca som nem fala: os métodos devolvem os
textos que a abertura e o fechamento leem.
"""
import copy
import random

from . import config as C
from . import data as D

DIRT_KEYS = ("mesa1", "mesa2", "mesa3", "chao_salao", "chao_cozinha", "chapa", "fritadeira",
             "louca", "lixo")


def money(value):
    return "%d reais" % value if value != 1 else "1 real"


def stars(rep):
    """Reputação de 0 a 5, falada em meias estrelas."""
    half = int(round(rep * 2))
    whole, has_half = divmod(half, 2)
    if whole == 0 and has_half:
        return "meia estrela"
    text = "%d %s" % (whole, "estrela" if whole == 1 else "estrelas")
    return text + " e meia" if has_half else text


class Casa:
    SAVE_VERSION = 1

    def __init__(self):
        self.year = 1
        self.season = C.FIRST_SEASON
        self.day = 1
        self.money = C.START_MONEY
        self.reputation = C.START_REPUTATION
        self.stock = {k: [] for k in D.INGREDIENTS}          # lotes [quantidade, dias]
        for k, packs in D.START_PACKS.items():
            for _ in range(packs):
                self._add_lot(k)
        self.menu = {k: True for k in D.RECIPE_ORDER}
        self.prices = {k: C.DEFAULT_TIER for k in D.RECIPE_ORDER}
        self.dirt = {k: 0 for k in DIRT_KEYS}
        self.morning_dirt = 0
        self.dirty_nights = 0
        self.letter = False
        self.inspection_day = None      # número absoluto do dia da visita
        self.weather = "sol"
        self.report = ""
        self.spent_today = 0
        self.checkpoint = None
        self.save_checkpoint()

    # --- calendário ------------------------------------------------------
    @property
    def absolute_day(self):
        return ((self.year - 1) * 4 + self.season) * C.DAYS_PER_SEASON + self.day

    def _prep(self):
        return "da" if self.season == 0 else "do"

    def date_text(self):
        return "Dia %d %s %s, ano %d" % (self.day, self._prep(), D.SEASONS[self.season], self.year)

    def short_date(self):
        return "dia %d %s %s" % (self.day, self._prep(), D.SEASONS[self.season])

    # --- estoque ---------------------------------------------------------
    def _add_lot(self, key):
        _, _, size, _, days = D.INGREDIENTS[key]
        self.stock[key].append([size, days])

    def count(self, key):
        return sum(q for q, _ in self.stock[key])

    def take(self, key, n=1):
        """Gasta n do lote mais velho primeiro. False se não tem."""
        if self.count(key) < n:
            return False
        lots = sorted(self.stock[key], key=lambda lot: lot[1])
        for lot in lots:
            used = min(lot[0], n)
            lot[0] -= used
            n -= used
            if n == 0:
                break
        self.stock[key] = [lot for lot in lots if lot[0] > 0]
        return True

    def buy(self, key):
        price = D.INGREDIENTS[key][3]
        if self.money < price:
            return False
        self.money -= price
        self.spent_today += price
        self._add_lot(key)
        return True

    def can_make(self, recipe):
        return all(self.count(k) > 0 for k in D.RECIPES[recipe][2])

    def stock_text(self, key):
        name, plural, size, price, days = D.INGREDIENTS[key]
        n = self.count(key)
        lots = self.stock[key]
        text = "%s: %d em estoque" % (name.capitalize(), n)
        if lots and days < 999:
            soon = min(d for _, d in lots)
            text += ", estraga em %d %s" % (soon, "dia" if soon == 1 else "dias")
        return text + ". Pacote com %d %s por %s" % (size, plural, money(price))

    # --- preços ----------------------------------------------------------
    def price(self, recipe):
        return int(round(D.RECIPES[recipe][1] * C.PRICE_TIERS[self.prices[recipe]][1]))

    def tier(self, recipe):
        return C.PRICE_TIERS[self.prices[recipe]]

    def active_menu(self):
        return [k for k in D.RECIPE_ORDER if self.menu[k]]

    def arrival_factor(self):
        """Movimento do dia: preços, reputação e clima juntos."""
        menu = self.active_menu() or list(D.RECIPE_ORDER)
        prices = sum(self.tier(k)[2] for k in menu) / len(menu)
        rep = 0.6 + 0.16 * self.reputation           # 2,5 estrelas -> 1,0
        return prices * rep * D.weather(self.weather)[2]

    # --- sujeira e vigilância --------------------------------------------
    def total_dirt(self):
        return sum(self.dirt.values())

    def add_dirt(self, key, n=1):
        self.dirt[key] += n

    @property
    def flies(self):
        """A casa abriu suja hoje: moscas no salão."""
        return self.morning_dirt > C.DIRT_DIRTY

    @property
    def inspection_today(self):
        return self.inspection_day == self.absolute_day

    def inspect(self):
        """A visita da vigilância. True se a casa passou."""
        self.inspection_day = None
        self.letter = False
        if self.morning_dirt > C.DIRT_DIRTY:
            return False
        self.dirty_nights = 0
        self.reputation = min(5.0, self.reputation + C.REP_INSPECTION_OK)
        return True

    # --- o dia -----------------------------------------------------------
    def start_day(self, rng=None):
        """Manhã: estraga o que venceu, sorteia o clima e lê os avisos."""
        rng = rng or random.Random()
        self.spent_today = 0
        self.morning_dirt = self.total_dirt()
        weights = [w[4][self.season] for w in D.WEATHER]
        self.weather = rng.choices([w[0] for w in D.WEATHER], weights)[0]
        lines = ["%s. %s." % (self.date_text(), D.weather(self.weather)[1].capitalize())]
        spoiled = []
        for key in D.INGREDIENT_ORDER:
            lost = sum(q for q, d in self.stock[key] if d <= 0)
            self.stock[key] = [lot for lot in self.stock[key] if lot[1] > 0]
            if lost:
                spoiled.append("%d %s" % (lost, D.INGREDIENTS[key][1] if lost > 1
                                          else D.INGREDIENTS[key][0]))
        if spoiled:
            lines.append("Estragou e foi para o lixo: %s." % ", ".join(spoiled))
        if self.inspection_today:
            pass    # a visita é surpresa
        elif self.letter:
            lines.append("A carta da vigilância sanitária continua em cima do balcão: "
                         "eles voltam nesta semana.")
        elif self.dirty_nights >= C.COMMENTS_AFTER:
            lines.append("Ontem um cliente comentou: vi uma mosca na mesa.")
        if self.morning_dirt > C.DIRT_DIRTY:
            lines.append("A casa abriu suja hoje, e as moscas deixam os clientes impacientes.")
        return lines

    def end_day(self, summary, rng=None):
        """Depois da limpeza: confere a sujeira que sobrou, avança o calendário e
        devolve o relatório do dia."""
        rng = rng or random.Random()
        left = self.total_dirt()
        notes = []
        if left <= C.DIRT_CLEAN:
            self.dirty_nights = 0
            notes.append("A casa ficou limpinha.")
        elif left > C.DIRT_DIRTY:
            self.dirty_nights += 1
            notes.append("Ficou bastante sujeira para amanhã.")
        else:
            notes.append("Ficou um pouco de sujeira para amanhã.")
        if self.dirty_nights >= C.LETTER_AFTER and not self.letter:
            self.letter = True
            self.inspection_day = self.absolute_day + rng.randint(*C.INSPECTION_WITHIN)
            notes.append("Chegou uma carta da vigilância sanitária: vamos voltar nesta "
                         "semana para uma visita.")
        self.report = self.report_text(summary, notes)
        for lots in self.stock.values():
            for lot in lots:
                lot[1] -= 1
        self.day += 1
        if self.day > C.DAYS_PER_SEASON:
            self.day = 1
            self.season += 1
            if self.season >= len(D.SEASONS):
                self.season = 0
                self.year += 1
            self.save_checkpoint()
        return self.report

    def report_text(self, s, notes):
        parts = ["Fim do %s." % self.short_date()]
        served = s.get("served", 0)
        parts.append("%d %s atendidos" % (served, "cliente" if served == 1 else "clientes")
                     + (", %d foram embora sem ser atendidos." % s["left"] if s.get("left")
                        else "."))
        parts.append("Vendas: %s. Gorjetas: %s. Compras: %s." % (
            money(s.get("sales", 0)), money(s.get("tips", 0)), money(self.spent_today)))
        if s.get("fires"):
            parts.append("Teve fogo na cozinha.")
        parts.append("Reputação: %s." % stars(self.reputation))
        parts.extend(notes)
        if s.get("comment"):
            parts.append("Um cliente disse: %s" % s["comment"])
        return " ".join(parts)

    # --- interdição ------------------------------------------------------
    def save_checkpoint(self):
        state = self.to_dict()
        state.pop("checkpoint", None)
        self.checkpoint = state

    def restore_checkpoint(self):
        """A casa interditada volta ao dia 1 da estação, como estava naquele dia."""
        checkpoint = self.checkpoint
        restored = Casa.from_dict(dict(checkpoint, checkpoint=None))
        self.__dict__.update(restored.__dict__)
        self.checkpoint = checkpoint

    # --- jogo salvo ------------------------------------------------------
    def to_dict(self):
        state = copy.deepcopy(self.__dict__)
        state["versao"] = self.SAVE_VERSION
        return state

    @classmethod
    def from_dict(cls, data):
        if data.get("versao") != cls.SAVE_VERSION:
            raise ValueError("versão de save desconhecida")
        casa = cls()
        for key, value in data.items():
            if key != "versao" and key in casa.__dict__:
                setattr(casa, key, copy.deepcopy(value))
        if casa.checkpoint is None:
            casa.save_checkpoint()
        return casa
