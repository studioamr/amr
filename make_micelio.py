#!/usr/bin/env python3
"""MICELIO — 8 rolas generadas en Gemini, masterizadas parejas y mezcladas en set.

QUÉ HACE ESTE ARCHIVO Y QUÉ NO
  No sintetiza nada. El material viene de Gemini y ya está mezclado; aquí se hace
  lo que sí se puede hacer bien con medición: emparejar, corregir, alinear y
  mezclar. Es el trabajo de mastering e ingeniería de un DJ mix, no de producción.

LAS TRES CORRECCIONES QUE SE APLICAN
  1. TEMPO. Todas midieron 119.78–119.97 BPM: son 120.000 con ruido de medición.
     Se estira cada una a 120.000 exacto (atempo, 0.06 % — inaudible) para que el
     compás valga 2.000 s = 88200 muestras justas y la rejilla no se despegue en
     los 20 minutos de set.
  2. FASE. Ninguna empieza en el 1. Se recorta la cabeza al primer compás medido
     por rejilla.py, si no los cruces caen a contratiempo.
  3. TONO. Murmuration reprobó el juez: centroide 1349 Hz (mínimo 1443) e
     inclinación −9.4 dB/oct (piso −8.0). Está sorda de arriba. Se le pone una
     repisa de agudos calculada para meterla al rango, y se vuelve a juzgar.

LA MEZCLA
  Cruces de 8 compases (16 s) con dos cosas pasando a la vez:
    · ganancia equal-power (sin/cos) — mantiene volumen constante, no hace hueco
    · intercambio de EQ — la que sale se va filtrando de graves hacia arriba
      mientras la que entra abre desde graves. Dos bombos y dos bajos sonando
      juntos se cancelan y embarran; separarlos por banda es lo que hace un DJ
      con los tres perillas del mixer.
"""
import os, json, subprocess, wave
import numpy as np
from dream_core import (SR, FF, ffdecode, wav_write, ffmeter, lp, hp,
                        master_file, fir_from_gain, fconv)
from rejilla import rejilla

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '_micelio', '_raw')
OUT = os.path.join(HERE, '_micelio', 'master')
TMP = os.path.join(HERE, '_micelio', '_tmp')

BPM = 120.000
BAR = 240.0 / BPM                       # 2.000 s exactos
BAR_N = int(round(BAR * SR))            # 88200 muestras
CRUCE = 8                               # compases de traslape = 16 s

# Nivel al que se emparejan las rolas ANTES de mezclar. Bajo a propósito: aquí
# sólo se iguala volumen, con ganancia lineal. Todo el margen se lo queda el
# único limitador de la cadena, que vive al final.
NIVEL_MEZCLA = -18.0

# ⭐ EL ARCO. Emparejar las 8 al MISMO nivel dejó el set plano — LRA 2.1 contra
# el 6.6 de AFELIO. Un set no es plano: abre bajito, llega a un pico y se apaga.
# Estos dB relativos son ese arco, y de paso le devuelven al set el rango
# dinámico de largo plazo que la nivelación uniforme le había quitado.
ARCO = {
    'BRUMA':      -2.5,   # abre en la niebla, casi vacío
    'SENDERO':    -1.5,
    'RAUDAL':     -0.8,
    'FLORESTA':   -0.5,
    'MICELIO':     0.0,   # el pico: asombro, no euforia
    'LUCIÉRNAGA': -0.6,
    'CLARO':      -1.2,   # se abre el cielo, y se afloja
    'ALBA':       -3.0,   # salir caminando, amaneciendo
}
# Techo del master. Se pide −1.5 y no −1.0 porque el AAC sobrepasa al codificar:
# la primera vuelta salió a −0.5 dBTP y reprobó. El colchón es el códec.
TECHO = -1.5

# archivo → (nº, nombre, qué es). El orden es una noche en el bosque, de la
# bruma de entrada al amanecer de salida.
#
# Ocho momentos místicos, la flauta como voz, agua/pájaros/grillos tejidos en
# todas. MICELIO (05) es el pico por ASOMBRO — la red que se enciende bajo tus
# pies — no por euforia. Ninguna en tonalidad mayor con "the peak" tipo AURORA.
SET = [
    ('01-BRUMA.mp3',       'BRUMA',
     'la niebla al entrar al bosque, al anochecer'),
    ('02-SENDERO.mp3',     'SENDERO',
     'la caminata; el groove se asienta'),
    ('03-RAUDAL.mp3',      'RAUDAL',
     'el arroyo; agua por todos lados'),
    ('04-FLORESTA.mp3',    'FLORESTA',
     'lo profundo del dosel; denso y vivo'),
    ('05-MICELIO.mp3',     'MICELIO',
     'la red se enciende bajo tus pies — el pico por asombro'),
    ('06-LUCIERNAGA.mp3',  'LUCIÉRNAGA',
     'chispas de luz entre los árboles'),
    ('07-CLARO.mp3',       'CLARO',
     'el claro bajo las estrellas; lo más ancho'),
    ('08-ALBA.mp3',        'ALBA',
     'amanece; salir caminando del bosque'),
]


# Repisa de agudos sólo para la que reprobó. Los valores salieron de barrer
# cinco combinaciones y leer las dos métricas en cada una — no de oído:
#   3500/+4.5 → 1811 Hz, −8.73   ·   2500/+5.5 → 1962, −8.31
#   2000/+6.0 → 2034,   −8.09    ·   1800/+6.5 → 2101, −7.94  ✓
# 1800/+6.5 es la corrección MÍNIMA que mete las dos al rango. Es fuerte, y se
# justifica: la fuente venía en −9.4 dB/oct, muy fuera de la distribución de
# Pestana. Además le sirve al concepto — la rola es la de "cien mil detallitos
# chiquitos", y estaban enterrados.
REPISA = {
    # SENDERO reprobó centroide (1368 Hz, mínimo 1443). Barrido de 5 puntos:
    # 2500/+4.0 → 1754 Hz, -6.62  fue la corrección MÍNIMA que la mete al rango.
    'SENDERO':    (2500.0, 4.0),
    # LUCIÉRNAGA reprobó inclinación (-8.54, piso -8.0) — pelín cálida de más.
    # 2500/+3.5 → -7.84 fue la mínima que la mete al rango.
    'LUCIÉRNAGA': (2500.0, 3.5),
}   # se llena si el juez reprueba alguna por sorda de agudos


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
    """Estira a 120.000, recorta al compás 1, corrige tono, masteriza."""
    src = os.path.join(RAW, fn)
    b, off, _ = rejilla(src)
    ratio = BPM / b

    # 1. estirar al tempo exacto (atempo preserva la afinación)
    est = os.path.join(TMP, f'{nombre}-est.wav')
    sh([FF, '-y', '-v', 'error', '-i', src, '-af', f'atempo={ratio:.9f}',
        '-ar', str(SR), '-ac', '2', est])

    x = ffdecode(est)
    if x.ndim == 1:
        x = np.stack([x, x])

    # 2. recortar al primer compás (el offset también se estiró)
    o = int(round(off * ratio))
    if o > 0:
        x = x[:, o:]
    nb = x.shape[1] // BAR_N                       # compases enteros
    x = x[:, :nb * BAR_N]

    # 3. corrección de tono si el juez la reprobó
    if nombre in REPISA:
        f0, db = REPISA[nombre]
        x = repisa_agudos(x, f0, db)

    crudo = os.path.join(TMP, f'{nombre}-crudo.wav')
    wav_write(crudo, x)
    return crudo, nb, ratio, b


def eq_barrido(x, fcs, modo):
    """EQ que se mueve durante el cruce: se parte en bloques y cada uno filtra
    a distinta frecuencia, imitando girar la perilla poco a poco."""
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
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    ovn = CRUCE * BAR_N

    print(f'rejilla {BPM} BPM · compás {BAR_N} muestras · cruce {CRUCE} compases\n')
    segs = []
    for fn, nombre, _ in SET:
        crudo, nb, ratio, b = prepara(fn, nombre)
        # ⚠️ AQUÍ SÓLO SE EMPAREJA NIVEL, NO SE MASTERIZA.
        # La primera versión masterizaba cada rola Y LUEGO el set completo: dos
        # limitadores en serie. El juez lo cachó — crest se cayó de 9/11 a
        # 6.3/6.6, o sea aplastado. El limitador va UNA sola vez, al final de la
        # cadena. Antes de eso, ganancia lineal y nada más.
        lufs = ffmeter(crudo)[0]
        g = 10.0 ** ((NIVEL_MEZCLA + ARCO[nombre] - lufs) / 20.0)
        x = ffdecode(crudo)
        if x.ndim == 1:
            x = np.stack([x, x])
        x = (x * g).astype(np.float32)
        x = x[:, :(x.shape[1] // BAR_N) * BAR_N]
        segs.append((nombre, x))
        print(f'  {nombre:17s} {b:7.3f}→120 ({ratio:.5f})  {x.shape[1]//BAR_N:3d} compases'
              f'  {x.shape[1]/SR:6.1f}s  {lufs:6.1f} LUFS {g:+5.2f}×', flush=True)

    total = sum(x.shape[1] for _, x in segs) - ovn * (len(segs) - 1)
    mix = np.zeros((2, total), dtype=np.float32)
    cortes, pos = [], 0
    for i, (nombre, x) in enumerate(segs):
        x = x.copy()
        n = x.shape[1]
        if i > 0:                                   # entra: abre de graves hacia arriba
            h = min(ovn, n)
            x[:, :h] *= np.sin(np.linspace(0, np.pi / 2, h), dtype=np.float32)
            x[:, :h] = eq_barrido(x[:, :h], [300, 700, 1600, 4000, 0, 0, 0, 0], 'lp')
        if i < len(segs) - 1:                       # sale: se le van quitando los graves
            t = min(ovn, n)
            x[:, -t:] = eq_barrido(x[:, -t:], [0, 0, 0, 0, 90, 200, 450, 1000], 'hp')
            x[:, -t:] *= np.cos(np.linspace(0, np.pi / 2, t), dtype=np.float32)
        mix[:, pos:pos + n] += x
        # el corte se marca donde la nueva ya manda: a la mitad del cruce
        cortes.append(round((pos + (ovn // 2 if i > 0 else 0)) / SR, 1))
        pos += n - ovn

    crudo_set = os.path.join(TMP, 'micelio-set-crudo.wav')
    wav_write(crudo_set, mix)
    dur = total / SR
    print(f'\nset: {dur:.1f}s = {dur/60:.1f} min · {total//BAR_N} compases')

    # picos para la onda de la página
    W = 900
    seg = total // W
    mono = np.abs(mix).mean(axis=0)[:seg * W].reshape(W, seg)
    pk = mono.max(axis=1)
    pk = (pk / max(1e-9, pk.max())).round(3).tolist()
    return crudo_set, dur, cortes, pk, segs


if __name__ == '__main__':
    crudo, dur, cortes, pk, segs = build()

    # ÚNICO paso de limitación en toda la cadena.
    #
    # El objetivo NO se eligió a gusto: se midió. Con la mezcla ya hecha se
    # masterizó a cuatro niveles y se leyó el crest de 1 s en cada uno:
    #     −11.5 → 8.0 (reprueba)   −12.0 → 8.4 (reprueba)
    #     −12.5 → 8.9 (pasa)       −13.0 → 9.3
    # −12.5 es donde cruza el umbral con margen. Y no cuesta nada real: Spotify
    # y Apple normalizan a −14, así que un master más fuerte no se oye más
    # fuerte — sólo llega con menos dinámica. El experimento que llevó aquí
    # midió los tres puntos de la cadena y mostró que la mezcla en sí sólo
    # cuesta 0.2 dB de crest; los 3.2 restantes eran el limitador.
    setm = os.path.join(TMP, 'micelio-set.wav')
    master_file(crudo, setm, target_i=-12.5, ceiling_db=TECHO)

    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    m4a = os.path.join(HERE, 'audio', 'amr-micelio.m4a')
    sh([FF, '-y', '-v', 'error', '-i', setm,
        '-af', 'aformat=sample_fmts=fltp:sample_rates=44100',
        '-c:a', 'aac_at', '-b:a', '192k', '-movflags', '+faststart', m4a])
    print(f'\nM4A {os.path.getsize(m4a)//1024//1024} MB · {m4a}')
    print('medido:', ffmeter(m4a))

    # Tonos MEDIDOS con analiza.py, no los que se pidieron: Gemini no respetó
    # las tonalidades del prompt, así que la ficha dice lo que las rolas son.
    # F MAJ es la modal del set (3 de 8) y es la que se usa para el Camelot.
    TONOS = ['A MIN', 'D MIN', 'F MAJ', 'E MAJ', 'G MIN', 'D MIN', 'A MIN', 'A MIN']
    meta = dict(
        id='amr-micelio', title='MICELIO', kicker='OCHO NOCHES · UNA MEZCLA',
        tracks=len(SET), dur=round(dur, 1),
        titles=[n for _, n, _ in SET], notes=[d for _, _, d in SET],
        keys=TONOS, offsets=cortes, file='audio/amr-micelio.m4a',
        art='art/micelio.svg', edition=8, peaks=pk, bpm=120, key='D MIN')
    with open(os.path.join(HERE, 'micelio.js'), 'w') as f:
        f.write('window.AMR_MICELIO=' + json.dumps(meta, ensure_ascii=False) + ';')
    print('micelio.js escrito ·', len(SET), 'cortes')
