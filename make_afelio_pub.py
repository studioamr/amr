#!/usr/bin/env python3
"""Publica AFELIO: m4a + afelio.js. Es un SINGLE — una pieza, sin cortes."""
import os, json, subprocess
import numpy as np, imageio_ffmpeg
from dream_core import ffmeter
from make_afelio import SECTIONS, SPB, BPM

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'masters', 'amr-afelio.wav')

def enc(src, dst):
    subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-c:a', 'aac_at', '-b:a', '256k',
                    '-movflags', '+faststart', dst], check=True)

def peaks(path, W=720):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', '4410',
                          '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.abs(np.frombuffer(raw, dtype='<f4')); seg = len(x) // W
    pk = x[:seg * W].reshape(W, seg).max(axis=1)
    return (pk / (pk.max() or 1)).round(3).tolist()

if __name__ == '__main__':
    m4a = os.path.join(HERE, 'audio', 'amr-afelio.m4a')
    enc(SRC, m4a)
    I, lra, tp = ffmeter(m4a)
    print(f'AFELIO m4a: {os.path.getsize(m4a)//1048576} MB · {I} LUFS · LRA {lra} · TP {tp}', flush=True)

    # marcas de sección (para que el reproductor pueda mostrar dónde va la rola)
    offsets, acc = [], 0.0
    for s in SECTIONS:
        offsets.append(round(acc, 1)); acc += s['bars'] * SPB / 44100.0
    meta = dict(id='amr-afelio', title='AFELIO', kicker='THE SINGLE · AFTERLIFE SCI-FI',
                tracks=1, dur=round(acc, 1),
                titles=[s['name'] for s in SECTIONS], offsets=offsets,
                file='audio/amr-afelio.m4a', art='art/afelio.svg', edition=12,
                peaks=peaks(m4a), bpm=int(BPM), key='G MIN')
    with open(os.path.join(HERE, 'afelio.js'), 'w') as f:
        f.write('window.AMR_AFELIO=' + json.dumps(meta) + ';')
    print(f'afelio.js escrito · {meta["dur"]}s · {meta["bpm"]} BPM · {meta["key"]}', flush=True)
