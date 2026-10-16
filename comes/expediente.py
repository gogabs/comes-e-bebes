"""O expediente: o salão e a cozinha em tempo real.

Não toca som nem fala direto: tudo passa por `ui`, que tem
    ui.say(texto, queue=False)
    ui.play(nome, spot=None, pitch=1.0)
    ui.loop(chave, nome, spot=None, pitch=1.0)   # começa ou ajusta um som contínuo
    ui.stop(chave)
    ui.open_bancada()                            # abre a lista de ingredientes
`spot` é (camada, índice, quantos na camada): o som sai daquele lugar.
O tempo anda por update(dt), então a partida inteira roda nos testes sem áudio.
"""
import random

from . import config as C
from . import data as D
from .casa import money

SALAO, COZINHA = 0, 1
STATIONS = ("bancada", "chapa", "fritadeira", "liquidificador", "pia", "lixeira")
STATION_NAMES = {"bancada": "Bancada", "chapa": "Chapa", "fritadeira": "Fritadeira",
                 "liquidificador": "Liquidificador", "pia": "Pia", "lixeira": "Lixeira",
                 "cafeteira": "Cafeteira"}
# Equipamentos comprados na lojinha entram no fim da cozinha.
EXTRA_STATIONS = ("cafeteira",)
FEMININE = ("batata", "coxinha")
COOKERS = ("chapa", "fritadeira")
STAGE_WORDS = ("cozinhando", "no ponto", "passando do ponto", "queimado")
TURN_WORDS = {"virar": ("virar", "Virou"), "sacudir": ("sacudir", "Sacudiu")}


def join(parts):
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " e " + parts[-1]


def clock(minutes):
    h, m = divmod(int(minutes), 60)
    m -= m % 10
    return "%d horas" % h + (" e %d" % m if m else "")


class Item:
    def __init__(self, kind, quality=1.0, count=1):
        self.kind = kind
        self.quality = quality
        self.count = count

    @property
    def name(self):
        if self.kind == "louca" and self.count > 1:
            return "louça de %d pratos" % self.count
        return D.item_name(self.kind)


class Table:
    def __init__(self, index):
        self.index = index
        self.clear()

    def clear(self):
        self.state = "livre"
        self.timer = 0.0
        self.patience = 0.0
        self.patience_max = 1.0
        self.stage = 0
        self.order = []          # o que ainda falta servir
        self.wanted = []         # o pedido inteiro
        self.served = []         # (receita, qualidade)
        self.mood = 1.0          # menor fração de paciência que sobrou nas esperas
        self.mult = 1.0
        self.louca = 0

    @property
    def name(self):
        return "Mesa %d" % (self.index + 1)

    @property
    def waiting(self):
        return self.state in ("pedir", "esperando", "pagar")


class Cooking:
    def __init__(self, kind):
        self.kind = kind
        self.t = 0.0
        self.stage = 0
        self.turned = False
        self.turn_cued = False

    @property
    def short(self):
        return D.COOK_SHORT[self.kind]


class Station:
    def __init__(self, name, slots):
        self.name = name
        self.cap = slots
        self.slots = []
        self.fire = False
        self.fire_t = 0.0


class Service:
    def __init__(self, casa, ui, rng=None, speed=1.0, on_done=None, on_closed=None):
        self.casa = casa
        self.ui = ui
        self.rng = rng or random.Random()
        self.sf = speed
        self.on_done = on_done            # on_done(resumo): todos foram embora
        self.on_closed = on_closed        # on_closed(): a vigilância interditou a casa
        self.layout = (["mesa"] * C.TABLES,
                       list(STATIONS) + [k for k in EXTRA_STATIONS if k in casa.equipment])
        self.layer = SALAO
        self.index = [C.TABLES // 2, 0]
        self.tables = [Table(i) for i in range(C.TABLES)]
        self.cookers = {"chapa": Station("chapa", C.CHAPA_SLOTS),
                        "fritadeira": Station("fritadeira", C.FRITADEIRA_SLOTS)}
        self.blender = None               # None, a fruta preparada ou o suco pronto
        self.blend = 0.0
        self.blending = False
        self.juice_quality = 1.0
        self.overdone = ""
        self.coffee = None                # None, "graos", "passando" ou "pronto"
        self.grind = 0.0
        self.grinding = False
        self.coffee_t = 0.0
        self.coffee_quality = 1.0
        self.hands = []
        self.bench = []                   # partes escolhidas na bancada
        self.busy = 0.0                   # apagando fogo
        self.busy_station = None
        self.t = 0.0
        self.open = True
        self.paused = False
        self.finished = False
        self.over = False
        self.next_arrival = C.FIRST_ARRIVAL
        self.inspect_at = None
        if casa.inspection_today:
            self.inspect_at = self.rng.uniform(*C.INSPECTION_TIME) * C.DAY_SECONDS
        self.stats = {"served": 0, "left": 0, "sales": 0, "tips": 0, "fires": 0,
                      "quality": [], "in_season": None}
        self.end_timer = None

    # --- tempo -----------------------------------------------------------
    @property
    def minutes(self):
        span = (C.CLOSE_HOUR - C.OPEN_HOUR) * 60
        return C.OPEN_HOUR * 60 + min(1.0, self.t / C.DAY_SECONDS) * span

    @property
    def fires(self):
        return [s for s in self.cookers.values() if s.fire]

    def patience_mult(self):
        m = self.sf * D.weather(self.casa.weather)[3]
        if self.casa.flies:
            m *= C.FLIES_PATIENCE
        return m

    def start(self):
        self.ui.play("porta")
        ambient = D.SEASON_INFO[self.casa.season]["ambient"]
        if ambient:
            self.ui.loop("ambiente", ambient, None, volume=C.AMBIENT_VOLUME)
        self.ui.say("A casa abriu: %s, %s. Você está no salão, na frente da %s."
                    % (clock(self.minutes), D.weather(self.casa.weather)[1],
                       self.tables[self.index[SALAO]].name.lower()))

    def update(self, dt):
        if self.paused or self.over or self.finished:
            return
        self.t += dt
        if self.busy > 0:
            self.busy -= dt
            if self.busy <= 0:
                self._extinguished()
        self._arrivals(dt)
        for table in self.tables:
            self._update_table(table, dt)
        for station in self.cookers.values():
            self._update_station(station, dt)
        self._update_blender(dt)
        self._update_coffee(dt)
        if self.inspect_at is not None and self.t >= self.inspect_at:
            self.inspect_at = None
            self._inspection()
            if self.over:
                return
        if self.open and self.t >= C.DAY_SECONDS:
            self.open = False
            self.ui.play("porta_fecha")
            busy = [t for t in self.tables if t.state not in ("livre", "suja")]
            self.ui.say("%s: a porta fechou." % clock(self.minutes)
                        + (" Termine de atender quem ficou." if busy else ""), queue=True)
        if not self.open:
            self._check_end(dt)

    # --- clientes --------------------------------------------------------
    def _arrivals(self, dt):
        if not self.open:
            return
        self.next_arrival -= dt
        if self.next_arrival > 0:
            return
        free = [t for t in self.tables if t.state == "livre"]
        if not free:
            self.next_arrival = 3.0
            return
        interval = self.rng.uniform(*C.ARRIVAL_INTERVAL) * self.sf
        self.next_arrival = interval / max(0.2, self.casa.arrival_factor())
        self._seat(self.rng.choice(free))

    def _choose_order(self):
        menu = [k for k in self.casa.active_menu() if self.casa.can_make(k)]
        if not menu:
            return []
        prefs = D.PREFERENCES[self.casa.season]
        weights = [prefs[k] * self.casa.tier(k)[2] for k in menu]
        first = self.rng.choices(menu, weights)[0]
        order = [first]
        special = self.casa.special()
        if self.rng.random() < (special[2] if special else C.TWO_ITEMS_CHANCE):
            others = [k for k in menu if k != first] or menu
            ow = [prefs[k] * self.casa.tier(k)[2] for k in others]
            order.append(self.rng.choices(others, ow)[0])
        return order

    def _seat(self, table):
        order = self._choose_order()
        spot = self._spot(SALAO, table.index)
        self.ui.play("porta")
        if self.casa.weather == "vento":
            self.ui.play("folhas")
        if not order:
            self._rep(C.REP_NOTHING)
            self.ui.say("Um cliente entrou, olhou o cardápio e foi embora: não tinha nada que "
                        "desse para fazer.", queue=True)
            return
        table.clear()
        table.state = "sentado"
        table.wanted = list(order)
        table.order = list(order)
        table.timer = self.rng.uniform(*C.CALL_DELAY)
        tiers = [self.casa.tier(k)[3] for k in order]
        table.mult = self.patience_mult() * sum(tiers) / len(tiers)
        self.ui.play("cadeira", spot)
        self.ui.say("Cliente na %s." % table.name.lower(), queue=True)

    def _wait(self, table, state, patience):
        table.state = state
        table.patience_max = patience * table.mult
        table.patience = table.patience_max
        table.stage = 0

    def _update_table(self, table, dt):
        spot = self._spot(SALAO, table.index)
        if table.state == "sentado":
            table.timer -= dt
            if table.timer <= 0:
                self._wait(table, "pedir", C.PATIENCE_ORDER)
                self.ui.play("chamar", spot)
                self.ui.say("%s quer pedir." % table.name, queue=True)
        elif table.state == "comendo":
            table.timer -= dt
            if table.timer <= 0:
                self._wait(table, "pagar", C.PATIENCE_PAY)
                self.ui.play("chamar", spot, pitch=1.2)
                self.ui.say("%s quer pagar." % table.name, queue=True)
        elif table.waiting:
            drain = C.FIRE_PATIENCE_DRAIN if self.fires else 1.0
            table.patience -= dt * drain
            frac = table.patience / table.patience_max
            table.mood = min(table.mood, max(0.0, frac))
            while table.stage < len(C.IMPATIENCE_STAGES) and frac <= C.IMPATIENCE_STAGES[table.stage]:
                table.stage += 1
                self.ui.play("impaciencia%d" % table.stage, spot)
                if table.stage == 2:
                    self.ui.say("%s está ficando impaciente." % table.name, queue=True)
            if table.patience <= 0:
                self._gives_up(table)

    def _gives_up(self, table):
        spot = self._spot(SALAO, table.index)
        if table.state == "pagar":
            bill = self._bill(table)
            self.casa.money += bill
            self.stats["sales"] += bill
            self.stats["served"] += 1
            self.ui.play("caixa", spot)
            self.ui.say("O cliente da %s cansou de esperar, deixou %s na mesa e foi embora, "
                        "sem gorjeta." % (table.name.lower(), money(bill)), queue=True)
            self._leaves_dirty(table)
            return
        self.stats["left"] += 1
        self._rep(C.REP_LEFT)
        self.ui.play("resmungo", spot)
        self.ui.say("O cliente da %s cansou de esperar e foi embora." % table.name.lower(),
                    queue=True)
        if table.served:
            self._leaves_dirty(table)
        else:
            table.clear()

    def _leaves_dirty(self, table):
        n = len(table.served)
        table.clear()
        table.state = "suja"
        table.louca = max(1, n)
        self.casa.add_dirt("mesa%d" % (table.index + 1))
        if self.rng.random() < 0.5:
            self.casa.add_dirt("chao_salao")

    def _bill(self, table):
        return sum(self.casa.price(k) for k, _ in table.served)

    def _rep(self, delta):
        self.casa.reputation = max(0.0, min(5.0, self.casa.reputation + delta))

    # --- ações nas mesas ---------------------------------------------------
    def _table_action(self, table):
        spot = self._spot(SALAO, table.index)
        if table.state in ("sentado", "pedir"):
            self._wait(table, "esperando", C.PATIENCE_FOOD)
            self.ui.play("anotar", spot)
            self.ui.say("%s pediu %s." % (table.name, self._order_text(table.order)))
        elif table.state == "esperando":
            item = next((i for i in self.hands if i.kind in table.order), None)
            if item is None:
                if any(i.kind in D.RECIPES for i in self.hands):
                    self.ui.play("errado", spot)
                    self.ui.say("Não foi isso que a %s pediu. Ela espera %s."
                                % (table.name.lower(), self._order_text(table.order)))
                else:
                    self.ui.say("%s espera %s." % (table.name, self._order_text(table.order)))
                return
            self.hands.remove(item)
            table.order.remove(item.kind)
            table.served.append((item.kind, item.quality))
            self.ui.play("servir", spot)
            if table.order:
                table.patience = max(table.patience, table.patience_max * 0.5)
                self.ui.say("Serviu %s. Falta %s." % (item.name, self._order_text(table.order)))
            else:
                table.state = "comendo"
                table.timer = self.rng.uniform(*C.EAT_TIME)
                self.ui.say("Serviu %s. %s está comendo." % (item.name, table.name))
        elif table.state == "pagar":
            self._pay(table)
        elif table.state == "suja":
            if len(self.hands) >= C.HANDS:
                self.ui.say("Suas mãos estão cheias.")
                return
            self.hands.append(Item("louca", count=table.louca))
            self.ui.play("louca", spot)
            self.ui.say("Recolheu a louça da %s." % table.name.lower())
            table.clear()
        else:
            self.ui.say(self.describe(SALAO, table.index))

    def _pay(self, table):
        spot = self._spot(SALAO, table.index)
        bill = self._bill(table)
        quality = sum(q for _, q in table.served) / len(table.served)
        prefs = D.PREFERENCES[self.casa.season]
        in_season = [k for k, _ in table.served if prefs[k] >= D.IN_SEASON]
        tip_mult = sum(self.casa.tier(k)[4] for k, _ in table.served) / len(table.served)
        tip = bill * C.TIP_MAX * max(0.0, (quality - 0.5) / 0.5) * table.mood * tip_mult
        if in_season:
            tip *= D.IN_SEASON_TIP
        special = self.casa.special()
        if special:
            tip *= special[3]
        tip = int(round(tip))
        self.casa.money += bill + tip
        self.stats["sales"] += bill
        self.stats["tips"] += tip
        self.stats["served"] += 1
        self.stats["quality"].append(quality)
        if in_season and quality >= 0.9:
            self.stats["in_season"] = in_season[0]
        if quality >= 0.9 and table.mood >= 0.4:
            self._rep(C.REP_HAPPY)
        elif quality >= 0.7:
            self._rep(C.REP_OK)
        self.ui.play("caixa", spot)
        if tip:
            self.ui.play("gorjeta", spot)
            self.ui.say("%s pagou %s, com %s de gorjeta." % (table.name, money(bill + tip),
                                                            money(tip)))
        else:
            self.ui.say("%s pagou %s." % (table.name, money(bill)))
        self._leaves_dirty(table)

    def _order_text(self, order):
        return D.order_text(list(order))

    # --- cozinha ---------------------------------------------------------
    def _times(self, kind):
        return [v * self.sf for v in C.COOK[kind]]

    def _update_station(self, station, dt):
        spot = self._spot(COZINHA, self._at(station.name))
        name = STATION_NAMES[station.name].lower()
        if station.fire:
            station.fire_t += dt
            if station.fire_t >= C.FIRE_SPREAD:
                station.fire_t = 0.0
                other = self.cookers["fritadeira" if station.name == "chapa" else "chapa"]
                if not other.fire:
                    self._catch_fire(other, spread=True)
            return
        for c in station.slots:
            c.t += dt
            tp, win, passing, burnt = self._times(c.kind)
            if c.kind in D.TURN and not c.turned and not c.turn_cued \
                    and c.t >= C.TURN_WINDOW[0] * tp and c.stage == 0:
                c.turn_cued = True
                verb = TURN_WORDS[D.TURN[c.kind]][0]
                self.ui.play("aviso_virar", spot)
                self.ui.say("Hora de %s %s." % (verb, self._the(c.short)), queue=True)
            limits = (tp, tp + win, tp + win + passing, tp + win + passing + burnt)
            while c.stage < 4 and c.t >= limits[c.stage]:
                c.stage += 1
                if c.stage == 1:
                    self.ui.play("ponto", spot)
                    self.ui.say("%s no ponto na %s." % (c.short.capitalize(), name), queue=True)
                elif c.stage == 2:
                    self.ui.play("passando", spot)
                    self.ui.say("%s passando do ponto!" % c.short.capitalize(), queue=True)
                elif c.stage == 3:
                    self.ui.play("fumaca", spot)
                    self.ui.say("Queimou %s na %s!" % (self._the(c.short), name))
                else:
                    self._catch_fire(station)
                    return
        self._station_loop(station)

    def _the(self, short):
        return ("a " if short in FEMININE else "o ") + short

    def _station_loop(self, station):
        spot = self._spot(COZINHA, self._at(station.name))
        if station.fire:
            self.ui.loop(station.name, "fogo", spot)
        elif station.slots:
            top = max(c.stage for c in station.slots)
            sound = "chiado" if station.name == "chapa" else "fritura"
            self.ui.loop(station.name, sound, spot, pitch=(1.0, 1.12, 1.3, 0.8)[min(top, 3)])
        else:
            self.ui.stop(station.name)

    def _catch_fire(self, station, spread=False):
        station.fire = True
        station.fire_t = 0.0
        station.slots = []
        self.stats["fires"] += 1
        self._rep(C.REP_FIRE)
        spot = self._spot(COZINHA, self._at(station.name))
        self.ui.play("alarme", spot)
        name = STATION_NAMES[station.name].lower()
        self.ui.say(("O fogo passou para a %s!" if spread else "Fogo na %s!") % name
                    + " Aperte B nela para usar o extintor.")
        for t in self.tables:
            if t.waiting:
                self.ui.play("impaciencia2", self._spot(SALAO, t.index))
        self._station_loop(station)

    def _extinguished(self):
        station = self.busy_station
        self.busy = 0.0
        self.busy_station = None
        station.fire = False
        station.fire_t = 0.0
        self.casa.add_dirt(station.name, 3)
        self.casa.add_dirt("chao_cozinha")
        self._station_loop(station)
        self.ui.say("Fogo apagado na %s. Ficou tudo sujo de pó do extintor."
                    % STATION_NAMES[station.name].lower())

    def _cooker_action(self, station):
        spot = self._spot(COZINHA, self._at(station.name))
        name = STATION_NAMES[station.name].lower()
        if station.fire:
            self.busy = C.EXTINGUISH_TIME
            self.busy_station = station
            self.ui.play("extintor", spot)
            self.ui.say("Apagando o fogo...")
            return
        free = len(self.hands) < C.HANDS
        ready = sorted([c for c in station.slots if c.stage >= 1], key=lambda c: -c.t)
        if ready and free:
            c = ready[0]
            station.slots.remove(c)
            if c.stage >= 3:
                item = Item("queimado")
                self.ui.say("Pegou comida queimada. Jogue na lixeira.")
            else:
                q = 1.0 if c.stage == 1 else C.PASSING_QUALITY
                if c.kind in D.TURN and not c.turned:
                    q *= C.MISSED_TURN_QUALITY
                item = Item(D.COOKED[c.kind], quality=q)
                extra = "" if q >= 1.0 else ", mas não ficou perfeito"
                self.ui.say("Pegou %s%s." % (item.name, extra))
            self.hands.append(item)
            self.ui.play("pegar", spot)
            self._station_loop(station)
            return
        turn = next((c for c in station.slots if c.turn_cued and not c.turned), None)
        if turn is not None:
            turn.turned = True
            verb = TURN_WORDS[D.TURN[turn.kind]][1]
            self.ui.play("virar" if station.name == "chapa" else "sacudir", spot)
            self.ui.say("%s %s." % (verb, self._the(turn.short)))
            return
        raw = next((i for i in self.hands if i.kind in D.STATION_ACCEPTS[station.name]), None)
        if raw is not None and len(station.slots) < station.cap:
            self.hands.remove(raw)
            station.slots.append(Cooking(raw.kind))
            self.ui.play("colocar", spot)
            self.ui.say("%s na %s." % (D.COOK_SHORT[raw.kind].capitalize(), name))
            self._station_loop(station)
            return
        if raw is not None:
            self.ui.say("A %s está cheia." % name)
        elif ready:
            self.ui.say("Suas mãos estão cheias.")
        else:
            self.ui.say("%s: %s." % (STATION_NAMES[station.name], self._station_text(station)))

    def _station_text(self, station):
        if station.fire:
            return "pegando fogo"
        if not station.slots:
            return "vazia"
        parts = []
        for c in station.slots:
            word = STAGE_WORDS[min(c.stage, 3)]
            if c.stage == 0 and c.turn_cued and not c.turned:
                word += ", na hora de %s" % TURN_WORDS[D.TURN[c.kind]][0]
            parts.append("%s %s" % (c.short, word))
        return join(parts)

    # --- liquidificador --------------------------------------------------
    def _blender_down(self):
        spot = self._spot(COZINHA, self._at("liquidificador"))
        if self.blender is None:
            item = next((i for i in self.hands if i.kind in D.BLENDS), None)
            if item is None:
                self.ui.say("Liquidificador vazio. Prepare a fruta ou o leite na bancada.")
                return
            self.hands.remove(item)
            self.blender = item.kind
            self.blend = 0.0
            self.ui.play("colocar", spot)
            self.ui.say("%s no liquidificador. Segure B para bater."
                        % D.BLENDS[item.kind][1].capitalize())
        elif self.blender in D.BLENDS:
            self.blending = True
            self.ui.loop("liquidificador", "liquidificador", spot, pitch=self._blend_pitch())
        else:
            self._take_juice()

    def _blender_up(self):
        if not self.blending:
            return
        self.blending = False
        self.ui.stop("liquidificador")
        if self.blend < C.BLEND_MIN:
            self.ui.say("Ainda tem pedaço. Segure mais um pouco.")
            return
        self.overdone = D.BLENDS[self.blender][2]
        self.blender = D.BLENDS[self.blender][0]
        self.juice_quality = 1.0 if self.blend <= C.BLEND_MAX else C.WARM_JUICE_QUALITY
        self._take_juice()

    def _take_juice(self):
        spot = self._spot(COZINHA, self._at("liquidificador"))
        name = D.item_name(self.blender).capitalize()
        warm = ", mas %s" % self.overdone if self.juice_quality < 1.0 else ""
        end = "a" if D.ORDER_WORDS.get(self.blender, ("um",))[0] == "uma" else "o"
        if len(self.hands) >= C.HANDS:
            self.ui.say("%s pront%s%s. Suas mãos estão cheias: %s espera no liquidificador."
                        % (name, end, warm, "ela" if end == "a" else "ele"))
            return
        self.hands.append(Item(self.blender, quality=self.juice_quality))
        self.blender = None
        self.blend = 0.0
        self.ui.play("servir_copo", spot)
        self.ui.say("%s pront%s%s. Na mão." % (name, end, warm))

    def _blend_pitch(self):
        return 0.8 + 0.5 * min(1.0, self.blend / C.BLEND_MAX)

    def _update_blender(self, dt):
        if not self.blending:
            return
        before = self.blend
        self.blend += dt
        spot = self._spot(COZINHA, self._at("liquidificador"))
        self.ui.loop("liquidificador", "liquidificador", spot, pitch=self._blend_pitch())
        if before < C.BLEND_MIN <= self.blend:
            self.ui.play("liso", spot)
        if before < C.BLEND_MAX <= self.blend:
            self.ui.play("passando", spot)

    # --- cafeteira -------------------------------------------------------
    def _coffee_down(self):
        spot = self._spot(COZINHA, self._at("cafeteira"))
        if self.coffee is None:
            if not self.casa.take("cafe"):
                self.ui.say("Acabou o café em grão. Compre na abertura.")
                return
            self.coffee = "graos"
            self.grind = 0.0
            self.ui.play("colocar", spot)
            self.ui.say("Café no moedor. Segure B para moer e solte para passar.")
        elif self.coffee == "graos":
            self.grinding = True
            self.ui.loop("moedor", "moedor", spot, pitch=self._grind_pitch())
        elif self.coffee == "passando":
            self.ui.say("O café está passando.")
        else:
            self._take_coffee()

    def _coffee_up(self):
        if not self.grinding:
            return
        self.grinding = False
        self.ui.stop("moedor")
        if self.grind < C.GRIND_MIN:
            self.ui.say("Ainda está grosso. Segure mais um pouco.")
            return
        self.coffee_quality = 1.0 if self.grind <= C.GRIND_MAX else C.BITTER_QUALITY
        self.coffee = "passando"
        self.coffee_t = 0.0
        spot = self._spot(COZINHA, self._at("cafeteira"))
        self.ui.loop("cafeteira", "cafe_passando", spot)
        self.ui.say("Passando o café.")

    def _grind_pitch(self):
        return 0.8 + 0.5 * min(1.0, self.grind / C.GRIND_MAX)

    def _update_coffee(self, dt):
        if self.coffee is None:
            return
        spot = self._spot(COZINHA, self._at("cafeteira"))
        if self.grinding:
            before = self.grind
            self.grind += dt
            self.ui.loop("moedor", "moedor", spot, pitch=self._grind_pitch())
            if before < C.GRIND_MIN <= self.grind:
                self.ui.play("liso", spot)
            if before < C.GRIND_MAX <= self.grind:
                self.ui.play("passando", spot)
        elif self.coffee == "passando":
            self.coffee_t += dt
            if self.coffee_t >= C.COFFEE_BREW * self.sf:
                self.coffee = "pronto"
                self.coffee_t = 0.0
                self.ui.stop("cafeteira")
                self.ui.play("ponto", spot)
                self.ui.say("Cafezinho pronto na cafeteira.", queue=True)
        elif self.coffee == "pronto":
            before = self.coffee_t
            self.coffee_t += dt
            limit = C.COFFEE_COOL * self.sf
            if before < limit <= self.coffee_t:
                self.coffee_quality = min(self.coffee_quality, C.COLD_COFFEE_QUALITY)
                self.ui.say("O cafezinho está esfriando na cafeteira.", queue=True)

    def _take_coffee(self):
        spot = self._spot(COZINHA, self._at("cafeteira"))
        if len(self.hands) >= C.HANDS:
            self.ui.say("Suas mãos estão cheias.")
            return
        item = Item("cafezinho", quality=self.coffee_quality)
        self.hands.append(item)
        self.coffee = None
        self.ui.play("servir_copo", spot)
        if self.coffee_quality >= 1.0:
            self.ui.say("Pegou o cafezinho.")
        elif self.coffee_t >= C.COFFEE_COOL * self.sf:
            self.ui.say("Pegou o cafezinho, mas esfriou um pouco.")
        else:
            self.ui.say("Pegou o cafezinho, mas amargou um pouco.")

    def _coffee_text(self):
        return {None: "vazia", "graos": "com café no moedor", "passando": "passando o café",
                "pronto": "com cafezinho pronto"}[self.coffee]

    # --- bancada ---------------------------------------------------------
    def bench_options(self):
        """O que dá para pôr na montagem agora: (chave, texto)."""
        chosen = list(self.bench)
        options = []
        for k, item in enumerate(self.hands):
            key = "mao:%d" % k
            if key not in chosen and item.kind not in ("louca", "queimado"):
                options.append((key, "%s, da mão" % item.name.capitalize()))
        for key in D.INGREDIENT_ORDER:
            left = self.casa.count(key) - chosen.count("ing:" + key)
            if left > 0:
                options.append(("ing:" + key, "%s, %d" % (D.INGREDIENTS[key][0].capitalize(),
                                                         left)))
        return options

    def bench_add(self, key):
        self.bench.append(key)
        spot = self._spot(COZINHA, 0)
        self.ui.play("ingrediente", spot, pitch=0.9 + 0.1 * len(self.bench))
        self.ui.say("%s." % self._part_name(key).capitalize())

    def _part_name(self, key):
        kind, value = key.split(":")
        return self.hands[int(value)].name if kind == "mao" else D.INGREDIENTS[value][0]

    def _part_kind(self, key):
        kind, value = key.split(":")
        return self.hands[int(value)].kind if kind == "mao" else value

    def bench_done(self):
        """Monta o que foi escolhido. True se montou."""
        parts = self.bench
        self.bench = []
        if not parts:
            return False
        product = D.assemble(self._part_kind(k) for k in parts)
        if product is None:
            self.ui.play("errado", self._spot(COZINHA, 0))
            self.ui.say("%s não vira nenhuma receita. Nada foi gasto."
                        % join([self._part_name(k) for k in parts]).capitalize())
            return False
        used = sorted((int(k.split(":")[1]) for k in parts if k.startswith("mao:")),
                      reverse=True)
        if len(self.hands) - len(used) >= C.HANDS:
            self.ui.say("Suas mãos estão cheias.")
            return False
        quality = min([self.hands[i].quality for i in used] or [1.0])
        for i in used:
            self.hands.pop(i)
        for k in parts:
            if k.startswith("ing:"):
                self.casa.take(k[4:])
        if len(parts) > 1 and self.rng.random() < 0.3:
            self.casa.add_dirt("chao_cozinha")
        item = Item(product, quality=quality)
        self.hands.append(item)
        self.ui.play("montar", self._spot(COZINHA, 0))
        self.ui.say("Montou %s. Na mão." % item.name)
        return True

    def bench_cancel(self):
        self.bench = []

    # --- pia e lixeira ---------------------------------------------------
    def _sink_action(self):
        spot = self._spot(COZINHA, self._at("pia"))
        dishes = [i for i in self.hands if i.kind == "louca"]
        if dishes:
            for i in dishes:
                self.hands.remove(i)
                self.casa.add_dirt("louca", i.count)
            self.ui.play("louca", spot)
        self.ui.say(self._sink_text().capitalize() + ("." if not dishes else
                                                      ", esperando a limpeza."))

    def _sink_text(self):
        n = self.casa.dirt["louca"]
        if n == 0:
            return "pia vazia"
        return "%d %s na pia" % (n, "prato" if n == 1 else "pratos")

    def _trash_action(self):
        spot = self._spot(COZINHA, self._at("lixeira"))
        candidates = [i for i in self.hands if i.kind != "louca"]
        if not candidates:
            self.ui.say("Louça vai na pia." if self.hands else "Mãos vazias.")
            return
        burnt = [i for i in candidates if i.kind == "queimado"]
        item = (burnt or candidates)[-1]
        self.hands.remove(item)
        self.casa.add_dirt("lixo")
        self.ui.play("lixo", spot)
        self.ui.say("Jogou fora: %s." % item.name)

    # --- controles -------------------------------------------------------
    def _spot(self, layer, index):
        return (layer, index, len(self.layout[layer]))

    def _at(self, station):
        return self.layout[COZINHA].index(station)

    def spot_name(self, layer, index):
        if layer == SALAO:
            return self.tables[index].name
        return STATION_NAMES[self.layout[COZINHA][index]]

    def describe(self, layer, index, detail=False):
        if layer == SALAO:
            t = self.tables[index]
            text = {"livre": "livre", "sentado": "cliente sentando", "pedir": "quer pedir",
                    "comendo": "comendo", "pagar": "quer pagar",
                    "suja": "louça para recolher"}.get(t.state)
            if t.state == "esperando":
                text = "espera " + self._order_text(t.order)
            if detail and t.waiting:
                frac = t.patience / t.patience_max
                text += (", tranquilo" if frac > 0.5 else ", impaciente" if frac > 0.25
                         else ", muito impaciente")
            return text
        name = self.layout[COZINHA][index]
        if name in self.cookers:
            return self._station_text(self.cookers[name])
        if name == "liquidificador":
            if self.blender is None:
                return "vazio"
            if self.blender in D.BLENDS:
                return "com " + D.BLENDS[self.blender][1]
            return "com %s pronto" % D.item_name(self.blender)
        if name == "pia":
            return self._sink_text()
        if name == "cafeteira":
            return self._coffee_text()
        if name == "bancada":
            return "pegar e montar"
        return "jogar fora"

    def announce_focus(self, with_layer=False):
        layer, index = self.layer, self.index[self.layer]
        prefix = ("Salão. " if layer == SALAO else "Cozinha. ") if with_layer else ""
        self.ui.play("foco", self._spot(layer, index))
        self.ui.say("%s%s, %s." % (prefix, self.spot_name(layer, index),
                                   self.describe(layer, index)))

    def step(self, delta):
        layer = self.layer
        new = self.index[layer] + delta
        if not 0 <= new < len(self.layout[layer]):
            self.ui.play("borda", self._spot(layer, self.index[layer]))
            return
        self.index[layer] = new
        self.announce_focus()

    def go_layer(self, layer):
        if layer == self.layer:
            self.ui.play("borda", self._spot(layer, self.index[layer]))
            return
        self.layer = layer
        self.announce_focus(with_layer=True)

    def _needs_you(self, layer, index):
        if layer == SALAO:
            t = self.tables[index]
            if t.state in ("pedir", "pagar"):
                return True
            if t.state == "suja":
                return len(self.hands) < C.HANDS
            if t.state == "esperando":
                return any(i.kind in t.order for i in self.hands)
            return False
        name = self.layout[COZINHA][index]
        if name in self.cookers:
            s = self.cookers[name]
            return s.fire or any(c.stage >= 1 or (c.turn_cued and not c.turned)
                                 for c in s.slots)
        if name == "liquidificador":
            return self.blender is not None and self.blender not in D.BLENDS
        if name == "pia":
            return any(i.kind == "louca" for i in self.hands)
        if name == "cafeteira":
            return self.coffee == "pronto"
        if name == "lixeira":
            return any(i.kind == "queimado" for i in self.hands)
        return False

    def jump(self, delta):
        """L1/R1: a mesa ou estação anterior/seguinte que precisa de você."""
        spots = [(SALAO, i) for i in range(C.TABLES)] + [(COZINHA, i)
                                                         for i in range(len(self.layout[COZINHA]))]
        here = spots.index((self.layer, self.index[self.layer]))
        for k in range(1, len(spots) + 1):
            layer, index = spots[(here + delta * k) % len(spots)]
            if self._needs_you(layer, index):
                changed = layer != self.layer
                self.layer = layer
                self.index[layer] = index
                self.announce_focus(with_layer=changed)
                return
        self.ui.play("borda")
        self.ui.say("Nada precisa de você agora.")

    def action_down(self):
        """B no foco."""
        if self.busy > 0:
            self.ui.say("Você está apagando o fogo.")
            return
        layer, index = self.layer, self.index[self.layer]
        if layer == SALAO:
            self._table_action(self.tables[index])
            return
        name = self.layout[COZINHA][index]
        if name in self.cookers:
            self._cooker_action(self.cookers[name])
        elif name == "liquidificador":
            self._blender_down()
        elif name == "bancada":
            self.bench = []
            self.ui.open_bancada()
        elif name == "pia":
            self._sink_action()
        elif name == "cafeteira":
            self._coffee_down()
        else:
            self._trash_action()

    def action_up(self):
        self._blender_up()
        self._coffee_up()

    def hands_text(self):
        if not self.hands:
            return "Mãos vazias."
        return "Nas mãos: %s." % join([i.name for i in self.hands])

    def status_text(self):
        return "%s. %s, %s. %s. Reputação: %s." % (
            clock(self.minutes), self.casa.date_text(), D.weather(self.casa.weather)[1],
            money(self.casa.money).capitalize(), _stars(self.casa.reputation))

    def summary_text(self):
        parts = []
        for t in self.tables:
            if t.state != "livre":
                parts.append("%s %s" % (t.name, self.describe(SALAO, t.index, detail=True)))
        for name in COOKERS:
            s = self.cookers[name]
            if s.slots or s.fire:
                parts.append("%s: %s" % (STATION_NAMES[name], self._station_text(s)))
        if self.blender:
            parts.append("Liquidificador %s" % self.describe(COZINHA, 3))
        if self.coffee:
            parts.append("Cafeteira %s" % self._coffee_text())
        if not parts:
            parts.append("Salão vazio e cozinha parada")
        if not self.open:
            parts.append("A porta está fechada")
        return ". ".join(parts) + "."

    # --- vigilância e fim -------------------------------------------------
    def _inspection(self):
        self.ui.play("vigilancia")
        self.ui.say("Chegou a vigilância sanitária para a visita!")
        if self.casa.inspect():
            self.ui.say("A fiscal olhou tudo e aprovou: casa limpa. A reputação subiu.",
                        queue=True)
            return
        self.over = True
        self._stop_loops()
        if self.on_closed:
            self.on_closed()

    def _stop_loops(self):
        for key in ("chapa", "fritadeira", "liquidificador", "moedor", "cafeteira", "ambiente"):
            self.ui.stop(key)

    def _check_end(self, dt):
        if any(t.state not in ("livre", "suja") for t in self.tables) or self.fires \
                or self.busy > 0:
            self.end_timer = None
            return
        if self.end_timer is None:
            self.end_timer = 2.0
            self.ui.say("O último cliente saiu. Hora de fechar a cozinha e limpar.", queue=True)
        self.end_timer -= dt
        if self.end_timer <= 0:
            self._finish()

    def _finish(self):
        self.finished = True
        self.blending = False
        self.grinding = False
        self._stop_loops()
        for s in self.cookers.values():
            if s.slots:
                self.casa.add_dirt("lixo", len(s.slots))
                s.slots = []
        if self.blender:
            self.casa.add_dirt("lixo")
        if self.coffee:
            self.casa.add_dirt("lixo")
        for item in self.hands:
            if item.kind == "louca":
                self.casa.add_dirt("louca", item.count)
            else:
                self.casa.add_dirt("lixo")
        self.hands = []
        for t in self.tables:
            if t.state == "suja":
                self.casa.add_dirt("louca", t.louca)
                t.clear()
        summary = dict(self.stats)
        summary["comment"] = self._comment()
        if self.on_done:
            self.on_done(summary)

    def _comment(self):
        s = self.stats
        special = self.casa.special()
        if special and s["served"] and not s["fires"]:
            return "que %s gostoso, obrigada pelo carinho!" % special[0]
        if s["fires"]:
            return "que fumaceira na cozinha hoje!"
        if s["left"] >= 3:
            return "esperei tanto que quase desisti."
        if s["in_season"]:
            return "esse %s caiu muito bem nesse %s!" % (
                D.recipe_name(s["in_season"]).lower(), D.SEASONS[self.casa.season].lower())
        if s["quality"] and min(s["quality"]) >= 0.9:
            return "tudo no ponto, volto amanhã!"
        if s["served"]:
            return "lugar simpático."
        return ""


def _stars(rep):
    from .casa import stars
    return stars(rep)
