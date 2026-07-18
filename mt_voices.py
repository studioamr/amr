#!/usr/bin/env python3
"""MÁQUINA — voces sintéticas melodic techno (SOLO lo melódico).
La batería, la percusión, los FX (crash, reverse cymbal/clap) y los ambientes
salen de SAMPLES REALES vía kit.py — por eso ya no suena a videojuego.

Aquí solo lo que sí conviene sintetizar: bajo LIMPIO, lead supersaw gated
(la firma melodic techno), pads cinemáticos, stabs FM y voz-musa etérea.
Todo con reverb generosa (André: "les faltan efectos")."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm, fconv

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)
MIN = [0, 2, 3, 5, 7, 8, 10]
MAJ = [0, 2, 4, 5, 7, 9, 11]
def deg(root, d, o=0, sc=MIN): return root + sc[d % 7] + 12 * (d // 7 + o)

# ---- reverbs (el espacio cinemático)
def _ir(decay, tone, seed):
    n = int(decay * SR); rng = np.random.default_rng(seed)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 6.2, n)).astype(np.float32)
    ir = lp(ir, tone, 2); ir /= np.sqrt((ir ** 2).sum()) + 1e-12
    return ir
IR_HALL = _ir(4.0, 5000, 51)
IR_PLATE = _ir(2.1, 6800, 52)
def rev(x, ir, mix=0.34):
    w = fconv(x, ir)
    return x + w[:len(x)] * mix

# ==================================================== BAJO (LIMPIO — lección de André)
def bass(f, dur, rng, cutoff=430, glide_from=None):
    """sub rolling limpio: sine sub + sine + saw suave por LP gentil. Sin drive duro."""
    n = max(8, int(dur * SR)); t = np.arange(n) / SR
    if glide_from:
        fr = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.05)
        ph = 2 * np.pi * np.cumsum(fr) / SR
    else:
        ph = 2 * np.pi * f * t
    x = (np.sin(ph * 0.5) * 0.55 + np.sin(ph) * 0.6
         + (2 * ((ph / (2 * np.pi)) % 1.0) - 1) * 0.15).astype(np.float32)
    env = np.minimum(1.0, t / 0.008) * np.exp(-np.maximum(0.0, t - dur * 0.72) / 0.06)
    return sat_warm(lp(x * env.astype(np.float32), cutoff, 2)) * 0.6

# ==================================================== LEAD supersaw GATED (la firma)
def lead(f, dur, rng, gate_hz=8.0, cut=2600, glide_from=None):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = (glide_from + (f - glide_from) * np.minimum(1.0, t / 0.06)) if glide_from else f * np.ones(n, np.float32)
    vib = 2.0 ** (4.0 * np.sin(2 * np.pi * 4.7 * t + rng.uniform(0, 6)) / 1200)
    x = np.zeros(n, np.float32)
    for det in (-14, -8, -3, 3, 8, 14):
        ph = 2 * np.pi * np.cumsum(fr * vib * 2 ** (det / 1200)) / SR + rng.uniform(0, 6)
        x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.16
    cenv = 700 + (cut - 700) * np.minimum(1.0, t / (dur * 0.45))
    seg = max(1, n // 10); out = np.zeros(n, np.float32)
    for k in range(10):
        a, b = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        out[a:b] = lp(x[a:b], float(cenv[min(n - 1, (a + b) // 2)]), 2)
    g = lp((0.5 + 0.5 * np.sign(np.sin(2 * np.pi * gate_hz * t))).astype(np.float32), 90, 1)
    env = np.minimum(1.0, t / 0.02) * np.exp(-np.maximum(0.0, t - dur * 0.85) / 0.2)
    return rev(sat(out * (env * (0.35 + 0.65 * g)).astype(np.float32) * 0.4, 1.2, 0.05), IR_HALL, 0.36)

def stab(f, dur, rng):
    """stab FM metálico (el grit puntual)."""
    n = int(dur * SR); t = np.arange(n) / SR
    mod = np.sin(2 * np.pi * f * 1.5 * t) * 2.3 * np.exp(-t / 0.05)
    car = (2 * (((2 * np.pi * f * t + mod) / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.07)
    return rev(sat(bp(car * env, 500, 5500, 2) * 0.4, 1.3, 0.08), IR_PLATE, 0.3)

def pad(ms, dur, rng, cut=1700):
    """pad cinemático ancho, reverb enorme."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-12, -5, 5, 12):
            ph = 2 * np.pi * f * 2 ** (det / 1200) * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.09
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t + rng.uniform(0, 6))
    env = np.minimum(1.0, t / 1.2) * np.minimum(1.0, np.maximum(0.0, dur - t) / 1.4)
    return rev(lp(x * (env * lfo).astype(np.float32), cut, 2) * 0.4, IR_HALL, 0.44)

def piano(ms, dur, rng):
    """acorde tenue de pegamento (FM suave)."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        mod = np.sin(2 * np.pi * f * 3.0 * t) * 1.5 * np.exp(-t / 0.4)
        x += np.sin(2 * np.pi * f * t + mod).astype(np.float32)
    env = np.exp(-t / (dur * 0.5))
    return rev((x * env.astype(np.float32) / max(1, len(ms))) * 0.3, IR_HALL, 0.32)

_V = dict(a=((760, 1.0), (1220, 0.5), (2600, 0.2)), o=((520, 1.0), (900, 0.5), (2500, 0.2)),
          u=((360, 1.0), (900, 0.4), (2400, 0.15)))
def vox(f, dur, rng, vow='a'):
    """voz-musa etérea (la máquina que canta), reverb enorme."""
    F = _V[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * (t + 0.004 * np.sin(2 * np.pi * 5.0 * t + rng.uniform(0, 6)))
    src = np.zeros(n, np.float32)
    for h in range(1, 24):
        src += (np.sin(h * ph) / h ** 1.15).astype(np.float32)
    env = np.minimum(1.0, t / 0.12) * np.minimum(1.0, np.maximum(0.0, dur - t) / 0.6)
    src *= env.astype(np.float32)
    out = sum(bp(src, q * 0.87, q * 1.15, 2) * g for q, g in F)
    br = hp(rng.standard_normal(n).astype(np.float32), 3200, 2) * env.astype(np.float32) * 0.04
    return rev(sat((out + br) * 0.5, 1.12, 0.04), IR_HALL, 0.46)

def arp(f, dur, rng):
    """arpegio corto y brillante."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for det in (-7, 7):
        ph = 2 * np.pi * f * 2 ** (det / 1200) * t + rng.uniform(0, 6)
        x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.4
    cenv = 600 + 3000 * np.exp(-t / 0.05)
    seg = max(1, n // 8); out = np.zeros(n, np.float32)
    for k in range(8):
        a, b = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        out[a:b] = lp(x[a:b], float(cenv[min(n - 1, (a + b) // 2)]), 2)
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.09)
    return rev(sat(out * env.astype(np.float32) * 0.42, 1.2, 0.06), IR_PLATE, 0.34)
