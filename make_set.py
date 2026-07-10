#!/usr/bin/env python3
# AMR — junta la playlist "set" en un mix continuo (THE SET) con crossfades.
# Requiere ffmpeg (imageio-ffmpeg). Corre con /usr/local/bin/python3.
import os, subprocess, glob, json, re, sys
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'set-src')
XF = 3.0          # segundos de crossfade entre pistas
OUT_WAV = os.path.join(HERE, 'masters', 'amr-set-the-set.wav')
OUT_M4A = os.path.join(HERE, 'audio', 'amr-set-the-set.m4a')

def order_files():
    """Pistas 01..17 de la playlist + Pomona (90) + Nov24 (91) al final."""
    files = sorted(glob.glob(os.path.join(SRC, '[01][0-9] - *.mp3')))   # 01..17
    files += sorted(glob.glob(os.path.join(SRC, '90 - Pomona.mp3')))    # Pomona
    files += sorted(glob.glob(os.path.join(SRC, '91 - Nov24.mp3')))     # Nov24
    return files

def track_title(path):
    b = os.path.basename(path)
    b = re.sub(r'^\d+ - ', '', b)
    b = re.sub(r' - .*SoundLoadMate.*', '', b)
    return os.path.splitext(b)[0].strip()

def build(files):
    # filtergraph: normaliza cada input y encadena con acrossfade
    n = len(files)
    parts = []
    for i in range(n):
        parts.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo,'
                     f'dynaudnorm=f=200:g=15[a{i}]')
    prev = 'a0'
    for i in range(1, n):
        out = 'mix' if i == n-1 else f'x{i}'
        parts.append(f'[{prev}][a{i}]acrossfade=d={XF}:c1=tri:c2=tri[{out}]')
        prev = out if i < n-1 else 'mix'
    fg = ';'.join(parts)
    cmd = [FF, '-y']
    for f in files:
        cmd += ['-i', f]
    cmd += ['-filter_complex', fg, '-map', '[mix]',
            '-c:a', 'pcm_s16le', OUT_WAV]
    return cmd

def _run():
    os.makedirs(os.path.dirname(OUT_WAV), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_M4A), exist_ok=True)
    files = order_files()
    print(f'{len(files)} pistas en el set:')
    for i, f in enumerate(files, 1):
        print(f'  {i:2d}. {track_title(f)}')
    cmd = build(files)
    print('\nMezclando (crossfades)…', flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print('ERROR ffmpeg:\n', r.stderr[-3000:]); sys.exit(1)
    # duración
    probe = subprocess.run([FF, '-i', OUT_WAV], capture_output=True, text=True).stderr
    dur = re.search(r'Duration: (\d+):(\d+):(\d+)', probe)
    secs = int(dur.group(1))*3600 + int(dur.group(2))*60 + int(dur.group(3)) if dur else 0
    print(f'WAV listo: {secs//60}:{secs%60:02d}  ({os.path.getsize(OUT_WAV)//1024//1024} MB)')
    # m4a para web
    subprocess.run([FF, '-y', '-i', OUT_WAV, '-c:a', 'aac', '-b:a', '192k', OUT_M4A],
                   capture_output=True)
    print(f'M4A listo: {os.path.getsize(OUT_M4A)//1024//1024} MB')
    # peaks para el waveform del player (720 puntos)
    import wave, numpy as np
    w = wave.open(OUT_WAV); raw = w.readframes(w.getnframes())
    x = np.frombuffer(raw, '<i2').astype(float).reshape(-1, 2).mean(axis=1)
    W = 720; seg = len(x)//W
    pk = np.abs(x[:seg*W]).reshape(W, seg).max(axis=1)
    pk = (pk/pk.max()).round(3).tolist()
    meta = dict(id='amr-set-the-set', title='THE SET', tracks=len(files),
                dur=secs, titles=[track_title(f) for f in files],
                file='audio/amr-set-the-set.m4a', art='art/amr-set-the-set.png',
                edition=25, peaks=pk)
    with open(os.path.join(HERE, 'set.js'), 'w') as f:
        f.write('window.AMR_SET=' + json.dumps(meta) + ';\n')
    print('set.js OK — dur', f'{secs//60}:{secs%60:02d}')
    make_cover(pk, len(files), secs)
    print('portada THE SET lista')

def make_cover(peaks, n_tracks, secs):
    """Portada NOCTURNA (otro branding): waveform real del set en ámbar sobre negro."""
    from PIL import Image
    BONE='#EAE6DF'; INK='#141210'; AMBER='#A62D3E'; NIGHT='#0e0b08'; MUT='#8a7f72'
    W=1400
    s=[f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">']
    s.append('<defs>')
    s.append('<radialGradient id="bg" cx="50%" cy="34%" r="80%">'
             f'<stop offset="0%" stop-color="#1d1014"/><stop offset="60%" stop-color="{NIGHT}"/>'
             '<stop offset="100%" stop-color="#070505"/></radialGradient>')
    s.append('<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0%" stop-color="#C24C5C"/><stop offset="100%" stop-color="{AMBER}"/></linearGradient>')
    s.append('</defs>')
    s.append(f'<rect width="{W}" height="{W}" fill="url(#bg)"/>')
    # marco fino
    s.append(f'<rect x="40" y="40" width="{W-80}" height="{W-80}" fill="none" stroke="{AMBER}" stroke-opacity="0.35" stroke-width="2"/>')
    # etiqueta arriba
    s.append(f'<text x="{W/2}" y="150" font-family="Courier New, monospace" font-size="26" letter-spacing="10" '
             f'fill="{MUT}" text-anchor="middle">AMR — CONTINUOUS MIX</text>')
    # waveform central (barras espejadas)
    cy=W/2; n=len(peaks); span=W-260; x0=130; bw=span/n
    for i,p in enumerate(peaks):
        h=max(3, p*360)
        x=x0+i*bw
        s.append(f'<rect x="{x:.1f}" y="{cy-h/2:.1f}" width="{max(1.2,bw*0.62):.2f}" height="{h:.1f}" rx="1" fill="url(#bar)"/>')
    # línea base
    s.append(f'<line x1="{x0}" y1="{cy}" x2="{x0+span}" y2="{cy}" stroke="{AMBER}" stroke-opacity="0.25" stroke-width="1"/>')
    # título
    s.append(f'<text x="{W/2}" y="{W-360}" font-family="Georgia, serif" font-weight="bold" font-size="210" '
             f'letter-spacing="6" fill="{BONE}" text-anchor="middle">THE SET</text>')
    s.append(f'<line x1="{W/2-190}" y1="{W-300}" x2="{W/2+190}" y2="{W-300}" stroke="{AMBER}" stroke-width="3"/>')
    # datos abajo
    mm=f'{secs//60}:{secs%60:02d}'
    s.append(f'<text x="{W/2}" y="{W-250}" font-family="Courier New, monospace" font-size="27" letter-spacing="7" '
             f'fill="{MUT}" text-anchor="middle">{n_tracks} TRACKS<tspan fill="{AMBER}">  ·  </tspan>{mm}<tspan fill="{AMBER}">  ·  </tspan>ONE TAKE</text>')
    # firma AMR grande abajo
    s.append(f'<text x="{W/2}" y="{W-120}" font-family="Georgia, serif" font-weight="bold" font-size="120" '
             f'letter-spacing="20" fill="{AMBER}" text-anchor="middle">AMR</text>')
    s.append(f'<text x="{W/2}" y="{W-70}" font-family="Courier New, monospace" font-size="20" letter-spacing="8" '
             f'fill="{MUT}" text-anchor="middle">MORELIA · MMXXVI</text>')
    s.append('</svg>')
    svg=''.join(s)
    os.makedirs(os.path.join(HERE,'art'), exist_ok=True)
    svgp=os.path.join(HERE,'art','amr-set-the-set.svg'); open(svgp,'w').write(svg)
    subprocess.run(['qlmanage','-t','-s','2800','-o',os.path.join(HERE,'art'),svgp], capture_output=True)
    raw=os.path.join(HERE,'art','amr-set-the-set.svg.png')
    if os.path.exists(raw):
        im=Image.open(raw).convert('RGB').resize((1400,1400), Image.LANCZOS)
        im.save(os.path.join(HERE,'art','amr-set-the-set.png')); os.remove(raw)

if __name__ == '__main__':
    _run()
