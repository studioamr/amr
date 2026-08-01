#!/usr/bin/env python3
"""SESIÓN 003 — el set de 3 horas, curado con método y no de oído.

EL MÉTODO (así lo hacen los profesionales)
  1. La biblioteca se analiza ANTES de curar: BPM, Camelot y energía de cada
     pieza. Eso ya está en biblioteca.json (lo escribe biblioteca.py).
  2. Se planea EL PICO PRIMERO y todo lo demás se construye como subida hacia
     él y descenso después.
  3. Arco: abre en 4 → sube a 6 → pico 7+ → BAJA 2-3 piezas → segundo pico →
     cierre en 4. El error clásico es picar temprano: si el pico cae en el
     primer tercio, los otros dos tercios se sienten cuesta abajo.
  4. Se piensa en BLOQUES de energía parecida y luego se escalona, no
     pieza-por-pieza.
  5. Después de un pico hay que BAJAR, porque el contraste es lo que hace que
     el siguiente pico se sienta pico.

QUÉ MATERIAL USA — y por qué los cortes y no los discos
  Los discos completos ya son mezclas continuas CON SU PROPIO ARCO interno;
  encadenarlos enteros no deja curar nada, sólo pega seis arcos ajenos. Los
  cortes son piezas sueltas de 2:30 a 7:30 y son el material con el que sí se
  puede construir un arco de tres horas.

  Todo lo que entra es material propio de AMR. Nada de terceros.

LA MEZCLA
  Cruces de 8 compases con equal-power e intercambio de EQ, igual que en los
  discos. Todo el catálogo cae en 118-125 BPM, así que se lleva a 121.000 (la
  mediana medida) y ningún estirón pasa de 3 %.
"""
import os, json, subprocess
import numpy as np
from dream_core import (SR, FF, ffdecode, wav_write, ffmeter, lp, hp, master_file)
from rejilla import rejilla

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, 'audio')
TMP = os.path.join(HERE, '_sesion003', '_tmp')

BPM = 121.000
BAR = 240.0 / BPM
BAR_N = int(round(BAR * SR))
CRUCE = 8
NIVEL_MEZCLA = -18.0
# Techo -3.0. Medido: vuelta 1 con -1.5 dejó el m4a en +0.5 dBTP, vuelta 2 con
# -3.0 lo dejó en -0.1. El AAC suma ~2.9 dB en material tan denso. Bajarlo a
# -4.5 (vuelta 3) NO ayudó: sólo hizo que el limitador apretara más sin tocar
# el techo. La solución del true peak no es el techo, es el TRIM MEDIDO sobre
# el m4a ya codificado, en un lazo — igual que en ECO y en la repisa.
TECHO = -3.0
META_MIN = 180.0

# EQ de los cruces. La primera versión usaba el mismo barrido que los discos,
# con la saliente filtrada pasa-altos HASTA 1000 Hz — o sea, el último tramo de
# cada cruce quedaba en puro agudo. En un disco de 6 cruces eso no se nota; en
# un set de 44 cruces son ~12 minutos de brillo acumulado, y el centroide del
# set entero se fue a 3770 Hz (máximo 3515) aunque ninguna de sus piezas pasa
# de 2100. Se suaviza el tope para que la saliente conserve medios.
EQ_ENTRA = [300, 700, 1600, 4000, 0, 0, 0, 0]      # abre de graves hacia arriba
EQ_SALE  = [0, 0, 0, 0, 60, 120, 210, 320]          # antes 1000, luego 450

# Techo de centroide por pieza. 12 de las 29 del pool lo exceden (los 8 cortes
# de TULUM miden 6400-7400 Hz y cuatro singles viejos 4000-6400), y como TULUM
# ocupa casi un tercio del set, el promedio del set entero se iba a 3742 Hz
# contra un máximo de 3515. No es la mezcla: es el material de origen, que
# nunca pasó por el juez. Se les baja el brillo al preparar, midiendo.
CEN_MAX = 3200.0        # se apunta abajo del 3515 del juez, con margen

# EL ARCO OBJETIVO: posición del set (0..1) → energía buscada.
# Los dos picos y el VALLE entre ellos son el punto de todo el diseño.
ARCO_OBJ = [
    (0.00, 4.2, 'APERTURA — el cuarto todavía vacío'),
    (0.12, 4.8, 'se empieza a llenar'),
    (0.24, 5.4, 'ya hay gente'),
    (0.36, 6.0, 'la construcción'),
    (0.46, 7.0, 'PICO UNO'),
    (0.55, 5.3, 'el valle — para que el segundo pico golpee'),
    (0.64, 6.2, 'vuelve a subir'),
    (0.76, 7.3, 'PICO DOS — el clímax'),
    (0.87, 5.6, 'empieza el descenso'),
    (1.00, 4.1, 'CIERRE — prenden las luces'),
]


# El arco de arriba está escrito en la escala 4.1-7.3 que tenía la biblioteca
# ANTES de corregir el bug del centroide. Con la medición correcta el rango real
# del catálogo es otro, así que el arco se REESCALA a lo que de verdad existe —
# si no, todas las posiciones piden energías que ninguna pieza tiene y la
# curaduría se vuelve ruido.
E_ARCO_MIN = min(e for _, e, _ in ARCO_OBJ)
E_ARCO_MAX = max(e for _, e, _ in ARCO_OBJ)
_RANGO_REAL = [None, None]      # lo llena curar() con el pool ya filtrado


def objetivo(t):
    for i in range(len(ARCO_OBJ) - 1):
        t0, e0, _ = ARCO_OBJ[i]
        t1, e1, _ = ARCO_OBJ[i + 1]
        if t0 <= t <= t1:
            k = (t - t0) / max(1e-9, t1 - t0)
            e = e0 + (e1 - e0) * k
            break
    else:
        e = ARCO_OBJ[-1][1]
    lo, hi = _RANGO_REAL
    if lo is None:
        return e
    k = (e - E_ARCO_MIN) / max(1e-9, E_ARCO_MAX - E_ARCO_MIN)
    return lo + (hi - lo) * k


def curar():
    lib = json.load(open(os.path.join(HERE, 'biblioteca.json')))
    pool = [x for x in lib
            if (x['corte'] or x['file'].startswith('amr-00')
                or x['file'] == 'amr-eco.m4a')
            and 'sesion' not in x['file']]     # el set no se come a sí mismo
    _RANGO_REAL[0] = min(x['energia'] for x in pool)
    _RANGO_REAL[1] = max(x['energia'] for x in pool)
    print(f'rango de energía real del pool: {_RANGO_REAL[0]:.1f} – '
          f'{_RANGO_REAL[1]:.1f} (el arco se reescala a esto)')
    brillantes = [x for x in pool if x['centroide'] > CEN_MAX]
    if brillantes:
        print(f'{len(brillantes)} de {len(pool)} piezas exceden {CEN_MAX:.0f} Hz '
              f'de centroide y se les corrige el brillo al preparar:')
        for x in sorted(brillantes, key=lambda y: -y['centroide'])[:6]:
            print(f'    {x["file"]:38s} {x["centroide"]:5.0f} Hz')
    disp = sum(x['dur'] for x in pool) / 60.0
    print(f'pool: {len(pool)} piezas propias · {disp:.0f} min disponibles')
    print(f'meta: {META_MIN:.0f} min → se repetirá material {META_MIN/disp:.1f}×\n')

    elegidas, usadas, acum = [], set(), 0.0
    meta_s = META_MIN * 60.0
    while acum < meta_s:
        obj = objetivo(min(1.0, acum / meta_s))
        libres = [x for x in pool if x['file'] not in usadas]
        if not libres:                       # se agotó la vuelta: se reinicia
            usadas = set()
            libres = [x for x in pool
                      if not elegidas or x['file'] != elegidas[-1]['file']]
        prev = elegidas[-1] if elegidas else None

        def costo(x):
            c = abs(x['energia'] - obj)
            if prev:                          # penaliza brincos de tempo
                c += abs(x['bpm'] - prev['bpm']) / 12.0
            return c

        mejor = min(libres, key=costo)
        elegidas.append(mejor)
        usadas.add(mejor['file'])
        acum += mejor['dur'] - CRUCE * BAR
    return elegidas


def eq_barrido(x, fcs, modo):
    n = x.shape[1]
    k = len(fcs)
    for i, fc in enumerate(fcs):
        a, b = i * n // k, (i + 1) * n // k
        if fc <= 0 or b <= a:
            continue
        for c in (0, 1):
            x[c, a:b] = (hp if modo == 'hp' else lp)(x[c, a:b], float(fc), 2)
    return x


def cen_juez(x):
    """Centroide con el método EXACTO de juez.py — acumula espectros y saca uno
    solo del promedio, a 44100. No usar medianas por ventana ni decodificar a
    22050: eso da un número más bajo y fue justo lo que escondió que los cortes
    de TULUM venían en ~6700 Hz."""
    m = 0.5 * (x[0] + x[1]) if x.ndim > 1 else x
    W = 1 << 11
    acc = np.zeros(W//2 + 1)
    n = 0
    for i in range(0, len(m) - W, W*4):
        acc += np.abs(np.fft.rfft(m[i:i+W] * np.hanning(W)))
        n += 1
    if not n:
        return 0.0
    fr = np.fft.rfftfreq(W, 1.0/SR)
    return float((acc*fr).sum() / (acc.sum() + 1e-12))


def repisa_agudos(x, f0, db):
    """Repisa de primer orden. Con db negativo BAJA los agudos, que es como se
    usa aquí: el material de origen viene demasiado brillante."""
    from dream_core import fir_from_gain, fconv
    g = 10.0 ** (db / 20.0)
    def gain(f):
        r = np.maximum(f, 1e-6) / f0
        return 1.0 + (g - 1.0) * (r ** 2 / (1.0 + r ** 2))
    h = fir_from_gain(gain, 2049)
    return np.stack([fconv(x[0], h, align=1), fconv(x[1], h, align=1)])


_cache = {}


def prepara(pieza, idx):
    """Estira a 121.000 y recorta al compás 1. Se cachea por archivo: el set
    repite piezas y no tiene caso re-estirar la misma varias veces."""
    fn = pieza['file']
    if fn in _cache:
        return _cache[fn]
    src = os.path.join(AUDIO, fn)
    nom = fn.replace('.m4a', '')
    b, off, _ = rejilla(src)
    ratio = BPM / b
    est = os.path.join(TMP, f'{nom}-est.wav')
    subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-af',
                    f'atempo={ratio:.9f}', '-ar', str(SR), '-ac', '2', est],
                   check=True, capture_output=True)
    x = ffdecode(est)
    if x.ndim == 1:
        x = np.stack([x, x])
    o = int(round(off * ratio))
    if o > 0:
        x = x[:, o:]
    x = x[:, :(x.shape[1] // BAR_N) * BAR_N]

    # CORRECCIÓN DE BRILLO, sólo si la pieza lo excede, y medida en un lazo.
    # La repisa se aplica con dB NEGATIVO (baja agudos en vez de subirlos) y se
    # vuelve a medir hasta cruzar el techo, en vez de elegir un valor a ojo.
    if pieza['centroide'] > CEN_MAX:
        db = 0.0
        for _ in range(6):
            db -= 1.5
            y = repisa_agudos(x, 2500.0, db)
            c = cen_juez(y)
            if c <= CEN_MAX:
                break
        x = y.astype(np.float32)
        print(f'      brillo {pieza["centroide"]:.0f} → {c:.0f} Hz '
              f'(repisa {db:+.1f} dB @ 2500)', flush=True)

    lufs = ffmeter(src)[0]
    g = 10.0 ** ((NIVEL_MEZCLA - lufs) / 20.0)
    x = (x * g).astype(np.float32)
    _cache[fn] = (x, ratio, b)
    return _cache[fn]


def gan_arco(t):
    """Ganancia relativa según la posición en el set, en dB.

    ESTE ERA EL ERROR. La vuelta 1-3 emparejó las 44 piezas al MISMO nivel y
    puso el arco sólo en la SELECCIÓN (qué pieza suena), no en la DINÁMICA
    (qué tan fuerte suena). Resultado: crest de 1 s en 7.7-8.1 contra un mínimo
    de 8.5, y el limitador ni siquiera tocaba el techo (TP -2.2 en todos los
    targets) — o sea el problema nunca fue el master, era la mezcla plana.

    Es exactamente la lección que ya estaba escrita en make_micelio.py:
    "emparejar todas al mismo nivel dejó el set plano". Un set abre bajito,
    llega a un pico y se apaga, y eso se hace TAMBIÉN con ganancia.

    La curva sigue el mismo arco de energía: -6 dB en la apertura, 0 dB en el
    pico dos, -6 dB en el cierre.
    """
    e = objetivo(t)                       # 4.1 .. 7.3
    return -6.0 * (7.3 - e) / (7.3 - 4.1)


if __name__ == '__main__':
    os.makedirs(TMP, exist_ok=True)
    plan = curar()

    print(f'{"#":>3}  {"min":>6}  {"pieza":38s} {"BPM":>7} {"E":>4}  meta')
    acum = 0.0
    meta_s = META_MIN * 60.0
    for i, p in enumerate(plan):
        obj = objetivo(min(1.0, acum / meta_s))
        print(f'{i+1:3d}  {acum/60:6.1f}  {p["file"]:38s} {p["bpm"]:7.2f} '
              f'{p["energia"]:4.1f}  {obj:.1f}')
        acum += p['dur'] - CRUCE * BAR

    print(f'\npreparando {len(plan)} entradas '
          f'({len(set(p["file"] for p in plan))} archivos únicos)...')
    segs = []
    tacum = 0.0
    for i, p in enumerate(plan):
        x, ratio, b = prepara(p, i)
        # el arco TAMBIÉN en ganancia, no sólo en la selección de piezas
        gdb = gan_arco(min(1.0, tacum / meta_s))
        segs.append((p['file'], (x * (10.0 ** (gdb / 20.0))).astype(np.float32)))
        tacum += p['dur'] - CRUCE * BAR
        if (i + 1) % 10 == 0:
            print(f'  {i+1}/{len(plan)}  (arco {gdb:+.1f} dB)', flush=True)

    ovn = CRUCE * BAR_N
    total = sum(x.shape[1] for _, x in segs) - ovn * (len(segs) - 1)
    mix = np.zeros((2, total), dtype=np.float32)
    cortes, pos = [], 0
    for i, (nom, x) in enumerate(segs):
        x = x.copy()
        n = x.shape[1]
        if i > 0:
            h = min(ovn, n)
            x[:, :h] *= np.sin(np.linspace(0, np.pi/2, h), dtype=np.float32)
            x[:, :h] = eq_barrido(x[:, :h], EQ_ENTRA, 'lp')
        if i < len(segs) - 1:
            t = min(ovn, n)
            x[:, -t:] = eq_barrido(x[:, -t:], EQ_SALE, 'hp')
            x[:, -t:] *= np.cos(np.linspace(0, np.pi/2, t), dtype=np.float32)
        mix[:, pos:pos+n] += x
        cortes.append(round((pos + (ovn//2 if i > 0 else 0)) / SR, 1))
        pos += n - ovn

    crudo = os.path.join(TMP, 'sesion003-crudo.wav')
    wav_write(crudo, mix)
    dur = total / SR
    print(f'\nset: {dur/60:.1f} min ({dur/3600:.2f} h) · {total//BAR_N} compases')

    # El target NO se adivina. La vuelta 2 con -12.5 dejó el crest de 1 s en 8.1
    # (mínimo 8.5) porque bajar el techo obliga al limitador a apretar más para
    # llegar al mismo volumen. Se masteriza a varios niveles midiendo el crest
    # de cada uno y se toma el MÁS FUERTE que aún pasa. Spotify normaliza a -14,
    # así que un master más caliente no se oye más fuerte: sólo llega aplastado.
    setm = os.path.join(TMP, 'sesion003.wav')
    mejor = None
    for tgt in (-13.0, -13.5, -14.0, -14.5):
        cand = os.path.join(TMP, f'ses-{abs(tgt):.1f}.wav')
        master_file(crudo, cand, target_i=tgt, ceiling_db=TECHO)
        y = ffdecode(cand)
        m = y.mean(axis=0) if y.ndim > 1 else y
        ns = len(m) // SR
        s = m[:ns*SR].reshape(ns, SR)
        crest = float(np.median(20*np.log10(
            (np.abs(s).max(axis=1)+1e-12) / (np.sqrt((s**2).mean(axis=1))+1e-12))))
        I, _, tp = ffmeter(cand)
        print(f'  target {tgt:+.1f} → LUFS {I:.1f} · TP {tp:+.1f} · crest 1s {crest:.1f}',
              flush=True)
        if crest >= 8.8 and (mejor is None or tgt > mejor[0]):
            mejor = (tgt, crest, cand)
        else:
            os.remove(cand)
    if mejor is None:
        raise SystemExit('ningún target pasa el crest — revisar la mezcla')
    tgt, crest, best = mejor
    print(f'→ elegido {tgt:+.1f} LUFS (crest {crest:.1f}, el más fuerte que pasa 8.8)')
    os.replace(best, setm)

    # TRIM MEDIDO sobre el m4a YA CODIFICADO. El true peak no se resuelve
    # bajando el techo del limitador (la vuelta 3 lo probó): se resuelve
    # codificando, midiendo el AAC real y bajando hasta que cumpla.
    tmp_m4a = os.path.join(TMP, 'ses-trim.m4a')
    trim = 0.0
    for _ in range(5):
        subprocess.run([FF, '-y', '-v', 'error', '-i', setm, '-af',
                        f'volume={trim:.2f}dB,'
                        'aformat=sample_fmts=fltp:sample_rates=44100',
                        '-c:a', 'aac_at', '-b:a', '160k', tmp_m4a],
                       check=True, capture_output=True)
        _, _, tp = ffmeter(tmp_m4a)
        print(f'  trim {trim:+.2f} dB → m4a TP {tp:+.2f} dBTP', flush=True)
        if tp <= -1.2:
            break
        trim += (-1.5 - tp)
    m4a = os.path.join(AUDIO, 'amr-sesion003.m4a')
    subprocess.run([FF, '-y', '-v', 'error', '-i', setm, '-af',
                    f'volume={trim:.2f}dB,'          # el trim que midió el lazo
                    'aformat=sample_fmts=fltp:sample_rates=44100',
                    '-c:a', 'aac_at', '-b:a', '160k', '-movflags', '+faststart',
                    m4a], check=True, capture_output=True)
    print(f'M4A {os.path.getsize(m4a)//1024//1024} MB · medido {ffmeter(m4a)}')

    W = 1400
    seg = total // W
    mono = np.abs(mix).mean(axis=0)[:seg*W].reshape(W, seg)
    pk = mono.max(axis=1)
    pk = (pk / max(1e-9, pk.max())).round(3).tolist()

    def bonito(f):
        return (f.replace('amr-', '').replace('.m4a', '')
                 .replace('-cut-', ' · ').upper())

    meta = dict(id='amr-sesion003', title='SESIÓN 003',
                kicker='TRES HORAS · UNA MEZCLA', tracks=len(plan),
                dur=round(dur, 1), titles=[bonito(p['file']) for p in plan],
                notes=[f'E {p["energia"]} · {p["bpm"]:.0f} BPM' for p in plan],
                keys=[p['camelot'] or '—' for p in plan], offsets=cortes,
                file='audio/amr-sesion003.m4a', art='art/sesion003.svg',
                edition=3, peaks=pk, bpm=121, key='—')
    with open(os.path.join(HERE, 'sesion003.js'), 'w') as f:
        f.write('window.AMR_SESION003=' + json.dumps(meta, ensure_ascii=False) + ';')
    print('sesion003.js escrito ·', len(plan), 'piezas')
