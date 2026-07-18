#!/usr/bin/env python3
"""AFELIO — single sci-fi estilo Afterlife. 126 BPM, Sol menor, ~7 min.

Afelio: el punto de la órbita más lejano al sol. El arco de la rola es ese viaje —
te alejas, cruzas el frío, y el clímax es el punto de máxima distancia.

Construido con la INVESTIGACIÓN de Anyma/Afterlife, no de oído (ver af_voices.py
y la memoria anyma-afterlife-produccion). Las decisiones que vienen del research:

  · 126 BPM / Sol menor           — las cifras de "Consciousness"
  · i–VI–III–VII (Gm–Eb–Bb–F)     — "The Afterlife Classic", 2 fuentes independientes
  · acordes cada 2 compases       — contención armónica
  · gate del lead a 18 Hz         — DESINCRONIZADO del 1/32 (16.8 Hz a 126)
  · ataque del lead 32-45 ms      — nunca cero
  · lead de DOS capas             — cuerpo oscuro + brillo, cadenas independientes
  · reverb duckeado en todo       — sube cuando la voz calla
  · sub mono en 1/16 CON HUECO    — lo que evita el lodo
  · 8 canales                     — "Vertigo" de Kevin de Vries se hizo con 8
  · arp: decay que crece en el     build y se corta justo antes del drop
  · −10.4 LUFS / −1 dBTP          — bajo el rango del research, a favor del crest

Batería REAL de kit.py (CC0). Cero voces de formantes — regla dura de André.
Uso: python3 make_afelio.py DERIVA (una sección) | sin args = rola completa."""
import os, sys
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, widen, sub_mono, pingpong,
                        master_file, ffmeter, wav_write, spectrum_pct, ffdecode)
import kit as K
import af_voices as A
from af_voices import midi_f, deg, MIN, MAJ

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_afelio_tmp'); os.makedirs(TMP, exist_ok=True)
BPM = 126.0
SPB = int(round(SR * 240.0 / BPM))          # muestras por compás
S16 = SPB / 16.0                             # un 1/16
BEAT = 60.0 / BPM                            # 476.2 ms
XF = 2                                       # compases de cruce entre secciones
ROOT = 55                                    # Sol (G3) — Sol menor = 6A Camelot
GATE_HZ = 18.0                               # ⭐ 1/32 a 126 BPM = 16.8 Hz. Va suelto a propósito.
# Trim GLOBAL (mismo para todas las secciones): la sección pico picaba en 1.156.
# Se aplica igual a todas a propósito — normalizar cada sección por separado aplana
# la macro-dinámica (lección de BATUQUE). Deja el pico en ~0.88 y crest ~4.3.
TRIM = 0.73

# nombre, compases, y el peso de cada uno de los 8 canales
def L(**kw):
    b = dict(drums=0, kick=0, sub=0, mid=0, lead=0, stab=0, pad=1.0, arp=0,
             drone=0, gain=1.0, hats=0, perc=0, fx=0)
    b.update(kw); return b

SECTIONS = [
 dict(name='ORIGEN',   bars=16, lay=L(pad=1.0, drone=1.0, stab=0.22, gain=0.52)),
 dict(name='SEÑAL',    bars=16, lay=L(kick=1, hats=0.35, sub=0.8, pad=0.85, drone=0.6,
                                      stab=0.45, arp=0.3, perc=0.25, gain=0.74)),
 dict(name='ORBITA',   bars=32, lay=L(kick=1, drums=1, hats=0.58, perc=0.5, sub=1.0, mid=0.7,
                                      stab=1.0, pad=1.0, arp=0.85, gain=0.92)),
 dict(name='SILENCIO', bars=16, lay=L(pad=1.0, drone=0.8, lead=0.6, arp=0.3, fx=1, gain=0.66)),
 dict(name='DERIVA',   bars=32, lay=L(kick=1, drums=1, hats=0.62, perc=0.6, sub=1.0, mid=0.8,
                                      lead=1.0, stab=0.7, pad=0.9, arp=0.35, gain=1.0)),
 dict(name='NUCLEO',   bars=24, lay=L(kick=1, drums=1, hats=0.55, perc=0.7, sub=1.0, mid=0.5,
                                      lead=0.5, stab=1.0, pad=0.8, arp=0.6, gain=0.96)),
 dict(name='ASCENSO',  bars=16, lay=L(kick=1, drums=1, hats=0.7, perc=0.5, sub=0.9, mid=0.6,
                                      stab=0.5, pad=0.9, arp=1.0, fx=1, gain=0.94)),
 dict(name='AFELIO',   bars=40, lay=L(kick=1, drums=1, hats=0.72, perc=0.7, sub=1.0, mid=0.9,
                                      lead=1.0, stab=1.0, pad=1.0, arp=0.45, gain=1.06)),
 dict(name='RETORNO',  bars=32, lay=L(kick=1, drums=0.6, hats=0.4, perc=0.3, sub=0.6,
                                      lead=0.6, pad=1.0, drone=0.7, arp=0.2, gain=0.86)),
]

# ---- i–VI–III–VII en Sol menor = Gm – Eb – Bb – F ("The Afterlife Classic")
PROG = [0, 5, 2, 6]
def chord(ci):
    d = PROG[ci % 4]
    tri = [deg(ROOT, d, 0, MIN), deg(ROOT, d + 2, 0, MIN), deg(ROOT, d + 4, 0, MIN)]
    return dict(bass=ROOT + MIN[d % 7] - 24, tri=tri, add9=deg(ROOT, d + 1, 1, MIN))

# ---- el lead se escribe de 2 COMPASES DEJANDO HUECOS (es una llamada, no un pad)
#      (compás, 1/16 de inicio, largo en 1/16, grado del acorde)
MOTIF = [(0,  4, 6, 0), (0, 10, 4, 2), (0, 14, 2, 1),
         (1,  0, 7, 2), (1, 10, 6, 0)]
MOTIF_HI = [(0, 4, 6, 2), (0, 10, 4, 4), (0, 14, 2, 3),
            (1, 0, 7, 4), (1, 10, 6, 2)]

def sc(n, kpos, depth, rel):
    """sidechain por envolvente disparada en cada kick (volume-shaper, no compresor —
    el research es unánime en que aquí gana el shaper)."""
    e = np.ones(n, np.float32)
    m = int(rel * 4 * SR)
    dip = 1.0 - depth * np.exp(-np.arange(m) / (rel * SR)).astype(np.float32)
    for p in kpos:
        q = min(n, p + m)
        if q > p: e[p:q] = np.minimum(e[p:q], dip[:q - p])
    return e

def render(sec, idx):
    rng = np.random.default_rng(1200 + idx * 53)
    bars = sec['bars']; lay = sec['lay']
    n = bars * SPB + XF * SPB
    kickb = np.zeros(n, np.float32); drumb = np.zeros(n, np.float32)
    subb  = np.zeros(n, np.float32); midb  = np.zeros(n, np.float32)
    leadb = np.zeros(n, np.float32); stabb = np.zeros(n, np.float32)
    padb  = np.zeros(n, np.float32); arpb  = np.zeros(n, np.float32)
    dronb = np.zeros(n, np.float32); fxb   = np.zeros(n, np.float32)
    kpos = []

    def add(buf, pos, x, g=1.0):
        pos = int(pos)
        if pos < 0: x = x[-pos:]; pos = 0
        e = min(len(buf), pos + len(x))
        if e > pos: buf[pos:e] += x[:e - pos] * g

    for bar in range(bars):
        base = bar * SPB
        c = chord(bar // 2)                     # acorde cada 2 compases
        p = bar / max(1, bars - 1)              # avance dentro de la sección

        # ================= BATERÍA REAL (kit.py)
        if lay['kick']:
            for beat in range(4):
                pos = base + beat * 4 * S16
                add(kickb, pos, K.vary(K.smp(K.KICK), rng, 0.010, 0.07), 0.95)
                kpos.append(int(pos))
        if lay['drums']:
            for s in (4, 12):
                add(drumb, base + s * S16 - 0.010 * SR,
                    K.vary(K.smp(K.CLAP), rng, 0.02, 0.14), lay['drums'] * 0.40)
            if bar % 8 == 0:
                add(drumb, base, K.vary(K.smp(K.CRASH), rng), lay['drums'] * 0.34)
        if lay['hats'] > 0:
            for s in range(16):
                op = (s % 4 == 2)
                sm = K.smp(K.HATO) if op else K.smp(K.HATC)
                add(drumb, base + s * S16 + rng.normal(0, .0016) * SR,
                    K.vary(sm, rng, 0.03, 0.28),
                    (0.32 if s % 2 else 0.20) * lay['hats'] * (0.7 if op else 1))
        if lay['perc'] > 0:
            for s in range(2, 16, 4):
                add(drumb, base + s * S16 + rng.normal(0, .0028) * SR,
                    K.vary(K.smp(K.SHAKER), rng, 0.04, 0.3), lay['perc'] * 0.28)
            if bar % 2 == 1:
                add(drumb, base + 10 * S16, K.vary(K.smp(K.RIM), rng, 0.03, 0.2), lay['perc'] * 0.36)
            if lay['perc'] >= 0.7 and bar % 4 == 2:
                add(drumb, base + 6 * S16, K.vary(K.smp(K.CONGA_L), rng, 0.03, 0.2), lay['perc'] * 0.4)

        # ================= SUB — 1/16 rodando CON HUECO entre notas
        if lay['sub'] > 0:
            f = midi_f(c['bass'])
            for s in range(16):
                if s % 4 == 3: continue                  # el hueco: nada en el 4º
                dur = (S16 / SR) * 0.72                  # 72% del paso = no se solapan
                add(subb, base + s * S16, A.sub(f, dur, rng), lay['sub'])

        # ================= BAJO MEDIO — sustain 0, decay 400 ms, HP 90
        if lay['mid'] > 0:
            f = midi_f(c['bass'] + 12)
            for s in (0, 6, 10):
                add(midb, base + s * S16, A.midbass(f, 0.42, rng), lay['mid'])

        # ================= LEAD gated de 2 capas (frases de 2 compases con huecos)
        if lay['lead'] > 0:
            mot = MOTIF_HI if (bar // 2) % 4 >= 2 else MOTIF
            for mb, s0, ln, dg in mot:
                if bar % 2 != mb: continue
                nt = c['tri'][dg % 3] + 12 * (1 + dg // 3)
                dur = ln * S16 / SR
                add(leadb, base + s0 * S16,
                    A.lead(midi_f(nt), dur, rng, GATE_HZ, 1900 + 700 * p), lay['lead'])

        # ================= STAB FM (en los huecos del lead)
        if lay['stab'] > 0 and bar % 2 == 1:
            for s in (2, 8, 13):
                nt = c['tri'][(s // 4) % 3] + 24
                add(stabb, base + s * S16, A.fmstab(midi_f(nt), 0.34, rng), lay['stab'] * 0.7)

        # ================= PAD — un acorde sostenido 2 compases, reverb 6.5 s
        if lay['pad'] > 0 and bar % 2 == 0:
            ms = c['tri'] + [c['add9']]
            add(padb, base, A.pad(ms, 2 * SPB / SR * 1.02, rng, 1300 + 500 * p), lay['pad'])

        # ================= ARP — el decay CRECE en el build y se corta antes del drop
        if lay['arp'] > 0:
            if sec['name'] == 'ASCENSO':
                dec = 0.16 + 0.85 * p                     # se va alargando…
                if bar >= bars - 1: dec = 0.05            # …y ¡zas! cortísimo
            else:
                dec = 0.26
            for s in range(0, 16, 2):
                nt = c['tri'][(s // 2) % 3] + 24
                add(arpb, base + s * S16, A.arp(midi_f(nt), 2 * S16 / SR, rng, dec), lay['arp'] * 0.6)

        # ================= DRONE sci-fi
        if lay['drone'] > 0 and bar % 8 == 0:
            add(dronb, base, A.drone(midi_f(c['bass']) * 2, 8 * SPB / SR, rng), lay['drone'])

        # ================= FX de transición
        if lay['fx']:
            if bar == bars - 4:
                add(fxb, base, A.riser(4 * SPB / SR, rng), 0.85)
            if bar == 0:
                add(fxb, base, A.downlifter(2 * SPB / SR, rng), 0.6)

    # ================= BUSES + SIDECHAIN (profundidad graduada por elemento)
    e_sub  = sc(n, kpos, 0.82, 0.105)     # sub: empinado, ~100%
    e_mid  = sc(n, kpos, 0.55, 0.10)      # medio: más suave
    e_musz = sc(n, kpos, 0.34, 0.13)      # leads/stabs: gentil
    e_pad  = sc(n, kpos, 0.22, 0.18)      # pads: apenas

    subb *= e_sub; midb *= e_mid

    drum_st = widen(drumb, amount=0.42, seed=idx * 5 + 3)
    lead_st = pingpong(leadb * e_musz, BEAT * 1.5, fb=0.44, mix=0.42, taps=7, damp=5000)  # 1/8 punteado = 357 ms
    stab_st = pingpong(stabb * e_musz, BEAT * 0.5, fb=0.34, mix=0.30, taps=5, damp=6200)
    arp_st  = pingpong(arpb * e_musz, BEAT * 0.75, fb=0.30, mix=0.28, taps=5, damp=6800)
    pad_st  = widen(padb * e_pad, amount=0.62, seed=idx * 5 + 7)
    dron_st = widen(dronb * e_pad, amount=0.75, seed=idx * 5 + 11)
    fx_st   = widen(fxb, amount=0.6, seed=idx * 5 + 13)

    # Balance MEDIDO con solo por bus, no de oído. El primer intento tenía el kick
    # picando solo en 1.02, el sub en rms 0.22, y el pad/arp (los que cargan 54-57%
    # de medios) en rms 0.007/0.010 — de ahí que la mezcla diera 22% de medios y
    # 21% de aire. Los graves bajan, los medios suben.
    music = (drum_st * 0.60 + lead_st * 0.84 + stab_st * 0.54 + arp_st * 0.66
             + pad_st * 1.15 + dron_st * 0.62 + fx_st * 0.55)

    # ancho M/S sobre lo musical (nunca sobre el sub) + el corte de lodo del research
    mm = 0.5 * (music[0] + music[1]); ss = bp(0.5 * (music[0] - music[1]), 220, 12000, 2) * 2.0
    mix = np.stack([mm + ss, mm - ss])
    # sub a 0.96: medido contra las refs reales y contra VALLE, a 0.58 la rola daba
    # 4% de sub cuando las referencias dan 10-19%. El sub es mono y estable, así que
    # sube el RMS sin castigar el pico.
    mix += kickb[None, :] * 0.92 + subb[None, :] * 1.10 + midb[None, :] * 0.58

    mix = np.stack([mud(mix[0]), mud(mix[1])])
    mix *= lay['gain'] * TRIM
    mix = np.stack([sat(mix[0], 1.05, 0.02), sat(mix[1], 1.05, 0.02)])
    mix = sub_mono(mix, 120.0)                       # <120 Hz mono estricto
    pk = float(np.abs(mix).max())
    if pk > 1.2: mix *= 1.2 / pk                     # red de seguridad, no normalización
    return mix

def mud(x):
    """el arreglo de lodo que sale una y otra vez en el research: −3 dB en 250-400 Hz."""
    return x - bp(x, 250.0, 400.0, 2) * 0.29

def _shave(x):
    # afeitado SUAVE: a 1.28 la rola daba crest 2.39 contra 3.1-4.4 de las
    # referencias reales. El research es explícito: el tamaño sale del arreglo,
    # no del limitador.
    x = np.stack([sat(x[0], 1.10, 0.02), sat(x[1], 1.10, 0.02)])
    return x * (0.90 / max(1e-9, float(np.abs(x).max())))

def build(only=None):
    tot = sum(s['bars'] for s in SECTIONS)
    print(f'AFELIO · {len(SECTIONS)} secciones · {tot} compases · '
          f'{tot*SPB/SR/60:.2f} min · {BPM:.0f} BPM Sol menor', flush=True)
    secs = []
    for i, s in enumerate(SECTIONS):
        if only and s['name'] != only: continue
        f = os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        if not only and os.path.exists(f):
            print(f'  ✓ {s["name"]}', flush=True); secs.append((i, s, f)); continue
        print(f'  … {s["name"]} ({s["bars"]} comp)', flush=True)
        mix = render(s, i); wav_write(f, mix); secs.append((i, s, f)); del mix
    if only:
        i, s, f = secs[0]; I, lra, tp = ffmeter(f)
        print(f'  {s["name"]}: {I} LUFS · LRA {lra} · TP {tp} · {spectrum_pct(ffdecode(f, mono=True))}')
        return
    print('  … cruces', flush=True)
    xf = XF * SPB; total = tot * SPB + xf
    out = np.zeros((2, total), np.float32); pos = 0
    for k, (i, s, f) in enumerate(secs):
        x = ffdecode(f)
        if k > 0: x[:, :xf] *= (np.linspace(0, 1, xf) ** 0.5).astype(np.float32)[None, :]
        a = min(total - pos, x.shape[1]); out[:, pos:pos + a] += x[:, :a]; pos += s['bars'] * SPB
        del x
    print('  … afeitado suave + master −10.4 LUFS / −1 dBTP', flush=True)
    out = _shave(out)
    raw = os.path.join(TMP, 'afelio-raw.wav'); wav_write(raw, out); del out
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    final = os.path.join(HERE, 'masters', 'amr-afelio.wav')
    hist = master_file(raw, final, target_i=-10.4, ceiling_db=-1.0)
    I, lra, tp = ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}')
    print(f'ESPECTRO: {spectrum_pct(ffdecode(final, mono=True))}')
    print(final)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else None)
