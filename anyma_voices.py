#!/usr/bin/env python3
"""ORÁCULO — paleta melodic techno cinemático sci-fi (estilo Anyma / Afterlife).
Investigado a fondo cómo construye Anyma sus sets: intro cinemático sin kick,
BPM que sube 122→126, keys menores con giro a MAYOR relativa en los picos, el
LEAD SUPERSAW GATED (su firma, con LFO de stutter), stabs FM (donde vive el
grit), pads cinemáticos anchos, voz-musa etérea + narración robótica, y MUCHO
efecto (reverb enorme, delays, risers, impactos, reverse swells).

⚠️ BAJO LIMPIO (sub sine+saw −2/−3 oct por LP suave, sidechain, sin drive duro).
⚠️ MÁS EFECTOS (André): todo respira en reverb/espacio; NADA seco.
Paleta propia. Filtros con freq ESCALAR (barridos por segmento)."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm, fconv

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

# --- reverbs cinemáticas (IRs de ruido exponencial, para el "espacio" Anyma)
def _ir(decay, tone, seed):
    n = int(decay * SR); rng = np.random.default_rng(seed)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 6.2, n)).astype(np.float32)
    ir = lp(ir, tone, 2); ir /= np.sqrt((ir ** 2).sum()) + 1e-12
    return ir
IR_HALL = _ir(3.8, 5200, 41)          # reverb grande (leads/pads)
IR_PLATE = _ir(2.0, 6800, 42)         # plate (voz/stabs)

def reverb(x, ir, mix=0.3):
    wet = fconv(x, ir)
    return x + wet[:len(x)] * mix

# ==================================================================== DRUMS melodic techno
def kick_mt():
    """kick melodic techno: redondo, profundo, cola cálida (no clicky)."""
    n = int(0.44 * SR); t = np.arange(n) / SR
    f = 50.0 + 70.0 * np.exp(-t / 0.030)               # glide suave 120→50
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.20)
    sub = np.sin(2 * np.pi * 46 * t) * np.exp(-t / 0.13) * 0.5
    clk = np.exp(-t / 0.004) * np.sin(2 * np.pi * 900 * t) * 0.18
    x = sat((body + sub).astype(np.float32), 1.3, 0.04) + clk.astype(np.float32)
    return lp(x, 2600, 2) * 0.92

def clap(rng):
    n = int(0.26 * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for d in (0.0, 0.009, 0.018):
        off = int(d * SR)
        x[off:] += (rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.012))[:n - off] * 0.8
    tail = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.13) * 0.6
    y = bp((x + tail), 1100, 5200, 2) * 0.5
    return reverb(y, IR_PLATE, 0.35)                   # clap con cola (espacio)

def hat(rng, open_=False):
    dec = (0.22 if open_ else 0.026) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32)
    x += 0.28 * np.sign(np.sin(2 * np.pi * 8400 * t)).astype(np.float32)
    x *= np.exp(-t / dec)
    return hp(x, 8200, 2) * (0.2 if open_ else 0.28) * rng.uniform(0.85, 1.0)

def shaker(rng):
    n = int(0.05 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * (np.exp(-t / 0.026) * (1 - np.exp(-t / 0.006)))
    return bp(x, 4400, 9200, 2) * rng.uniform(0.4, 0.7)

def perc_metal(rng, f0=520):
    n = int(0.2 * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for r in (1.0, 1.74, 2.61, 3.44):
        x += np.sin(2 * np.pi * f0 * r * t).astype(np.float32) * (1.0 / r)
    x *= np.exp(-t / 0.06)
    return reverb(bp(x * 0.35, 900, 7000, 2), IR_PLATE, 0.3) * 0.4

# ==================================================================== EL BAJO (LIMPIO)
def bass_mt(f, dur, rng, cutoff=440, glide_from=None):
    """sub rolling melodic techno: sine sub (−2 oct) + saw suave (−1 oct) por LP
    suave, sin resonancia ni drive agresivo. Limpio, redondo, en el pocket."""
    n = max(8, int(dur * SR)); t = np.arange(n) / SR
    if glide_from:
        fr = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.05)
        ph = 2 * np.pi * np.cumsum(fr) / SR
    else:
        ph = 2 * np.pi * f * t
    sub = np.sin(ph * 0.5).astype(np.float32)                    # una octava abajo = peso
    sine = np.sin(ph).astype(np.float32)
    saw = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    x = sub * 0.55 + sine * 0.6 + saw * 0.16
    env = np.minimum(1.0, t / 0.008) * np.exp(-np.maximum(0.0, t - dur * 0.72) / 0.06)
    x = lp(x * env.astype(np.float32), cutoff, 2)
    return sat_warm(x) * 0.6

# ==================================================================== LEAD SUPERSAW GATED (la firma Anyma)
def lead_gated(f, dur, rng, gate_hz=8.0, glide_from=None, cut=2600):
    """el lead supersaw gated de Anyma: 6+2 saws detune, un LFO de STUTTER que
    corta el volumen (gating), filtro que abre, y MUCHO reverb+delay-friendly."""
    n = int(dur * SR); t = np.arange(n) / SR
    if glide_from:
        fr = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.06)
    else:
        fr = f * np.ones(n, np.float32)
    vib = 2.0 ** (4.0 * np.sin(2 * np.pi * 4.6 * t + rng.uniform(0, 6)) / 1200)
    x = np.zeros(n, np.float32)
    for det in (-14, -8, -3, 3, 8, 14):                          # supersaw 6 voces
        ph = 2 * np.pi * np.cumsum(fr * vib * 2 ** (det / 1200)) / SR + rng.uniform(0, 6)
        x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.16
    # filtro que abre (wow) en el ataque
    cenv = 700 + (cut - 700) * np.minimum(1.0, t / (dur * 0.45))
    seg = max(1, n // 10); out = np.zeros(n, np.float32)
    for k in range(10):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        out[a:b_] = lp(x[a:b_], float(cenv[min(n - 1, (a + b_) // 2)]), 2)
    # GATE/STUTTER: LFO cuadrado suavizado corta el volumen
    lfo = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * gate_hz * t))
    lfo = lp(lfo.astype(np.float32), 90, 1)                      # suaviza los flancos
    gate = 0.35 + 0.65 * lfo
    env = np.minimum(1.0, t / 0.02) * np.exp(-np.maximum(0.0, t - dur * 0.85) / 0.2)
    y = sat(out * (env * gate).astype(np.float32) * 0.4, 1.2, 0.05)
    return reverb(y, IR_HALL, 0.34)                              # espacio grande

def fm_stab(f, dur, rng):
    """stab FM metálico (donde vive el grit): saw FM-modulado, corto, rítmico."""
    n = int(dur * SR); t = np.arange(n) / SR
    mod = np.sin(2 * np.pi * f * 1.5 * t) * 2.4 * np.exp(-t / 0.05)
    car = (2 * (((2 * np.pi * f * t + mod) / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.07)
    y = sat(bp(car * env, 500, 5500, 2) * 0.4, 1.3, 0.08)
    return reverb(y, IR_PLATE, 0.28)

# ==================================================================== PADS / PIANO / VOZ
def pad_cine(ms, dur, rng, cut=1700):
    """pad cinemático ancho (2 notas dispersas), reverb enorme."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-12, -5, 5, 12):
            ph = 2 * np.pi * f * 2 ** (det / 1200) * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.09
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t + rng.uniform(0, 6))
    env = np.minimum(1.0, t / 1.2) * np.minimum(1.0, np.maximum(0.0, dur - t) / 1.4)
    y = lp(x * (env * lfo).astype(np.float32), cut, 2) * 0.4
    return reverb(y, IR_HALL, 0.42)

def piano_glue(ms, dur, rng):
    """piano tenue de pegamento (acorde), FM-ish + reverb."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        mod = np.sin(2 * np.pi * f * 3.0 * t) * 1.6 * np.exp(-t / 0.4)
        x += np.sin(2 * np.pi * f * t + mod).astype(np.float32)
    env = np.exp(-t / (dur * 0.5))
    return reverb((x * env.astype(np.float32) / max(1, len(ms))) * 0.3, IR_HALL, 0.3)

_VOW = dict(a=((760, 1.0), (1220, 0.5), (2600, 0.2)), o=((520, 1.0), (900, 0.5), (2500, 0.2)),
            u=((360, 1.0), (900, 0.4), (2400, 0.15)), e=((540, 1.0), (1900, 0.4), (2500, 0.2)))

def vox_muse(f, dur, rng, vow='a'):
    """voz-musa etérea (la androide): armónicos + formantes, vibrato, reverb ENORME."""
    F = _VOW[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * (t + 0.004 * np.sin(2 * np.pi * 5.0 * t + rng.uniform(0, 6)))
    src = np.zeros(n, np.float32)
    for h in range(1, 24):
        src += (np.sin(h * ph) / h ** 1.15).astype(np.float32)
    env = np.minimum(1.0, t / 0.12) * np.minimum(1.0, np.maximum(0.0, dur - t) / 0.6)
    src *= env.astype(np.float32)
    out = sum(bp(src, fq * 0.87, fq * 1.15, 2) * g for fq, g in F)
    breath = hp(rng.standard_normal(n).astype(np.float32), 3200, 2) * env.astype(np.float32) * 0.04
    return reverb(sat((out + breath) * 0.5, 1.12, 0.04), IR_HALL, 0.45)

def vox_robot(f, dur, rng, vow='o'):
    """narración/voz robótica (la IA): saw por formantes + ring-mod, plate reverb."""
    F = _VOW[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    saw = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    env = np.minimum(1.0, t / 0.02) * np.exp(-np.maximum(0.0, t - dur * 0.6) / 0.1)
    saw *= env.astype(np.float32)
    out = sum(bp(saw, fq * 0.9, fq * 1.1, 2) * g for fq, g in F)
    ring = np.sin(2 * np.pi * (f * 0.5) * t)
    return reverb(sat((out * (0.7 + 0.3 * ring)).astype(np.float32) * 0.45, 1.2, 0.06), IR_PLATE, 0.36)

# ==================================================================== FX cinemáticos (MÁS efectos)
def riser(dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    nz = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32); seg = max(1, n // 30)
    for k in range(30):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        p = float(prog[min(n - 1, (a + b_) // 2)])
        out[a:b_] = bp(nz[a:b_], 300 + 5200 * p ** 2, 700 + 9000 * p ** 2, 2)
    y = (out * (prog ** 1.6)).astype(np.float32) * 0.4
    return reverb(y, IR_HALL, 0.3)

def downlift(rng):
    n = int(0.9 * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    f = 1100 * (1 - prog) + 55
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    return reverb(sat(bp(x * np.exp(-t / 0.4), 150, 4800, 2), 1.2, 0.07) * 0.4, IR_HALL, 0.3)

def impact(rng):
    n = int(1.8 * SR); t = np.arange(n) / SR
    f = 42 + 75 * np.exp(-t / 0.06)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.6)
    nz = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.6)
    y = (sat(boom.astype(np.float32), 1.25, 0.04) + bp(nz, 200, 3600, 2) * 0.4) * 0.6
    return reverb(y, IR_HALL, 0.35)

def revswell(dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    x = hp(rng.standard_normal(n).astype(np.float32), 3500, 2)
    y = (x * (prog ** 2.3)).astype(np.float32) * 0.3
    return reverb(y, IR_HALL, 0.4)

def drone(dur, ms, rng):
    """dron cinemático de fondo (el útero ambiental de la intro)."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        x += np.sin(2 * np.pi * f * t + 2.5 * np.sin(2 * np.pi * 0.05 * t)).astype(np.float32) * 0.3
        x += (2 * ((2 * np.pi * f * 2 ** (0.08 / 12) * t / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.08
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.04 * t + rng.uniform(0, 6))
    return reverb(lp(x * lfo.astype(np.float32), 1200, 2) * 0.32, IR_HALL, 0.5)

if __name__ == '__main__':
    from dream_core import wav_write, spectrum_pct
    rng = np.random.default_rng(13)
    bpm = 124; spb = int(SR * 240 / bpm); s16 = spb / 16
    n = spb * 2; mix = np.zeros(n, np.float32)
    def put(buf, pos, x, g=1.0):
        pos = int(pos); e = min(len(buf), pos + len(x))
        if e > pos: buf[pos:e] += x[:e - pos] * g
    K = kick_mt()
    for bar in range(2):
        base = bar * spb
        for b in range(4): put(mix, base + b * 4 * s16, K)
        put(mix, base + 4 * s16, clap(rng), 0.7); put(mix, base + 12 * s16, clap(rng), 0.7)
        for s in range(16): put(mix, base + s * s16, hat(rng, open_=(s % 4 == 2)), 0.35 if s % 2 else 0.24)
        # sub rolling 16vos limpio (Sol menor, root G1=31)
        for s in range(16):
            if s % 4 != 0: put(mix, base + s * s16, bass_mt(midi_f(31), 0.9 * s16 / SR, rng), 0.85)
    # lead gated + FM stabs (Sol menor)
    put(mix, 0, lead_gated(midi_f(67), 2 * s16 * 8 / SR * 1.0, rng, gate_hz=8.0), 0.6)
    for s in (6, 7, 14, 15): put(mix, int(s * s16), fm_stab(midi_f(70), 0.12, rng), 0.5)
    put(mix, 0, pad_cine([55, 58], 2 * spb / SR, rng), 0.6)
    mix /= max(1e-9, np.abs(mix).max())
    wav_write('_test_anyma.wav', np.stack([mix, mix]))
    print('ORÁCULO groove:', {k: round(v, 1) for k, v in spectrum_pct(mix).items()})
    print('_test_anyma.wav listo')
