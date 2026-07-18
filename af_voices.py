#!/usr/bin/env python3
"""AF_VOICES — paleta Afterlife/Anyma, construida desde la INVESTIGACIÓN, no de oído.

Cada función implementa un hallazgo concreto (ver memoria anyma-afterlife-produccion):

  · gate()      LFO ~18 Hz DESINCRONIZADO del grid. A 126 BPM el 1/32 es 16.8 Hz,
                así que 18 Hz desliza contra la grilla — eso es lo que suena a
                máquina y no a groove. Es LA firma del género.
  · duck_rev()  el reverb SUBE cuando el lead calla e invierte al tocar. La técnica
                de mayor valor de toda la investigación (5 fuentes independientes):
                espacio enorme sin embarrar los ataques.
  · lead_*()    DOS capas con cadenas de FX independientes (cuerpo oscuro y ancho +
                brillo arriba), saw + saw una QUINTA arriba (no supersaw de unísono).
                Ataque 30-60 ms — NUNCA cero, el dato más repetido del research.
  · sub/mid()   sub mono estricto en 1/16 CON HUECO entre notas; el medio con
                sustain a cero, decay 400 ms y HP en 90 para no pelear con el sub.
  · fmstab()    FM real + transitorio ruidoso en CADA golpe (eso lo vuelve "shot").

Lo melódico se sintetiza aquí; batería y percusión salen de samples reales (kit.py).
NO hay voces de formantes — regla dura de André (2 strikes: PLAYA y MÁQUINA)."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm, fconv

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)
MIN = [0, 2, 3, 5, 7, 8, 10]
MAJ = [0, 2, 4, 5, 7, 9, 11]
def deg(root, d, o=0, sc=MIN): return root + sc[d % 7] + 12 * (d // 7 + o)

# ============================================================ ESPACIO
def _ir(decay, tone, seed, predelay=0.0):
    """IR con pre-delay y damping de agudos (el research pide 4-6 kHz)."""
    n = int(decay * SR); rng = np.random.default_rng(seed)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 6.4, n)).astype(np.float32)
    ir = lp(ir, tone, 2)
    if predelay > 0:
        ir = np.concatenate([np.zeros(int(predelay * SR), np.float32), ir])
    ir /= np.sqrt((ir ** 2).sum()) + 1e-12
    return ir

IR_VAST  = _ir(6.5, 4600, 71, 0.045)   # pads/atmósfera: 4-8 s, damping 4-6k
IR_HALL  = _ir(3.4, 5200, 72, 0.028)   # leads
IR_PLATE = _ir(1.6, 6400, 73, 0.014)   # stabs: 1.6 s exacto del research

def rev(x, ir, mix=0.34):
    return x + fconv(x, ir)[:len(x)] * mix

def duck_rev(x, ir, mix=0.55, depth=0.8):
    """⭐ REVERB DUCKEADO — la técnica clave del sonido Afterlife.

    Seguidor de envolvente del SECO, invertido, manejando el bus wet: cuando el
    lead calla el reverb florece; cuando toca, se agacha y deja pasar el ataque.
    El follower asimétrico (ataque rápido / release lento) se aproxima vectorizado
    con max(lp_rápido, lp_lento) — un bucle muestra a muestra sobre 18M de
    muestras sería inviable en numpy."""
    w = fconv(x, ir)[:len(x)]
    a = np.abs(x).astype(np.float32)
    env = np.maximum(lp(a, 26.0, 1), lp(a, 3.2, 1))      # ataque ~6 ms / release ~200 ms
    m = float(np.percentile(env, 99.0))
    if m > 1e-9: env = np.clip(env / m, 0.0, 1.0)
    return x + w * (mix * (1.0 - depth * env)).astype(np.float32)

# ============================================================ EL GATE (la firma)
def gate(n, hz=18.0, duty=0.5, floor=0.12, phase=0.0):
    """Gate casi cuadrado corriendo en tiempo ABSOLUTO, no en tempo.

    18 Hz contra un 1/32 de 16.8 Hz (a 126 BPM) = deslizamiento deliberado.
    Bordes suavizados ~1.5 ms para que no chasquee."""
    t = np.arange(n, dtype=np.float32) / SR
    g = ((t * hz + phase) % 1.0 < duty).astype(np.float32)
    return (floor + (1.0 - floor) * lp(g, 620.0, 1)).astype(np.float32)

# ============================================================ LEAD (dos capas)
def _saws(f, n, dets, rng, fifth=False):
    """banco de saws detuneadas con fase aleatoria; opcionalmente la quinta arriba."""
    t = np.arange(n, dtype=np.float32) / SR
    mult = 2 ** (7 / 12.0) if fifth else 1.0
    x = np.zeros(n, np.float32)
    for d in dets:
        ph = 2 * np.pi * f * mult * 2 ** (d / 1200.0) * t + rng.uniform(0, 6.28)
        x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    return x / max(1, len(dets))

def _sweep_lp(x, c0, c1, steps=12):
    """barrido de filtro por segmentos — lp() de dream_core exige cutoff ESCALAR."""
    n = len(x); seg = max(1, n // steps); out = np.zeros(n, np.float32)
    for k in range(steps):
        a, b = k * seg, (n if k == steps - 1 else (k + 1) * seg)
        if a >= n: break
        out[a:b] = lp(x[a:b], float(c0 + (c1 - c0) * (k / max(1, steps - 1))), 2)
    return out

def lead_body(f, dur, rng, gate_hz=18.0, cut=1900, atk=0.045):
    """capa CUERPO: oscura, ancha, la que sostiene. Ataque 45 ms (nunca cero)."""
    n = max(64, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    x = (_saws(f, n, (-16, -9, -3, 3, 9, 16), rng) * 0.62
         + _saws(f, n, (-6, 6), rng, fifth=True) * 0.26
         + _saws(f * 0.5, n, (-4, 4), rng) * 0.20)          # octava abajo = peso
    x = _sweep_lp(x, 620, cut)
    env = np.minimum(1.0, t / atk) * np.exp(-np.maximum(0.0, t - dur * 0.80) / 0.28)
    g = gate(n, gate_hz, 0.52, 0.14, rng.uniform(0, 1))
    return duck_rev(sat_warm(x * (env * g).astype(np.float32) * 0.34), IR_HALL, 0.52, 0.78)

def lead_top(f, dur, rng, gate_hz=18.0, atk=0.032):
    """capa BRILLO: cadena propia (más saturación, plate corto). Se suma a la de cuerpo."""
    n = max(64, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    x = _saws(f * 2.0, n, (-11, -4, 4, 11), rng)
    x = hp(_sweep_lp(x, 1400, 5200), 900.0, 2)
    env = np.minimum(1.0, t / atk) * np.exp(-np.maximum(0.0, t - dur * 0.62) / 0.16)
    g = gate(n, gate_hz, 0.46, 0.08, rng.uniform(0, 1))
    return duck_rev(sat(x * (env * g).astype(np.float32) * 0.15, 1.35, 0.06), IR_PLATE, 0.4, 0.7)

def lead(f, dur, rng, gate_hz=18.0, cut=1900):
    return lead_body(f, dur, rng, gate_hz, cut) + lead_top(f, dur, rng, gate_hz)

# ============================================================ BAJO
def sub(f, dur, rng):
    """sub MONO limpio. Se llama en 1/16 con hueco — el hueco lo pone el arreglo."""
    n = max(32, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    ph = 2 * np.pi * f * t
    x = (np.sin(ph) * 0.86 + np.sin(ph * 2) * 0.10).astype(np.float32)
    env = np.minimum(1.0, t / 0.006) * np.exp(-np.maximum(0.0, t - dur * 0.55) / 0.045)
    return lp(x * env.astype(np.float32), 190.0, 2) * 0.62

def midbass(f, dur, rng):
    """bajo medio: sustain A CERO, decay 400 ms, HP 90 para no pisar el sub.
    El env también abre un shelf de agudos en el ataque (truco barato y efectivo)."""
    n = max(32, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    x = _saws(f, n, (-8, 8), rng) * 0.7 + _saws(f * 2, n, (-5, 5), rng) * 0.3
    env = (np.minimum(1.0, t / 0.005) * np.exp(-t / 0.40)).astype(np.float32)
    x = _sweep_lp(x * env, 1500, 380, 8)
    bright = hp(x, 1800.0, 2) * np.exp(-t / 0.05).astype(np.float32) * 0.5
    return hp(sat_warm(x + bright), 90.0, 2) * 0.34

# ============================================================ STAB FM
def fmstab(f, dur, rng, fm=0.72):
    """stab metálico: FM real (fase modulada) + TRANSITORIO RUIDOSO en cada golpe.
    Sin ese transitorio suena a nota de synth; con él suena a disparo."""
    n = max(32, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    pm = np.sin(2 * np.pi * f * 1.497 * t).astype(np.float32) * (fm * 6.0) * np.exp(-t / 0.045)
    car = np.sin(2 * np.pi * f * t + pm).astype(np.float32)
    pitchblip = np.exp(-t / 0.012) * 0.3                       # Env3 -> pitch, muy corto
    car += np.sin(2 * np.pi * f * (1 + pitchblip) * t).astype(np.float32) * 0.25
    env = np.minimum(1.0, t / 0.002) * np.exp(-t / 0.085)
    tr = bp(rng.standard_normal(n).astype(np.float32), 1800, 7200, 2) * np.exp(-t / 0.008) * 0.5
    return duck_rev(sat(bp((car * env + tr).astype(np.float32), 320, 6200, 2) * 0.34, 1.5, 0.09),
                    IR_PLATE, 0.5, 0.6)

# ============================================================ PAD / ATMÓSFERA
def pad(ms, dur, rng, cut=1500):
    """pad cinemático: ataque lento, LFO de filtro 0.1-0.5 Hz, reverb 6.5 s."""
    n = max(64, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        x += _saws(midi_f(m), n, (-14, -6, 6, 14), rng) * 0.34
    lfo = 0.72 + 0.28 * np.sin(2 * np.pi * 0.16 * t + rng.uniform(0, 6.28))
    env = np.minimum(1.0, t / 1.6) * np.minimum(1.0, np.maximum(0.0, dur - t) / 2.2)
    x = _sweep_lp(x * (env * lfo).astype(np.float32), cut * 0.55, cut, 10)
    # OJO: _saws() ya normaliza por número de voces — dividir otra vez entre len(ms)
    # dejaba el pad en rms 0.007, inaudible. El pad es el que CARGA LOS MEDIOS.
    return rev(x * 1.35, IR_VAST, 0.5)

def drone(f, dur, rng):
    """cama sci-fi: dos sines batiendo + ruido filtrado, todo muy atrás."""
    n = max(64, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    x = (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * 1.006 * t) * 0.8).astype(np.float32)
    air = bp(rng.standard_normal(n).astype(np.float32), 900, 4200, 2) * 0.06
    env = np.minimum(1.0, t / 3.0) * np.minimum(1.0, np.maximum(0.0, dur - t) / 3.0)
    return rev((x * 0.10 + air) * env.astype(np.float32), IR_VAST, 0.6)

# ============================================================ ARP
def arp(f, dur, rng, decay=0.27, sustain=0.30):
    """pluck/arp. decay y sustain son PARÁMETROS para poder alargarlos durante el
    build y devolverlos a cortísimo justo antes del drop (truco del research)."""
    n = max(32, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    x = _saws(f, n, (-7, 7), rng)
    sizzle = hp(rng.standard_normal(n).astype(np.float32), 5200, 2) * np.exp(-t / 0.006) * 0.28
    env = (sustain + (1 - sustain) * np.exp(-t / decay)) * np.minimum(1.0, t / 0.003)
    env *= np.minimum(1.0, np.maximum(0.0, dur - t) / 0.06)
    x = _sweep_lp((x + sizzle) * env.astype(np.float32), 900, 3600, 6)
    return duck_rev(sat(x * 0.3, 1.25, 0.05), IR_HALL, 0.44, 0.72)

# ============================================================ FX de transición
def riser(dur, rng, f0=180.0, f1=2600.0):
    """uplifter: ruido barrido + sine subiendo. Para los builds."""
    n = max(64, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    p = (t / dur).astype(np.float32)
    nz = rng.standard_normal(n).astype(np.float32)
    steps = 16; seg = max(1, n // steps); out = np.zeros(n, np.float32)
    for k in range(steps):
        a, b = k * seg, (n if k == steps - 1 else (k + 1) * seg)
        if a >= n: break
        c = f0 + (f1 - f0) * (k / (steps - 1)) ** 1.7
        out[a:b] = bp(nz[a:b], float(c * 0.72), float(c * 1.45), 2)
    fr = f0 * (f1 / f0) ** (p ** 1.5)
    tone = np.sin(2 * np.pi * np.cumsum(fr) / SR).astype(np.float32) * 0.16
    return rev((out * 0.5 + tone) * (p ** 1.8).astype(np.float32) * 0.5, IR_HALL, 0.4)

def downlifter(dur, rng, f0=2400.0, f1=140.0):
    n = max(64, int(dur * SR)); t = np.arange(n, dtype=np.float32) / SR
    p = (t / dur).astype(np.float32)
    fr = f0 * (f1 / f0) ** (p ** 0.8)
    tone = np.sin(2 * np.pi * np.cumsum(fr) / SR).astype(np.float32)
    nz = bp(rng.standard_normal(n).astype(np.float32), 400, 3000, 2) * 0.35
    return rev((tone * 0.3 + nz) * np.exp(-t / (dur * 0.45)).astype(np.float32) * 0.55, IR_VAST, 0.55)
