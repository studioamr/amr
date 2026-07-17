#!/usr/bin/env python3
"""COLIBRÍ — paleta de síntesis para el set estilo Polo & Pan.
Sonido LUMINOSO en tonalidades MAYORES: marimba, flauta, arpegios brillantes,
vocal chops alegres, bajo funky, glockenspiel, percusión suave. Todo nuevo —
nada de la paleta oscura de deep tech. DSP base de dream_core (genérico)."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm, fconv

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

# escalas brillantes
MAJ = [0, 2, 4, 5, 7, 9, 11]           # jónico
LYD = [0, 2, 4, 6, 7, 9, 11]           # lidio (#4 — el brillo psicodélico)
MIX = [0, 2, 4, 5, 7, 9, 10]           # mixolidio (b7 — el color funky)

def deg(root, scale, d, oct_=0):
    return root + scale[d % 7] + 12 * (d // 7 + oct_)

# ------------------------------------------------------------------ melódicos
def marimba(f, dur, rng, mall=1.0):
    """marimba de madera: fundamental + armónico 4:1 (tubo resonante), mallet suave."""
    n = int(dur * SR); t = np.arange(n) / SR
    dec = 0.42 * rng.uniform(0.9, 1.1)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / dec)
    x += 0.35 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t / (dec * 0.35))   # el "cuarto armónico" clásico
    x += 0.12 * np.sin(2 * np.pi * f * 9.6 * t) * np.exp(-t / 0.03)
    x += mall * 0.18 * rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.003)  # golpe del mazo
    return sat(x.astype(np.float32) * 0.8, 1.3, 0.08)

def glocken(f, dur, rng):
    """glockenspiel/campana de juguete: brillante, inarmónico, cristalino."""
    n = int(dur * SR); t = np.arange(n) / SR
    dec = 0.9 * rng.uniform(0.9, 1.1)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / dec)
    x += 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / (dec * 0.5))
    x += 0.28 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / (dec * 0.3))
    return (x * 0.55).astype(np.float32)

def flauta(f, dur, rng, air=0.35):
    """flauta dulce / pan: seno con vibrato + soplido, ataque suave de aire."""
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.2 * t + rng.uniform(0, 6))
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    x = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    breath = bp(rng.standard_normal(n).astype(np.float32), 1800, 6000, 2)
    env = np.minimum(1.0, t / 0.05) * np.minimum(1.0, (dur - t) / 0.08)
    return ((x * (1 - air) + breath * air) * env * 0.5).astype(np.float32)

def pluck_bright(f, dur, rng, cutoff=3200):
    """pluck brillante: saw con env de filtro rápido (síntesis sustractiva French touch)."""
    n = int(dur * SR); t = np.arange(n) / SR
    saw = (2.0 * ((f * t) % 1.0) - 1.0).astype(np.float32)
    saw += 0.5 * (2.0 * ((f * 1.005 * t) % 1.0) - 1.0)     # detune sutil
    fenv = cutoff * (0.25 + 0.75 * np.exp(-t / 0.06))
    y = np.zeros(n, np.float32); a = 0.0
    # LP de 1 polo con cutoff que cae (barato, por muestra vectorizado por bloques)
    coef = np.exp(-2 * np.pi * fenv / SR)
    for i in range(0, n, 512):
        j = min(i + 512, n); c = coef[i:j]
        for k in range(i, j):
            a = saw[k] * (1 - coef[k]) + a * coef[k]; y[k] = a
    env = np.exp(-t / (dur * 0.6))
    return sat(y * env * 0.9, 1.2, 0.06)

def arp_note(f, dur, rng):
    """nota de arpegiador: pluck cortito muy brillante con delay incorporado luego."""
    return pluck_bright(f, dur, rng, cutoff=4200)

def vocal_la(f, dur, rng, vowel='a'):
    """vocal chop alegre: fuente glotal + 3 formantes de vocal, en mayor."""
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1.0 + 0.008 * np.sin(2 * np.pi * 5.5 * t + rng.uniform(0, 6))
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    glottal = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.22 * np.sin(3 * ph)
               + 0.12 * np.sin(4 * ph) + 0.06 * np.sin(5 * ph)).astype(np.float32)
    F = dict(a=(800, 1150, 2900), e=(500, 1800, 2500), i=(320, 2200, 3000),
             o=(500, 900, 2400), u=(360, 800, 2200))[vowel]
    v = sum(bp(glottal, f0 * 0.9, f0 * 1.1, 2) * g for f0, g in zip(F, (1.0, 0.6, 0.35)))
    env = np.minimum(1.0, t / 0.02) * np.minimum(1.0, (dur - t) / 0.04)
    return (v * env * 0.4).astype(np.float32)

# ------------------------------------------------------------------ groove
def bass_funk(f, dur, rng, cutoff=900):
    """bajo redondo funky: seno + saw suave, pluck de filtro, cálido."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * 1.0
    x += 0.4 * (2.0 * ((f * t) % 1.0) - 1.0)
    env = np.minimum(1.0, t / 0.006) * np.exp(-np.maximum(0.0, t - dur * 0.7) / 0.05)
    y = lp((x * env).astype(np.float32), cutoff, 2)
    return sat_warm(y * 1.3) * 0.5

def hit_kick_soft():
    """kick redondo suave, house cálido (no el kick seco de tech)."""
    n = int(0.42 * SR); t = np.arange(n) / SR
    f = 48.0 + 46.0 * np.exp(-t / 0.026)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.20)
    x += 0.10 * np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.06)
    return lp(sat(x.astype(np.float32), 1.35, 0.08), 2600, 2) * 0.8

def hit_clap_soft(rng):
    n = int(0.22 * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for d in (0.0, 0.008, 0.015):
        o = int(d * SR); b = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.007)
        if o < n: x[o:] += b[:n - o]
    x += rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.05) * 0.4
    return bp(x, 1000, 4500, 2) * 0.5

def hit_shaker_s(rng):
    n = int(0.06 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * (np.exp(-t / 0.03) * (1 - np.exp(-t / 0.004)))
    return bp(x, 4000, 9000, 2) * rng.uniform(0.7, 1.0)

def hit_tamb(rng):
    """pandereta: varios jingles metálicos."""
    n = int(0.16 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.05)
    x = sum(bp(x, fq * 0.98, fq * 1.02, 2) for fq in (6200, 8100, 9800))
    return (x * 0.3).astype(np.float32)

def hit_conga_s(rng, f0=200, open_=True):
    dec = (0.14 if open_ else 0.05) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f0 * (1 + 0.2 * np.exp(-t / 0.01)) * t) * np.exp(-t / dec)
    return sat(x.astype(np.float32) * 0.7, 1.4, 0.1)

def rimclick(rng):
    n = int(0.05 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * rng.uniform(1600, 2000) * t) * np.exp(-t / 0.008)
    x += 0.4 * rng.standard_normal(n) * np.exp(-t / 0.002)
    return bp(x.astype(np.float32), 900, 4000, 2) * 0.6

# ------------------------------------------------------------------ naturaleza (el "viaje")
def water(dur, rng):
    """agua: ruido filtrado suave + 'plips' de seno aleatorios (gotas)."""
    n = int(dur * SR); t = np.arange(n) / SR
    stream = lp(rng.standard_normal(n).astype(np.float32), 900, 2) * 0.06
    stream *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t)).astype(np.float32)
    x = stream.copy()
    for _ in range(int(dur * 3)):                              # gotas
        p = rng.integers(0, n - 4000); f = rng.uniform(900, 2400)
        tt = np.arange(4000) / SR
        drop = (np.sin(2 * np.pi * f * (1 + 6 * np.exp(-tt / 0.01)) * tt) * np.exp(-tt / 0.02)).astype(np.float32)
        x[p:p + 4000] += drop * 0.25
    return x

def birds(dur, rng):
    """pájaros: chirps FM (barridos rápidos de pitch) esparcidos."""
    n = int(dur * SR); x = np.zeros(n, np.float32)
    for _ in range(int(dur * 1.5)):
        p = rng.integers(0, n - 8000); L = rng.integers(2000, 7000)
        tt = np.arange(L) / SR; up = rng.uniform() > 0.5
        f = rng.uniform(2200, 3600) * (1 + (0.6 if up else -0.4) * (tt / (L / SR)))
        chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-((tt - tt.mean()) ** 2) / (0.02))
        for k in range(rng.integers(1, 4)):
            o = k * rng.integers(1500, 3500)
            if p + o + L < n: x[p + o:p + o + L] += chirp.astype(np.float32) * 0.12
    return x

if __name__ == '__main__':
    # banco de pruebas: cada instrumento tocando un acorde/frase, medir brillo
    from dream_core import wav_write, spectrum_pct
    rng = np.random.default_rng(3)
    root = 60  # Do mayor, brillante
    def spec_line(name, x):
        s = spectrum_pct(x if x.ndim == 1 else x.mean(0))
        print(f'{name:14s} sub={s.get("sub",0):4.1f} bass={s.get("bass",0):4.1f} '
              f'lowmid={s.get("lowmid",0):4.1f} mid={s.get("mid",0):4.1f} '
              f'himid={s.get("himid",0):4.1f} air={s.get("air",0):4.1f}')
    tests = {
        'marimba': lambda: np.concatenate([marimba(midi_f(deg(root, MAJ, d)), 0.45, rng) for d in (0, 2, 4, 6, 4, 2)]),
        'glocken': lambda: np.concatenate([glocken(midi_f(deg(root, LYD, d, 1)), 0.6, rng) for d in (0, 4, 2, 6)]),
        'flauta':  lambda: np.concatenate([flauta(midi_f(deg(root, MAJ, d)), 0.6, rng) for d in (4, 2, 0, 2)]),
        'pluck':   lambda: np.concatenate([pluck_bright(midi_f(deg(root, LYD, d, 1)), 0.3, rng) for d in (0, 2, 4, 6, 7, 6, 4, 2)]),
        'vocal_la':lambda: np.concatenate([vocal_la(midi_f(deg(root, MAJ, d)), 0.4, rng, v) for d, v in [(0,'a'),(2,'e'),(4,'a'),(2,'o')]]),
        'bass_funk':lambda:np.concatenate([bass_funk(midi_f(deg(root-24, MIX, d)), 0.3, rng) for d in (0, 0, 4, 0, 2, 0, 4, 5)]),
    }
    for name, fn in tests.items():
        x = fn().astype(np.float32); x /= (np.abs(x).max() + 1e-9)
        spec_line(name, x)
        wav_write(f'_test_{name}.wav', np.stack([x, x]))
    print('bank ok — brillo esperado: marimba/glocken/pluck con himid+air altos, bass con sub/bass')
