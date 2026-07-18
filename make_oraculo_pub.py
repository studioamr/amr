#!/usr/bin/env python3
"""Publica ORÁCULO: m4a (ya masterizado) + oraculo.js + cortes. BPM por sección."""
import os, json, subprocess
import numpy as np, imageio_ffmpeg
from dream_core import ffmeter, master_file, ffdecode, wav_write, sat, SR
from make_oraculo import SECTIONS, TMP

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'masters', 'amr-oraculo.wav')
CUTS = ['MUSA', 'DESCENSO', 'VACIO', 'HIMNO', 'CORAZON']

def enc(src, dst):
    subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-c:a', 'aac_at', '-b:a', '256k',
                    '-movflags', '+faststart', dst], check=True)

def peaks(path, W=720):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', '4410',
                          '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.abs(np.frombuffer(raw, dtype='<f4'))
    seg = len(x) // W
    pk = x[:seg * W].reshape(W, seg).max(axis=1)
    return (pk / (pk.max() or 1)).round(3).tolist()

if __name__ == '__main__':
    m4a = os.path.join(HERE, 'audio', 'amr-oraculo.m4a')
    enc(SRC, m4a)
    I, lra, tp = ffmeter(m4a)
    print(f'SET m4a: {os.path.getsize(m4a)//1048576} MB · {I} LUFS · LRA {lra} · TP {tp}', flush=True)

    offsets, acc = [], 0.0
    for s in SECTIONS:
        offsets.append(round(acc, 1))
        acc += s['bars'] * 240.0 / s['bpm']      # duración de sección = bars * 240/bpm seg
    titles = [s['name'] for s in SECTIONS]

    meta = dict(id='amr-oraculo', title='ORÁCULO', kicker='MELODIC TECHNO · SCI-FI · 0→100',
                tracks=len(titles), dur=round(acc, 1), titles=titles, offsets=offsets,
                file='audio/amr-oraculo.m4a', art='art/shots/shot-oraculo.svg', edition=12,
                peaks=peaks(m4a), bpm=124, key='G MIN')
    with open(os.path.join(HERE, 'oraculo.js'), 'w') as f:
        f.write('window.AMR_ORACULO=' + json.dumps(meta) + ';')
    print('oraculo.js escrito', flush=True)

    for i, s in enumerate(SECTIONS):
        if s['name'] not in CUTS: continue
        secw = os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        x = ffdecode(secw)
        x = np.stack([sat(x[0], 1.3, 0.02), sat(x[1], 1.3, 0.02)])
        x *= 0.90 / max(1e-9, float(np.abs(x).max()))
        pre = os.path.join(TMP, f'pre-{s["name"].lower()}.wav'); wav_write(pre, x); del x
        mst = os.path.join(TMP, f'cut-{s["name"].lower()}.wav')
        master_file(pre, mst, target_i=-10.0, ceiling_db=-1.6)
        dst = os.path.join(HERE, 'audio', f'amr-oraculo-cut-{s["name"].lower()}.m4a')
        enc(mst, dst); os.remove(mst); os.remove(pre)
        Ic, _, tpc = ffmeter(dst)
        print(f'  corte {s["name"]}: {Ic} LUFS · TP {tpc} · {os.path.getsize(dst)//1048576} MB', flush=True)
    print('done', flush=True)
