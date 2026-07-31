#!/usr/bin/env python3
"""Aplica la REPISA elegida por el barrido y deja el WAV para que lo juzgue juez.py.

OJO con la métrica: mi centroide (barre_repisa_purpurina.py) y el de juez.py NO
dan el mismo número — el mío mide la mediana de ventanas de 2048, el del juez usa
su propio método. Por eso el barrido sólo sirve para ORDENAR las opciones, y quien
decide si pasa o no es juez.py sobre el archivo ya corregido. Nunca al revés.
"""
import os, subprocess
import numpy as np
from dream_core import FF, SR, ffmeter

RAW = '_purpurina/_raw'
OUT = '_purpurina/_fix'

# del barrido: la corrección más suave que cruzaba el umbral con margen
REPISA = {
    'Keys_Left_on_the_Table.mp3': (2000.0, 6.5),
}


def fir_from_gain(gain, n):
    f = np.fft.rfftfreq(n, 1.0 / SR)
    h = np.fft.irfft(gain(f), n)
    return np.roll(h, n // 2) * np.hanning(n)


def repisa(x, f0, db):
    g = 10.0 ** (db / 20.0)
    def gain(f):
        r = np.maximum(f, 1e-6) / f0
        return 1.0 + (g - 1.0) * (r ** 2 / (1.0 + r ** 2))
    h = fir_from_gain(gain, 2049)
    return np.stack([np.convolve(x[0], h, mode='same'),
                     np.convolve(x[1], h, mode='same')])


def decode_st(path):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '2', '-ar',
                          str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4').astype(np.float64)
    return x.reshape(-1, 2).T


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for fn, (f0, db) in REPISA.items():
        x = decode_st(os.path.join(RAW, fn))
        y = repisa(x, f0, db)
        # La repisa SUBE nivel. Normalizar el pico de muestra a 0.98 NO basta:
        # el true peak (picos inter-muestra) quedó en -0.1 dBTP y el juez pide
        # <= -1.0. Así que el nivel se decide MIDIENDO el true peak real en un
        # lazo, igual que se hizo con el m4a de ECO.
        y /= max(np.abs(y).max(), 1e-9)       # arranca en pico 1.0
        dst = os.path.join(OUT, fn.replace('.mp3', '.wav'))
        for _ in range(6):
            inter = y.T.astype('<f4').tobytes()
            subprocess.run([FF, '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR),
                            '-ac', '2', '-i', '-', dst], input=inter, check=True)
            _, _, tp = ffmeter(dst)
            print(f'  pico {np.abs(y).max():.3f} → TP {tp:+.2f} dBTP')
            if tp <= -1.2:
                break
            y *= 10 ** ((-1.4 - tp) / 20.0)
        print(f'{fn}  →  {dst}   (repisa f0={f0:.0f} Hz {db:+.1f} dB)')
