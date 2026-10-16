#!/usr/bin/env python3
"""Comes e Bebes: uma lanchonete para tocar no seu ritmo, de ouvido."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Durante o desenvolvimento, usa a biblioteca do repositório vizinho se não houver cópia aqui.
if not os.path.isdir(os.path.join(HERE, "r36s_a11y")):
    sys.path.insert(1, os.path.join(HERE, "..", "r36s-a11y-sdk", "python"))

import r36s_a11y as a11y

from comes import config as C
from comes import data as D
from comes import texts as T
from comes.casa import Casa, money
from comes.expediente import Service
from comes.limpeza import Cleaning

game = a11y.Game(repeat=True)
SAVE_FILE = os.path.join(game.save_dir, "casa.json")
sounds = {}
for f in sorted(os.listdir(os.path.join(game.dir, "sounds"))):
    base, ext = os.path.splitext(f)
    if ext.lower() in (".wav", ".ogg"):
        sounds[base] = game.sound.load(base, os.path.join("sounds", f))
menu_sounds = {"move": sounds.get("menu_mover"), "select": sounds.get("menu_confirmar"),
               "edge": sounds.get("borda")}

# phase: None (menus), "abertura", "expediente" ou "limpeza"
state = {"casa": None, "phase": None, "service": None, "cleaning": None, "summary": None,
         "speed": C.DEFAULT_SPEED}


def speed_factor():
    return dict(C.SPEEDS)[state["speed"]]


# --- jogo salvo ----------------------------------------------------------------
def has_save():
    return os.path.isfile(SAVE_FILE)


def read_save():
    with open(SAVE_FILE, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("velocidade") in dict(C.SPEEDS):
        state["speed"] = data["velocidade"]
    return Casa.from_dict(data["casa"])


def write_save():
    """Grava por cima, com arquivo temporário e troca, para um desligamento no meio
    não deixar o save pela metade."""
    tmp = SAVE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"casa": state["casa"].to_dict(), "velocidade": state["speed"]}, f,
                  ensure_ascii=False)
    os.replace(tmp, SAVE_FILE)


# --- som e fala ------------------------------------------------------------------
class UI:
    """Ponte entre a lógica e o áudio: (camada, índice, quantos) vira posição 3D."""

    def __init__(self):
        self.loops = {}

    def say(self, text, queue=False):
        game.say(text, queue=queue)

    @staticmethod
    def position(spot):
        layer, index, count = spot
        x = 0.0 if count <= 1 else -C.SPREAD_X / 2 + C.SPREAD_X * index / (count - 1)
        return (x, 0.0, C.SALAO_Z if layer == 0 else C.COZINHA_Z)

    def play(self, name, spot=None, pitch=1.0, volume=1.0):
        sound = sounds.get(name)
        if sound is None:
            return
        if spot is None:
            sound.play(pitch=pitch, volume=volume)
        else:
            sound.play(pitch=pitch, volume=volume, pos=self.position(spot))

    def loop(self, key, name, spot=None, pitch=1.0, volume=1.0):
        voice = self.loops.get(key)
        if voice is not None and voice.name == name and voice.playing:
            voice.set_pitch(pitch)
            return
        if voice is not None:
            voice.stop()
        sound = sounds.get(name)
        if sound is None:
            return
        pos = self.position(spot) if spot else None
        voice = sound.play(loop=True, pitch=pitch, volume=volume, pos=pos)
        voice.name = name
        self.loops[key] = voice

    def stop(self, key):
        voice = self.loops.pop(key, None)
        if voice is not None:
            voice.stop(fade=0.15)

    def stop_all(self):
        for key in list(self.loops):
            self.stop(key)

    def open_bancada(self):
        open_bench()


ui = UI()


# --- dia -------------------------------------------------------------------------
def new_game():
    """Escolhe a estação do primeiro dia e começa."""
    main_menu.close()
    season_menu.open(index=C.FIRST_SEASON, announce_help=False)


def on_season(index, item):
    season_menu.close()
    state["casa"] = Casa(season=index)
    write_save()
    game.say("Você pegou as chaves de uma lanchonete pequena, com três mesas, uma chapa, "
             "uma fritadeira e um liquidificador.", on_done=lambda done: begin_day())


def close_season():
    season_menu.close()
    open_main()


season_menu = a11y.Menu(game, "Começar em qual estação?", list(D.SEASONS), on_select=on_season,
                        on_back=close_season, sounds=menu_sounds)


def continue_game():
    try:
        state["casa"] = read_save()
    except (OSError, ValueError, KeyError) as exc:
        print("[comes] save ilegível: %s" % exc, file=sys.stderr)
        game.say("Não deu para ler o jogo salvo.")
        return
    main_menu.close()
    begin_day()


def begin_day():
    casa = state["casa"]
    lines = casa.start_day()
    write_save()
    state["phase"] = "abertura"
    ui.play("festa" if casa.special() else "manha")
    game.say(" ".join(lines), on_done=lambda done: open_opening())


def open_opening(item=None):
    opening_menu.items = opening_items()
    index = opening_menu.items.index(item) if item in opening_menu.items else 0
    opening_menu.title = "Abertura"
    opening_menu.open(index=index, announce_help=False)


def opening_items():
    return ["Abrir a casa", "Compras", "Cardápio", "Preços", "Velocidade: " + state["speed"],
            "Dinheiro e estoque", "Resumo de ontem", "Salvar e sair"]


def on_opening(index, item):
    casa = state["casa"]
    if item == "Abrir a casa":
        opening_menu.close()
        open_house()
    elif item == "Compras":
        opening_menu.close()
        shop_menu.items = shop_items()
        shop_menu.open(announce_help=False)
    elif item == "Cardápio":
        opening_menu.close()
        menu_menu.items = menu_items()
        menu_menu.open(announce_help=False)
    elif item == "Preços":
        opening_menu.close()
        prices_menu.items = price_items()
        prices_menu.open(announce_help=False)
    elif item.startswith("Velocidade"):
        cycle_speed()
        opening_menu.items = opening_items()
        game.say(opening_menu.items[index])
        write_save()
    elif item == "Dinheiro e estoque":
        stock = ["%s %d" % (D.INGREDIENTS[k][0], casa.count(k)) for k in D.INGREDIENT_ORDER
                 if casa.count(k) or casa.can_buy(k)]
        game.say("%s. Reputação: %s. Estoque: %s." % (money(casa.money).capitalize(),
                                                     stars(casa.reputation), ", ".join(stock)))
    elif item == "Resumo de ontem":
        game.say(casa.report or "Hoje é o primeiro dia.")
    else:
        write_save()
        opening_menu.close()
        state["phase"] = None
        game.say("Jogo salvo.", on_done=lambda done: open_main())


def stars(rep):
    from comes.casa import stars as s
    return s(rep)


def cycle_speed():
    names = [n for n, _ in C.SPEEDS]
    state["speed"] = names[(names.index(state["speed"]) + 1) % len(names)]
    if state["service"] is not None:
        state["service"].sf = speed_factor()


opening_menu = a11y.Menu(game, "Abertura", opening_items(), on_select=on_opening,
                         on_back=lambda: None, sounds=menu_sounds)


# compras
def shop_items():
    casa = state["casa"]
    return [casa.stock_text(k) for k in casa.shop_keys()] + ["Voltar"]


def on_shop(index, item):
    if item == "Voltar":
        back_to_opening(shop_menu, "Compras")
        return
    casa = state["casa"]
    key = casa.shop_keys()[index]
    if not casa.buy(key):
        ui.play("errado")
        game.say("Não dá: o pacote custa %s e você tem %s." % (money(D.INGREDIENTS[key][3]),
                                                             money(casa.money)))
        return
    write_save()
    ui.play("caixa")
    shop_menu.items = shop_items()
    game.say("Comprou %s. Agora %d em estoque. Sobram %s." % (
        D.INGREDIENTS[key][0], casa.count(key), money(casa.money)))


def back_to_opening(menu, item):
    menu.close()
    open_opening(item)


shop_menu = a11y.Menu(game, "Compras", ["Voltar"], on_select=on_shop,
                      on_back=lambda: back_to_opening(shop_menu, "Compras"), sounds=menu_sounds)


# cardápio
def menu_items():
    casa = state["casa"]
    return ["%s: %s" % (D.recipe_name(k), "no cardápio" if casa.menu[k] else "fora do cardápio")
            for k in casa.known_recipes()] + ["Voltar"]


def on_menu(index, item):
    if item == "Voltar":
        back_to_opening(menu_menu, "Cardápio")
        return
    casa = state["casa"]
    key = casa.known_recipes()[index]
    if casa.menu[key] and len(casa.active_menu()) == 1:
        game.say("O cardápio precisa de pelo menos uma receita.")
        return
    casa.menu[key] = not casa.menu[key]
    write_save()
    menu_menu.items = menu_items()
    game.say(menu_menu.items[index])


menu_menu = a11y.Menu(game, "Cardápio", ["Voltar"], on_select=on_menu,
                      on_back=lambda: back_to_opening(menu_menu, "Cardápio"), sounds=menu_sounds)


# preços
def price_items():
    casa = state["casa"]
    return ["%s: %s, %s" % (D.recipe_name(k), casa.tier(k)[0].lower(), money(casa.price(k)))
            for k in casa.known_recipes()] + ["Voltar"]


def on_prices(index, item):
    if item == "Voltar":
        back_to_opening(prices_menu, "Preços")
        return
    key = state["casa"].known_recipes()[index]
    state["pricing"] = key
    prices_menu.close()
    base = D.RECIPES[key][1]
    tier_menu.title = D.recipe_name(key)
    tier_menu.items = ["%s, %s" % (t[0], money(int(round(base * t[1])))) for t in C.PRICE_TIERS]
    tier_menu.open(index=state["casa"].prices[key], announce_help=False)


def on_tier(index, item):
    key = state["pricing"]
    state["casa"].prices[key] = index
    write_save()
    tier_menu.close()
    prices_menu.items = price_items()
    prices_menu.open(index=state["casa"].known_recipes().index(key), announce_help=False)


def close_tier():
    tier_menu.close()
    prices_menu.items = price_items()
    prices_menu.open(index=state["casa"].known_recipes().index(state["pricing"]),
                     announce_help=False)


prices_menu = a11y.Menu(game, "Preços", ["Voltar"], on_select=on_prices,
                        on_back=lambda: back_to_opening(prices_menu, "Preços"),
                        sounds=menu_sounds)
tier_menu = a11y.Menu(game, "Preço", ["Voltar"], on_select=on_tier, on_back=close_tier,
                      sounds=menu_sounds)


# --- expediente ------------------------------------------------------------------
def open_house():
    state["phase"] = "expediente"
    service = Service(state["casa"], ui, speed=speed_factor(), on_done=service_done,
                      on_closed=closed_down)
    state["service"] = service
    service.start()


def service_done(summary):
    state["summary"] = summary
    state["service"] = None
    ui.stop_all()
    state["phase"] = "limpeza"
    cleaning = Cleaning(state["casa"], ui, on_done=cleaning_done)
    state["cleaning"] = cleaning
    game.after(1.5, cleaning.start)


def cleaning_done():
    casa = state["casa"]
    state["cleaning"] = None
    ui.stop_all()
    state["phase"] = None
    report = casa.end_day(state["summary"] or {})
    state["summary"] = None
    write_save()
    ui.play("noite")
    game.say("Você trancou a porta e foi para casa. " + report,
             on_done=lambda done: begin_day())


def closed_down():
    casa = state["casa"]
    state["service"] = None
    state["phase"] = None
    ui.stop_all()
    ui.play("interdicao")
    casa.restore_checkpoint()
    write_save()
    game.say("A fiscal encontrou a sujeira de ontem e interditou a casa. Depois de tudo "
             "resolvido, você volta para o %s, com o que tinha naquele dia." % casa.short_date(),
             queue=True, on_done=lambda done: begin_day())


# bancada
def open_bench():
    service = state["service"]
    bench_menu.items = ["Montar"] + [label for _, label in service.bench_options()]
    state["bench_keys"] = [key for key, _ in service.bench_options()]
    bench_menu.open(index=1 if len(bench_menu.items) > 1 else 0, announce_help=False)


def on_bench(index, item):
    service = state["service"]
    if service is None:
        bench_menu.close()
        return
    if index == 0:
        bench_menu.close()
        if not service.bench:
            game.say("Nada escolhido.")
            return
        service.bench_done()
        return
    service.bench_add(state["bench_keys"][index - 1])
    options = service.bench_options()
    state["bench_keys"] = [key for key, _ in options]
    bench_menu.items = ["Montar"] + [label for _, label in options]
    bench_menu.index = min(bench_menu.index, len(bench_menu.items) - 1)


def cancel_bench():
    bench_menu.close()
    if state["service"] is not None:
        state["service"].bench_cancel()
    game.say("Saiu da bancada.")


bench_menu = a11y.Menu(game, "Bancada", ["Montar"], on_select=on_bench, on_back=cancel_bench,
                       sounds=menu_sounds)


# --- pausa -----------------------------------------------------------------------
def pause_items():
    if state["phase"] == "limpeza":
        return ["Continuar", "Ir para casa", "Sair para o menu"]
    return ["Continuar", "Velocidade: " + state["speed"], "Sair para o menu"]


def open_pause():
    current = state["service"] or state["cleaning"]
    current.action_up()          # soltar B na pausa não chegaria ao jogo
    current.paused = True
    game.sound.pause_all()
    pause_menu.items = pause_items()
    pause_menu.open(announce_help=False)


def on_pause(index, item):
    current = state["service"] or state["cleaning"]
    if item.startswith("Velocidade"):
        cycle_speed()
        write_save_speed()
        pause_menu.items = pause_items()
        game.say(pause_menu.items[index])
        return
    pause_menu.close()
    game.sound.resume_all()
    current.paused = False
    if item == "Continuar":
        current.announce_focus(with_layer=True)
    elif item == "Ir para casa":
        current.go_home()
    else:
        quit_to_menu()


def write_save_speed():
    """Muda só a velocidade no save: o resto do dia em andamento não é gravado."""
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return
    data["velocidade"] = state["speed"]
    with open(SAVE_FILE + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(SAVE_FILE + ".tmp", SAVE_FILE)


def quit_to_menu():
    """Sair no meio do dia: o dia recomeça da abertura na próxima vez."""
    ui.stop_all()
    state["service"] = state["cleaning"] = None
    state["phase"] = None
    game.say("O dia vai recomeçar da abertura.", on_done=lambda done: open_main())


pause_menu = a11y.Menu(game, "Pausa", ["Continuar"], on_select=on_pause,
                       on_back=lambda: on_pause(0, "Continuar"), sounds=menu_sounds)


# --- menu principal ----------------------------------------------------------------
def main_items():
    if has_save():
        try:
            casa = read_save()
            label = "Continuar: " + casa.short_date()
        except (OSError, ValueError, KeyError):
            label = "Continuar"
        return [label, "Novo jogo", "Como jogar", "Sair"]
    return ["Jogar", "Como jogar", "Sair"]


def open_main(item=None, announce_help=False):
    main_menu.items = main_items()
    index = main_menu.items.index(item) if item in main_menu.items else 0
    main_menu.open(index=index, announce_help=announce_help)


def on_main(index, item):
    if item.startswith("Continuar"):
        continue_game()
    elif item == "Jogar":
        new_game()
    elif item == "Novo jogo":
        main_menu.close()
        confirm_menu.open(announce_help=False)
    elif item == "Como jogar":
        main_menu.close()
        help_menu.open()
    else:
        game.quit()


main_menu = a11y.Menu(game, "Comes e Bebes", ["Jogar"], on_select=on_main,
                      on_back=game.quit, sounds=menu_sounds)


def on_confirm(index, item):
    confirm_menu.close()
    if item.startswith("Sim"):
        new_game()
    else:
        open_main("Novo jogo")


confirm_menu = a11y.Menu(game, "Começar de novo apaga a lanchonete salva. Tem certeza?",
                         ["Não, voltar", "Sim, começar de novo"], on_select=on_confirm,
                         on_back=lambda: on_confirm(0, "Não"), sounds=menu_sounds)


def close_help():
    help_menu.close()
    open_main("Como jogar")


help_menu = a11y.Menu(game, "Como jogar", [t for t, _ in T.HELP] + ["Voltar"],
                      on_select=lambda i, item: close_help() if item == "Voltar"
                      else game.say(T.HELP[i][1]),
                      on_back=close_help, sounds=menu_sounds)


# --- controles -------------------------------------------------------------------
@game.on_button
def button(b, st, ms):
    phase = state["phase"]
    if phase == "expediente" and state["service"] is not None:
        service_button(state["service"], b, st)
    elif phase == "limpeza" and state["cleaning"] is not None:
        cleaning_button(state["cleaning"], b, st)


def service_button(s, b, st):
    if st == a11y.UP:
        if b == "b":
            s.action_up()
        return
    if st == a11y.REPEAT:
        if b in ("left", "right"):
            s.step(-1 if b == "left" else 1)
        return
    if b == "up":
        s.go_layer(0)
    elif b == "down":
        s.go_layer(1)
    elif b in ("left", "right"):
        s.step(-1 if b == "left" else 1)
    elif b == "b":
        s.action_down()
    elif b == "a":
        layer, index = s.layer, s.index[s.layer]
        game.say("%s, %s." % (s.spot_name(layer, index), s.describe(layer, index, detail=True)))
    elif b == "x":
        game.say(s.hands_text())
    elif b == "y":
        game.say(s.status_text())
    elif b == "select":
        game.say(s.summary_text())
    elif b in ("l1", "r1"):
        s.jump(-1 if b == "l1" else 1)
    elif b == "start":
        open_pause()


def cleaning_button(c, b, st):
    if st == a11y.UP:
        if b == "b":
            c.action_up()
        return
    if st == a11y.REPEAT:
        if b in ("left", "right") and not c.scrubbing:
            c.step(-1 if b == "left" else 1)
        return
    if b == "up":
        c.go_layer(0)
    elif b == "down":
        c.go_layer(1)
    elif b in ("left", "right"):
        c.step(-1 if b == "left" else 1)
    elif b == "b":
        c.action_down()
    elif b == "a":
        c.back()
    elif b in ("y", "select"):
        game.say(c.left_text())
    elif b in ("l1", "r1"):
        c.jump(-1 if b == "l1" else 1)
    elif b == "start":
        open_pause()


@game.on_update
def update(dt):
    if state["service"] is not None:
        state["service"].update(dt)
    elif state["cleaning"] is not None:
        state["cleaning"].update(dt)


@game.on_start
def start():
    open_main(announce_help=True)


game.run()
