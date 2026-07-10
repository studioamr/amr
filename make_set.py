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
    """Portada del SET: un vinilo real sobre papel hueso (coherente con el hero, no el bloque negro)."""
    from PIL import Image
    BONE='#EAE6DF'; BONE2='#e0dad1'; INK='#141210'; WINE='#A62D3E'; WINE_LT='#C24C5C'; MUT='#6E675E'
    W=1400; cx=cy=W/2; R=560
    mm=f'{secs//60}:{secs%60:02d}'
    s=[f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">']
    s.append('<defs>')
    s.append('<radialGradient id="disc" cx="42%" cy="38%" r="72%">'
             '<stop offset="0%" stop-color="#211c17"/><stop offset="55%" stop-color="#17130e"/>'
             '<stop offset="100%" stop-color="#0c0a07"/></radialGradient>')
    s.append('<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1">'
             '<stop offset="0%" stop-color="#fff" stop-opacity="0.10"/><stop offset="40%" stop-color="#fff" stop-opacity="0"/>'
             '<stop offset="60%" stop-color="#fff" stop-opacity="0"/><stop offset="100%" stop-color="#fff" stop-opacity="0.05"/></linearGradient>')
    s.append('<radialGradient id="lbl" cx="46%" cy="40%" r="60%">'
             f'<stop offset="0%" stop-color="{WINE_LT}"/><stop offset="100%" stop-color="{WINE}"/></radialGradient>')
    s.append('</defs>')
    # papel hueso
    s.append(f'<rect width="{W}" height="{W}" fill="{BONE}"/>')
    s.append(f'<rect x="46" y="46" width="{W-92}" height="{W-92}" fill="none" stroke="{INK}" stroke-opacity="0.14" stroke-width="2"/>')
    # etiquetas mono arriba
    s.append(f'<text x="120" y="118" font-family="Courier New, monospace" font-size="24" letter-spacing="8" fill="{MUT}">AMR</text>')
    s.append(f'<text x="{W-120}" y="118" font-family="Courier New, monospace" font-size="24" letter-spacing="8" fill="{WINE}" text-anchor="end">MMXXVI</text>')
    # sombra + disco
    s.append(f'<ellipse cx="{cx}" cy="{cy+R*0.9}" rx="{R*0.8}" ry="26" fill="{INK}" opacity="0.06"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#disc)"/>')
    # surcos concéntricos
    r=200
    i=0
    while r <= R-8:
        op=0.5*(0.5 if i%2 else 1.0)
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="#3a332b" stroke-width="1.2" opacity="{op:.2f}"/>')
        r+=6.5; i+=1
    # un surco resaltado en vino = el "hilo" del mix
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{R*0.74:.0f}" fill="none" stroke="{WINE}" stroke-width="2.5" opacity="0.55"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#sheen)"/>')
    # etiqueta central vino
    s.append(f'<circle cx="{cx}" cy="{cy}" r="212" fill="none" stroke="#0c0a07" stroke-width="6"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="205" fill="url(#lbl)"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="205" fill="none" stroke="#7d1f2e" stroke-width="2"/>')
    s.append(f'<path id="atop" d="M {cx-160} {cy} A 160 160 0 0 1 {cx+160} {cy}" fill="none"/>')
    s.append('<text font-family="Courier New, monospace" font-size="23" letter-spacing="8" '
             f'fill="{BONE}" opacity="0.9"><textPath href="#atop" startOffset="50%" text-anchor="middle">CONTINUOUS MIX</textPath></text>')
    s.append(f'<text x="{cx}" y="{cy-6}" font-family="Georgia, serif" font-weight="bold" font-size="82" '
             f'letter-spacing="3" fill="{BONE}" text-anchor="middle">THE SET</text>')
    s.append(f'<text x="{cx}" y="{cy+44}" font-family="Courier New, monospace" font-size="22" letter-spacing="4" '
             f'fill="{BONE}" opacity="0.85" text-anchor="middle">{n_tracks} TRACKS · {mm}</text>')
    s.append(f'<path id="abot" d="M {cx-160} {cy} A 160 160 0 0 0 {cx+160} {cy}" fill="none"/>')
    s.append('<text font-family="Courier New, monospace" font-size="21" letter-spacing="6" '
             f'fill="{BONE}" opacity="0.7"><textPath href="#abot" startOffset="50%" text-anchor="middle">AMR — MORELIA</textPath></text>')
    # hoyo
    s.append(f'<circle cx="{cx}" cy="{cy}" r="17" fill="{BONE}"/>')
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
