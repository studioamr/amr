#!/usr/bin/env python3
# AMR — MINIMAL SET sintetizado desde 0: gotas de agua, mar (olas), eco/reverb.
# Dub/ambient minimal de ~1h. Corre con /usr/local/bin/python3 (numpy). Reutiliza el DSP de make_tracks.
import os, subprocess, json, wave, math
import numpy as np, imageio_ffmpeg
import make_tracks as mt, make_set

SR = mt.SR
FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(HERE, '_minimal_tmp')
OUT_WAV = os.path.join(HERE, 'masters', 'amr-minimal.wav')
M4A = os.path.join(HERE, 'audio', 'amr-minimal.m4a')
rng = np.random.default_rng(7)

# ---------- texturas de agua ----------
def brown(n):
    w = rng.standard_normal(n); b = np.cumsum(w); b -= np.linspace(b[0], b[-1], n)  # quita deriva
    return b / (np.abs(b).max() + 1e-9)

def droplet(f0, dur=0.34, amp=0.32):
    """Gota: 'ploc' con pitch que sube (burbuja) + decay corto."""
    n = int(dur*SR); t = np.arange(n)/SR
    freq = f0*(1 + 1.3*(1-np.exp(-t*9)))
    ph = 2*np.pi*np.cumsum(freq)/SR
    x = np.sin(ph)*np.exp(-t*13)*amp
    return mt.bandpass(x, f0*1.4, q=3)

def sea(N, amp=0.13):
    """Mar: rumor grave (brown lowpass) + espuma (rompientes periódicas de ruido agudo), marea lenta."""
    t = np.arange(N)/SR
    lowL = mt.lowpass(brown(N), 480); lowR = mt.lowpass(brown(N), 480)
    tide = 0.45 + 0.35*np.sin(2*np.pi*0.035*t + 1)
    foam = np.zeros(N)
    p = 9.5
    k = 0
    while k*p*SR < N:
        i = int((k*p + rng.uniform(-1,1))*SR)
        if i < 0: k += 1; continue
        dl = int(3.2*SR); e = np.zeros(dl); a = int(0.6*SR)
        e[:a] = np.linspace(0, 1, a)**1.5
        e[a:] = np.exp(-np.linspace(0, 1, dl-a)*3.2)
        j = min(N, i+dl); foam[i:j] += e[:j-i]
        k += 1
    hi = mt.highpass(rng.standard_normal(N), 1400)
    L = (lowL*tide + hi*foam*0.55)*amp
    R = (lowR*tide + mt.highpass(rng.standard_normal(N),1400)*foam*0.55)*amp
    return np.vstack([L, R])

# ---------- una sección del set (un "corte") ----------
def section(dur_s, chord, bpm, kick_amp, drop_dens, pad_amp=0.05):
    N = int(dur_s*SR); mix = np.zeros((2, N))
    beat = 60.0/bpm; s16 = beat/4
    # mar de fondo
    mix += sea(N, amp=0.12)
    # gotas: rítmicas (en contratiempos) + dispersas, con delay pingpong + reverb = ECO
    drops = np.zeros((2, N))
    scale = [f*m for f in chord for m in (1, 2)]
    tt = 0.0
    while tt < dur_s-0.5:
        step = int(round(tt/s16)) % 16
        if step in (2, 6, 10, 14) and rng.random() < drop_dens:
            f = rng.choice(scale)*rng.choice([1, 1.5, 2])
            g = droplet(f*200 if f < 20 else f, amp=0.28)
            pan = rng.uniform(0.3, 1.0)
            mt.place(drops, np.vstack([g*pan, g*(1.3-pan)]), tt)
        tt += s16
    # gotas ambientales dispersas
    for _ in range(int(dur_s*drop_dens*1.4)):
        f = rng.uniform(500, 2200); g = droplet(f, dur=rng.uniform(0.25,0.5), amp=0.18)
        mt.place(drops, mt.st(g), rng.uniform(0, dur_s-0.6))
    drops = drops + mt.fbdelay(drops, beat*0.75, fb=0.55, damp=2200)*0.7
    mix += drops + mt.reverb(drops, 2.0, damp=2600, mix=0.85)
    # pad deep que respira
    mix += mt.mk_pad(chord, N, lfo_hz=0.04, dark=300, bright=900, amp=pad_amp)
    # drone grave
    mix += mt.mk_drone(chord[0]/2, N, amp=0.16)
    # groove minimal (si kick_amp>0): kick 4/4 + sub + hat tenue
    if kick_amp > 0:
        kick = mt.mk_kick(f0=120, f1=44, amp=kick_amp, dur=0.4)
        hatc = mt.mk_hat(False)
        sub = mt.mk_bass(chord[0], dur=beat*0.9, amp=0.26)
        bars = int(dur_s/(4*beat))
        for bar in range(bars):
            for step in range(16):
                t0 = bar*4*beat + step*s16
                if step % 4 == 0: mt.place(mix, kick, t0)
                if step % 4 == 2 and rng.random() < 0.6:
                    pan = 0.9 if step % 8 else 1.1
                    mt.place(mix, np.vstack([hatc*pan, hatc*(2-pan)])*0.5, t0)
                if step in (0, 10): mt.place(mix, sub, t0)
    # fades de sección
    fi = int(1.5*SR); fo = int(2.5*SR)
    mix[:, :fi] *= np.linspace(0, 1, fi); mix[:, -fo:] *= np.linspace(1, 0, fo)
    return mt.softclip(mix, 1.05)

# progresión hipnótica (frecuencias de acorde) + arco de energía del set
Am=[110,130.81,164.81]; Dm=[146.83,174.61,110]; F=[87.31,130.81,174.61]
Em=[82.41,123.47,164.81]; C=[130.81,196.0,164.81]
SECTIONS = [   # (nombre, dur_s, chord, bpm, kick_amp, drop_dens, pad_amp)
    ('Bruma',      380, Am, 122, 0.00, 0.35, 0.055),
    ('Marea baja', 400, Em, 122, 0.30, 0.45, 0.05),
    ('Corriente',  420, Dm, 123, 0.42, 0.6,  0.05),
    ('Oleaje',     420, F,  123, 0.50, 0.7,  0.045),
    ('Profundo',   440, Am, 124, 0.52, 0.75, 0.045),
    ('Resaca',     420, C,  123, 0.48, 0.65, 0.05),
    ('Deriva',     420, Dm, 122, 0.38, 0.5,  0.05),
    ('Reflujo',    400, Em, 122, 0.28, 0.4,  0.055),
    ('Calma',      380, Am, 121, 0.00, 0.35, 0.06),
]

if __name__ == '__main__':
    import sys
    os.makedirs(SCR, exist_ok=True); os.makedirs(os.path.join(HERE,'masters'), exist_ok=True)
    XF = 8.0
    seg_paths = []
    for idx, (name, dur, chord, bpm, ka, dd, pa) in enumerate(SECTIONS):
        p = os.path.join(SCR, f'{idx:02d}.wav')
        if '--finalize' not in sys.argv:
            print(f'  sintetizando {name} ({dur//60}:{dur%60:02d})…', flush=True)
            x = section(dur, chord, bpm, ka, dd, pa)
            x = x/ (np.max(np.abs(x)) or 1) * 0.9
            with wave.open(p, 'w') as wf:
                wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
                wf.writeframes((x.T*32767).astype('<i2').tobytes())
        seg_paths.append(p)
    # encadenar secciones con crossfade + master
    n = len(seg_paths); parts = []
    for i in range(n):
        parts.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo[a{i}]')
    prev='a0'
    for i in range(1,n):
        out='premix' if i==n-1 else f'x{i}'
        parts.append(f'[{prev}][a{i}]acrossfade=d={XF}:c1=tri:c2=tri[{out}]'); prev=out
    master=("equalizer=f=55:t=q:w=0.9:g=1.5,equalizer=f=250:t=q:w=1.3:g=-1.5,equalizer=f=8000:t=h:w=0.7:g=1.5,"
            "acompressor=threshold=-18dB:ratio=2:attack=40:release=320:makeup=2,loudnorm=I=-13:TP=-1.0:LRA=12,"
            "alimiter=level_out=0.96:limit=0.96")
    parts.append(f'[premix]{master}[m]')
    cmd=[FF,'-y']
    for p in seg_paths: cmd+=['-i',p]
    cmd+=['-filter_complex',';'.join(parts),'-map','[m]','-c:a','pcm_s16le',OUT_WAV]
    print('Encadenando + master…', flush=True)
    r=subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode!=0: print(r.stderr[-3000:]); raise SystemExit(1)
    secs = int(make_set and __import__('make_sesion').dur_of(OUT_WAV))
    br = max(112, min(160, int(95*1024*1024*8/secs/1000)))
    subprocess.run([FF,'-y','-i',OUT_WAV,'-c:a','aac','-b:a',f'{br}k',M4A], capture_output=True)
    print(f'WAV {secs//60}:{secs%60:02d} · m4a {br}k = {os.path.getsize(M4A)//1024//1024} MB', flush=True)
    # offsets, peaks
    durs = [d for (_,d,_,_,_,_,_) in SECTIONS]
    off=[0.0]
    for i in range(1,len(durs)): off.append(round(max(0, off[-1]+durs[i-1]-XF),1))
    raw=subprocess.run([FF,'-v','quiet','-i',OUT_WAV,'-ac','1','-ar','2000','-f','f32le','-'],capture_output=True).stdout
    x=np.frombuffer(raw,dtype='<f4'); W=720; seg=max(1,len(x)//W)
    pk=np.abs(x[:seg*W]).reshape(W,seg).max(axis=1); pk=(pk/(pk.max() or 1)).round(3).tolist()
    titles=[s[0] for s in SECTIONS]
    meta=dict(id='amr-minimal', title='MINIMAL SET', kicker='GOTAS · MAR · ECO', tracks=len(titles),
              dur=secs, titles=titles, offsets=off, file='audio/amr-minimal.m4a', art='art/amr-minimal.png',
              edition=10, peaks=pk, color='blue')
    open(os.path.join(HERE,'minimal.js'),'w').write('window.AMR_MIN='+json.dumps(meta, ensure_ascii=False)+';\n')
    make_set.make_cover(pk, len(titles), secs, title='MINIMAL SET', kicker='GOTAS · MAR · ECO', out='amr-minimal',
                        accent='#2E6FB0', accent_lt='#5B9BD5', accent_dk='#1a4a7a')
    print(f'minimal.js + portada azul OK — {secs//60}:{secs%60:02d}', flush=True)
