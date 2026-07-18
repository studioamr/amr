#!/usr/bin/env python3
"""Publica MÁQUINA: m4a + maquina.js + cortes."""
import os, json, subprocess
import numpy as np, imageio_ffmpeg
from dream_core import ffmeter, master_file, ffdecode, wav_write, sat
from make_maquina import SECTIONS, TMP, SPB, BPM

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'masters', 'amr-maquina.wav')
CUTS = ['MUSA', 'MOTOR', 'VACIO', 'CUMBRE', 'NUCLEO']

def enc(src, dst):
    subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-c:a', 'aac_at', '-b:a', '256k',
                    '-movflags', '+faststart', dst], check=True)

def peaks(path, W=720):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', '4410',
                          '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.abs(np.frombuffer(raw, dtype='<f4')); seg = len(x)//W
    pk = x[:seg*W].reshape(W, seg).max(axis=1)
    return (pk/(pk.max() or 1)).round(3).tolist()

if __name__ == '__main__':
    m4a = os.path.join(HERE, 'audio', 'amr-maquina.m4a')
    enc(SRC, m4a)
    I, lra, tp = ffmeter(m4a)
    print(f'SET m4a: {os.path.getsize(m4a)//1048576} MB · {I} LUFS · LRA {lra} · TP {tp}', flush=True)

    offsets, acc = [], 0.0
    for s in SECTIONS:
        offsets.append(round(acc, 1)); acc += s['bars'] * SPB / 44100.0
    titles = [s['name'] for s in SECTIONS]
    meta = dict(id='amr-maquina', title='MÁQUINA', kicker='MELODIC TECHNO · DRUMS REALES',
                tracks=len(titles), dur=round(acc, 1), titles=titles, offsets=offsets,
                file='audio/amr-maquina.m4a', art='art/shots/shot-maquina.svg', edition=12,
                peaks=peaks(m4a), bpm=int(BPM), key='A MIN')
    with open(os.path.join(HERE, 'maquina.js'), 'w') as f:
        f.write('window.AMR_MAQUINA=' + json.dumps(meta) + ';')
    print('maquina.js escrito', flush=True)

    for i, s in enumerate(SECTIONS):
        if s['name'] not in CUTS: continue
        secw = os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        x = ffdecode(secw)
        x = np.stack([sat(x[0], 1.3, 0.02), sat(x[1], 1.3, 0.02)])
        x *= 0.90 / max(1e-9, float(np.abs(x).max()))
        pre = os.path.join(TMP, f'pre-{s["name"].lower()}.wav'); wav_write(pre, x); del x
        mst = os.path.join(TMP, f'cut-{s["name"].lower()}.wav')
        master_file(pre, mst, target_i=-11.0, ceiling_db=-1.2)
        dst = os.path.join(HERE, 'audio', f'amr-maquina-cut-{s["name"].lower()}.m4a')
        enc(mst, dst); os.remove(mst); os.remove(pre)
        Ic, _, tpc = ffmeter(dst)
        print(f'  corte {s["name"]}: {Ic} LUFS · TP {tpc} · {os.path.getsize(dst)//1048576} MB', flush=True)
    print('done', flush=True)
