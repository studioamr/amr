#!/usr/bin/env python3
"""BATUQUE — paleta TECH HOUSE con SWING brasileño (estilo Volkoder real).

Investigado a fondo: Volkoder NO es "brazilian bass" — es tech house rítmico
(Hot Creations/Diynamic/CUFF), su brasileñidad es el SWING y la PERCUSIÓN.
Marcas del sonido:
  • BAJO "WONKY/WOBBLING": mono, medio-forward, ROLLING en el pocket con el kick,
    con un filtro resonante que se MUEVE (LFO wobble) — nada de donk plucky; es
    un bajo coiled/gritty que ronronea. LA ESTRELLA, sidechaineado duro.
  • Kick tech house limpio y punchy; hats MUY swingueados + percusión tribal/conga
    que serpentea alrededor del kick ("shuffle harder than a packed terrace").
  • VOCAL CHOPS picados/afinados y VOCODER/computarizados (su gancho-lead).
  • Stabs rítmicos secos, lead "cósmico" que corta, pads brillantes en comedowns.
  • Mezcla chunky, un poco cruda/sleazy — groove sobre brillo.
Paleta propia — NADA compartido con otros discos. Filtros con freq ESCALAR
(barridos por segmento, nunca arrays a bp/lp)."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

MINP = [0, 3, 5, 7, 10]                        # pentatónica menor
MAJP = [0, 2, 4, 7, 9]                         # pentatónica mayor (set en Do mayor = 8B, brillante)
def pdeg(root, d, o=0, scale=MAJP): return root + scale[d % 5] + 12 * (d // 5 + o)

# ==================================================================== BATERÍA
def kick_house():
    """kick tech house: 909 punchy + cuerpo boomy corto, afinado a Do (~65Hz)."""
    n = int(0.38 * SR); t = np.arange(n) / SR
    f = 65.0 + 95.0 * np.exp(-t / 0.028)                    # glide ~160→65Hz en ~28ms
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.125)
    clic = np.exp(-t / 0.003) * (np.sin(2 * np.pi * 1650 * t) + 0.6 * np.random.default_rng(1).standard_normal(n))
    x = sat(body.astype(np.float32), 1.5, 0.05) + 0.30 * clic.astype(np.float32)
    return lp(x, 3400, 2) * 0.92

def clap(rng):
    """clap en 2&4: 4 ráfagas de ruido bandpass + cola con reverb corto."""
    n = int(0.24 * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for d in (0.0, 0.009, 0.018, 0.028):
        off = int(d * SR)
        seg = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.010)
        x[off:] += seg[:n - off] * 0.8
    tail = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.10) * 0.55   # "rebote"
    return bp((x + tail), 1100, 6200, 2) * 0.6

def snare_ghost(rng):
    """ghost snare suave (empujado por el swing, antes del 3er/7mo kick)."""
    n = int(0.10 * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.035)
    return bp(nz, 1600, 6500, 2) * 0.26

def hat(rng, open_=False):
    """closed corto / open offbeat — ruido HPF ~7.5k con filo metálico."""
    dec = (0.17 if open_ else 0.030) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32)
    x += 0.35 * np.sign(np.sin(2 * np.pi * 7600 * t)).astype(np.float32)
    x *= np.exp(-t / dec)
    return hp(x, 7500, 2) * (0.24 if open_ else 0.34) * rng.uniform(0.85, 1.0)

def shaker(rng):
    n = int(0.055 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * (np.exp(-t / 0.028) * (1 - np.exp(-t / 0.006)))
    return bp(x, 4000, 8600, 2) * rng.uniform(0.5, 0.8)

def conga(f0, rng):
    """conga/tumbao afinada: sine con caída de pitch + transiente de piel."""
    n = int(0.16 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.5 * np.exp(-t / 0.012))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.075)
    tk = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.006) * 0.5
    return sat((tone.astype(np.float32) + bp(tk, 900, 4000, 2)) * 0.7, 1.25, 0.06)

def rimshot(rng):
    n = int(0.05 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * rng.uniform(1600, 1800) * t) * np.exp(-t / 0.007)
    return bp(x.astype(np.float32), 1000, 4200, 2) * 0.5

def tom(f0, rng):
    n = int(0.28 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.4 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)
    return sat(x.astype(np.float32) * 0.7, 1.25, 0.06)

# ==================================================================== EL BAJO WONKY (la estrella)
def bass_wonky(f, dur, rng, wob_hz=6.3, clo=170, hi=1500, drive=2.2, glide_from=None, res=1.0):
    """bajo tech-house 'wonky/wobbling': saws detune + square + sub (coil reese-ish)
    por un LP RESONANTE cuyo cutoff lo MUEVE un LFO (wob_hz) entre `clo`..`chi` —
    ese barrido resonante es el 'wonky'. Mono, medio-forward, gritty, rolling.
    Click de pitch corto al ataque para definición; drive tanh para armónicos."""
    n = max(8, int(dur * SR)); t = np.arange(n) / SR
    click = np.exp(-t / 0.010)
    fmul = 2.0 ** (12.0 / 12.0 * click)                     # tick +12st ~10ms (sutil, no donk)
    if glide_from:
        fbase = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.045)
    else:
        fbase = f * np.ones(n, np.float32)
    ph = 2 * np.pi * np.cumsum(fbase * fmul) / SR
    x = np.zeros(n, np.float32)
    for det in (-13, 0, 11):                                # coil: saws desafinados
        phd = ph * 2 ** (det / 1200) + rng.uniform(0, 6)
        x += (2 * ((phd / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.36
    x += np.sign(np.sin(ph * 0.5 + 0.3)).astype(np.float32) * 0.18   # square una 8va abajo = grosor
    x += np.sin(ph).astype(np.float32) * 0.72               # sub al fundamental = peso mono
    # LFO wobble del cutoff (senoidal, fase aleatoria) con leve caída de nota
    lfo = 0.5 - 0.5 * np.cos(2 * np.pi * wob_hz * t + rng.uniform(0, 6))
    cut = clo + (hi - clo) * lfo
    cut *= (0.55 + 0.45 * np.minimum(1.0, t / 0.004))       # ataque
    seg = max(1, n // 40); body = np.zeros(n, np.float32); reso = np.zeros(n, np.float32)
    for k in range(40):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        c = float(cut[min(n - 1, (a + b_) // 2)])
        body[a:b_] = lp(x[a:b_], c, 2)
        reso[a:b_] = bp(x[a:b_], c * 0.85, c * 1.18, 2)     # pico resonante que barre = wonky
    out = body + reso * (0.75 * res)
    amp = np.minimum(1.0, t / 0.004) * np.exp(-np.maximum(0.0, t - dur * 0.7) / 0.05)
    out = sat(out * amp.astype(np.float32), drive, 0.06)
    return sat_warm(out) * 0.8

def bass_roll(f, rng):
    """nota corta rolling (16vos en picos): wobble más rápido, cuerpo apretado."""
    return bass_wonky(f, 0.12, rng, wob_hz=12.6, clo=190, hi=1400, drive=2.4)

# ==================================================================== VOCAL CHOPS (el gancho)
_VOW = dict(a=((760, 1.0), (1220, 0.55), (2600, 0.25)),
            e=((540, 1.0), (1800, 0.45), (2600, 0.2)),
            i=((320, 1.0), (2300, 0.4), (3200, 0.2)),
            o=((520, 1.0), (900, 0.55), (2500, 0.2)),
            u=((360, 1.0), (860, 0.4), (2400, 0.15)))

def vox_chop(f, dur, rng, vow='o'):
    """chop vocal afinado: fuente glotal rica por 3 formantes (vocal), stab corto.
    Se toca como instrumento re-pitcheando por grados = el hook del género."""
    F = _VOW[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    src = np.zeros(n, np.float32)
    for h in range(1, 20):
        src += (np.sin(h * ph + rng.uniform(0, 0.3)) / h ** 1.1).astype(np.float32)
    env = np.minimum(1.0, t / 0.012) * np.exp(-np.maximum(0.0, t - dur * 0.45) / 0.07)
    src *= env.astype(np.float32)
    out = sum(bp(src, fq * 0.86, fq * 1.16, 2) * g for fq, g in F)
    out += src * 0.05
    oct_ = 0.4 * bp(src, F[0][0] * 0.43, F[0][0] * 0.58, 2)  # doble una 8va abajo = grosor
    return sat((out + oct_) * 0.6, 1.25, 0.08)

def vox_vocoder(f, dur, rng, vow='e'):
    """chop vocal VOCODER/computarizado (el 'sharp computerized vocal' de Volkoder):
    portadora saw por formantes + ring-mod leve = frío y robótico, corta la mezcla."""
    F = _VOW[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    saw = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    env = np.minimum(1.0, t / 0.008) * np.exp(-np.maximum(0.0, t - dur * 0.5) / 0.055)
    saw *= env.astype(np.float32)
    out = sum(bp(saw, fq * 0.9, fq * 1.1, 2) * g for fq, g in F)
    ring = np.sin(2 * np.pi * (f * 0.5) * t)                # ring-mod = timbre metálico
    return sat((out * (0.72 + 0.28 * ring)).astype(np.float32) * 0.6, 1.3, 0.1)

def vox_air(f, dur, rng, vow='a'):
    """chop vocal largo/etéreo con aire y cola — para el breakdown."""
    F = _VOW[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * (t + 0.003 * np.sin(2 * np.pi * 5.0 * t + rng.uniform(0, 6)))
    src = np.zeros(n, np.float32)
    for h in range(1, 24):
        src += (np.sin(h * ph) / h ** 1.15).astype(np.float32)
    env = np.minimum(1.0, t / 0.08) * np.minimum(1.0, np.maximum(0.0, dur - t) / 0.4)
    src *= env.astype(np.float32)
    out = sum(bp(src, fq * 0.87, fq * 1.15, 2) * g for fq, g in F)
    breath = hp(rng.standard_normal(n).astype(np.float32), 3000, 2) * env.astype(np.float32) * 0.05
    return sat((out + breath) * 0.55, 1.2, 0.06)

# ==================================================================== STABS / ARMONÍA
def pluck(f, dur, rng):
    """pluck brillante: saw por LP con decay rápido — stab rítmico seco."""
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    x = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    cenv = 400 + 4200 * np.exp(-t / 0.05)
    seg = max(1, n // 10); out = np.zeros(n, np.float32)
    for k in range(10):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        out[a:b_] = lp(x[a:b_], float(cenv[min(n - 1, (a + b_) // 2)]), 2)
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.09)
    return sat(out * env.astype(np.float32) * 0.5, 1.3, 0.08)

def organ_stab(ms, dur, rng):
    """stab de órgano (drawbars aditivos): fundamental + octava + 5ta + 2oct."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    draw = [(1.0, 1.0), (2.0, 0.7), (3.0, 0.45), (4.0, 0.35)]
    for m in ms:
        f = midi_f(m)
        for r, g in draw:
            x += (np.sin(2 * np.pi * f * r * t) * g).astype(np.float32)
    env = np.minimum(1.0, t / 0.006) * np.exp(-np.maximum(0.0, t - dur * 0.4) / 0.06)
    x *= env.astype(np.float32) / max(1, len(ms))
    return sat(lp(x, 5000, 2) * 0.4, 1.3, 0.09)

def saw_chord(ms, dur, rng, cut=1900):
    """acorde supersaw filtrado — para breakdowns brillantes/comedown."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-12, -5, 0, 6, 11):
            fv = f * 2 ** (det / 1200)
            ph = 2 * np.pi * fv * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.11
    env = np.minimum(1.0, t / 0.5) * np.minimum(1.0, np.maximum(0.0, dur - t) / 0.6)
    return lp(x * env.astype(np.float32), cut, 2) * 0.5

def lead_cosmic(f, dur, rng, glide_from=None):
    """lead 'cósmico-animado' que corta (She Kisses): saws detune por filtro con
    LFO + vibrato + glide; para el 2do drop y remates."""
    n = int(dur * SR); t = np.arange(n) / SR
    if glide_from:
        fr = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.06)
    else:
        fr = f * np.ones(n, np.float32)
    vib = 2.0 ** (6.0 * np.sin(2 * np.pi * 5.2 * t + rng.uniform(0, 6)) / 1200)
    x = np.zeros(n, np.float32)
    for det in (-10, 0, 11):
        ph = 2 * np.pi * np.cumsum(fr * vib * 2 ** (det / 1200)) / SR + rng.uniform(0, 6)
        x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.33
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 / max(0.1, dur) * 4 * t + rng.uniform(0, 6))
    seg = max(1, n // 10); out = np.zeros(n, np.float32)
    for k in range(10):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        c = 700 + 3800 * float(lfo[min(n - 1, (a + b_) // 2)]) ** 2
        out[a:b_] = x[a:b_] * 0.4 + bp(x[a:b_], c * 0.6, c * 1.5, 2) * 1.2
    env = np.minimum(1.0, t / 0.02) * np.exp(-np.maximum(0.0, t - dur * 0.8) / 0.16)
    return sat(out * env.astype(np.float32) * 0.42, 1.3, 0.08)

def pad_warm(ms, dur, rng):
    """pad cálido/brillante de fondo (comedowns e intros)."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-8, 0, 7):
            fv = f * 2 ** (det / 1200)
            ph = 2 * np.pi * fv * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.14
    env = np.minimum(1.0, t / 0.9) * np.minimum(1.0, np.maximum(0.0, dur - t) / 1.0)
    return lp(x * env.astype(np.float32), 1600, 2) * 0.42

# ==================================================================== FX de transición
def riser(dur, rng):
    """uplifter: ruido cuyo bandpass sube exponencial + swell de volumen."""
    n = int(dur * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    nz = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32); seg = max(1, n // 28)
    for k in range(28):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        p = float(prog[min(n - 1, (a + b_) // 2)])
        lo = 300 + 5000 * p ** 2; hi = 700 + 9000 * p ** 2
        out[a:b_] = bp(nz[a:b_], lo, hi, 2)
    return (out * (prog ** 1.6)).astype(np.float32) * 0.4

def downlift(rng):
    """downlifter: barrido de pitch que cae al arranque de una sección nueva."""
    n = int(0.6 * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    f = 1100 * (1 - prog) + 70
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    return sat(bp(x * np.exp(-t / 0.3), 200, 5000, 2), 1.3, 0.1) * 0.4

def impact(rng):
    """sub-drop/boom cinemático en el beat 1 del drop."""
    n = int(1.3 * SR); t = np.arange(n) / SR
    f = 46 + 90 * np.exp(-t / 0.05)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    nz = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.5)
    return (sat(boom.astype(np.float32), 1.3, 0.05) + bp(nz, 200, 3800, 2) * 0.45) * 0.6

def revcrash(dur, rng):
    """crash reverso hacia el drop (swell de ruido brillante)."""
    n = int(dur * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    x = hp(rng.standard_normal(n).astype(np.float32), 5000, 2)
    return (x * (prog ** 2.2)).astype(np.float32) * 0.3

def noise_sweep(dur, rng, up=True):
    """barrido de ruido filtrado para fades DJ entre secciones."""
    n = int(dur * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    nz = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32); seg = max(1, n // 16)
    for k in range(16):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        p = float(prog[min(n - 1, (a + b_) // 2)]);  p = p if up else 1 - p
        out[a:b_] = bp(nz[a:b_], 400 + 6000 * p, 900 + 9000 * p, 2)
    return out * 0.14

if __name__ == '__main__':
    from dream_core import wav_write, spectrum_pct
    rng = np.random.default_rng(11)
    bpm = 128; spb = int(SR * 240 / bpm); s16 = spb / 16
    n = spb * 2; mix = np.zeros(n, np.float32)
    def put(buf, pos, x, g=1.0):
        pos = int(pos); e = min(len(buf), pos + len(x))
        if e > pos: buf[pos:e] += x[:e - pos] * g
    K = kick_house(); SWING = 0.62                              # ~62% swing (empuja el 2do 16vo)
    for bar in range(2):
        base = bar * spb
        for b in range(4): put(mix, base + b * 4 * s16, K)
        put(mix, base + 4 * s16, clap(rng), 0.8); put(mix, base + 12 * s16, clap(rng), 0.8)
        for s in range(16):
            sw = base + s * s16 + ((SWING - 0.5) * 2 * s16 if s % 2 else 0)
            put(mix, sw, hat(rng, open_=(s % 4 == 2)), 0.4 if s % 2 else 0.26)
        for s in range(0, 16, 2): put(mix, base + s * s16, shaker(rng), 0.3)
        for s in (2, 6, 11, 14): put(mix, base + s * s16, conga(midi_f(48 if s % 3 else 55), rng), 0.4)
        put(mix, base + 6 * s16, snare_ghost(rng), 0.6)         # ghost antes del 3er kick
        # bajo WONKY rolling en el pocket (Do): notas cortas con wobble
        pat = [(0, 36, 2), (4, 36, 1), (6, 43, 1), (8, 36, 2), (12, 36, 1), (14, 48, 1)]
        for st, m, ln in pat:
            put(mix, base + st * s16, bass_wonky(midi_f(m - 12), ln * s16 / SR * 1.5, rng), 0.95)
    # vocal chops (afinado + vocoder) call-response con el bajo, en Do mayor
    put(mix, int(4 * s16), vox_chop(midi_f(pdeg(72, 0)), 0.2, rng, 'o'), 0.6)
    put(mix, int(10 * s16), vox_vocoder(midi_f(pdeg(72, 2)), 0.16, rng, 'e'), 0.55)
    put(mix, int(20 * s16), vox_chop(midi_f(pdeg(72, 4)), 0.2, rng, 'a'), 0.6)
    put(mix, int(26 * s16), vox_vocoder(midi_f(pdeg(72, 1)), 0.16, rng, 'e'), 0.55)
    put(mix, spb + 8 * s16, pluck(midi_f(72), 0.18, rng), 0.5)
    mix /= max(1e-9, np.abs(mix).max())
    wav_write('_test_batuque.wav', np.stack([mix, mix]))
    print('BATUQUE groove:', {k: round(v, 1) for k, v in spectrum_pct(mix).items()})
    print('_test_batuque.wav listo')
