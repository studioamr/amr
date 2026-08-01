#!/usr/bin/env python3
"""RESACA — Brazilian bass sintetizado desde cero. Sin Gemini: puro numpy.

EL PROBLEMA QUE HAY QUE NO REPETIR
  Ya hubo un intento de este género en el proyecto (BATUQUE) y André lo mandó
  tirar entero: el bajo salió "durísimo, sobresaturado". El error fue buscar el
  carácter del bajo con SATURACIÓN.

  El carácter real de este bajo no viene de saturar. Viene de una CAÍDA DE TONO
  muy corta —10-12 ms— al inicio de cada nota: un envelope rápido sobre el pitch
  de los osciladores. Eso es el "slap". Da mordida y ataque sin volver áspero el
  sonido. La saturación aquí es un condimento (drive bajo), no el plato.

  Regla dura de este archivo: el bajo se mide, y si el juez dice que quedó
  áspero, se corrige el pitch envelope — nunca se sube el drive.

LA RECETA DEL GÉNERO (de la investigación)
  · bajo con pitch-drop de ~11 ms  → el slap
  · sub MONO abajo de 120 Hz       → que no se despedace en sistemas grandes
  · el bajo cae ENTRE los kicks    → el vaivén que define el género
  · sidechain fuerte contra el kick
  · compresión multibanda suave y saturación LIGERA
  · delay corto tipo slap + reverb de cuarto chico, nunca en el grave

LA MÚSICA ES ORIGINAL. Se tomó el género —que es una técnica, no una obra— y no
ninguna melodía existente. Progresión propia en La menor, melodía propia.
"""
import os, subprocess
import numpy as np
from dream_core import (SR, FF, wav_write, ffmeter, lp, hp, sat, sub_mono,
                        widen, stereo_verb, master_file, limit)

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_resaca')

BPM = 126.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
def n(b): return int(round(b * BEAT * SR))      # beats → muestras


# ── la música ──────────────────────────────────────────────────────────────
# La menor. Progresión i–VI–III–VII, la cadencia melancólica que sostiene todo
# el género: suena triste y aun así te mueve. Cuatro compases que dan la vuelta.
RAIZ = {'A': 55.00, 'F': 43.65, 'C': 65.41, 'G': 49.00}
PROG = ['A', 'F', 'C', 'G']

# la melodía del gancho, en semitonos sobre La. Original: sube, se detiene en la
# séptima y cae — el gesto de "casi llegar" que hace que quieras repetirla.
GANCHO = [(0, 12, 1.5), (1.5, 15, 0.5), (2, 17, 1.0), (3, 15, 1.0),
          (4, 12, 1.5), (5.5, 10, 0.5), (6, 12, 2.0)]

ESTRUCTURA = [
    ('intro',  8), ('build',  8), ('drop',  16), ('puente', 8),
    ('drop2', 16), ('salida', 8),
]


def env(N, a, d, s, r, sus_level=0.7):
    """ADSR en muestras."""
    e = np.zeros(N)
    a, d, r = max(1, a), max(1, d), max(1, r)
    e[:a] = np.linspace(0, 1, a)
    e[a:a+d] = np.linspace(1, sus_level, d)
    fin = N - r
    if fin > a + d:
        e[a+d:fin] = sus_level
    e[fin:] = np.linspace(e[fin-1] if fin > 0 else sus_level, 0, N - fin)
    return e


def bajo_slap(f0, N, drive=1.35):
    """EL BAJO. Su carácter viene del PITCH ENVELOPE, no de la saturación.

    Un envelope de 11 ms que arranca 7 semitonos arriba y cae a la nota. Eso es
    el 'slap': el oído lo lee como un golpe de dedo en una cuerda. Con esto el
    bajo muerde sin necesidad de drive alto — que es exactamente lo que arruinó
    a BATUQUE.
    """
    t = np.arange(N) / SR
    ms11 = int(0.011 * SR)
    pitch = np.ones(N)
    pitch[:ms11] = 2 ** (np.linspace(7.0, 0.0, ms11) / 12.0)   # cae 7 semitonos
    fase = 2 * np.pi * np.cumsum(f0 * pitch) / SR

    # dos osciladores: diente (cuerpo y armónicos) + seno (el fundamental)
    dientes = 2.0 * (fase / (2*np.pi) % 1.0) - 1.0
    seno = np.sin(fase)
    x = 0.55 * dientes + 0.75 * seno

    # el envelope de amplitud, corto y percusivo
    x *= env(N, int(0.004*SR), int(0.09*SR), 0, int(0.05*SR), 0.55)

    # saturación LIGERA: condimento, no plato. drive 1.35, no 3+.
    x = sat(x, drive=drive, asym=0.06)
    # se le quita el ruido de arriba, que es donde vive la aspereza
    # 2600 dejaba el bajo sin definición y el mix entero oscuro (centroide
    # 1315, mínimo 1443). 3400 conserva la mordida del slap sin traer la
    # aspereza — que de todos modos no vive aquí, vive en el drive.
    x = lp(x, 3400.0, 2)
    return x


def kick(N):
    """Bombo: pitch drop de 55→42 Hz y click corto."""
    t = np.arange(N) / SR
    f = 42 + 120 * np.exp(-t / 0.022)
    x = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t / 0.16)
    click = (np.random.default_rng(3).standard_normal(N) * np.exp(-t/0.004) * 0.18)
    return x + hp(click, 1800.0, 2)


def pluck(f0, N, seed=1):
    """Acorde corto y brillante, el que hace el contratiempo."""
    t = np.arange(N) / SR
    rng = np.random.default_rng(seed)
    x = np.zeros(N)
    for k, amp in ((1, 1.0), (2, 0.42), (3, 0.22), (4, 0.10)):
        det = 1 + rng.uniform(-0.0025, 0.0025)
        x += amp * np.sin(2*np.pi*f0*k*det*t + rng.uniform(0, 6.28))
    x *= env(N, int(0.003*SR), int(0.16*SR), 0, int(0.10*SR), 0.25)
    return lp(x, 7000.0, 2) * 0.5


def lead(f0, N, seed=2):
    """La melodía: sinte cálido, sin filo."""
    t = np.arange(N) / SR
    rng = np.random.default_rng(seed)
    x = np.zeros(N)
    for det in (-0.004, 0.0, 0.004):
        ph = rng.uniform(0, 6.28)
        x += np.sin(2*np.pi*f0*(1+det)*t + ph)
        x += 0.30 * np.sin(2*np.pi*f0*2*(1+det)*t + ph)
    x /= 3.4
    x *= env(N, int(0.02*SR), int(0.10*SR), 0, int(0.16*SR), 0.72)
    return lp(x, 6200.0, 2)


def hats(N, beat_s, seed=5):
    """Hi-hats en corcheas, con el swing suave del género."""
    rng = np.random.default_rng(seed)
    out = np.zeros(N)
    paso = int(beat_s * SR / 2)
    for i in range(0, N - paso, paso):
        off = int(paso * 0.06) if (i // paso) % 2 else 0     # swing leve
        L = int(0.05 * SR)
        if i + off + L >= N:
            break
        t = np.arange(L) / SR
        h = rng.standard_normal(L) * np.exp(-t / 0.012)
        out[i+off:i+off+L] += hp(h, 7000.0, 2) * (0.5 if (i//paso) % 2 else 0.32)
    return out


def sidechain(N, beat_s, prof=0.62):
    """La bomba contra el bombo — el vaivén del género."""
    e = np.ones(N)
    p = int(beat_s * SR)
    forma = 1 - prof * np.exp(-np.arange(p) / (p * 0.16))
    for i in range(0, N - p, p):
        e[i:i+p] = forma
    return e


def construir():
    total_bars = sum(b for _, b in ESTRUCTURA)
    N = int(total_bars * BAR * SR) + SR
    K = np.zeros(N); B = np.zeros(N); P = np.zeros(N)
    L = np.zeros(N); H = np.zeros(N); S = np.zeros(N)

    bar = 0
    for nombre, nbars in ESTRUCTURA:
        for c in range(nbars):
            b0 = int((bar + c) * BAR * SR)
            acorde = PROG[(bar + c) % 4]
            f_raiz = RAIZ[acorde]
            fuerte = nombre in ('drop', 'drop2')
            medio = nombre in ('build', 'puente')

            # ── KICK: 4/4 en los drops y el build
            if fuerte or medio:
                for k in range(4):
                    a = b0 + n(k)
                    L_ = int(0.42 * SR)
                    if a + L_ < N:
                        K[a:a+L_] += kick(L_) * (1.0 if fuerte else 0.72)

            # ── BAJO: cae ENTRE los kicks (el contratiempo del género)
            if fuerte:
                for k in range(4):
                    a = b0 + n(k + 0.5)
                    L_ = int(0.30 * SR)
                    if a + L_ < N:
                        B[a:a+L_] += bajo_slap(f_raiz, L_)
                    # la nota extra que le da el vaivén
                    a2 = b0 + n(k + 0.75)
                    L2 = int(0.16 * SR)
                    if a2 + L2 < N and k % 2 == 1:
                        B[a2:a2+L2] += bajo_slap(f_raiz * 2, L2) * 0.55
            elif medio:
                for k in (0.5, 2.5):
                    a = b0 + n(k)
                    L_ = int(0.34 * SR)
                    if a + L_ < N:
                        B[a:a+L_] += bajo_slap(f_raiz, L_) * 0.7

            # ── PLUCK: acorde en contratiempo, siempre presente salvo la intro
            if nombre != 'intro':
                for k in (0.5, 1.5, 2.5, 3.5):
                    a = b0 + n(k)
                    L_ = int(0.28 * SR)
                    if a + L_ < N:
                        for mult in (2.0, 2.5, 3.0):        # tríada
                            P[a:a+L_] += pluck(f_raiz * mult, L_, seed=int(k*7)) * 0.36

            # ── MELODÍA: en los drops y el puente
            if fuerte or nombre == 'puente':
                for (bt, semi, dur) in GANCHO:
                    a = b0 + n(bt)
                    L_ = int(dur * BEAT * SR * 0.92)
                    if a + L_ < N:
                        f = 220.0 * 2 ** (semi / 12.0)
                        L[a:a+L_] += lead(f, L_) * (0.34 if fuerte else 0.22)

            # ── HATS
            if nombre != 'intro':
                seg = int(BAR * SR)
                if b0 + seg < N:
                    H[b0:b0+seg] += hats(seg, BEAT) * (0.85 if fuerte else 0.55)

            # ── PAD de fondo, siempre
            seg = int(BAR * SR)
            if b0 + seg < N:
                t = np.arange(seg) / SR
                pad = np.zeros(seg)
                for mult in (1.0, 1.5, 2.0):
                    pad += np.sin(2*np.pi*f_raiz*mult*t) / 3
                S[b0:b0+seg] += lp(pad, 900.0, 2) * 0.10
        bar += nbars

    # ── mezcla ────────────────────────────────────────────────────────────
    sc = sidechain(N, BEAT, prof=0.62)
    B *= sc                      # el bajo respira con el bombo
    P *= (0.35 + 0.65 * sc)
    S *= (0.45 + 0.55 * sc)

    mono = (0.92*K + 0.80*B + 0.68*P + 0.50*L + 0.52*H + 0.42*S)

    # OJO: widen() y stereo_verb() reciben MONO y devuelven el par estéreo.
    # El reverb se hace ANTES de ensanchar, y sólo sobre la parte media/alta:
    # meterle cola al grave es lo que embarra un mix de este género.
    mono = mono.astype(np.float32)
    cola = hp(mono, 320.0, 2)                       # nada de reverb en el grave
    rev = stereo_verb(cola, decay_s=1.1, mix=0.10, tone=5000.0, seed=4)
    rev_m = 0.5 * (rev[0] + rev[1])
    mono = mono + 0.22 * (rev_m - cola)             # sólo la cola, no la señal

    LR = widen(mono, amount=0.42, lo=260.0, hi=11000.0, seed=11)
    LR = sub_mono(LR, fc=120.0)          # el grave al centro, 1er orden
    return LR


if __name__ == '__main__':
    os.makedirs(TMP, exist_ok=True)
    LR = construir()
    LR = LR / (np.abs(LR).max() + 1e-9) * 0.89
    crudo = os.path.join(TMP, 'resaca-crudo.wav')
    wav_write(crudo, LR)
    dur = LR.shape[1] / SR
    print(f'crudo: {int(dur//60)}:{dur%60:04.1f}  ·  {BPM:.0f} BPM  ·  La menor')

    # El target se MIDE. A -13.0 el crest de 1 s quedaba en 8.1 (mínimo 8.5).
    # Se masteriza a varios niveles leyendo el crest de cada uno y se toma el
    # más fuerte que aún pasa: un master más caliente no se oye más fuerte
    # (Spotify normaliza a -14), sólo llega con menos dinámica.
    setm = os.path.join(TMP, 'resaca.wav')
    from dream_core import ffdecode
    mejor = None
    for tgt in (-13.0, -13.5, -14.0, -14.5):
        cand = os.path.join(TMP, f'res-{abs(tgt):.1f}.wav')
        master_file(crudo, cand, target_i=tgt, ceiling_db=-2.0)
        y = ffdecode(cand)
        m = y.mean(axis=0) if y.ndim > 1 else y
        ns = len(m) // SR
        s = m[:ns*SR].reshape(ns, SR)
        cr = float(np.median(20*np.log10(
            (np.abs(s).max(axis=1)+1e-12) / (np.sqrt((s**2).mean(axis=1))+1e-12))))
        I, _, tp = ffmeter(cand)
        print(f'  target {tgt:+.1f} → {I:.1f} LUFS · TP {tp:+.1f} · crest 1s {cr:.1f}')
        if cr >= 8.8 and (mejor is None or tgt > mejor[0]):
            mejor = (tgt, cr, cand)
        else:
            os.remove(cand)
    if mejor is None:
        raise SystemExit('ningún target pasa el crest — revisar la mezcla')
    print(f'→ elegido {mejor[0]:+.1f} LUFS (crest {mejor[1]:.1f})')
    os.replace(mejor[2], setm)

    m4a = os.path.join(HERE, 'audio', 'amr-resaca.m4a')
    trim = 0.0
    for _ in range(5):                    # el AAC sobrepasa: se mide, no se calcula
        subprocess.run([FF, '-y', '-v', 'error', '-i', setm, '-af',
                        f'volume={trim:.2f}dB,'
                        'aformat=sample_fmts=fltp:sample_rates=44100',
                        '-c:a', 'aac_at', '-b:a', '192k', '-movflags', '+faststart',
                        m4a], check=True, capture_output=True)
        I, lra, tp = ffmeter(m4a)
        print(f'  trim {trim:+.2f} dB → {I:.1f} LUFS · TP {tp:+.2f}')
        if tp <= -1.2:
            break
        trim += (-1.5 - tp)
    print(f'M4A {os.path.getsize(m4a)//1024} KB · {m4a}')
