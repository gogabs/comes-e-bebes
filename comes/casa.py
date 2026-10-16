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

    def __init__(self, season=C.FIRST_SEASON):
        self.year = 1
        self.season = season
        self.day = 1
        self.money = C.START_MONEY
        self.reputation = C.START_REPUTATION
        self.stock = {k: [] for k in D.INGREDIENTS}          # lotes [quantidade, dias]
        for k, packs in D.START_PACKS.items():
            for _ in range(packs):
                self._add_lot(k)
        self.learned = list(D.BASE_RECIPES)
        self.equipment = []
        self.menu = {k: k in self.learned for k in D.RECIPE_ORDER}
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

    def can_buy(self, key):
        """Fruta da estação só aparece nas compras na estação dela."""
        seasons = D.INGREDIENT_SEASONS.get(key)
        return seasons is None or self.season in seasons

    def shop_keys(self):
        """O que aparece nas compras: só o que as receitas conhecidas usam."""
        used = set(k for r in self.known_recipes() for k in D.RECIPES[r][2])
        return [k for k in D.INGREDIENT_ORDER if k in used and self.can_buy(k)]

    def buy(self, key):
        if not self.can_buy(key):
            return False
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
        if key in D.INGREDIENT_SEASONS:
            text = text.replace(":", ", da estação:", 1)
        if lots and days < 999:
            soon = min(d for _, d in lots)
            text += ", estraga em %d %s" % (soon, "dia" if soon == 1 else "dias")
        return text + ". Pacote com %d %s por %s" % (size, plural, money(price))

    # --- lojinha -------------------------------------------------------
    def buy_equipment(self, key):
        """Compra um equipamento. Devolve a fala, ou None se não deu."""
        name, price, _, recipes, gift = D.EQUIPMENT[key]
        if key in self.equipment or self.money < price:
            return None
        self.money -= price
        self.spent_today += price
        self.equipment.append(key)
        for k in recipes:
            if k not in self.learned:
                self.learned.append(k)
                self.menu[k] = True
        text = "Comprou a %s. %s entrou no cardápio." % (
            name.lower(), " e ".join(D.recipe_name(k) for k in recipes))
        if gift and self.count(gift) == 0:
            self._add_lot(gift)
            text += " De presente da loja: um pacote de %s." % D.INGREDIENTS[gift][0]
        return text

    # --- preços ----------------------------------------------------------
    def price(self, recipe):
        return int(round(D.RECIPES[recipe][1] * C.PRICE_TIERS[self.prices[recipe]][1]))

    def tier(self, recipe):
        return C.PRICE_TIERS[self.prices[recipe]]

    def known_recipes(self):
        return [k for k in D.RECIPE_ORDER if k in self.learned]

    def active_menu(self):
        return [k for k in self.known_recipes() if self.menu.get(k)]

    def special(self):
        """A data especial de hoje, ou None: (nome, movimento, dois itens, gorjeta, fala)."""
        return D.SEASON_INFO[self.season]["special"].get(self.day)

    def arrival_factor(self):
        """Movimento do dia: preços, reputação e clima juntos."""
        menu = self.active_menu() or list(D.RECIPE_ORDER)
        prices = sum(self.tier(k)[2] for k in menu) / len(menu)
        rep = 0.6 + 0.16 * self.reputation           # 2,5 estrelas -> 1,0
        special = self.special()
        return prices * rep * D.weather(self.weather)[2] * (special[1] if special else 1.0)

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
        if self.day == 1:
            lines.append(D.SEASON_INFO[self.season]["arrival"])
            gifts = []
            for k in D.SEASON_RECIPES.get(self.season, ()):
                if k not in self.learned:
                    self.learned.append(k)
                    self.menu[k] = True
                    for ing in D.RECIPES[k][2]:
                        if self.count(ing) == 0 and self.can_buy(ing):
                            self._add_lot(ing)
                            gifts.append(D.INGREDIENTS[ing][0])
            if gifts:
                gifts = ["um de %s" % g for g in gifts]
                gifts[0] = "um pacote de" + gifts[0][5:]
                text = gifts[0] if len(gifts) == 1 else "%s e %s" % (", ".join(gifts[:-1]),
                                                                     gifts[-1])
                lines.append("De presente do fornecedor, para começar: %s." % text)
        special = self.special()
        if special:
            lines.append(special[4])
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
        new_recipes = [k for k in D.RECIPE_ORDER if k not in data.get("menu", {})]
        for key, value in data.items():
            if key != "versao" and key in casa.__dict__:
                setattr(casa, key, copy.deepcopy(value))
        # Saves de versões com menos receitas e ingredientes.
        for k in D.INGREDIENTS:
            casa.stock.setdefault(k, [])
        for k in D.RECIPE_ORDER:
            casa.menu.setdefault(k, False)
            casa.prices.setdefault(k, C.DEFAULT_TIER)
        for k in DIRT_KEYS:
            casa.dirt.setdefault(k, 0)
        if "learned" not in data:
            casa.learned = list(D.BASE_RECIPES) + [k for k in D.RECIPE_ORDER
                                                   if k not in D.BASE_RECIPES and casa.menu[k]]
        # Receitas básicas que chegaram numa versão nova entram no cardápio.
        for k in D.BASE_RECIPES:
            if k not in casa.learned:
                casa.learned.append(k)
                if k in new_recipes:
                    casa.menu[k] = True
        if casa.checkpoint is None:
            casa.save_checkpoint()
        return casa
