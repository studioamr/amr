#!/usr/bin/env python3
"""Publica PLAYA: m4a del set (ya masterizado), playa.js, cortes standalone."""
import os, json, subprocess
import numpy as np, imageio_ffmpeg
from dream_core import ffmeter, master_file
from make_playa import SECTIONS, TMP, SPB, XF_BARS

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'masters', 'amr-playa.wav')
CUTS = ['POLVO', 'CARAVANA', 'ESPEJISMO', 'AMANECER', 'FUEGO', 'BAILE']

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
    m4a = os.path.join(HERE, 'audio', 'amr-playa.m4a')
    enc(SRC, m4a)
    I, lra, tp = ffmeter(m4a)
    print(f'SET m4a: {os.path.getsize(m4a)//1048576} MB · {I} LUFS · LRA {lra} · TP {tp}', flush=True)

    offsets, acc = [], 0.0
    for s in SECTIONS:
        offsets.append(round(acc, 1))
        acc += s['bars'] * SPB / 44100.0
    titles = [s['name'] for s in SECTIONS]

    meta = dict(id='amr-playa', title='PLAYA', kicker='DESERT FUNK · 0→100',
                tracks=len(titles), dur=round(acc, 1), titles=titles, offsets=offsets,
                file='audio/amr-playa.m4a', art='art/shots/shot-playa.svg', edition=12,
                peaks=peaks(m4a), bpm=119, key='A MIN')
    with open(os.path.join(HERE, 'playa.js'), 'w') as f:
        f.write('window.AMR_PLAYA=' + json.dumps(meta) + ';')
    print('playa.js escrito', flush=True)

    from dream_core import ffdecode, wav_write, sat
    for i, s in enumerate(SECTIONS):
        if s['name'] not in CUTS: continue
        secw = os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        x = ffdecode(secw)                                   # mismo afeitado que el set:
        x = np.stack([sat(x[0] * 1.5, 2.0, 0.04), sat(x[1] * 1.5, 2.0, 0.04)])
        x *= 0.72 / max(1e-9, float(np.abs(x).max()))
        pre = os.path.join(TMP, f'pre-{s["name"].lower()}.wav')
        wav_write(pre, x); del x
        mst = os.path.join(TMP, f'cut-{s["name"].lower()}.wav')
        hist = master_file(pre, mst, target_i=-10.0, ceiling_db=-3.8)
        dst = os.path.join(HERE, 'audio', f'amr-playa-cut-{s["name"].lower()}.m4a')
        enc(mst, dst)
        os.remove(mst); os.remove(pre)
        Ic, _, tpc = ffmeter(dst)
        print(f'  corte {s["name"]}: {Ic} LUFS · TP {tpc} · {os.path.getsize(dst)//1048576} MB', flush=True)
    print('done', flush=True)
