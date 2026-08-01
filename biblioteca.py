#!/usr/bin/env python3
"""LA BIBLIOTECA ANALIZADA — el paso 0 del método profesional.

Ningún DJ cura un set de oído sobre una carpeta suelta: primero analiza toda la
biblioteca y le pone a cada pieza su BPM, su tono en notación Camelot y su
energía. Después cura sobre esa tabla. Esto hace eso con el catálogo de AMR.

QUÉ MIDE Y POR QUÉ
  · BPM         — rejilla.py (fino). Define qué se puede pegar con qué.
  · TONO        — analiza.py (Krumhansl-Schmuckler) → se traduce a CAMELOT, que
                  es la notación que usan los DJs: mismo número = compatible,
                  ±1 número = compatible, misma letra = mismo modo.
  · ENERGÍA 1-10— no existe un "medidor de energía" objetivo, así que se compone
                  de tres cosas medibles y se dice de qué está hecho:
                    densidad de graves (¿hay bombo empujando?)
                    centroide (¿brilla arriba?)
                    crest bajo = más comprimido = se siente más fuerte
                  Es una heurística declarada, no un número mágico.

El resultado se guarda en biblioteca.json para curar encima sin re-analizar.
"""
import os, re, json, subprocess
import numpy as np
from dream_core import FF, SR
from rejilla import rejilla

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, 'audio')

# tono → Camelot. La rueda: 12 posiciones, A = menor, B = mayor.
CAMELOT = {
    'A MIN': '8A',  'A# MIN': '3A', 'B MIN': '10A', 'C MIN': '5A',
    'C# MIN': '12A','D MIN': '7A',  'D# MIN': '2A', 'E MIN': '9A',
    'F MIN': '4A',  'F# MIN': '11A','G MIN': '6A',  'G# MIN': '1A',
    'A MAJ': '11B', 'A# MAJ': '6B', 'B MAJ': '1B',  'C MAJ': '8B',
    'C# MAJ': '3B', 'D MAJ': '10B', 'D# MAJ': '5B', 'E MAJ': '12B',
    'F MAJ': '7B',  'F# MAJ': '2B', 'G MAJ': '9B',  'G# MAJ': '4B',
}
ALIAS = {'Bb': 'A#', 'Eb': 'D#', 'Ab': 'G#', 'Db': 'C#', 'Gb': 'F#'}


def dur(path):
    r = subprocess.run([FF, '-i', path], capture_output=True, text=True).stderr
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', r)
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3)) if m else 0.0


def decode(path, sr=44100):
    """OJO CON EL SAMPLE RATE. Esto decodificaba a 22050, lo que por Nyquist
    corta TODO arriba de 11 kHz — y el centroide salía sistemáticamente más
    bajo que el de juez.py, que decodifica a 44100 y ve el espectro completo.
    Esa es la razón real de que mis barridos de repisa dieran cifras que no
    cuadraban con el veredicto del juez. El juez manda; esta función ahora mide
    en la misma banda que él."""
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar',
                          str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype='<f4').astype(np.float64), sr


def rasgos(path):
    """Las tres medidas de las que se compone la energía."""
    x, sr = decode(path)
    if len(x) < sr:
        return None
    w = 2048
    n = len(x) // w
    seg = x[:n*w].reshape(n, w) * np.hanning(w)
    sp = np.abs(np.fft.rfft(seg, axis=1))
    f = np.fft.rfftfreq(w, 1.0/sr)

    # densidad de graves: proporción de energía bajo 200 Hz
    lo = sp[:, f < 200].sum()
    tot = sp.sum() + 1e-12
    graves = float(lo / tot)

    # CENTROIDE — método idéntico al de juez.py: se ACUMULAN los espectros y se
    # saca UN solo centroide del promedio. Antes se sacaba la mediana de los
    # centroides por ventana, que da un número distinto y más bajo; con eso la
    # biblioteca decía que los cortes de TULUM eran normales cuando en realidad
    # miden ~6700 Hz. El juez es la autoridad, así que se mide como él.
    W = 1 << 11
    acc = np.zeros(W//2 + 1)
    nn = 0
    for i in range(0, len(x) - W, W*4):
        acc += np.abs(np.fft.rfft(x[i:i+W] * np.hanning(W)))
        nn += 1
    fr = np.fft.rfftfreq(W, 1.0/sr)
    cen = float((acc*fr).sum() / (acc.sum() + 1e-12)) if nn else 0.0

    # crest de 1 s: cuánto respira. Menos crest = más apretado = más "fuerte".
    ws = sr
    ns = len(x) // ws
    s = x[:ns*ws].reshape(ns, ws)
    crest = float(np.median(20*np.log10(
        (np.abs(s).max(axis=1)+1e-12) / (np.sqrt((s**2).mean(axis=1))+1e-12))))
    return graves, cen, crest


def energia(graves, cen, crest, bpm):
    """Heurística DECLARADA, no un número mágico. Cada término dice qué aporta."""
    e = 0.0
    e += np.clip((graves - 0.10) / 0.22, 0, 1) * 3.4     # ¿empuja el bombo?
    e += np.clip((cen - 900) / 1400.0, 0, 1) * 2.2       # ¿brilla arriba?
    e += np.clip((11.5 - crest) / 4.0, 0, 1) * 2.2       # ¿va apretado?
    e += np.clip((bpm - 112) / 20.0, 0, 1) * 2.2         # ¿va rápido?
    return float(np.clip(e, 1, 10))


if __name__ == '__main__':
    # los tonos que ya se midieron y quedaron escritos en los .js de cada disco
    tonos = {}
    for js in os.listdir(HERE):
        if not js.endswith('.js') or js in ('waveforms.js',):
            continue
        t = open(os.path.join(HERE, js)).read()
        m = re.search(r'"file":\s*"([^"]+)"', t)
        k = re.search(r'"key":\s*"([^"]+)"', t)
        if m and k:
            tonos[os.path.basename(m.group(1))] = k.group(1)

    filas = []
    for f in sorted(os.listdir(AUDIO)):
        if not f.endswith('.m4a'):
            continue
        p = os.path.join(AUDIO, f)
        d = dur(p)
        try:
            bpm, _, _ = rejilla(p)
        except Exception:
            bpm = 0.0
        r = rasgos(p)
        if r is None:
            continue
        graves, cen, crest = r
        e = energia(graves, cen, crest, bpm)
        tono = tonos.get(f, '')
        for a, b in ALIAS.items():
            tono = tono.replace(a, b)
        cam = CAMELOT.get(tono.upper().strip(), '')
        filas.append(dict(file=f, dur=round(d, 1), bpm=round(bpm, 2), key=tono,
                          camelot=cam, energia=round(e, 1),
                          graves=round(graves, 3), centroide=round(cen),
                          crest=round(crest, 1), corte=('cut' in f)))
        print(f'  {f:40s} {int(d//60):3d}:{int(d%60):02d} {bpm:7.2f} '
              f'{tono:7s} {cam:4s} E{e:4.1f}', flush=True)

    with open(os.path.join(HERE, 'biblioteca.json'), 'w') as fh:
        json.dump(filas, fh, indent=1, ensure_ascii=False)
    print(f'\nbiblioteca.json · {len(filas)} piezas · '
          f'{sum(x["dur"] for x in filas)/3600:.1f} h en total')
