#!/usr/bin/env python3
"""¿CONFETI está apagada, o sólo se desviste al final como se le pidió?

El juez midió 983 Hz de centroide y reprobó. Pero el prompt pedía explícitamente
que el último tercio se quedara sin bombo, con puro pad y arpegio — y eso baja el
centroide promedio POR DISEÑO, no por defecto de mezcla.

Este script parte la rola en tramos y mide cada uno. Si el cuerpo está bien y sólo
la cola arrastra el promedio, la rola sirve y el problema es el umbral aplicado a
una rola completa. Si TODA está apagada, entonces sí está mal y se descarta.
"""
import subprocess
import numpy as np
from dream_core import FF, SR

SRC = '_purpurina/_raw/Lights_at_Five_AM.mp3'
REF = '_purpurina/_raw/Velvet_Salon_Hour.mp3'      # la que sí aprobó, para comparar
TRAMOS = 8


def decode(path):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar',
                          str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype='<f4').astype(np.float64)


def centroide(x):
    w = 2048
    n = len(x) // w
    if n < 2:
        return float('nan')
    seg = x[:n * w].reshape(n, w) * np.hanning(w)
    sp = np.abs(np.fft.rfft(seg, axis=1))
    f = np.fft.rfftfreq(w, 1.0 / SR)
    return float(np.median((sp * f).sum(axis=1) / (sp.sum(axis=1) + 1e-12)))


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


for nombre, path in (('CONFETI (reprobada)', SRC), ('SALON  (aprobada)', REF)):
    x = decode(path)
    n = len(x) // TRAMOS
    print(f'\n{nombre}   total {len(x)/SR/60:.0f}:{len(x)/SR%60:04.1f}')
    print('  tramo    seg       centroide    nivel')
    for i in range(TRAMOS):
        seg = x[i*n:(i+1)*n]
        t0 = i * n / SR
        print(f'   {i+1}/{TRAMOS}   {t0:5.0f}s      {centroide(seg):6.0f} Hz   '
              f'{rms_db(seg):6.1f} dB')
    # el promedio sin la última cuarta parte: ¿el cuerpo sí sirve?
    cuerpo = x[:int(len(x) * 0.66)]
    print(f'  → rola completa   {centroide(x):.0f} Hz')
    print(f'  → primeros 2/3    {centroide(cuerpo):.0f} Hz  '
          f'(sin la parte que se desviste)')
