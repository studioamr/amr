#!/usr/bin/env python3
"""GUERRERO — set b2b estilo Mayan Warrior (Adam Ten b2b Mita Gami / Maccabi House).
DJ A = rolas de André (SoundCloud) · DJ B = movimientos frescos de DELIRIO + VESSEL.
Todo beatmatcheado a 122 BPM con detección de fase de beat (los kicks caen juntos).
Rotación b2b real: turnos de 2 al abrir → track por track al cierre. Groove constante."""
import os, json, subprocess, wave, sys
import numpy as np, imageio_ffmpeg
import make_tracks as mt

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
TMP = os.path.join(HERE, '_djset_tmp'); os.makedirs(TMP, exist_ok=True)

BPM = 122.0
BAR = 240.0 / BPM                       # 1.9672 s
BEAT = 60.0 / BPM
OV = 8                                  # overlap: 8 compases (~16 s) — groove ágil Maccabi

def load_meta(fn):
    s = open(fn).read()
    return json.loads(s[s.index('=') + 1:s.rstrip().rstrip(';').rindex('}') + 1])
TOFF = load_meta('tulum.js')['offsets']; TDUR = load_meta('tulum.js')['dur']

def sh(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0: print(r.stderr[-500:]); sys.exit(1)

def load_wav(path):
    w = wave.open(path); n = w.getnframes()
    x = np.frombuffer(w.readframes(n), dtype='<i2').astype(np.float32) / 32768.0
    return x.reshape(-1, w.getnchannels()).T.copy()

# ---------- detección de BPM fino + fase de beat (para mp3 reales) ----------
def beat_grid(path, bpm_hint):
    SRr = 11025
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SRr), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4')
    hop = 256; nw = (len(x) - 512) // hop
    idx = np.arange(nw)[:, None] * hop + np.arange(512)[None, :]
    E = (x[idx] ** 2).mean(axis=1)
    on = np.maximum(0, np.diff(E)); on = on - on.mean()
    fps = SRr / hop
    # BPM fino alrededor del hint
    best = (-1, bpm_hint)
    for bpm in np.arange(bpm_hint - 0.5, bpm_hint + 0.52, 0.02):
        P = fps * 60.0 / bpm
        ks = np.arange(0, len(on) - 1, P)
        sc = on[np.round(ks).astype(int)].sum()
        # fase óptima para este bpm
        ph_best = 0; sc_best = -1e18
        for ph in np.linspace(0, P, 24, endpoint=False):
            kk = np.round(np.arange(ph, len(on) - 1, P)).astype(int)
            v = on[kk].sum()
            if v > sc_best: sc_best = v; ph_best = ph
        if sc_best > best[0]: best = (sc_best, bpm, ph_best)
    _, bpm, ph = best
    t0 = ph / fps                        # primer beat (segundos)
    return bpm, t0

# ---------- preparación de segmentos ----------
def sc_seg(name, fname, bpm_hint, bars):
    """rola de SoundCloud: fase de beat + atempo a 122 + corte en beat exacto."""
    out = os.path.join(TMP, f'g-{name}.wav')
    if os.path.exists(out): return out
    src = os.path.join('set-src', fname)
    bpm, t0 = beat_grid(src, bpm_hint)
    ratio = BPM / bpm
    full = os.path.join(TMP, f'g-{name}-t.wav')
    sh([FF, '-y', '-v', 'error', '-i', src, '-filter:a', f'atempo={ratio:.6f}',
        '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', full])
    t0p = t0 / ratio                      # el primer beat tras el stretch
    start = t0p + 2 * BAR                 # entra 2 compases después del primer beat
    sh([FF, '-y', '-v', 'error', '-ss', f'{start:.4f}', '-t', f'{bars * BAR:.4f}',
        '-i', full, '-c:a', 'pcm_s16le', out])
    os.remove(full)
    print(f'    {name:12s} bpm_real={bpm:6.2f} fase={t0:.3f}s', flush=True)
    return out

def delirio_seg(name, sec_idx, bars):
    """movimiento de DELIRIO (121 → 122)."""
    out = os.path.join(TMP, f'g-{name}.wav')
    if os.path.exists(out): return out
    start = TOFF[sec_idx]
    dur121 = min(bars * BAR * (122.0 / 121.0), TDUR - start)
    raw = os.path.join(TMP, f'g-{name}-r.wav')
    sh([FF, '-y', '-v', 'error', '-ss', f'{start:.4f}', '-t', f'{dur121:.4f}',
        '-i', 'masters/amr-tulum.wav', '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', raw])
    sh([FF, '-y', '-v', 'error', '-i', raw, '-filter:a', f'atempo={122.0/121.0:.6f}',
        '-c:a', 'pcm_s16le', out])
    os.remove(raw)
    return out

def vessel_seg(bars):
    """VESSEL es 122 nativo — cero stretch."""
    out = os.path.join(TMP, 'g-vessel.wav')
    if os.path.exists(out): return out
    sh([FF, '-y', '-v', 'error', '-ss', f'{BAR:.4f}', '-t', f'{bars * BAR:.4f}',
        '-i', 'masters/amr-003-vessel.wav', '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', out])
    return out

# el set — rotación b2b: A=SoundCloud, B=Studio (turnos 2-2 → 1-1 al cierre)
SET = [
    ('FTMO',       'A', lambda: sc_seg('ftmo', '02 - ftmo.mp3', 115.0, 96), ),
    ('POMONA',     'A', lambda: sc_seg('pomona', '90 - Pomona.mp3', 115.0, 96), ),
    ('GAMA',       'B', lambda: delirio_seg('gama', 2, 96), ),
    ('LUNES',      'B', lambda: delirio_seg('lunes', 3, 96), ),
    ('LIBALI',     'A', lambda: sc_seg('libali', '01 - Libali.mp3', 120.5, 112), ),
    ('HOLLYWOOD',  'A', lambda: sc_seg('hollywood', '03 - Hollywood.mp3', 120.5, 96), ),
    ('VOCES',      'B', lambda: delirio_seg('voces', 6, 96), ),
    ('SHINY DAYS', 'A', lambda: sc_seg('shiny', '04 - shiny days.mp3', 120.5, 96), ),
    ('SODA',       'B', lambda: delirio_seg('soda', 7, 96), ),
    ('AURA',       'A', lambda: sc_seg('aura', '06 - Aura.mp3', 120.5, 112), ),
    ('VESSEL',     'B', lambda: vessel_seg(87), ),
    ('SUNSET',     'A', lambda: sc_seg('sunset', '08 - Sunset.mp3', 120.5, 112), ),
    ('ADIOS',      'B', lambda: delirio_seg('adios', 8, 96), ),
    ('ROSABLANCA', 'A', lambda: sc_seg('rosablanca', '10 - Rosablanca.mp3', 120.5, 82), ),
    ('CALIENTE',   'B', lambda: delirio_seg('caliente', 14, 112), ),
    ('TROUBLE',    'A', lambda: sc_seg('trouble', '13 - trouble.mp3', 115.0, 96), ),
    ('NOV24',      'A', lambda: sc_seg('nov24', '91 - Nov24.mp3', 120.5, 168), ),
]

def eq_blocks(x, fcs, mode):
    n = x.shape[1]; k = len(fcs); bl = n // k
    for i, fc in enumerate(fcs):
        if fc <= 0: continue
        a, b = i * bl, (i + 1) * bl if i < k - 1 else n
        for c in (0, 1):
            x[c, a:b] = (mt.highpass if mode == 'hp' else mt.lowpass)(x[c, a:b], fc)
    return x

def build():
    bar_n = int(round(BAR * SR)); ovn = OV * bar_n
    print('preparando %d tracks…' % len(SET), flush=True)
    segs = []
    for title, dj, loader in SET:
        x = load_wav(loader())
        nb = x.shape[1] // bar_n
        x = x[:, :nb * bar_n]
        # nivelar loudness por segmento (los mp3 vienen a niveles distintos)
        rms = float(np.sqrt((x ** 2).mean()))
        g = float(np.clip(0.21 / max(rms, 1e-6), 0.6, 1.9))
        x *= g
        segs.append((title, dj, x))
        print(f'  [{dj}] {title:12s} {nb:4d} bars  {x.shape[1]/SR:6.1f}s  rms={rms:.3f}→x{g:.2f}', flush=True)
    total = sum(x.shape[1] for _, _, x in segs) - ovn * (len(segs) - 1)
    mix = np.zeros((2, total), dtype=np.float32)
    offsets = []; pos = 0
    for i, (title, dj, x) in enumerate(segs):
        x = x.copy(); n = x.shape[1]
        if i > 0:
            h = min(ovn, n)
            x[:, :h] *= np.sin(np.linspace(0, np.pi / 2, h), dtype=np.float32)
            half = h // 2
            x[:, :half] = eq_blocks(x[:, :half], [380, 800, 1600, 3200], 'lp')
        if i < len(segs) - 1:
            t_ = min(ovn, n)
            x[:, -t_:] = eq_blocks(x[:, -t_:], [0, 140, 380, 950], 'hp')
            x[:, -t_:] *= np.cos(np.linspace(0, np.pi / 2, t_), dtype=np.float32)
        mix[:, pos:pos + n] += x
        offsets.append(round(pos / SR + (OV * BAR if i > 0 else 0), 1))
        pos += n - ovn
        del x
    mix = mt.softclip(mix, 1.05)
    mix /= max(1e-9, np.abs(mix).max()) / 0.89
    dur = total / SR
    print(f'set total: {dur:.1f}s = {dur/60:.1f} min', flush=True)
    wavp = os.path.join(TMP, 'guerrero.wav')
    with wave.open(wavp, 'w') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix.T * 32767).astype('<i2').tobytes())
    W = 720; seg = total // W
    mono = np.abs(mix).mean(axis=0)[:seg * W].reshape(W, seg)
    pk = mono.max(axis=1); pk = (pk / pk.max()).round(3).tolist()
    return wavp, dur, offsets, pk

if __name__ == '__main__':
    wavp, dur, offsets, pk = build()
    m4a = os.path.join(HERE, 'audio', 'amr-guerrero.m4a')
    sh([FF, '-y', '-v', 'error', '-i', wavp, '-af', 'loudnorm=I=-10.5:TP=-1.0:LRA=11',
        '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', m4a])
    print('M4A:', m4a, os.path.getsize(m4a) // 1024 // 1024, 'MB', flush=True)
    titles = [t for t, _, _ in SET]
    meta = dict(id='amr-guerrero', title='GUERRERO', kicker='B2B · DESERT SET', tracks=len(titles),
                dur=round(dur, 1), titles=titles, offsets=offsets,
                file='audio/amr-guerrero.m4a', art='art/amr-guerrero.svg', edition=12,
                peaks=pk, bpm=122, key=None)
    with open(os.path.join(HERE, 'guerrero.js'), 'w') as f:
        f.write('window.AMR_GUER=' + json.dumps(meta) + ';')
    print('guerrero.js escrito —', len(titles), 'tracks. done', flush=True)
