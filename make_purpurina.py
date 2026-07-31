#!/usr/bin/env python3
"""PURPURINA — 6 rolas generadas en Gemini, emparejadas y mezcladas en un set.

QUÉ HACE Y QUÉ NO
  No sintetiza nada. El material viene de Gemini; aquí se hace lo que sí se puede
  hacer bien midiendo: emparejar, corregir, alinear y mezclar. Mastering e
  ingeniería de un DJ mix, no producción.

POR QUÉ SON 6 Y NO 8
  Se generaron 8. Dos salieron con el centroide irrecuperablemente bajo
  (Before_the_Light_Returns y Lights_at_Five_AM: 24 combinaciones de repisa
  barridas, ninguna cruza el mínimo de 1443 Hz) y se descartaron. Antes de tirar
  la segunda se comprobó la hipótesis de que sólo la cola la arrastraba —
  diagnostica_confeti.py la partió en 8 tramos y la refutó: estaba apagada de
  punta a punta. No se mete una rola rota a un disco por completar el número.

LAS TRES CORRECCIONES
  1. TEMPO. Cinco de seis midieron 124.94–125.17: son 125.000 con ruido de
     medición y se estiran a exacto. La sexta (REFLECTOR) venía a 120.53 y sí
     necesita un estirón real de 3.7 %, audible pero aceptable en un set.
  2. FASE. Ninguna empieza en el 1; se recorta la cabeza al primer compás medido
     por rejilla.py o los cruces caen a contratiempo.
  3. TONO. REFLECTOR reprobó centroide (1387, mínimo 1443). Repisa medida por
     barrido, no de oído.

LA MEZCLA
  Cruces de 8 compases con ganancia equal-power (sin/cos) e intercambio de EQ:
  la que sale se filtra de graves hacia arriba mientras la que entra abre desde
  graves. Dos bombos juntos se embarran; separarlos por banda es lo que hace un
  DJ con las perillas.
"""
import os, json, subprocess
import numpy as np
from dream_core import (SR, FF, ffdecode, wav_write, ffmeter, lp, hp,
                        master_file, fir_from_gain, fconv)
from rejilla import rejilla

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '_purpurina', '_raw')
TMP = os.path.join(HERE, '_purpurina', '_tmp')

BPM = 125.000
BAR = 240.0 / BPM                       # 1.920 s exactos
BAR_N = int(round(BAR * SR))            # 84672 muestras
CRUCE = 8                               # compases de traslape

NIVEL_MEZCLA = -18.0
TECHO = -1.5                            # colchón para el sobrepaso del AAC

# EL ARCO. Emparejar todo al mismo nivel deja el set plano; un disco abre bajito,
# sube al pico y se apaga. Estos dB relativos son ese arco.
ARCO = {
    'VESTIDOR':  -3.0,   # sola en el camerino, casi sin bombo
    'REFLECTOR': -1.5,   # se prende la luz
    'LENTEJUELA': -0.7,
    'SALÓN':     -0.3,   # la pista llena, lo más físico
    'PURPURINA':  0.0,   # el pico
    'ÚLTIMA':    -2.6,   # prenden las luces y te vas
}

# archivo → (nombre, qué es). El orden es una noche de salón, del camerino
# vacío al piso lleno de brillos. PURPURINA (05) es el pico y es la única que
# midió MAYOR con correlación fuerte (Fa# mayor, r=.83) — por eso va ahí.
SET = [
    ('Porcelain_and_Light.mp3',        'VESTIDOR',
     'antes de salir; el arpegio solo, sin bombo'),
    ('Keys_Left_on_the_Table.mp3',     'REFLECTOR',
     'se prende la luz y entra el groove'),
    ('Light_Through_Glass.mp3',        'LENTEJUELA',
     'brillo puro; el arpegio gira'),
    ('Velvet_Salon_Hour.mp3',          'SALÓN',
     'la pista llena; lo más físico del disco'),
    ('Before_The_Curtains_Close.mp3',  'PURPURINA',
     'el pico: la melodía-himno, mayor y brillante'),
    ('Sunlight_On_A_Closed_Door.mp3',  'ÚLTIMA',
     'prenden las luces, el piso lleno de brillos, te vas'),
]

# Tonos MEDIDOS con analiza.py, no los que se pidieron — Gemini ignora la
# tonalidad del prompt de forma consistente, así que la ficha dice lo que las
# rolas SON. Dos salieron mayor de verdad, y el pico es una de ellas.
TONOS = ['E MIN', 'F# MIN', 'A# MAJ', 'D MIN', 'F# MAJ', 'E MAJ']

# Repisa sólo para la que reprobó. Salió de barrer 24 combinaciones (f0 2000-3500
# × +1.5 a +6.5 dB) midiendo el centroide de cada una: 2000/+6.5 fue la única que
# cruza el umbral con margen. Es la corrección más agresiva del catálogo (MICELIO
# necesitó +3.5/+4.0) y se anota como tal: si al escucharla suena artificial en
# los agudos, se regenera la rola en vez de forzarla más.
REPISA = {
    'REFLECTOR': (2000.0, 6.5),
}


def sh(args):
    subprocess.run(args, check=True, capture_output=True)


def repisa_agudos(x, f0, db):
    """Repisa suave de primer orden: plana abajo, +db arriba de f0."""
    g = 10.0 ** (db / 20.0)
    def gain(f):
        r = np.maximum(f, 1e-6) / f0
        return 1.0 + (g - 1.0) * (r ** 2 / (1.0 + r ** 2))
    h = fir_from_gain(gain, 2049)
    return np.stack([fconv(x[0], h, align=1), fconv(x[1], h, align=1)])


def prepara(fn, nombre):
    """Estira a 125.000, recorta al compás 1, corrige tono si hace falta."""
    src = os.path.join(RAW, fn)
    b, off, _ = rejilla(src)
    ratio = BPM / b

    est = os.path.join(TMP, f'{nombre}-est.wav')
    sh([FF, '-y', '-v', 'error', '-i', src, '-af', f'atempo={ratio:.9f}',
        '-ar', str(SR), '-ac', '2', est])

    x = ffdecode(est)
    if x.ndim == 1:
        x = np.stack([x, x])

    o = int(round(off * ratio))
    if o > 0:
        x = x[:, o:]
    nb = x.shape[1] // BAR_N
    x = x[:, :nb * BAR_N]

    if nombre in REPISA:
        f0, db = REPISA[nombre]
        x = repisa_agudos(x, f0, db)

    crudo = os.path.join(TMP, f'{nombre}-crudo.wav')
    wav_write(crudo, x)
    return crudo, nb, ratio, b


def eq_barrido(x, fcs, modo):
    """EQ que se mueve durante el cruce, imitando girar la perilla poco a poco."""
    n = x.shape[1]
    k = len(fcs)
    for i, fc in enumerate(fcs):
        a, b = i * n // k, (i + 1) * n // k
        if fc <= 0 or b <= a:
            continue
        for c in (0, 1):
            x[c, a:b] = (hp if modo == 'hp' else lp)(x[c, a:b], float(fc), 2)
    return x


def build():
    os.makedirs(TMP, exist_ok=True)
    ovn = CRUCE * BAR_N
    print(f'rejilla {BPM} BPM · compás {BAR_N} muestras · cruce {CRUCE} compases\n')

    segs = []
    for fn, nombre, _ in SET:
        crudo, nb, ratio, b = prepara(fn, nombre)
        # AQUÍ SÓLO SE EMPAREJA NIVEL, NO SE MASTERIZA. El limitador va UNA vez
        # al final; dos en serie aplastan el crest (lección de MICELIO).
        lufs = ffmeter(crudo)[0]
        g = 10.0 ** ((NIVEL_MEZCLA + ARCO[nombre] - lufs) / 20.0)
        x = ffdecode(crudo)
        if x.ndim == 1:
            x = np.stack([x, x])
        x = (x * g).astype(np.float32)
        x = x[:, :(x.shape[1] // BAR_N) * BAR_N]
        segs.append((nombre, x))
        print(f'  {nombre:11s} {b:7.3f}→125 ({ratio:.5f})  {x.shape[1]//BAR_N:3d} compases'
              f'  {x.shape[1]/SR:6.1f}s  {lufs:6.1f} LUFS  {g:5.2f}×', flush=True)

    total = sum(x.shape[1] for _, x in segs) - ovn * (len(segs) - 1)
    mix = np.zeros((2, total), dtype=np.float32)
    cortes, pos = [], 0
    for i, (nombre, x) in enumerate(segs):
        x = x.copy()
        n = x.shape[1]
        if i > 0:                       # entra: abre de graves hacia arriba
            h = min(ovn, n)
            x[:, :h] *= np.sin(np.linspace(0, np.pi / 2, h), dtype=np.float32)
            x[:, :h] = eq_barrido(x[:, :h], [300, 700, 1600, 4000, 0, 0, 0, 0], 'lp')
        if i < len(segs) - 1:           # sale: se le van quitando los graves
            t = min(ovn, n)
            x[:, -t:] = eq_barrido(x[:, -t:], [0, 0, 0, 0, 90, 200, 450, 1000], 'hp')
            x[:, -t:] *= np.cos(np.linspace(0, np.pi / 2, t), dtype=np.float32)
        mix[:, pos:pos + n] += x
        cortes.append(round((pos + (ovn // 2 if i > 0 else 0)) / SR, 1))
        pos += n - ovn

    crudo_set = os.path.join(TMP, 'purpurina-set-crudo.wav')
    wav_write(crudo_set, mix)
    dur = total / SR
    print(f'\nset: {dur:.1f}s = {dur/60:.1f} min · {total//BAR_N} compases')

    W = 900
    seg = total // W
    mono = np.abs(mix).mean(axis=0)[:seg * W].reshape(W, seg)
    pk = mono.max(axis=1)
    pk = (pk / max(1e-9, pk.max())).round(3).tolist()
    return crudo_set, dur, cortes, pk


if __name__ == '__main__':
    crudo, dur, cortes, pk = build()

    # ÚNICO paso de limitación de la cadena. El target NO se elige a gusto: se
    # masteriza a varios niveles y se lee el crest de cada uno, quedándose con
    # el más fuerte que aún pasa el juez. Spotify normaliza a -14, así que un
    # master más caliente no se oye más fuerte: sólo llega con menos dinámica.
    setm = os.path.join(TMP, 'purpurina-set.wav')
    mejor = None
    for tgt in (-11.5, -12.0, -12.5, -13.0):
        cand = os.path.join(TMP, f'purpurina-{abs(tgt):.1f}.wav')
        master_file(crudo, cand, target_i=tgt, ceiling_db=TECHO)
        x = ffdecode(cand)
        m = x.mean(axis=0) if x.ndim > 1 else x
        w = SR
        n = len(m) // w
        s = m[:n * w].reshape(n, w)
        crest = float(np.median(20 * np.log10(
            (np.abs(s).max(axis=1) + 1e-12) /
            (np.sqrt((s ** 2).mean(axis=1)) + 1e-12))))
        I, _, tp = ffmeter(cand)
        print(f'  target {tgt:+.1f} → LUFS {I:.1f} · TP {tp:+.1f} · crest 1s {crest:.1f} dB')
        if crest >= 8.5 and (mejor is None or tgt > mejor[0]):
            mejor = (tgt, crest, cand)
    tgt, crest, best = mejor
    print(f'→ elegido {tgt:+.1f} LUFS (crest {crest:.1f} dB, el más fuerte que pasa 8.5)')
    os.replace(best, setm)

    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    m4a = os.path.join(HERE, 'audio', 'amr-purpurina.m4a')
    sh([FF, '-y', '-v', 'error', '-i', setm,
        '-af', 'aformat=sample_fmts=fltp:sample_rates=44100',
        '-c:a', 'aac_at', '-b:a', '192k', '-movflags', '+faststart', m4a])
    print(f'\nM4A {os.path.getsize(m4a)//1024//1024} MB · {m4a}')
    print('medido:', ffmeter(m4a))

    meta = dict(
        id='amr-purpurina', title='PURPURINA', kicker='SEIS LUCES · UNA MEZCLA',
        tracks=len(SET), dur=round(dur, 1),
        titles=[n for _, n, _ in SET], notes=[d for _, _, d in SET],
        keys=TONOS, offsets=cortes, file='audio/amr-purpurina.m4a',
        art='art/purpurina.svg', edition=6, peaks=pk, bpm=125, key='F# MAJ')
    with open(os.path.join(HERE, 'purpurina.js'), 'w') as f:
        f.write('window.AMR_PURPURINA=' + json.dumps(meta, ensure_ascii=False) + ';')
    print('purpurina.js escrito ·', len(SET), 'cortes')
