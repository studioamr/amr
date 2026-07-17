#!/usr/bin/env python3
"""Publica HECHIZO: m4a del set (ya masterizado, sin loudnorm), cantera.js, cortes standalone."""
import os, json, subprocess
import numpy as np, imageio_ffmpeg
from dream_core import ffmeter, master_file
from make_hechizo import SECTIONS, TMP, SPB, XF_BARS

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'masters', 'amr-hechizo.wav')
CUTS = ['OJOS', 'VOZ', 'EMBRUJO', 'TRANCE', 'CONJURO', 'MAGIA']

def sh(cmd): subprocess.run(cmd, check=True)

def enc(src, dst):
    sh([FF, '-y', '-v', 'error', '-i', src, '-c:a', 'aac_at', '-b:a', '256k',
        '-movflags', '+faststart', dst])

def peaks(path, W=720):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', '4410',
                          '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.abs(np.frombuffer(raw, dtype='<f4'))
    seg = len(x) // W
    pk = x[:seg * W].reshape(W, seg).max(axis=1)
    return (pk / (pk.max() or 1)).round(3).tolist()

if __name__ == '__main__':
    # 1. set completo
    m4a = os.path.join(HERE, 'audio', 'amr-hechizo.m4a')
    enc(SRC, m4a)
    I, lra, tp = ffmeter(m4a)
    print(f'SET m4a: {os.path.getsize(m4a)//1048576} MB · {I} LUFS · LRA {lra} · TP {tp}', flush=True)

    # 2. offsets por sección (compases exactos × 2 s)
    offsets, acc = [], 0.0
    for s in SECTIONS:
        offsets.append(round(acc, 1))
        acc += s['bars'] * SPB / 44100.0
    titles = [s['name'] for s in SECTIONS]

    meta = dict(id='amr-hechizo', title='HECHIZO', kicker='HECHIZO DE ELLA · 0→100',
                tracks=len(titles), dur=round(acc, 1), titles=titles, offsets=offsets,
                file='audio/amr-hechizo.m4a', art='art/shots/shot-hechizo.svg', edition=12,
                peaks=peaks(m4a), bpm=125, key='A MIN')
    with open(os.path.join(HERE, 'hechizo.js'), 'w') as f:
        f.write('window.AMR_HECHIZO=' + json.dumps(meta) + ';')
    print('hechizo.js escrito', flush=True)

    # 3. cortes standalone: la sección pre-master se masteriza individual (mismo chain)
    for i, s in enumerate(SECTIONS):
        if s['name'] not in CUTS: continue
        secw = os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        mst = os.path.join(TMP, f'cut-{s["name"].lower()}.wav')
        hist = master_file(secw, mst, target_i=-8.5, ceiling_db=-1.1)
        dst = os.path.join(HERE, 'audio', f'amr-hechizo-cut-{s["name"].lower()}.m4a')
        enc(mst, dst)
        os.remove(mst)
        Ic, _, tpc = ffmeter(dst)
        print(f'  corte {s["name"]}: {Ic} LUFS · TP {tpc} · {os.path.getsize(dst)//1048576} MB', flush=True)
    print('done', flush=True)
