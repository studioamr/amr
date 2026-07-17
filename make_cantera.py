#!/usr/bin/env python3
"""CANTERA — deep tech de la piedra rosa de Morelia (~42 min, 125 BPM). Motor v4.

Motor v2, construido sobre la investigación:
  · Léger: UN solo kick para todo el set; célula melódica como origen; estructura no lineal
  · Lane 8: percusión propia — cada golpe con variación única (nada de "sample pack plano")
  · Szabo (tesis KTH): supersaw JP-8000 con ratios medidos, fase libre, voces repartidas L/R
  · EBU 3342: LRA 4-8 por construcción — breakdowns sin kick/bajo a -3/-6 dB
  · Burridge: valles, no picos; olas de energía; estado sostenido
  · Messan/PIV: kicks suaves, hats aireados, una frase melódica como gancho

Uso:  python3 make_dream.py            → set completo
      python3 make_dream.py CORAL      → sólo esa sección (+ métricas rápidas)
"""
import os, sys, subprocess
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, sat_warm, widen, sub_mono, pingpong,
                        stereo_verb, master_file, ffmeter, wav_write, spectrum_pct,
                        fconv, _decorr_ir)

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_cantera_tmp')
os.makedirs(TMP, exist_ok=True)

BPM = 125.0
SPB = int(round(SR * 240.0 / BPM))        # muestras por compás (88200 exacto)
S16 = SPB / 16.0
BEAT_S = 60.0 / BPM
XF_BARS = 4                                # crossfade entre secciones
SWINGS = dict(bass=0.54, hats=0.57, shaker=0.56, conga=0.55, keys=0.55)   # v4: por instrumento

# ------------------------------------------------------------------ osciladores
def _saw(fs, phase):
    return (2.0 * ((phase + np.cumsum(fs) / SR) % 1.0) - 1.0).astype(np.float32)

def drift(n, cents=4.0, seed=0):
    """deriva de pitch: 3 senos lentos en ratios primos (consenso KVR: ±5 cents máx)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    p = rng.uniform(0, 6.28, 3)
    d = (np.sin(2 * np.pi * t / 3.1 + p[0]) + np.sin(2 * np.pi * t / 7.3 + p[1])
         + np.sin(2 * np.pi * t / 11.9 + p[2])) / 3.0
    return (2.0 ** (cents * d / 1200.0)).astype(np.float32)

# supersaw JP-8000 — números medidos por Szabo (KTH 2010)
SS_OFF = np.array([-0.11002313, -0.06288439, -0.01952356, 0.0,
                   0.01991221, 0.06216538, 0.10745242])
_SS_C = [10028.7312891634, -50818.8652045924, 111363.4808729368, -138150.6761080548,
         106649.6679158292, -53046.9642751875, 17019.9518580080, -3425.0836591318,
         404.2703938388, -24.1878824391, 0.6717417634, 0.0030115596]

def _ss_curve(d):
    return sum(c * d ** (11 - i) for i, c in enumerate(_SS_C))

def supersaw_st(f, n, det=0.40, mix=0.72, seed=0):
    """pad ancho por construcción: sierras laterales repartidas L/R, fase libre."""
    rng = np.random.default_rng(seed)
    scale = _ss_curve(det) / _ss_curve(1.0)
    amp_c = -0.55366 * mix + 0.99785
    amp_s = -0.73764 * mix * mix + 1.2841 * mix + 0.044372
    dft = drift(n, 3.0, seed + 5)
    fs = np.full(n, f, dtype=np.float32) * dft
    L = np.zeros(n, dtype=np.float32); R = np.zeros(n, dtype=np.float32)
    sides = {0: 'L', 5: 'L', 4: 'L', 6: 'R', 1: 'R', 2: 'R'}
    for i, off in enumerate(SS_OFF):
        v = _saw(fs * (1.0 + off * scale), rng.uniform())
        if i == 3:
            L += v * amp_c * 0.55; R += v * amp_c * 0.55
        elif sides[i] == 'L':
            L += v * amp_s * 0.85
        else:
            R += v * amp_s * 0.85
    out = np.stack([L, R]) * (1.0 / 3.2)
    return np.stack([hp(out[0], f * 0.95, 2), hp(out[1], f * 0.95, 2)])  # HP clavado al fundamental (Szabo)

def juno_chorus(x, rate=0.75, base_ms=3.6, depth_ms=1.5):
    """chorus Juno-106: un LFO triangular, una línea normal y la otra invertida."""
    n = len(x)
    t = np.arange(n) / SR
    tri = 2.0 * np.abs(2.0 * ((rate * t) % 1.0) - 1.0) - 1.0
    idx = np.arange(n, dtype=np.float64)
    d1 = (base_ms + depth_ms * tri) * SR / 1000.0
    d2 = (base_ms - depth_ms * tri) * SR / 1000.0
    w1 = np.interp(idx - d1, idx, x).astype(np.float32)
    w2 = np.interp(idx - d2, idx, x).astype(np.float32)
    return np.stack([x * 0.72 + w1 * 0.5, x * 0.72 + w2 * 0.5])

# ------------------------------------------------------------------ percusión "grabada"
# cada golpe se sintetiza con variación aleatoria (pitch/decay/filtro) — lección Lane 8
def hit_kick():
    """EL kick del set — uno solo, suave y redondo, se genera una vez (lección Léger)."""
    n = int(0.50 * SR)
    t = np.arange(n) / SR
    f = 46.0 + 52.0 * np.exp(-t / 0.020)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.16)
    x += 0.12 * np.sin(2 * np.pi * 92.0 * t) * np.exp(-t / 0.05)     # cuerpo, no click
    x = sat(x.astype(np.float32), 1.6, 0.1)
    return lp(x, 3200, 2) * 0.82

KICK = hit_kick()

def hit_conga(rng, f0=185.0, open_=True):
    dec = (0.16 if open_ else 0.055) * rng.uniform(0.88, 1.12)
    n = int(dec * 6 * SR)
    t = np.arange(n) / SR
    f = f0 * rng.uniform(0.96, 1.04) * (1.0 + 0.25 * np.exp(-t / 0.012))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec)
    x += 0.30 * np.sin(2 * np.pi * np.cumsum(f * 1.68) / SR) * np.exp(-t / (dec * 0.4))
    slap = rng.standard_normal(n) * np.exp(-t / 0.004) * (0.35 if open_ else 0.5)
    return (sat((x + bp(slap.astype(np.float32), 900, 5200, 2)).astype(np.float32), 1.8, 0.12)
            * rng.uniform(0.85, 1.0))

def hit_bongo(rng):
    return hit_conga(rng, f0=rng.uniform(330, 390), open_=rng.uniform() > 0.4) * 0.7

def hit_shaker(rng):
    dec = 0.07 * rng.uniform(0.8, 1.25)
    n = int(dec * 5 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * (np.exp(-t / dec) * (1 - np.exp(-t / 0.006)))
    return bp(x, rng.uniform(2200, 3000), rng.uniform(6500, 7800), 2) * rng.uniform(0.7, 1.0)

def hit_hat(rng, open_=False):
    dec = (0.32 if open_ else 0.045) * rng.uniform(0.85, 1.15)
    n = int(dec * 5 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * np.exp(-t / dec)
    return hp(x, rng.uniform(6200, 7000), 2) * (0.38 if open_ else 0.46) * rng.uniform(0.8, 1.0)

def hit_rim(rng):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = rng.uniform(1700, 2100)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012)
    x += 0.4 * rng.standard_normal(n) * np.exp(-t / 0.003)
    return bp(x.astype(np.float32), 900, 5000, 2) * 0.8 * rng.uniform(0.8, 1.0)

# ------------------------------------------------------------------ voces melódicas
def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

def kalimba(f, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    dec = 0.55 * rng.uniform(0.9, 1.1)
    x = np.sin(2 * np.pi * f * t * rng.uniform(0.998, 1.002)) * np.exp(-t / dec)
    x += 0.16 * np.sin(2 * np.pi * f * 5.9 * t) * np.exp(-t / 0.04)
    x += 0.10 * rng.standard_normal(n) * np.exp(-t / 0.004)
    return sat(x.astype(np.float32) * 0.8, 1.4, 0.1)

def campana(f, dur, rng):
    """campana de catedral afinada: FM inarmónica 1:3.47, decay largo, cuerpo cálido."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    idx = 1.4 * np.exp(-t / 0.8)
    x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.47 * t))
    x += 0.3 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / 0.5)
    x = x * np.exp(-t / (dur * 0.55)) * rng.uniform(0.9, 1.0)
    return lp(sat(x.astype(np.float32) * 0.7, 1.5, 0.12), 3800, 2)

def hit_cincel(rng):
    """golpe de cincel sobre piedra: click tonal seco — la firma del taller."""
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    f = rng.uniform(2300, 3100)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006)
    x += 0.6 * rng.standard_normal(n) * np.exp(-t / 0.0025)
    x += 0.25 * np.sin(2 * np.pi * f * 1.62 * t) * np.exp(-t / 0.01)
    return bp(x.astype(np.float32), 1200, 7500, 2) * 0.7 * rng.uniform(0.8, 1.0)

def rhodes(f, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t / (dur * 0.7))
    bell = np.exp(-t / 0.06)
    x = np.sin(2 * np.pi * f * t + 0.35 * bell * np.sin(2 * np.pi * f * 14.0 * t))
    x = x * env * (1.0 + 0.1 * np.sin(2 * np.pi * 5.2 * t))
    return sat(x.astype(np.float32) * 0.75, 2.0, 0.22)     # asimetría = pares, calor de tubo

def lead_warm(f0, f1, dur, seed, cutoff=1600.0):
    """lead de 2 sierras ±5c + sub, con drift, portamento y saturación — no chiptune."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    glide = f0 + (f1 - f0) * np.minimum(1.0, t / 0.045)
    dft = drift(n, 4.0, seed)
    fs = glide.astype(np.float32) * dft
    x = (_saw(fs * 2 ** (+5 / 1200), rng.uniform()) + _saw(fs * 2 ** (-5 / 1200), rng.uniform())) * 0.5
    x += 0.25 * np.sign(_saw(fs * 0.5, rng.uniform()))
    x = lp(sat(x.astype(np.float32) * 0.8, 2.2, 0.15), cutoff, 2)
    env = np.minimum(1.0, t / 0.01) * np.exp(-np.maximum(0.0, t - dur * 0.75) / 0.09)
    return x * env.astype(np.float32)

def bass_note(f, dur, rng, mode='round', fc=760.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if mode == 'round':
        # v4: UNA sierra corrida caliente + sub (el 90% de los bajos de Jansons es un SH-101)
        x = 1.1 * _saw(np.full(n, f, np.float32), rng.uniform())
        x += 0.8 * np.sin(2 * np.pi * f * t)
        env = np.minimum(1.0, t / 0.008) * np.exp(-np.maximum(0.0, t - dur * 0.8) / 0.06)
    else:  # roll — 2 sierras detuned, ataque mínimo, decay medio (Léger)
        x = (_saw(np.full(n, f * 2 ** (+6 / 1200), np.float32), rng.uniform())
             + _saw(np.full(n, f * 2 ** (-6 / 1200), np.float32), rng.uniform())) * 0.55
        x += 0.65 * np.sin(2 * np.pi * f * t)
        env = np.minimum(1.0, t / 0.004) * np.exp(-t / (dur * 0.6))
    y = sat_warm((x * env).astype(np.float32) * 1.5)         # AQUÍ nacen los medios
    return lp(y, fc, 2) * 0.5

# ------------------------------------------------------------------ teoría
NAT = [0, 2, 3, 5, 7, 8, 10]; DOR = [0, 2, 3, 5, 7, 9, 10]

def deg(root, scale, d, oct_=0):
    return root + scale[d % 7] + 12 * (d // 7 + oct_)

# ------------------------------------------------------------------ secciones
# cada sección = un "track": raíz midi, escala, acordes (semitonos midi), motivo gancho
# motivo = (step16 dentro de 2 compases, grado, octava, largo en 16avos)
SECTIONS = [
 dict(name='VETA', root=45, sc=NAT, energy=0.42, shape='rise', bars=88, bass='round',
      chords=[[45,52,60,64,67],[41,48,57,60]],
      motif=[(0,4,1,4),(8,2,1,3),(14,0,1,2),(16,4,1,4),(24,5,1,6)]),
 dict(name='BLOQUE', root=45, sc=DOR, energy=0.58, shape='wave', bars=120, bass='roll',
      chords=[[45,52,60,62],[50,57,65,69],[45,52,60,62],[43,50,58,62]],
      motif=[(0,0,2,2),(4,2,2,2),(8,4,2,3),(16,2,2,2),(20,0,2,2),(24,4,2,5)]),
 dict(name='CINCEL', root=40, sc=NAT, energy=0.68, shape='wave', bars=128, bass='roll',
      chords=[[40,47,55,59],[45,52,60,64],[36,43,52,55],[43,50,58,62]],
      motif=[(0,4,2,1),(2,4,2,1),(4,5,2,2),(8,4,2,2),(12,2,2,3),(16,4,2,1),(18,5,2,2),(22,7,1,4),(28,4,2,4)]),
 dict(name='TALLER', root=40, sc=DOR, energy=0.88, shape='peak', bars=136, bass='roll',
      chords=[[40,47,55,62],[45,52,60,66]],
      motif=[(0,0,2,1),(2,2,2,1),(4,4,2,2),(7,6,1,2),(10,4,2,2),(16,0,2,1),(18,2,2,1),(20,4,2,2),(24,3,2,4),(30,2,2,2)]),
 dict(name='ACUEDUCTO', root=38, sc=NAT, energy=0.55, shape='valley', bars=112, bass='round',
      chords=[[38,45,53,57,60],[34,41,50,53]],
      motif=[(0,4,1,4),(8,3,1,4),(16,2,1,4),(24,0,1,8)]),
 dict(name='PORTALES', root=43, sc=DOR, energy=0.72, shape='wave', bars=128, bass='roll',
      chords=[[43,50,58,62],[48,55,64,67],[43,50,58,62],[41,48,57,60]],
      motif=[(0,4,2,2),(3,5,2,1),(4,4,2,2),(8,2,2,2),(12,0,2,3),(16,4,2,2),(20,7,1,3),(26,4,2,4)]),
 dict(name='CATEDRAL', root=45, sc=NAT, energy=0.48, shape='deep', bars=104, bass='round',
      chords=[[45,52,60,63,67],[40,47,55,60]],
      motif=[(0,2,1,6),(8,0,1,4),(16,3,1,6),(24,2,1,8)]),
 dict(name='CAMPANAS', root=45, sc=NAT, energy=0.97, shape='peak', bars=152, bass='roll',
      chords=[[45,52,60,64],[48,55,64,67],[41,48,57,60],[43,50,58,62]],
      motif=[(0,4,2,1),(2,4,2,1),(4,7,2,3),(8,5,2,2),(12,4,2,2),(16,2,2,1),(18,4,2,1),(20,7,2,3),(24,9,1,3),(28,7,2,4)]),
 dict(name='PLAZA', root=43, sc=NAT, energy=0.74, shape='wave', bars=120, bass='roll',
      chords=[[43,50,58,62],[40,47,55,59],[38,45,53,57],[40,47,55,59]],
      motif=[(0,4,1,3),(6,5,1,2),(10,4,1,2),(16,2,1,3),(22,4,1,2),(26,5,1,5)]),
 dict(name='ROSA', root=45, sc=NAT, energy=0.50, shape='outro', bars=88, bass='round',
      chords=[[45,52,60,64,69],[41,48,57,64]],
      motif=[(0,4,1,6),(12,2,1,4),(16,0,1,8)]),
]


# ------------------------------------------------------------------ arreglo
def plan_blocks(sec):
    """bloques de 8 compases: capas que entran/salen, filtros que abren, valles.
    Regla: algo cambia cada bloque (cada 8), cambio mayor cada 2 (cada 16)."""
    nb = sec['bars'] // 8
    e = sec['energy']; shape = sec['shape']
    blocks = []
    for i in range(nb):
        p = i / max(1, nb - 1)
        b = dict(kick=1, bass=1, pads=0.5, keys=0, pluck=0, lead=0, perc=0.5,
                 shaker=1, hats=0.6, atmo=0.35, gain=1.0, pad_fc=900, dly=0.18)
        # capas entran progresivo (layering: +1 elemento por bloque)
        if i == 0: b.update(bass=0, pads=0.35, perc=0.25, hats=0.3, shaker=0)
        if i == 1: b.update(pads=0.4, perc=0.35)
        if i >= 2: b['keys'] = 1
        if i >= 3: b['pluck'] = 1
        if p > 0.30: b['lead'] = 1
        # el filtro del pad abre a lo largo de la sección (32-64 compases)
        b['pad_fc'] = 800 + (2600 * e) * min(1.0, p * 1.4)
        b['dly'] = 0.15 + 0.20 * p                       # sends crecen hacia la transición
        # olas y valles según la forma
        if shape == 'valley' and 0.42 < p < 0.68:
            b.update(kick=0, bass=0, gain=0.60, pluck=0, perc=0.15, shaker=0, lead=0,
                     pads=0.8, pad_fc=700 + 2400 * abs(p - 0.55) * 4)
        if shape == 'deep' and 0.30 < p < 0.72:
            b.update(kick=0, bass=0, gain=0.52, pluck=0, perc=0.0, shaker=0, hats=0.15,
                     pads=0.9, keys=1, atmo=0.6)
        if shape == 'wave' and 0.48 < p < 0.62:
            b.update(bass=0, gain=0.82, perc=0.3)        # mini-valle: respiración
        if shape == 'rise':
            b['gain'] = 0.75 + 0.25 * p
        if shape == 'peak':
            if 0.35 < p < 0.5:
                b.update(kick=0, bass=0, gain=0.66, pads=0.85)   # el breakdown que agranda el drop
            elif p >= 0.5:
                b.update(perc=0.85, hats=0.8, pluck=2, gain=1.0)
        if shape == 'outro':
            b['gain'] = 1.0 - 0.45 * max(0.0, p - 0.4)
            if p > 0.6: b.update(lead=0, pluck=0, keys=0)
        # micro-cambio garantizado por bloque
        b['var'] = i
        blocks.append(b)
    return blocks

_VIRS = {}
def _verb_ir(decay_s, tone, seed):
    key = (decay_s, tone, seed)
    if key not in _VIRS:
        m = int(decay_s * SR)
        rng = np.random.default_rng(seed)
        ir = rng.standard_normal(m).astype(np.float32) * np.exp(-np.linspace(0, 6.5, m)).astype(np.float32)
        ir = lp(ir, tone, 2)
        ir /= np.sqrt((ir ** 2).sum()) + 1e-12
        _VIRS[key] = ir * 0.30
    return _VIRS[key]

def sidechain_env(n, kick_steps, depth=0.42, rel_s=0.11):
    """se siente, no se escucha: ~4-6 dB, release ~110 ms."""
    env = np.ones(n, dtype=np.float32)
    dip = 1.0 - depth * np.exp(-np.arange(int(rel_s * 4 * SR)) / (rel_s * SR)).astype(np.float32)
    for pos in kick_steps:
        end = min(n, pos + len(dip))
        if end > pos:
            env[pos:end] = np.minimum(env[pos:end], dip[:end - pos])
    return env

def add(buf, pos, x, g=1.0):
    if pos < 0: x = x[-pos:]; pos = 0
    end = min(len(buf), pos + len(x))
    if end > pos:
        buf[pos:end] += x[:end - pos] * g

def render_section(sec, idx):
    rng = np.random.default_rng(1000 + idx * 7)
    bars = sec['bars']
    tail = XF_BARS * SPB
    n = bars * SPB + tail
    blocks = plan_blocks(sec)
    root, sc = sec['root'], sec['sc']
    chords = sec['chords']

    kickb = np.zeros(n, np.float32)
    bassb = np.zeros(n, np.float32)
    drumb = np.zeros(n, np.float32)
    keysb = np.zeros(n, np.float32)
    leadb = np.zeros(n, np.float32)
    pads = np.zeros((2, n), np.float32)
    kick_pos = []

    def sw(s, who='keys'):
        a = SWINGS[who]
        return s * S16 + (a - 0.5) * 2 * S16 * (s % 2)
    def swing16(s):
        return sw(s, 'keys')

    # patrones de bajo por bloque: cada 8 compases el roll CAMBIA de figura
    ROLL_VARS = [
        [s for s in range(16) if s % 4 != 0],          # roll completo (Léger)
        [2, 3, 6, 7, 10, 11, 14, 15],                  # pares al offbeat, más aire
        [1, 3, 6, 9, 11, 14],                          # sincopado, saltos
        [2, 5, 7, 10, 13, 15],                         # empujado, anticipos
    ]
    for bi, b in enumerate(blocks):
        bvar = (bi + idx) % len(ROLL_VARS)             # figura del bajo de ESTE bloque
        kmode = (bi + idx) % 4                         # sabor del kick de ESTE bloque
        for bar in range(8):
            gb = bi * 8 + bar
            if gb >= bars: break
            base = gb * SPB
            chord = chords[(gb // 2) % len(chords)]
            last16 = (gb % 16 == 15)                   # fin de frase de 16
            blockend = (bar == 7)                      # fin de bloque de 8
            # --- kick: 4x4 de base, pero RESPIRA al fin de frase y varía por bloque
            if b['kick']:
                for beat in range(4):
                    if last16 and beat >= 2 and (gb // 16) % 2 == 1:
                        continue                        # medio compás de silencio cada 32
                    add(kickb, base + int(beat * 4 * S16), KICK, 1.0)
                    kick_pos.append(base + int(beat * 4 * S16))
                if kmode == 1 and bar % 4 == 3 and not last16:
                    add(kickb, base + int(14 * S16), KICK, 0.4)      # ghost de arranque
                if kmode == 3 and bar % 2 == 1:
                    add(kickb, base + int(7 * S16), KICK, 0.3)       # empuje sincopado suave
            # --- bajo
            if b['bass']:
                fr = midi_f(chord[0] - 12 if chord[0] >= 45 else chord[0])
                fifth = fr * 1.5
                if sec['bass'] == 'round':
                    if bar % 2 == 0:
                        dur = BEAT_S * rng.choice([2.0, 1.5, 2.5])
                        add(bassb, base, bass_note(fr, dur, rng, 'round', 700), 0.95)
                        add(bassb, base + int(10 * S16), bass_note(fr * rng.choice([1.0, 1.5]), BEAT_S * 1.2, rng, 'round', 700), 0.6)
                    else:                               # el compás impar contesta distinto
                        add(bassb, base + int(2 * S16), bass_note(fr, BEAT_S * 1.3, rng, 'round', 700), 0.8)
                        add(bassb, base + int(8 * S16), bass_note(fifth if bvar % 2 else fr, BEAT_S * 1.6, rng, 'round', 700), 0.85)
                        if bvar == 2:
                            add(bassb, base + int(14 * S16), bass_note(fr * 2, BEAT_S * 0.5, rng, 'round', 900), 0.5)
                else:
                    # rolling: la figura cambia por bloque, el filtro abre, y hay fills
                    fc = 620 + 500 * (bi / max(1, len(blocks) - 1))
                    steps = ROLL_VARS[bvar]
                    for s in steps:
                        if rng.uniform() < 0.10: continue
                        f = fr
                        if s % 8 == 7 and rng.uniform() < 0.4: f = fr * 2.0
                        elif bvar == 2 and s in (6, 11): f = fifth
                        elif b.get('gain', 1.0) >= 0.95 and s >= 14: f = fr * 2.0
                        vel = 0.9 if s % 4 == 2 else 0.65
                        gate = 1.7 if bvar != 1 else 2.6
                        pos = base + int(sw(s, 'bass') + rng.normal(0, 0.004) * SR)
                        add(bassb, pos, bass_note(f, S16 / SR * gate, rng, 'roll', fc), vel)
                    if blockend:                        # fill: caminata al siguiente bloque
                        for k, d in enumerate([0, 2, 3, 4]):
                            fw = midi_f(deg(root, sc, d, 0) - 12 if chord[0] >= 45 else deg(root, sc, d, 0))
                            pos = base + int(swing16(12 + k))
                            add(bassb, pos, bass_note(fw, S16 / SR * 1.5, rng, 'roll', fc * 1.2), 0.75)
            # --- percusión orgánica: el TUMBAO cambia de figura por bloque
            pg = b['perc']
            pvar = (bi + idx + 1) % 3
            if pg > 0:
                TUMBAOS = [
                    [(3, 'cm', 0.8), (7, 'co', 1.0), (11, 'cm', 0.7), (14, 'co', 0.9)],
                    [(2, 'cm', 0.7), (5, 'co', 0.9), (10, 'cm', 0.8), (13, 'co', 0.9), (15, 'cm', 0.5)],
                    [(7, 'co', 1.0), (15, 'co', 0.8)],
                ]
                thin = last16 and (gb // 16) % 2 == 1   # la percusión también respira
                for s, kind, v in TUMBAOS[pvar]:
                    if thin and s >= 8: continue
                    if rng.uniform() < 0.85:
                        pos = base + int(sw(s, 'conga') + rng.normal(0, 0.005) * SR)
                        add(drumb, pos, hit_conga(rng, open_=(kind == 'co')), pg * v * 0.55)
                if bar % 2 == 1 and pg > 0.4 and pvar != 1:
                    for s in rng.choice([5, 9, 13], size=2, replace=False):
                        pos = base + int(swing16(int(s)) + rng.normal(0, 0.006) * SR)
                        add(drumb, pos, hit_bongo(rng), pg * (0.55 if pvar == 2 else 0.4))
                if pvar == 2 and bar % 2 == 0:          # clave 3-2 en rim cuando el tumbao abre espacio
                    for s in (0, 3, 6, 10, 12):
                        pos = base + int(swing16(s) + rng.normal(0, 0.004) * SR)
                        add(drumb, pos, hit_rim(rng), pg * 0.3)
                elif bar % 4 == 3 and rng.uniform() < 0.7:
                    add(drumb, base + int(swing16(15)), hit_rim(rng), pg * 0.5)
                if blockend and pg > 0.3:               # fill alterna: caminata de congas / redoble de bongo
                    if bi % 2 == 0:
                        for k, s in enumerate((12, 13, 14, 15)):
                            pos = base + int(swing16(s) + rng.normal(0, 0.004) * SR)
                            add(drumb, pos, hit_conga(rng, f0=175 + 30 * k, open_=(k == 3)), pg * (0.35 + 0.12 * k))
                    else:
                        for k, s in enumerate((12, 12.5, 13, 13.5, 14, 15)):
                            pos = base + int(s * S16 + rng.normal(0, 0.003) * SR)
                            add(drumb, pos, hit_bongo(rng), pg * (0.3 + 0.08 * k))
                        add(drumb, base + int(15 * S16), hit_hat(rng, open_=True), pg * 0.5)
            # --- shaker: tres figuras que rotan, y calla al final de frase
            if b['shaker']:
                svar = (bi + idx) % 3
                if not (last16 and (gb // 16) % 2 == 0):
                    if svar == 0: sk = range(16)
                    elif svar == 1: sk = range(0, 16, 2)
                    else: sk = (0, 3, 4, 7, 8, 11, 12, 15)          # galope
                    for s in sk:
                        acc = 1.0 if s % 4 == 2 else (0.55 if s % 2 == 0 else 0.75)
                        pos = base + int(sw(s, 'shaker') + rng.normal(0, 0.003) * SR)
                        add(drumb, pos, hit_shaker(rng), 0.19 * acc)
            # --- hats aireados: patrón por bloque y open hat que cambia de lugar
            hv = b['hats']
            if hv > 0:
                hvar = (bi + idx + 2) % 3
                HATS = [(2, 6, 10, 14), (2, 6, 9, 10, 14), (2, 5, 10, 13)]
                for s in HATS[hvar]:
                    pos = base + int(sw(s, 'hats') + rng.normal(0, 0.003) * SR)
                    add(drumb, pos, hit_hat(rng), hv * 0.55)
                if hvar == 0 and bar % 2 == 1:
                    add(drumb, base + int(swing16(8)), hit_hat(rng, open_=True), hv * 0.5)
                elif hvar == 1 and bar % 4 == 2:
                    add(drumb, base + int(swing16(12)), hit_hat(rng, open_=True), hv * 0.45)
                elif hvar == 2 and bar % 2 == 0:
                    add(drumb, base + int(swing16(4)), hit_hat(rng, open_=True), hv * 0.35)
            # --- pads supersaw (2 capas: grave + brillante) cada 2 compases
            if bar % 2 == 0 and b['pads'] > 0:
                durp = int(2 * SPB * 1.05)
                var = 1 if (gb >= bars - 2) else 0     # cambia UNA nota al final de la frase
                for lay, (o, det, g) in enumerate([(0, 0.32, 1.0), (1, 0.48, 0.38)]):
                    for ni, m in enumerate(chord[1:]):
                        mm = m + 12 * o + (2 if (var and ni == len(chord) - 2) else 0)
                        st = supersaw_st(midi_f(mm), durp, det, 0.7,
                                         seed=idx * 91 + gb * 7 + lay * 3 + ni)
                        cut = b['pad_fc'] * (1.0 + 0.8 * lay)
                        st = np.stack([lp(st[0], cut, 2), lp(st[1], cut, 2)])
                        env = np.minimum(1.0, np.arange(durp) / (0.9 * SR)).astype(np.float32)
                        env *= np.minimum(1.0, (durp - np.arange(durp)) / (0.8 * SR)).astype(np.float32)
                        gg = b['pads'] * g * 0.16 / max(1, len(chord) - 1)
                        add(pads[0], base, st[0] * env, gg)
                        add(pads[1], base, st[1] * env, gg)
            # --- rhodes stabs en 2 y 4 (llenan 200Hz-2k)
            if b['keys']:
                for s in (4, 12):
                    if rng.uniform() < 0.9:
                        pos = base + int(swing16(s) + rng.normal(0, 0.004) * SR)
                        for m in chord[1:4]:
                            add(keysb, pos, rhodes(midi_f(m), 0.55, rng), 0.30)
            # --- campanas: el gancho del pico y acentos de asombro en CATEDRAL
            if sec['name'] in ('CAMPANAS', 'CATEDRAL') and bar % 4 == 0 and b['pads'] > 0.3:
                bell_deg = [0, 4, 2, 4][(gb // 4) % 4]
                m = deg(root, sc, bell_deg, 1 if sec['name'] == 'CATEDRAL' else 2)
                add(keysb, base, campana(midi_f(m), 3.2, rng), 0.55 if sec['name'] == 'CAMPANAS' else 0.35)
            # --- cincel: el taller trabajando — la firma de piedra del disco
            if b['perc'] > 0.3 and (bi + idx) % 2 == 0:
                for s2 in ((3, 7, 11) if sec['name'] != 'TALLER' else (1, 3, 7, 9, 11, 15)):
                    if rng.uniform() < 0.6:
                        pos2 = base + int(sw(s2, 'hats') + rng.normal(0, 0.004) * SR)
                        add(drumb, pos2, hit_cincel(rng), b['perc'] * 0.42)
            # --- kalimba/pluck: el color tropical, contesta al motivo
            if b['pluck'] and bar % 2 == 1:
                pat = rng.choice([3, 6, 9, 11, 14], size=2 + b['pluck'], replace=False)
                for s in pat:
                    d = int(rng.integers(0, 5))
                    m = deg(root, sc, d, 2)
                    pos = base + int(swing16(int(s)) + rng.normal(0, 0.005) * SR)
                    add(keysb, pos, kalimba(midi_f(m), 0.8, rng), 0.5)
            # --- el gancho (frase melódica old-school — lección Messan)
            if b['lead'] and gb % 2 == 0:
                prev_f = None
                for (s, d, o, ln) in sec['motif']:
                    m = deg(root, sc, d, o)
                    f = midi_f(m)
                    dur = ln * S16 / SR * 1.15
                    pos = base + int(swing16(s % 16)) + (SPB if s >= 16 else 0)
                    x = lead_warm(prev_f or f, f, dur, seed=idx * 313 + gb * 17 + s,
                                  cutoff=1200 + 900 * b['gain'])
                    add(leadb, pos, x, 0.5)
                    prev_f = f

    # ---------------- buses → estéreo
    sc_env = sidechain_env(n, kick_pos)
    bassb *= sc_env
    keysb *= sc_env * 0.5 + 0.5
    drum_st = widen(sat(drumb, 1.3, 0.06), amount=0.7, seed=idx * 3 + 1)
    keys_st = pingpong(keysb, BEAT_S, fb=0.44, mix=0.42, taps=7, damp=4200)
    lead_st = pingpong(leadb, BEAT_S, fb=0.40, mix=0.48, taps=6, damp=3600)
    pads *= (sc_env * 0.4 + 0.6)[None, :]
    verb = np.stack([fconv(pads[0], _verb_ir(2.6, 4800, idx)),
                     fconv(pads[1], _verb_ir(2.6, 4800, idx + 77))])
    pads_st = pads + verb * 0.95              # reverb estéreo real: IR distinta por canal

    atmo = rng.standard_normal(n).astype(np.float32)
    wave_lfo = (0.5 + 0.5 * np.sin(2 * np.pi * np.arange(n) / (SR * 14.0))) ** 2
    atmo = lp(atmo, 1000, 2) * wave_lfo.astype(np.float32)
    atmo_st = widen(atmo, amount=0.6, seed=idx * 5 + 2)

    music = (drum_st * 0.8 + keys_st * 0.7 + lead_st * 0.75 + pads_st * 0.9 + atmo_st * 0.05)
    # realce lateral banda-limitada SOLO en el bus musical (kick/bajo intactos al centro)
    mm = 0.5 * (music[0] + music[1]); ss = 0.5 * (music[0] - music[1])
    ss = bp(ss, 220, 11000, 2) * 2.6
    music = np.stack([mm + ss, mm - ss])

    mix = np.zeros((2, n), np.float32)
    mix += kickb[None, :] * 1.18
    mix += bassb[None, :] * 1.45
    mix += music
    mix += rng.standard_normal((2, n)).astype(np.float32) * 0.0006   # piso análogo

    # v4: silencio de medio compás antes de cada subida fuerte (el impacto viene del silencio)
    prev_gain = 1.0
    for bi2, b2 in enumerate(blocks):
        if b2['gain'] >= 0.95 and prev_gain < 0.9 and bi2 > 0:
            cut0 = bi2 * 8 * SPB - SPB // 2
            cut1 = bi2 * 8 * SPB
            if cut0 > 0:
                for bufz in (kickb, bassb, drumb, leadb):
                    bufz[cut0:cut1] *= np.linspace(1.0, 0.0, cut1 - cut0).astype(np.float32) ** 0.4
        prev_gain = b2['gain']

    # macro-dinámica por bloque (la palanca del LRA)
    genv = np.ones(n, np.float32)
    for bi, b in enumerate(blocks):
        a, z = bi * 8 * SPB, min(n, (bi + 1) * 8 * SPB)
        genv[a:z] = b['gain']
    genv = lp(genv, 2.0, 1)                                # sin escalones audibles
    mix *= genv[None, :]

    mix = np.stack([sat(mix[0], 1.25, 0.05), sat(mix[1], 1.25, 0.05)])   # pegamento de bus
    mix = sub_mono(mix, 120.0)
    pk = np.abs(mix).max()
    if pk > 0.95: mix *= 0.95 / pk
    return mix

# ------------------------------------------------------------------ set completo
def build(only=None):
    total_bars = sum(s['bars'] for s in SECTIONS)
    print(f'CANTERA · {len(SECTIONS)} secciones · {total_bars} compases ≈ {total_bars*2/60:.0f} min')
    secs = []
    for i, s in enumerate(SECTIONS):
        if only and s['name'] != only: continue
        f = os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        expect = (s['bars'] + XF_BARS) * SPB * 8 + 44
        if not only and os.path.exists(f) and os.path.getsize(f) == expect:
            print(f'  ✓ {s["name"]} (ya renderizada)', flush=True)
            secs.append((i, s, f))
            continue
        print(f'  … {s["name"]} ({s["bars"]} compases, e={s["energy"]})', flush=True)
        mix = render_section(s, i)
        wav_write(f, mix)
        secs.append((i, s, f))
        del mix
    if only:
        i, s, f = secs[0]
        I, lra, tp = ffmeter(f)
        from dream_core import ffdecode
        mono = ffdecode(f, mono=True)
        print(f'  {s["name"]}: {I} LUFS, LRA {lra}, TP {tp} | spec {spectrum_pct(mono)}')
        return
    # concat con crossfade beat-aligned (la cola de cada sección suena bajo el fade-in de la siguiente)
    print('  … pegando con crossfades', flush=True)
    xf = XF_BARS * SPB
    total = sum(s['bars'] for s in SECTIONS) * SPB + xf
    out = np.zeros((2, total), np.float32)
    pos = 0
    for k, (i, s, f) in enumerate(secs):
        from dream_core import ffdecode
        x = ffdecode(f)
        if k > 0:
            ramp = np.linspace(0, 1, xf).astype(np.float32) ** 0.5
            x[:, :xf] *= ramp[None, :]
        add2 = min(total - pos, x.shape[1])
        out[:, pos:pos + add2] += x[:, :add2]
        pos += s['bars'] * SPB
        del x
    raw = os.path.join(TMP, 'cantera-raw.wav')
    wav_write(raw, out)
    del out
    print('  … masterizando a -8 LUFS', flush=True)
    final = os.path.join(HERE, 'masters', 'amr-cantera.wav')
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    hist = master_file(raw, final, target_i=-8.0, ceiling_db=-1.1)
    I, lra, tp = ffmeter(final)
    print(f'MASTER: pasos {hist} → {I} LUFS, LRA {lra}, TP {tp} dBTP')
    print(final)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else None)
