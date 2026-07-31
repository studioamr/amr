#!/usr/bin/env python3
"""Barrido de REPISA para las dos rolas de PURPURINA que reprobó el juez.

Before_the_Light_Returns (centroide 1345 Hz) y Keys_Left_on_the_Table (1387 Hz)
quedaron abajo del mínimo de 1443 Hz: les faltan agudos. En vez de elegir la
corrección "de oído", se barren f0 y dB, se mide el centroide resultante de cada
combinación, y se queda la MÁS SUAVE que cruza el umbral con margen — subir de
más las volvería brillantes y rompería la unidad del disco por el otro lado.
"""
import os, subprocess
import numpy as np
from dream_core import FF, SR

RAW = '_purpurina/_raw'
OBJETIVO = 1443.0      # mínimo del juez (ISMIR 2014)
MARGEN = 120.0         # se busca cruzarlo con holgura, no rasparlo

FALLAN = ['Lights_at_Five_AM.mp3']


def fir_from_gain(gain, n):
    f = np.fft.rfftfreq(n, 1.0 / SR)
    h = np.fft.irfft(gain(f), n)
    h = np.roll(h, n // 2) * np.hanning(n)
    return h


def repisa(x, f0, db):
    """Repisa suave de primer orden: plana abajo, +db arriba de f0."""
    g = 10.0 ** (db / 20.0)
    def gain(f):
        r = np.maximum(f, 1e-6) / f0
        return 1.0 + (g - 1.0) * (r ** 2 / (1.0 + r ** 2))
    h = fir_from_gain(gain, 2049)
    return np.convolve(x, h, mode='same')


def centroide(x):
    """Mismo cálculo que juez.py: centroide espectral promedio por ventana."""
    w = 2048
    n = len(x) // w
    seg = x[:n * w].reshape(n, w) * np.hanning(w)
    sp = np.abs(np.fft.rfft(seg, axis=1))
    f = np.fft.rfftfreq(w, 1.0 / SR)
    num = (sp * f).sum(axis=1)
    den = sp.sum(axis=1) + 1e-12
    return float(np.median(num / den))


def decode(path):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar',
                          str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype='<f4').astype(np.float64)


if __name__ == '__main__':
    for fn in FALLAN:
        x = decode(os.path.join(RAW, fn))
        base = centroide(x)
        print(f'\n{fn}  ·  centroide actual {base:.0f} Hz  (falta '
              f'{OBJETIVO - base:+.0f} para el mínimo)')
        elegido = None
        for f0 in (2000.0, 2500.0, 3000.0, 3500.0):
            fila = []
            for db in (1.5, 2.5, 3.5, 4.5, 5.5, 6.5):
                c = centroide(repisa(x, f0, db))
                fila.append(f'{db:+.1f}dB→{c:.0f}')
                if c >= OBJETIVO + MARGEN and elegido is None:
                    elegido = (f0, db, c)
            print(f'  f0={f0:6.0f} Hz   ' + '  '.join(fila))
        if elegido:
            print(f'  → ELEGIDO f0={elegido[0]:.0f} Hz  {elegido[1]:+.1f} dB  '
                  f'→ centroide {elegido[2]:.0f} Hz (la corrección más suave '
                  f'que cruza {OBJETIVO:.0f}+{MARGEN:.0f})')
        else:
            print('  → ninguna combinación del barrido alcanza el objetivo')
