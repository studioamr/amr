#!/usr/bin/env python3
# AMR — TULUM: set original sintetizado siguiendo la estructura del Boiler Room Tulum 2015 de Solomun.
# 16 secciones · ~112 min · 121 BPM constante · beats alineados en las transiciones (XF = 4 bars exactos).
# Deep house: bajos rodantes funky + stabs cálidos + pianos + chops vocales + pico emocional a los 2/3.
import os, subprocess, json, wave, sys
import numpy as np, imageio_ffmpeg
import make_tracks as mt, make_set

SR = mt.SR
FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(HERE, '_tulum_tmp')
OUT_WAV = os.path.join(HERE, 'masters', 'amr-tulum.wav')
M4A = os.path.join(HERE, 'audio', 'amr-tulum.m4a')

BPM = 121.0
SPB = round(SR * 240.0 / BPM)          # samples por compás (bar) — entero para no derivar
S16 = SPB / 16.0                        # samples por 1/16
XF_BARS = 4
XF_S = XF_BARS * SPB / SR              # crossfade exacto de 4 compases → beats alineados
rng = np.random.default_rng(2015)

MIN = [0,2,3,5,7,8,10]; MAJ = [0,2,4,5,7,9,11]
def note(root, deg, octv=0, mode=MIN):
    return root * 2**(octv + mode[deg % 7]/12.0 + (deg//7))

# ---------- kit house ----------
def house_kick(amp=0.62):
    n = int(0.30*SR); t = np.arange(n)/SR
    f = 44 + 116*np.exp(-t*38)
    ph = 2*np.pi*np.cumsum(f)/SR
    x = np.sin(ph)*np.exp(-t*10)*amp
    click = mt.highpass(rng.standard_normal(int(0.008*SR)), 2500)*np.exp(-np.linspace(0,1,int(0.008*SR))*10)*0.15
    x[:len(click)] += click
    return x

def clap(amp=0.30):
    n = int(0.28*SR); x = np.zeros(n)
    for d in (0, 0.010, 0.021):
        i = int(d*SR); m = int(0.012*SR)
        x[i:i+m] += rng.standard_normal(m)*np.exp(-np.linspace(0,1,m)*5)
    tail = rng.standard_normal(n)*np.exp(-np.linspace(0,1,n)*11)*0.5
    x = mt.bandpass(x+tail, 1300, q=0.9)
    return x*amp/ (np.abs(x).max()+1e-9) * amp * 3

def bass_note(f, dur_s, amp=0.34):
    n = int(dur_s*SR); t = np.arange(n)/SR
    saw = 2*((f*t) % 1) - 1
    sub = np.sin(2*np.pi*f*t)
    x = mt.lowpass(0.6*saw + 0.7*sub, 320)
    e = np.minimum(np.linspace(0,1,n)*60, 1)*np.exp(-np.linspace(0,1,n)*3.2)
    return x*e*amp

def chord_stab(freqs, dur_s=0.30, amp=0.15, bright=1300):
    n = int(dur_s*SR); t = np.arange(n)/SR
    L = np.zeros(n); R = np.zeros(n)
    for i, f in enumerate(freqs):
        dt = (6 if i % 2 else -6)/1200
        L += 2*((f*(1+dt)*t) % 1) - 1
        R += 2*((f*(1-dt)*t) % 1) - 1
    x = np.vstack([L, R])/len(freqs)
    x = mt.lowpass(x, bright)
    e = np.minimum(np.linspace(0,1,n)*90, 1)*np.exp(-np.linspace(0,1,n)*7)
    return x*e*amp

def piano_chord(freqs, dur_s=0.9, amp=0.16):
    n = int(dur_s*SR)
    out = np.zeros((2, n))
    for i, f in enumerate(freqs):
        p = mt.mk_pluck(f, dur=dur_s, amp=amp/len(freqs)*1.6, bright=2400)
        pan = 0.85 + 0.3*(i/(len(freqs)-1) if len(freqs) > 1 else 0.5)
        m = min(n, len(p))
        out[0, :m] += p[:m]*pan; out[1, :m] += p[:m]*(2-pan)
    return out

def vocal_stab(f, dur_s=0.32, amp=0.11):
    """Chop 'vocal': saw con formantes (ah) — textura, no palabras."""
    n = int(dur_s*SR); t = np.arange(n)/SR
    saw = 2*((f*t) % 1) - 1
    x = (mt.bandpass(saw, 800, q=4) + 0.8*mt.bandpass(saw, 1150, q=5) + 0.35*mt.bandpass(saw, 2900, q=6))
    e = np.minimum(np.linspace(0,1,n)*50, 1)*np.exp(-np.linspace(0,1,n)*6)
    return x*e*amp

def noise_riser(bars, amp=0.05):
    n = int(bars*SPB); x = rng.standard_normal(n)
    out = np.zeros(n); blocks = 28
    for b in range(blocks):
        a, bb = b*n//blocks, (b+1)*n//blocks
        fc = 300 + 5000*(b/blocks)**2
        out[a:bb] = mt.bandpass(x[a:bb], fc, 1.2)
    return mt.st(out*np.linspace(0.05,1,n)**1.6*amp)

# ---------- sección (un "track" del set) ----------
def render_section(cfg):
    bars = cfg['bars']; N = bars*SPB
    root = cfg['root']; mode = MAJ if cfg.get('maj') else MIN
    mix = np.zeros((2, N))
    kick_s = house_kick(); clap_s = clap(); chat = mt.mk_hat(False); ohat = mt.mk_hat(True)
    # patrones
    bass_pat = cfg['bass']                     # [(step, deg, oct, dur16)]
    chord_freqs = [note(root, d, o, mode) for d, o in cfg['chord']]
    stab_s = chord_stab(chord_freqs, bright=cfg.get('bright', 1300))
    piano_s = piano_chord([note(root, d, o+1, mode) for d, o in cfg['chord']]) if cfg.get('piano') else None
    arp = cfg.get('arp')                       # [(step, deg, oct)] por frase de 2 bars
    kick_times = []
    bd0, bd1 = cfg.get('bd', (int(bars*0.58), int(bars*0.58)+16))   # breakdown 16 bars
    intro = cfg.get('intro', 0); outro = cfg.get('outro', 0)
    arp_канvas = np.zeros((2, N)); voc = np.zeros((2, N)); pno = np.zeros((2, N))
    for bar in range(bars):
        t0 = bar*SPB
        in_bd = bd0 <= bar < bd1
        sparse = bar < intro or bar >= bars-outro
        for step in range(16):
            ts = (t0 + step*S16)/SR
            # drums
            if not in_bd and not (sparse and cfg.get('intro_nokick')):
                if step % 4 == 0:
                    mt.place(mix, kick_s, ts); kick_times.append(ts)
                if cfg.get('clap') and step in (4, 12) and not sparse:
                    mt.place(mix, mt.st(clap_s), ts)
                if step % 4 == 2:
                    mt.place(mix, mt.st(ohat)*0.5, ts)
                if step % 2 == 1 and rng.random() < cfg.get('hat', 0.7):
                    pan = 0.85 if (step//2) % 2 else 1.15
                    mt.place(mix, np.vstack([chat*pan, chat*(2-pan)])*0.55, ts)
            # bass (sigue en breakdown sólo si melódico)
            if not sparse and (not in_bd):
                for (st_, dg, oc, d16) in bass_pat:
                    if st_ == step:
                        mt.place(mix, mt.st(bass_note(note(root, dg, oc, mode), d16*S16/SR)), ts)
            # chords
            if not sparse and step in cfg.get('cpat', (4, 12)):
                if not in_bd or cfg.get('bd_chords'):
                    mt.place(mix, stab_s, ts)
            # piano (anthem): en drop, cada bar steps 0,3,6,10
            if piano_s is not None and not in_bd and not sparse and step in (0, 3, 6, 10) and bar % 2 == 0:
                mt.place(pno, piano_s, ts)
            # vocal chop
            if cfg.get('vocal') and not sparse and bar % 4 in (1, 3) and step in (6, 14):
                f = note(root, rng.choice([0, 2, 4]), 2, mode)
                mt.place(voc, mt.st(vocal_stab(f)), ts)
        # arp/melodía: frases de 2 bars, activa en breakdown y drop
        if arp and (in_bd or (bd1 <= bar < min(bars-outro, bd1+48))):
            ph = bar % 2
            for (st_, dg, oc) in arp:
                if st_ // 16 == ph:
                    f = note(root, dg, oc, mode)
                    g = mt.mk_pluck(f, dur=0.4, amp=0.15, bright=2000)
                    mt.place(arp_канvas, mt.st(g), (t0 + (st_ % 16)*S16)/SR)
    # eco y espacio para melodía/vocal
    beat = 60.0/BPM
    arp_w = arp_канvas + mt.fbdelay(arp_канvas, beat*0.75, fb=0.45, damp=2400)*0.6
    mix += arp_w + mt.reverb(arp_w, 1.2, mix=0.35)
    if cfg.get('vocal'):
        vw = voc + mt.fbdelay(voc, beat*0.75, fb=0.4, damp=2000)*0.5
        mix += vw + mt.reverb(vw, 1.4, mix=0.4)
    mix += pno
    # pad de fondo + duck por kick
    pad = mt.mk_pad(chord_freqs, N, lfo_hz=0.05, dark=350, bright=1000, amp=cfg.get('pad', 0.045))
    duck = mt.duck_env(N, kick_times, depth=0.5, rec=0.32)
    mix += pad*duck
    mix[0] *= duck**0.3; mix[1] *= duck**0.3
    # riser hacia el drop
    if bd1 < bars:
        r = noise_riser(4)
        mt.place(mix, r, (bd1-4)*SPB/SR)
    # bordes: primera sección fade-in propio, última fade-out
    if cfg.get('first'):
        fi = 2*SPB; mix[:, :fi] *= np.linspace(0, 1, fi)
    if cfg.get('last'):
        fo = 8*SPB; mix[:, -fo:] *= np.linspace(1, 0.0, fo)
    return mt.softclip(mix, 1.06)

# ---------- el arco del Tulum 2015 (16 secciones ≈ 112 min) ----------
A2=110.0; C2=65.41; D2=73.42; E2=82.41; F2=87.31; G2=98.0
B1 = [(0,0,0,3),(6,0,0,2),(8,0,1,2),(11,4,0,2),(14,0,0,2)]           # roller clásico
B2 = [(0,0,0,2),(4,0,0,2),(7,4,0,2),(10,0,1,2),(12,5,0,2),(14,4,0,1)] # funky sincopado
B3 = [(0,0,0,4),(8,3,0,3),(12,4,0,3)]                                 # profundo lento
CH1=[(0,0),(2,0),(4,0),(6,0)]      # 7ma en bloque
CH2=[(0,0),(2,0),(4,0),(1,1)]      # con 9na arriba
ARP_EUF=[(0,4,2),(2,2,2),(4,0,2),(6,4,2),(8,5,2),(10,4,2),(12,2,2),(14,0,2),(16,4,2),(18,7,2),(20,5,2),(22,4,2),(24,2,2),(28,0,2)]
ARP_EMO=[(0,0,2),(3,2,2),(6,4,2),(10,7,2),(16,5,2),(19,4,2),(22,2,2),(26,0,2)]
SECTIONS = [
 dict(name='LLEGADA',    bars=200, root=A2, bass=B3, chord=CH1, cpat=(4,12), hat=0.5, pad=0.06, intro=16, intro_nokick=True, first=True),
 dict(name='ATLAS',      bars=216, root=F2, maj=True, bass=B1, chord=CH2, arp=ARP_EMO, hat=0.6, clap=True),
 dict(name='GAMA',       bars=216, root=G2, bass=B1, chord=CH1, cpat=(2,10), hat=0.7, bright=1000),
 dict(name='LUNES',      bars=216, root=C2, bass=B3, chord=CH1, hat=0.6, vocal=True, bright=900),
 dict(name='METRONOMO',  bars=216, root=E2, bass=B2, chord=CH2, clap=True, hat=0.8),
 dict(name='TARDE',      bars=216, root=A2, bass=B1, chord=CH2, arp=ARP_EUF, clap=True, hat=0.7, bd_chords=True),
 dict(name='VOCES',      bars=216, root=D2, bass=B2, chord=CH1, vocal=True, clap=True, hat=0.8),
 dict(name='SODA',       bars=216, root=F2, maj=True, bass=B2, chord=CH2, clap=True, hat=0.85, bright=1600),
 dict(name='ADIOS',      bars=216, root=G2, bass=B3, chord=CH1, vocal=True, hat=0.55, pad=0.055),
 dict(name='SINCRONIA',  bars=232, root=A2, bass=B1, chord=CH2, arp=ARP_EUF, clap=True, hat=0.75, bd=(120,140), bd_chords=True, piano=True),
 dict(name='PERDIDOS',   bars=216, root=A2, bass=B2, chord=CH1, vocal=True, clap=True, hat=0.8),
 dict(name='ADORAR',     bars=216, root=F2, maj=True, bass=B1, chord=CH2, arp=ARP_EMO, hat=0.6, pad=0.055),
 dict(name='PALMAS',     bars=216, root=D2, bass=B2, chord=CH2, clap=True, hat=0.9),
 dict(name='PIANO VIEJO',bars=216, root=C2, maj=True, bass=B1, chord=CH2, piano=True, clap=True, hat=0.8),
 dict(name='CALIENTE',   bars=216, root=E2, bass=B2, chord=CH1, vocal=True, clap=True, hat=0.85),
 dict(name='AMANECER',   bars=200, root=A2, bass=B3, chord=CH1, hat=0.4, pad=0.065, outro=24, last=True),
]

if __name__ == '__main__':
    FINAL = '--finalize' in sys.argv
    os.makedirs(SCR, exist_ok=True); os.makedirs(os.path.join(HERE,'masters'), exist_ok=True)
    paths = []
    for i, cfg in enumerate(SECTIONS):
        p = os.path.join(SCR, f'{i:02d}.wav'); paths.append(p)
        if FINAL and os.path.exists(p): continue
        if not FINAL or not os.path.exists(p):
            print(f'  [{i+1:2d}/16] {cfg["name"]} ({cfg["bars"]} bars)…', flush=True)
            x = render_section(cfg)
            x = x/(np.max(np.abs(x)) or 1)*0.9
            with wave.open(p, 'w') as wf:
                wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
                wf.writeframes((x.T*32767).astype('<i2').tobytes())
    # encadenar con XF exacto de 4 bars (beats alineados) + master
    n = len(paths); parts = []
    for i in range(n): parts.append(f'[{i}:a]aformat=channel_layouts=stereo[a{i}]')
    prev = 'a0'
    for i in range(1, n):
        out = 'premix' if i == n-1 else f'x{i}'
        parts.append(f'[{prev}][a{i}]acrossfade=d={XF_S:.6f}:c1=tri:c2=tri[{out}]'); prev = out
    master = ("highpass=f=24,equalizer=f=55:t=q:w=0.9:g=1.6,equalizer=f=220:t=q:w=1.4:g=-1.8,"
              "equalizer=f=3200:t=q:w=1.2:g=0.8,equalizer=f=9000:t=h:w=0.7:g=2,"
              "acompressor=threshold=-15dB:ratio=2.2:attack=22:release=250:makeup=2.5,"
              "loudnorm=I=-10.5:TP=-1.0:LRA=11,alimiter=level_out=0.97:limit=0.97")
    parts.append(f'[premix]{master}[m]')
    cmd = [FF, '-y']
    for p in paths: cmd += ['-i', p]
    cmd += ['-filter_complex', ';'.join(parts), '-map', '[m]', '-c:a', 'pcm_s16le', OUT_WAV]
    print('Encadenando (beats alineados) + master…', flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0: print(r.stderr[-3000:]); raise SystemExit(1)
    import make_sesion
    secs = int(make_sesion.dur_of(OUT_WAV))
    br = max(80, min(128, int(93*1024*1024*8/secs/1000)))
    subprocess.run([FF, '-y', '-i', OUT_WAV, '-c:a', 'aac', '-b:a', f'{br}k', M4A], capture_output=True)
    print(f'WAV {secs//60}:{secs%60:02d} · m4a {br}k = {os.path.getsize(M4A)//1024//1024} MB', flush=True)
    # offsets/peaks/meta/portada
    bar_s = SPB/SR
    off = [0.0]
    for i in range(1, n):
        off.append(round(off[-1] + SECTIONS[i-1]['bars']*bar_s - XF_S, 1))
    raw = subprocess.run([FF,'-v','quiet','-i',OUT_WAV,'-ac','1','-ar','2000','-f','f32le','-'], capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4'); W = 720; seg = max(1, len(x)//W)
    pk = np.abs(x[:seg*W]).reshape(W, seg).max(axis=1); pk = (pk/(pk.max() or 1)).round(3).tolist()
    titles = [s['name'] for s in SECTIONS]
    meta = dict(id='amr-tulum', title='TULUM', kicker='IN SYNC · MMXV', tracks=n, dur=secs,
                titles=titles, offsets=off, file='audio/amr-tulum.m4a', art='art/amr-tulum.png',
                edition=15, peaks=pk, color='blue')
    open(os.path.join(HERE, 'tulum.js'), 'w').write('window.AMR_TUL='+json.dumps(meta, ensure_ascii=False)+';\n')
    make_set.make_cover(pk, n, secs, title='TULUM', kicker='IN SYNC · MMXV', out='amr-tulum',
                        accent='#2E6FB0', accent_lt='#5B9BD5', accent_dk='#1a4a7a')
    print(f'tulum.js + portada OK — {secs//60}:{secs%60:02d}', flush=True)
