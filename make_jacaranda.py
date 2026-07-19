#!/usr/bin/env python3
"""JACARANDA — 7 rolas generadas en Gemini, masterizadas parejas y mezcladas en set.

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
RAW = os.path.join(HERE, '_jacaranda', '_raw')
OUT = os.path.join(HERE, '_jacaranda', 'master')
TMP = os.path.join(HERE, '_jacaranda', '_tmp')

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
    'VÍSPERA':   -2.5,   # abre, casi vacío
    'AUGURIO':   -1.2,
    'FULGOR':    -0.5,
    'LETANÍA':   -0.6,
    'EPIFANÍA':   0.0,   # el pico
    'PENUMBRA':  -1.8,   # se apaga la luz, y se oye
    'ÉTER':      -1.0,
    'VESTIGIO':  -3.0,   # irse caminando
}
# Techo del master. Se pide −1.5 y no −1.0 porque el AAC sobrepasa al codificar:
# la primera vuelta salió a −0.5 dBTP y reprobó. El colchón es el códec.
TECHO = -1.5

# archivo → (nº, nombre, qué es). El orden es el del florecimiento.
#
# LOS NOMBRES son místicos, no botánicos. Un primer intento fue por el ciclo del
# árbol (savia, yema, dosel, vaina…) y André lo rechazó: "pon otra cosa mística".
# Tiene razón — el jacarandá interesa como EVENTO, no como lección de botánica:
# un árbol que pone violeta una ciudad entera tres semanas y se acaba. Visto así
# es un presagio, un resplandor y un vestigio, no un diagrama de partes.
#
# ⚠️ Ninguno repite los nombres de los dos discos JACARANDA viejos que se
# borraron (SEMILLA, BROTE, RAMA, SOMBRA, FLOR, ABRIL, PETALOS, PRIMAVERA,
# RAIZ, CALMA, LLUVIA) — se revisó uno por uno.
#
# Sky_Catches_Fire.mp3 (aquí EPIFANÍA) salió y volvió a entrar. André dijo
# "parece Avicii" señalando el minuto 11:30, y se quitó; después aclaró que se
# había confundido y que esa sí le gustaba. Vuelve tal cual, en su lugar.
# Se deja anotado para no volver a sacarla por error.
SET = [
    ('Before_The_Sun_Hits.mp3',   'VÍSPERA',
     'la noche antes de que algo pase'),
    ('Cooling_The_Soil.mp3',      'AUGURIO',
     'la primera flor: la señal de que ya viene'),
    ('Glow_in_the_Deep.mp3',      'FULGOR',
     'el resplandor — la ciudad entera prendida en violeta'),
    ('Murmuration_at_Dusk.mp3',   'LETANÍA',
     'miles de flores idénticas repitiendo hasta volverse una sola'),
    ('Sky_Catches_Fire.mp3',      'EPIFANÍA',
     'la luz que llega de golpe y lo explica todo'),
    ('Midnight_at_Noon.mp3',      'PENUMBRA',
     'la sombra parcial: ni luz ni oscuridad'),
    ('Salt_Flat_Mirror.mp3',      'ÉTER',
     'lo que llena el vacío. La única sin voz'),
    ('Between_The_Tides.mp4',     'VESTIGIO',
     'lo que queda cuando ya pasó'),
]


# Repisa de agudos sólo para la que reprobó. Los valores salieron de barrer
# cinco combinaciones y leer las dos métricas en cada una — no de oído:
#   3500/+4.5 → 1811 Hz, −8.73   ·   2500/+5.5 → 1962, −8.31
#   2000/+6.0 → 2034,   −8.09    ·   1800/+6.5 → 2101, −7.94  ✓
# 1800/+6.5 es la corrección MÍNIMA que mete las dos al rango. Es fuerte, y se
# justifica: la fuente venía en −9.4 dB/oct, muy fuera de la distribución de
# Pestana. Además le sirve al concepto — la rola es la de "cien mil detallitos
# chiquitos", y estaban enterrados.
REPISA = {'LETANÍA': (1800.0, 6.5)}


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

    crudo_set = os.path.join(TMP, 'jacaranda-set-crudo.wav')
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
    setm = os.path.join(TMP, 'jacaranda-set.wav')
    master_file(crudo, setm, target_i=-12.5, ceiling_db=TECHO)

    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    m4a = os.path.join(HERE, 'audio', 'amr-jacaranda.m4a')
    sh([FF, '-y', '-v', 'error', '-i', setm,
        '-af', 'aformat=sample_fmts=fltp:sample_rates=44100',
        '-c:a', 'aac_at', '-b:a', '192k', '-movflags', '+faststart', m4a])
    print(f'\nM4A {os.path.getsize(m4a)//1024//1024} MB · {m4a}')
    print('medido:', ffmeter(m4a))

    # Tonos MEDIDOS con analiza.py, no los que se pidieron: Gemini no respetó
    # las tonalidades del prompt, así que la ficha dice lo que las rolas son.
    # F MAJ es la modal del set (3 de 8) y es la que se usa para el Camelot.
    TONOS = ['F MAJ', 'F MAJ', 'C MAJ', 'C MAJ', 'F MAJ', 'A MIN', 'E MIN', 'D MIN']
    meta = dict(
        id='amr-jacaranda', title='JACARANDA', kicker='FLORACIÓN · UNA MEZCLA',
        tracks=len(SET), dur=round(dur, 1),
        titles=[n for _, n, _ in SET], notes=[d for _, _, d in SET],
        keys=TONOS, offsets=cortes, file='audio/amr-jacaranda.m4a',
        art='art/jacaranda.svg', edition=8, peaks=pk, bpm=120, key='F MAJ')
    with open(os.path.join(HERE, 'jacaranda.js'), 'w') as f:
        f.write('window.AMR_JACARANDA=' + json.dumps(meta, ensure_ascii=False) + ';')
    print('jacaranda.js escrito ·', len(SET), 'cortes')
