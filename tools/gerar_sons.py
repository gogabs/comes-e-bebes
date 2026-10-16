#!/usr/bin/env python3
"""Gera os sons provisórios do Comes e Bebes, só com a biblioteca padrão.

São esboços para o jogo funcionar: sininho, chiado, fogo, louça. Para trocar
um som, ponha um arquivo com o mesmo nome em sounds/ (WAV ou OGG) e apague o
provisório. Os sons contínuos (chiado, fritura, fogo, liquidificador,
raspar) tocam em laço.

    python3 tools/gerar_sons.py
"""
import math
import os
import random
import struct
import wave

RATE = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")
rng = random.Random(11)


def n(sec):
    return int(RATE * sec)


def tone(freq, sec, harmonics=1, decay=0.15, glide=0.0, attack=0.005):
    out, phase = [], 0.0
    for k in range(n(sec)):
        t = k / RATE
        f = freq * (1 + glide * t / sec)
        phase += 2 * math.pi * f / RATE
        v = sum(math.sin(phase * h) / h for h in range(1, harmonics + 1))
        out.append(v * min(1.0, t / attack) * math.exp(-t / decay))
    return out


def bell(freq, sec=0.6, decay=0.25):
    """Sino: parciais fora da série harmônica."""
    return mix(*[[v * a for v in tone(freq * r, sec, 1, decay * d)]
                 for r, a, d in ((1, 1, 1), (2.76, 0.5, 0.6), (5.4, 0.25, 0.4))])


def noise(sec, smooth=0.3, decay=None, rise=False, shape=None):
    """Ruído; smooth perto de 1 deixa mais grave."""
    out, last = [], 0.0
    total = n(sec)
    for k in range(total):
        t = k / RATE
        last = smooth * last + (1 - smooth) * rng.uniform(-1, 1)
        if shape:
            env = shape(t / sec)
        elif rise:
            env = t / sec
        elif decay:
            env = math.exp(-t / decay)
        else:
            env = 1.0
        out.append(last * env)
    return out


def sweep(f0, f1, sec, harmonics=3, decay=None):
    out, phase = [], 0.0
    for k in range(n(sec)):
        t = k / RATE
        f = f0 * (f1 / f0) ** (t / sec)
        phase += 2 * math.pi * f / RATE
        env = min(1.0, t / 0.02) * ((1 - t / sec) if decay is None else math.exp(-t / decay))
        out.append(env * sum(math.sin(phase * h) / h for h in range(1, harmonics + 1)))
    return out


def saw(freq, sec, tremolo=0.0, trem_rate=0.0):
    out = []
    for k in range(n(sec)):
        t = k / RATE
        v = 2 * ((t * freq) % 1.0) - 1
        out.append(v * (1 - tremolo * (0.5 + 0.5 * math.sin(2 * math.pi * trem_rate * t))))
    return out


def mix(*parts, offsets=None, gains=None):
    offsets = offsets or [0.0] * len(parts)
    gains = gains or [1.0] * len(parts)
    length = max(n(o) + len(p) for p, o in zip(parts, offsets))
    out = [0.0] * length
    for p, o, g in zip(parts, offsets, gains):
        start = n(o)
        for k, v in enumerate(p):
            out[start + k] += v * g
    return out


def pops(sec, count, smooth=0.5, length=0.012):
    """Estalos espalhados: gordura, fogo, fritura."""
    parts = [noise(length, smooth, decay=length / 3) for _ in range(count)]
    offsets = [rng.uniform(0, sec - length) for _ in range(count)]
    gains = [rng.uniform(0.3, 1.0) for _ in range(count)]
    out = mix(*parts, offsets=offsets, gains=gains)
    return out + [0.0] * max(0, n(sec) - len(out))


def env(samples, shape):
    total = len(samples)
    return [v * shape(k / total) for k, v in enumerate(samples)]


def hump(x):
    return math.sin(math.pi * x)


def write(name, samples, gain=0.8, loop=False):
    peak = max(1e-9, max(abs(v) for v in samples))
    fade = 0 if loop else min(len(samples), n(0.01))
    data = bytearray()
    for k, v in enumerate(samples):
        if fade and k >= len(samples) - fade:
            v *= (len(samples) - k) / float(fade)
        data += struct.pack("<h", int(max(-1, min(1, v / peak * gain)) * 32767))
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(bytes(data))


def crossfade_loop(samples, sec=0.1):
    """Junta o fim no começo para o laço não estalar."""
    k = n(sec)
    head, body, tail = samples[:k], samples[k:-k], samples[-k:]
    joined = [t * (1 - i / k) + h * (i / k) for i, (h, t) in enumerate(zip(head, tail))]
    return body + joined


def main():
    os.makedirs(OUT, exist_ok=True)
    # salão
    write("porta", mix(bell(1568, 0.7, 0.3), bell(2093, 0.7, 0.25), offsets=[0, 0.09]), 0.6)
    write("porta_fecha", mix(bell(1175, 0.8, 0.3), noise(0.15, 0.85, decay=0.04),
                             offsets=[0, 0.1]), 0.6)
    write("cadeira", env(mix(noise(0.35, 0.6), saw(140, 0.35, 0.6, 30), gains=[1, 0.3]), hump), 0.55)
    write("chamar", bell(2637, 0.8, 0.35), 0.6)
    write("impaciencia1", mix(*[noise(0.03, 0.85, decay=0.01) for _ in range(4)],
                              offsets=[0, 0.09, 0.18, 0.27]), 0.6)
    write("impaciencia2", noise(0.8, 0.9, shape=lambda x: hump(x) * (1 - 0.5 * x)), 0.5)
    write("impaciencia3", mix(tone(130, 0.5, 6, 0.4, glide=-0.2, attack=0.05),
                              tone(137, 0.5, 6, 0.4, glide=-0.2, attack=0.05)), 0.6)
    write("resmungo", mix(tone(120, 0.7, 6, 0.5, glide=-0.3, attack=0.05),
                          noise(0.15, 0.85, decay=0.04), offsets=[0, 0.75]), 0.6)
    write("caixa", mix(noise(0.05, 0.3, decay=0.015), bell(2000, 0.6, 0.25), bell(2500, 0.6, 0.2),
                       offsets=[0, 0.06, 0.06]), 0.6)
    write("gorjeta", mix(*[tone(rng.uniform(3000, 5000), 0.12, 2, 0.04) for _ in range(5)],
                         offsets=[0, 0.05, 0.11, 0.15, 0.22]), 0.5)
    write("anotar", mix(*[noise(0.06, 0.1, decay=0.03) for _ in range(5)],
                        offsets=[0, 0.07, 0.15, 0.22, 0.3]), 0.4)
    write("errado", mix(tone(311, 0.18, 4, 0.1), tone(233, 0.25, 4, 0.12), offsets=[0, 0.15]), 0.55)
    write("servir", mix(bell(1300, 0.3, 0.08), noise(0.06, 0.8, decay=0.02)), 0.6)
    write("louca", mix(*[bell(rng.uniform(1800, 2600), 0.25, 0.06) for _ in range(4)],
                       offsets=[0, 0.07, 0.13, 0.22]), 0.5)
    # cozinha
    write("aviso_virar", mix(tone(900, 0.08, 2, 0.03), tone(900, 0.08, 2, 0.03),
                             offsets=[0, 0.12]), 0.6)
    write("ponto", bell(1760, 0.6, 0.25), 0.65)
    write("passando", mix(sweep(600, 900, 0.18, 2), sweep(600, 900, 0.18, 2), offsets=[0, 0.22]), 0.6)
    write("fumaca", mix(noise(0.8, 0.2, rise=True), *[noise(0.12, 0.8, decay=0.05)
                                                     for _ in range(2)],
                        offsets=[0, 0.85, 1.05]), 0.6)
    write("alarme", mix(*[tone(f, 0.18, 3, 1.0) for f in (880, 660, 880, 660)],
                        offsets=[0, 0.2, 0.4, 0.6]), 0.6)
    write("fogo", crossfade_loop(mix(noise(2.2, 0.92), pops(2.2, 40, 0.3))), 0.7, loop=True)
    write("chiado", crossfade_loop(mix(noise(1.6, 0.05), pops(1.6, 25, 0.1, 0.006),
                                       gains=[0.6, 1.0])), 0.45, loop=True)
    write("fritura", crossfade_loop(mix(noise(1.6, 0.4), pops(1.6, 30, 0.7, 0.02),
                                        gains=[0.4, 1.0])), 0.5, loop=True)
    write("liquidificador", crossfade_loop(mix(saw(110, 1.2, 0.2, 8), noise(1.2, 0.3),
                                               gains=[0.6, 0.4])), 0.45, loop=True)
    write("extintor", noise(1.8, 0.0, shape=lambda x: min(1.0, x * 10) * (1 - x) ** 0.5), 0.6)
    write("pegar", noise(0.04, 0.5, decay=0.012), 0.5)
    write("virar", mix(noise(0.12, 0.05, shape=hump), bell(900, 0.3, 0.08), offsets=[0, 0.1]), 0.55)
    write("sacudir", mix(*[noise(0.07, 0.2, decay=0.03) for _ in range(4)],
                         offsets=[0, 0.1, 0.2, 0.3]), 0.55)
    write("colocar", mix(noise(0.05, 0.6, decay=0.02), noise(0.6, 0.05, decay=0.3),
                         offsets=[0, 0.03]), 0.5)
    write("liso", mix(*[tone(f, 0.3, 2, 0.15) for f in (784, 988, 1175)],
                      offsets=[0, 0.07, 0.14]), 0.5)
    write("servir_copo", mix(noise(0.5, 0.6, shape=hump), sweep(300, 700, 0.5, 1),
                             gains=[0.7, 0.3]), 0.5)
    write("ingrediente", tone(520, 0.1, 3, 0.04), 0.45)
    write("montar", mix(tone(659, 0.25, 2, 0.12), tone(988, 0.3, 2, 0.15), offsets=[0, 0.09]), 0.55)
    write("lixo", mix(noise(0.1, 0.9, decay=0.04), noise(0.4, 0.4, shape=hump),
                      offsets=[0, 0.05], gains=[1, 0.4]), 0.55)
    # interface
    write("foco", tone(1000, 0.05, 2, 0.015), 0.35)
    write("borda", tone(90, 0.14, 3, 0.05), 0.7)
    write("menu_mover", tone(660, 0.06, 2, 0.03), 0.4)
    write("menu_confirmar", mix(tone(660, 0.12, 2, 0.06), tone(990, 0.12, 2, 0.06),
                                offsets=[0.0, 0.05]), 0.5)
    write("manha", mix(*[tone(f, 0.5, 2, 0.25) for f in (523, 659, 784, 1047)],
                       offsets=[0, 0.12, 0.24, 0.36]), 0.55)
    write("noite", mix(*[tone(f, 0.8, 2, 0.4) for f in (784, 659, 523, 392)],
                       offsets=[0, 0.25, 0.5, 0.75]), 0.5)
    write("silencio", mix(*[tone(f, 1.0, 2, 0.5) for f in (392, 494, 587)],
                          offsets=[0, 0.05, 0.1]), 0.45)
    write("vigilancia", mix(*[noise(0.08, 0.9, decay=0.03) for _ in range(3)],
                            tone(2200, 0.4, 1, 0.3, glide=0.1),
                            offsets=[0, 0.25, 0.5, 0.9]), 0.7)
    write("interdicao", mix(tone(110, 1.5, 6, 0.8), tone(116.5, 1.5, 6, 0.8),
                            tone(155, 1.5, 4, 0.7)), 0.7)
    # limpeza
    write("mosca", env(saw(210, 0.6, 0.6, 7), hump), 0.35)
    write("passos_grudando", mix(noise(0.08, 0.85, decay=0.03), noise(0.12, 0.2, decay=0.05),
                                 noise(0.08, 0.85, decay=0.03), noise(0.12, 0.2, decay=0.05),
                                 offsets=[0, 0.05, 0.4, 0.45]), 0.5)
    write("gordura", pops(0.5, 8, 0.2, 0.01), 0.5)
    write("lixo_cheio", noise(0.5, 0.5, shape=hump), 0.4)
    write("pano", noise(0.15, 0.3, shape=hump), 0.5)
    write("brilho", mix(*[tone(f, 0.25, 1, 0.12) for f in (1568, 2093, 2637, 3136)],
                        offsets=[0, 0.05, 0.1, 0.15]), 0.45)
    write("raspar", crossfade_loop(mix(noise(1.0, 0.05, shape=lambda x: 0.6 + 0.4 * math.sin(
        2 * math.pi * 4 * x) ** 2), pops(1.0, 10, 0.2, 0.008))), 0.5, loop=True)
    write("lavar", mix(noise(0.3, 0.3, shape=hump), bell(2200, 0.25, 0.06),
                       offsets=[0, 0.2], gains=[0.6, 1.0]), 0.5)
    write("passos", mix(*[noise(0.08, 0.9, decay=0.03) for _ in range(4)],
                        offsets=[0, 0.45, 0.9, 1.35]), 0.6)
    write("lixo_fora", mix(noise(0.08, 0.6, decay=0.03), bell(600, 0.4, 0.1), offsets=[0, 0.02]), 0.6)
    print("sons gerados em %s" % os.path.normpath(OUT))


if __name__ == "__main__":
    main()
