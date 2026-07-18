#!/usr/bin/env python3
"""Remaster profesional del catálogo con ffmpeg (streaming, aguanta sets de 90min).
Cadena: highpass 28 · EQ por track (baja lo áspero / calienta) · ancho estéreo
sutil · loudnorm true-peak (ARREGLA EL CLIPEO + loudness consistente) · encode
aac_at. Fuente = master WAV limpio si existe, si no el m4a."""
import os, subprocess, sys
import imageio_ffmpeg
from dream_core import ffmeter, ffdecode, width_corr, spectrum_pct

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))

# label, src (relativo), out m4a, air_db(agudos>8.5k), warm_db(graves 250), width(extrastereo m), target LUFS
TRACKS = [
 ('MONUMENTS', 'audio/amr-monuments-side.m4a', 'audio/amr-monuments-side.m4a', -2.0,  1.0, 1.6, -8.5),
 ('SESIÓN 001','audio/amr-set-the-set.m4a',    'audio/amr-set-the-set.m4a',    -1.0,  0.0, 1.5, -8.5),
 ('DELIRIO',   'audio/amr-tulum.m4a',           'audio/amr-tulum.m4a',          -3.5,  2.0, 1.6, -8.5),
 ('GUERRERO',  'audio/amr-guerrero.m4a',        'audio/amr-guerrero.m4a',        0.5,  0.5, 1.9, -8.5),
 ('JACARANDA', 'masters/amr-jacaranda.wav',     'audio/amr-jacaranda.m4a',      -1.0,  0.5, 1.6, -8.5),
 ('PLAYA',     'masters/amr-playa.wav',         'audio/amr-playa.m4a',          -2.5,  1.5, 1.6, -8.5),
 ('ORÁCULO',   'masters/amr-oraculo.wav',       'audio/amr-oraculo.m4a',         1.5, -1.0, 1.9, -9.0),
 ('FIEBRE',    'masters/amr-fiebre.wav',        'audio/amr-fiebre.m4a',          0.0,  0.5, 1.7, -8.5),
 ('IMÁN',      'masters/amr-iman.wav',          'audio/amr-iman.m4a',            0.0,  0.0, 1.7, -8.5),
 ('FICCIÓN',   'masters/amr-ficcion.wav',       'audio/amr-ficcion.m4a',         1.0,  0.0, 1.7, -8.5),
]

def chain(air, warm, width, tgt):
    f = ['highpass=f=28']
    if abs(air) >= 0.1:  f.append(f'treble=g={air}:f=8500')
    if abs(warm) >= 0.1: f.append(f'bass=g={warm}:f=250')
    if width > 1.01:     f.append(f'extrastereo=m={width}')
    # loudnorm lineal (no comprime) con true-peak → arregla clipeo + loudness parejo
    f.append(f'loudnorm=I={tgt}:TP=-1.5:LRA=11:linear=true')
    # limitador de seguridad (post-encode headroom)
    f.append('alimiter=level_in=1:level_out=0.94:limit=0.94:attack=4:release=60')
    # loudnorm resamplea a 192k → forzar formato que aac_at acepta
    f.append('aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo')
    return ','.join(f)

def remaster(label, src, out, air, warm, width, tgt):
    s = os.path.join(HERE, src); o = os.path.join(HERE, out)
    tmp = o + '.rm.m4a'
    subprocess.run([FF, '-y', '-v', 'error', '-i', s, '-af', chain(air, warm, width, tgt),
                    '-c:a', 'aac_at', '-b:a', '256k', '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, o)
    return o

def w90(path):
    """ancho medido en un fragmento de 90s (rápido; no carga el track entero)."""
    import numpy as np
    raw = subprocess.run([FF, '-v', 'error', '-ss', '30', '-t', '90', '-i', path,
                          '-ac', '2', '-ar', '44100', '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4')
    n = len(x)//2; L, R = x[:n*2].reshape(-1,2).T.astype(np.float64)
    m=(L+R)/2; s=(L-R)/2
    return round(float((s**2).mean()/((m**2).mean()+1e-12)), 3)

if __name__ == '__main__':
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for label, src, out, air, warm, width, tgt in TRACKS:
        if only and only.upper() not in label.upper(): continue
        op = os.path.join(HERE, out)
        I0, l0, t0 = ffmeter(op)                              # ffmeter hace streaming (rápido)
        print(f'{label:11s} ANTES  {str(I0):>6s} LUFS · TP {str(t0):>5s} · LRA {str(l0):>4s} · width {w90(op)}', flush=True)
        o = remaster(label, src, out, air, warm, width, tgt)
        I1, l1, t1 = ffmeter(o)
        print(f'{label:11s} DESPUÉS {str(I1):>5s} LUFS · TP {str(t1):>5s} · LRA {str(l1):>4s} · width {w90(o)} · {os.path.getsize(o)//1048576}MB', flush=True)
