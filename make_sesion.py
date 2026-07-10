#!/usr/bin/env python3
# AMR — SESIÓN 002: DJ set fino de ~3h con TODO el catálogo de André.
# Analiza energía por track, los ordena en un arco de set (montaña de energía),
# mezcla con crossfades y masteriza. Corre con /usr/local/bin/python3.
import os, subprocess, re, json, wave, math, sys
import numpy as np, imageio_ffmpeg
import make_set

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'session-src')
OUT_WAV = os.path.join(HERE, 'masters', 'amr-sesion-002.wav')
M4A = os.path.join(HERE, 'audio', 'amr-sesion-002.m4a')
XF = 7.0                      # crossfade entre tracks (seg) — transición de DJ
EXCLUDE = ['wish you were here']   # Pink Floyd remake: fuera del producto a la venta

def dur_of(p):
    s = subprocess.run([FF, '-i', p], capture_output=True, text=True).stderr
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', s)
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3)) if m else 0

def analyze(p):
    """Decodifica a mono 8k y saca energía (RMS) + brillo (proporción de agudos)."""
    raw = subprocess.run([FF, '-v','quiet','-i', p, '-ac','1','-ar','8000','-f','f32le','-'],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4')
    if len(x) < 8000:
        return dict(rms=0, bright=0)
    # ignora silencios de intro/outro para energía representativa (percentil 70 de RMS por ventana)
    win = 8000  # 1s
    n = len(x)//win
    if n < 1: n = 1
    seg = x[:n*win].reshape(n, win)
    rms_w = np.sqrt((seg**2).mean(axis=1))
    rms = float(np.percentile(rms_w, 70))
    # brillo: energía sobre 2kHz vs total (agudos = más "activo")
    X = np.abs(np.fft.rfft(x[:min(len(x), 8000*60)]))  # primer minuto
    f = np.fft.rfftfreq(min(len(x), 8000*60), 1/8000)
    hi = X[f > 2000].sum(); tot = X.sum() + 1e-9
    return dict(rms=rms, bright=float(hi/tot))

def clean_title(path):
    b = os.path.basename(path)
    b = re.sub(r'^\d+ - ', '', b)
    return os.path.splitext(b)[0].strip()

def arc_order(tracks):
    """Montaña de energía: menor energía en los bordes (intro/outro), mayor al centro (peak)."""
    by_e = sorted(tracks, key=lambda t: t['rms'])
    n = len(by_e); arc = [None]*n
    left, right = 0, n-1
    for i, t in enumerate(by_e):
        if i % 2 == 0: arc[left] = t; left += 1
        else: arc[right] = t; right -= 1
    return arc

def build_cmd(order):
    n = len(order); parts = []
    for i in range(n):
        parts.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo,dynaudnorm=f=200:g=12[a{i}]')
    prev = 'a0'
    for i in range(1, n):
        out = 'premix' if i == n-1 else f'x{i}'
        parts.append(f'[{prev}][a{i}]acrossfade=d={XF}:c1=tri:c2=tri[{out}]'); prev = out
    master = ("highpass=f=22,equalizer=f=55:t=q:w=0.9:g=1.5,equalizer=f=200:t=q:w=1.4:g=-2,"
              "equalizer=f=8500:t=h:w=0.7:g=2,acompressor=threshold=-16dB:ratio=2.2:attack=25:release=260:makeup=2.5,"
              "loudnorm=I=-10:TP=-1.0:LRA=12,alimiter=level_out=0.97:limit=0.97")
    parts.append(f'[premix]{master}[m]')
    cmd = [FF, '-y']
    for t in order: cmd += ['-i', t['path']]
    cmd += ['-filter_complex', ';'.join(parts), '-map', '[m]', '-c:a', 'pcm_s16le', OUT_WAV]
    return cmd

if __name__ == '__main__':
    files = sorted([os.path.join(SRC, f) for f in os.listdir(SRC) if f.endswith('.mp3')])
    files = [f for f in files if not any(x in os.path.basename(f).lower() for x in EXCLUDE)]
    print(f'Analizando {len(files)} pistas…', flush=True)
    tracks = []
    for f in files:
        a = analyze(f); d = dur_of(f)
        if d < 30: continue          # descarta clips muy cortos
        tracks.append(dict(path=f, title=clean_title(f), dur=d, **a))
        print(f'  {clean_title(f)[:34]:34s}  {int(d//60)}:{int(d%60):02d}  e={a["rms"]:.3f}', flush=True)
    order = arc_order(tracks)
    total = sum(t['dur'] for t in order) - XF*(len(order)-1)
    print(f'\nArco del set ({len(order)} pistas, ~{int(total//60)} min):', flush=True)
    for i, t in enumerate(order): print(f'  {i+1:2d}. {t["title"][:38]:38s} e={t["rms"]:.3f}', flush=True)

    FINAL = '--finalize' in sys.argv
    if not FINAL:
        print('\nMezclando el set (crossfades + master)…', flush=True)
        r = subprocess.run(build_cmd(order), capture_output=True, text=True)
        if r.returncode != 0:
            print('ERROR:\n', r.stderr[-3000:]); raise SystemExit(1)
    secs = int(dur_of(OUT_WAV))
    # bitrate dinámico para caber < 95 MB en GitHub
    br = max(64, min(128, int(95*1024*1024*8 / secs / 1000)))
    if not FINAL or not os.path.exists(M4A):
        subprocess.run([FF, '-y', '-i', OUT_WAV, '-c:a', 'aac', '-b:a', f'{br}k', M4A], capture_output=True)
    print(f'WAV {secs//60}:{secs%60:02d}  ·  m4a {br}k = {os.path.getsize(M4A)//1024//1024} MB', flush=True)

    # offsets por track (inicio de cada canción en el mix, con crossfade)
    off = [0.0]
    for i in range(1, len(order)):
        off.append(round(max(0, off[-1] + order[i-1]['dur'] - XF), 1))
    # peaks robustos: decodifica a mono 2kHz vía ffmpeg (el WAV es demasiado grande para wave)
    raw = subprocess.run([FF,'-v','quiet','-i',OUT_WAV,'-ac','1','-ar','2000','-f','f32le','-'], capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4')
    W = 720; seg = max(1, len(x)//W); pk = np.abs(x[:seg*W]).reshape(W, seg).max(axis=1); pk = (pk/(pk.max() or 1)).round(3).tolist()
    meta = dict(id='amr-sesion-002', title='SESIÓN 002', kicker='THE 3-HOUR SET', tracks=len(order),
                dur=secs, titles=[t['title'] for t in order], offsets=off,
                file='audio/amr-sesion-002.m4a', art='art/amr-sesion-002.png', edition=10, peaks=pk)
    open(os.path.join(HERE, 'sesion2.js'), 'w').write('window.AMR_S2='+json.dumps(meta, ensure_ascii=False)+';\n')
    make_set.make_cover(pk, len(order), secs, title='SESIÓN 002', kicker='THE 3-HOUR SET', out='amr-sesion-002')
    print(f'sesion2.js + portada OK — {secs//60}:{secs%60:02d}', flush=True)
