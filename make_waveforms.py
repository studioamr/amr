#!/usr/bin/env python3
"""Analiza el audio REAL de cada disco y hornea una onda rekordbox de 3 bandas
(bajos/medios/agudos) por columna → waveforms.js (window.AMR_WF).
STFT por ventana: energía en <200 Hz (azul), 200-2000 (naranja), >2000 (blanco).
Cada banda queda como bytes 0-255 en base64 (compacto). 1400 columnas por track."""
import os, base64, subprocess
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SR = 22050          # suficiente para separar hasta ~8-10k; ligero en memoria
COLS = 3000         # columnas de forma de onda por disco (detalle para el zoom)

DISCS = [
    'audio/amr-monuments-side.m4a',
    'audio/amr-set-the-set.m4a',
    'audio/amr-tulum.m4a',
    'audio/amr-guerrero.m4a',
    'audio/amr-jacaranda.m4a',
    'audio/amr-colibri.m4a',
    'audio/amr-fiebre.m4a',
    'audio/amr-playa.m4a',
    'audio/amr-iman.m4a',
]

def decode_mono(path):
    cmd = [FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, dtype='<f4')

def bands(path):
    x = decode_mono(path)
    n = len(x)
    hop = n / COLS
    win = int(hop)                      # ventanas contiguas ~ del tamaño del hop
    if win < 256: win = 256
    hann = np.hanning(win).astype(np.float32)
    freqs = np.fft.rfftfreq(win, 1.0 / SR)
    mlo = freqs < 200.0
    mmi = (freqs >= 200.0) & (freqs < 2000.0)
    mhi = freqs >= 2000.0
    lo = np.zeros(COLS, np.float32); mi = np.zeros(COLS, np.float32); hi = np.zeros(COLS, np.float32)
    for i in range(COLS):
        a = int(i * hop)
        seg = x[a:a + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        sp = np.abs(np.fft.rfft(seg * hann))
        p = sp * sp
        lo[i] = np.sqrt(p[mlo].sum())
        mi[i] = np.sqrt(p[mmi].sum())
        hi[i] = np.sqrt(p[mhi].sum())
    # normaliza las 3 con un factor común (percentil 98 de la envolvente total)
    # → conserva el balance entre bandas y deja ver la dinámica del track
    tot = lo + mi + hi
    ref = np.percentile(tot, 98.0)
    if ref <= 1e-9: ref = tot.max() + 1e-9
    k = 1.0 / ref
    # curva suave tipo pantalla (un poco de gamma para que respire)
    def q(b):
        v = np.clip(b * k, 0, 1.0)
        v = v ** 0.72
        return np.clip(v * 255.0, 0, 255).astype(np.uint8)
    return q(lo), q(mi), q(hi)

def b64(u8): return base64.b64encode(u8.tobytes()).decode('ascii')

out = {}
for rel in DISCS:
    p = os.path.join(HERE, rel)
    if not os.path.exists(p):
        print('  falta', rel); continue
    lo, mi, hi = bands(p)
    out[rel] = {'lo': b64(lo), 'mi': b64(mi), 'hi': b64(hi)}
    print(f'  {rel:32s} lo~{lo.mean():.0f} mi~{mi.mean():.0f} hi~{hi.mean():.0f}')

import json
js = 'window.AMR_WF=' + json.dumps(out, separators=(',', ':')) + ';'
with open(os.path.join(HERE, 'waveforms.js'), 'w') as f:
    f.write(js)
print('waveforms.js', round(len(js) / 1024, 1), 'KB ·', len(out), 'discos ·', COLS, 'columnas')
