#!/usr/bin/env python3
"""ECO — single de dub-electrónica. Masteriza y publica.

Ya pasó el juez sin corrección (crest 9.1/12.9, centroide 2103, inclinación -4.9,
side/mid 0.033) así que aquí no hay REPISA: sólo se lleva a un LUFS de catálogo.

El target se ELIGE midiendo, no adivinando: se prueban varios y se queda el que
conserva mejor el crest, porque la gracia de esta rola es el aire entre los ecos
— si la aplasto a -8 como una de tech house, se le va justo lo que la hace dub.
"""
import os, subprocess
import numpy as np
from dream_core import FF, SR, ffmeter, master_file

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '_eco', '_raw', 'ECO.mp3')
TMP = os.path.join(HERE, '_eco', '_tmp')
OUT_M4A = os.path.join(HERE, 'audio', 'amr-eco.m4a')

BPM = 120.010
TONO = 'A MIN'


def decode_wav(src, dst):
    subprocess.run([FF, '-v', 'error', '-y', '-i', src, '-ac', '2', '-ar', str(SR),
                    dst], check=True)


def crest_db(path):
    cmd = [FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    x = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, dtype='<f4')
    w = SR // 10                                   # ventanas de 100 ms
    n = len(x) // w
    seg = x[:n * w].reshape(n, w)
    rms = np.sqrt((seg ** 2).mean(axis=1) + 1e-12)
    pk = np.abs(seg).max(axis=1) + 1e-12
    return float(np.median(20 * np.log10(pk / rms)))


if __name__ == '__main__':
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)

    src = os.path.join(TMP, 'eco_src.wav')
    decode_wav(RAW, src)
    I0, _, _ = ffmeter(src)
    print(f'fuente · LUFS {I0:.1f} · crest {crest_db(src):.1f} dB')

    # se prueban targets y se mide qué le hace cada uno al crest
    mejor = None
    for tgt in (-12.0, -11.0, -10.0, -9.0):
        cand = os.path.join(TMP, f'eco_{abs(tgt):.0f}.wav')
        master_file(src, cand, target_i=tgt, ceiling_db=-1.0)
        I, _, tp = ffmeter(cand)
        c = crest_db(cand)
        print(f'  target {tgt:+.0f} → LUFS {I:.1f} · TP {tp:.1f} · crest {c:.1f} dB')
        if mejor is None or c > mejor[1]:
            mejor = (tgt, c, cand)

    tgt, c, best = mejor
    print(f'→ elegido {tgt:+.0f} LUFS (crest {c:.1f} dB, el que más aire conserva)')

    # el AAC genera picos inter-muestra por encima del WAV (aquí midió +3 dB),
    # así que el trim se decide midiendo el m4a YA CODIFICADO, no el wav
    trim = 0.0
    for _ in range(6):
        subprocess.run([FF, '-v', 'error', '-y', '-i', best, '-af', f'volume={trim}dB',
                        '-c:a', 'aac', '-b:a', '192k', OUT_M4A], check=True)
        _, _, tp = ffmeter(OUT_M4A)
        print(f'  trim {trim:+.1f} dB → TP {tp:+.1f} dBTP')
        if tp <= -1.0:
            break
        trim -= (tp + 1.4)
    # no hay ffprobe en esta máquina — la duración se cuenta decodificando
    raw = subprocess.run([FF, '-v', 'error', '-i', OUT_M4A, '-ac', '1', '-ar',
                          str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    dur = len(raw) / 4 / SR
    # OJO: los minutos van con int(), no con :.0f — :.0f REDONDEA (168 s salía
    # como "3:48" en vez de 2:48) y eso ya me hizo reportar mal una duración
    print(f'{OUT_M4A} · {int(dur//60)}:{dur%60:02.0f} · {os.path.getsize(OUT_M4A)//1024} KB')

    with open(os.path.join(HERE, 'eco.js'), 'w') as f:
        f.write('window.AMR_ECO=' + repr({
            'id': 'amr-eco', 'title': 'ECO', 'kicker': 'SINGLE · DUB',
            'dur': round(dur), 'file': 'audio/amr-eco.m4a', 'art': 'art/eco.svg',
            'edition': 1, 'bpm': round(BPM), 'key': TONO,
        }).replace("'", '"') + ';')
    print('eco.js escrito')
