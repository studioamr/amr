#!/usr/bin/env python3
# AMR — GUERRERO: set original 0→100 estilo Maccabi House (Adam Ten b2b Mita Gami / Mayan Warrior).
# MOTOR NUEVO — nada de la paleta DELIRIO. La receta investigada:
#   · bajo protagonista 3 capas: saw -2oct con VIBRATO LFO a 1/8 del tempo + acid square PWM + drive asimétrico + bitcrush
#   · filtro resonante tipo Moog con movimiento · kick suave sin click · percusión orgánica humanizada
#   · toms sincopados offbeat · hats "acústicos" con micro-timing · cowbell/conga/shaker juguetones
#   · leads Minimoog (3 osc, portamento) espejando el bajo · vocales gateadas breves
#   · TENSIÓN DE SEMITONOS simultáneos · tonalidades MAYORES · groove constante, cero drops épicos
# 12 rolas nuevas · 123 BPM · ~58 min · transiciones beat-aligned (4 bars)
import os, subprocess, json, wave, sys
import numpy as np, imageio_ffmpeg
import make_tracks as mt          # solo DSP genérico: filtros/place/delay/reverb/softclip

SR = mt.SR
FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(HERE, '_warrior_tmp')
OUT_WAV = os.path.join(HERE, 'masters', 'amr-guerrero.wav')
M4A = os.path.join(HERE, 'audio', 'amr-guerrero.m4a')

BPM = 123.0
SPB = round(SR * 240.0 / BPM)          # samples por compás — entero, no deriva
S16 = SPB / 16.0
BEAT = 60.0 / BPM
XF_BARS = 4
XF_S = XF_BARS * SPB / SR
rng = np.random.default_rng(777)

MIN = [0, 2, 3, 5, 7, 8, 10]; MAJ = [0, 2, 4, 5, 7, 9, 11]
def note(root, deg, octv=0, mode=MIN):
    return root * 2 ** (octv + mode[deg % 7] / 12.0 + (deg // 7))

def st(y, pan=1.0): return np.vstack([y * pan, y * (2 - pan)])

# ---------- procesado análogo (el anti-videojuego) ----------
def drive(x, k=1.6):
    """saturación asimétrica: calidez de circuito, no de chip."""
    return np.tanh(k * x + 0.13 * x * np.abs(x)) / np.tanh(k)

def crush(x, srr=5, amt=0.22):
    """bitcrush sutil por sample-hold — el grano de alta frecuencia Maccabi."""
    held = np.repeat(x[::srr], srr)[:len(x)]
    return x * (1 - amt) + held * amt

def reslp(x, fc, res=0.55):
    """lowpass resonante tipo Moog: LP + pico resonante en el corte."""
    return mt.lowpass(x, fc) + res * mt.bandpass(x, fc, q=5.5)

# ---------- percusión orgánica ----------
def kick_soft(amp=0.60):
    n = int(0.34 * SR); t = np.arange(n) / SR
    f = 43 + 78 * np.exp(-t * 30)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8.5)
    return mt.lowpass(x, 1600) * amp

def tom(f0=120, amp=0.20):
    n = int(0.15 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.4 * np.exp(-t * 50))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x = mt.highpass(x, 70) * np.exp(-t / 0.055)
    a = int(0.002 * SR); x[:a] *= np.linspace(0, 1, a)
    return x * amp

def hat_ac(dec=0.020, amp=0.20, tone=5200):
    """hat 'acústico': dos bandas + shimmer, decay variable por golpe."""
    n = int(0.07 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    y = mt.bandpass(x, tone, 1.4) + 0.35 * mt.bandpass(x, tone * 1.55, 2.2)
    return y * np.exp(-t / dec) * amp

def shaker_s(amp=0.055):
    n = int(0.055 * SR); t = np.arange(n) / SR
    y = mt.highpass(rng.standard_normal(n), 7500)
    e = np.exp(-t / 0.020); a = int(0.008 * SR); e[:a] *= np.linspace(0, 1, a)
    return y * e * amp

def cowbell(amp=0.13):
    n = int(0.11 * SR); t = np.arange(n) / SR
    y = np.sign(np.sin(2 * np.pi * 540 * t)) * 0.6 + np.sign(np.sin(2 * np.pi * 815 * t)) * 0.4
    y = mt.bandpass(y, 950, q=1.6) * np.exp(-t / 0.035)
    return y * amp

def conga_t(f=210, amp=0.15):
    n = int(0.12 * SR); t = np.arange(n) / SR
    ft = f * (1 + 0.3 * np.exp(-t * 60))
    y = np.sin(2 * np.pi * np.cumsum(ft) / SR) * np.exp(-t / 0.045)
    a = int(0.002 * SR); y[:a] *= np.linspace(0, 1, a)
    return mt.lowpass(y, 2600) * amp

def clap_soft(amp=0.20):
    n = int(0.20 * SR); x = np.zeros(n)
    for d in (0, 0.009, 0.019):
        i = int(d * SR); m = int(0.011 * SR)
        x[i:i + m] += rng.standard_normal(m) * np.exp(-np.linspace(0, 1, m) * 5)
    x += rng.standard_normal(n) * np.exp(-np.linspace(0, 1, n) * 13) * 0.4
    x = mt.bandpass(x, 1250, q=1.0)
    return x / (np.abs(x).max() + 1e-9) * amp

# ---------- EL BAJO (protagonista, 3 capas) ----------
def bass_maccabi(f, dur_s, amp=0.58, vib=0.011, acid_fc=900, acid_amt=0.5, crush_amt=0.12):
    n = int(dur_s * SR); t = np.arange(n) / SR
    lfo = 1 + vib * np.sin(2 * np.pi * t / (BEAT / 2) + 0.6)      # vibrato LFO a 1/8 — LA firma
    ph = 2 * np.pi * np.cumsum(f * lfo) / SR
    # capa 1: saw -1 oct gruesa (aditiva con rolloff cálido)
    saw = np.zeros(n)
    for k in range(1, 11):
        saw += np.sin(k * ph) / k ** 1.15
    # capa 2: sub -2 oct
    sub = np.sin(ph / 2) * 0.8
    # capa 3: acid square con PWM lento
    pw = 0.5 + 0.22 * np.sin(2 * np.pi * t / (BEAT * 4))
    acid = np.sign(np.sin(ph) - (2 * pw - 1) * 0.6)
    acid = reslp(acid, acid_fc, res=0.8) * acid_amt
    x = reslp(saw * 0.7 + acid, acid_fc * 1.6, res=0.5) + sub
    x = drive(x, 1.7)
    x = crush(x, srr=5, amt=crush_amt)
    e = np.minimum(np.linspace(0, 1, n) * 70, 1) * np.exp(-np.linspace(0, 1, n) * 2.6)
    return mt.lowpass(x, 2000) * e * amp / 2.2

# ---------- lead Minimoog (espeja el bajo, portamento) ----------
def moog_lead(freqs_durs, amp=0.14, fc=2100):
    """freqs_durs: [(f, dur_s)] — una frase con glide entre notas."""
    total = sum(d for _, d in freqs_durs)
    n = int(total * SR); t = np.arange(n) / SR
    fcur = np.zeros(n); pos = 0; prev = freqs_durs[0][0]
    for f, d in freqs_durs:
        m = int(d * SR); g = min(int(0.045 * SR), m // 3)
        fcur[pos:pos + g] = np.linspace(prev, f, g)
        fcur[pos + g:pos + m] = f
        prev = f; pos += m
    fcur[pos:] = prev
    ph = 2 * np.pi * np.cumsum(fcur) / SR
    y = np.zeros(n)
    for det, w in ((1.0, 1.0), (1.004, 0.8)):
        for k in range(1, 9):
            y += np.sin(k * ph * det) / k * w
    y += np.sign(np.sin(ph / 2)) * 0.35          # square -1 oct
    y = drive(reslp(y, fc, 0.6), 1.5)
    e = np.ones(n); a = int(0.01 * SR); r = int(min(0.12 * SR, n // 4))
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    return st(y * e * amp / 3.2)

# ---------- vocal juguetona gateada ----------
def voc_chop(f, dur_s=0.16, amp=0.12, vw='ah'):
    F = {'ah': (820, 1250, 2900), 'oh': (470, 850, 2700), 'eh': (620, 1900, 2650)}[vw]
    n = int(dur_s * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    src = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.33 * np.sin(3 * ph) + 0.22 * np.sin(4 * ph) + 0.15 * np.sin(5 * ph)
    v = mt.bandpass(src, F[0], 1.2) + 0.7 * mt.bandpass(src, F[1], 1.3) + 0.3 * mt.bandpass(src, F[2], 1.5)
    e = np.minimum(np.linspace(0, 1, n) * 60, 1) * np.exp(-np.linspace(0, 1, n) * 7)
    return drive(v, 1.3) * e * amp

# ---------- stab de tensión (semitonos simultáneos) ----------
def tension_stab(root, amp=0.13):
    n = int(0.24 * SR); t = np.arange(n) / SR
    f1 = root * 4; f2 = f1 * 2 ** (1 / 12.0)          # ¡semitono simultáneo!
    y = np.zeros(n)
    for f, w in ((f1, 1.0), (f2, 0.85)):
        for k in range(1, 7):
            y += np.sin(2 * np.pi * k * f * t + rng.uniform(0, 6)) / k * w
    y = drive(reslp(y, 1800, 0.7), 1.6) * np.exp(-t / 0.07)
    a = int(0.002 * SR); y[:a] *= np.linspace(0, 1, a)
    return st(y * amp / 2.5)

def riser_org(bars, amp=0.045):
    n = int(bars * SPB); x = rng.standard_normal(n)
    out = np.zeros(n)
    for b in range(24):
        a, bb = b * n // 24, (b + 1) * n // 24
        out[a:bb] = mt.bandpass(x[a:bb], 400 + 3800 * (b / 24) ** 2, 1.3)
    return st(out * np.linspace(0.05, 1, n) ** 1.7 * amp)

# ---------- una sección (una rola del set) ----------
def render_section(cfg):
    bars = cfg['bars']; N = bars * SPB
    root = cfg['root']; mode = MAJ if cfg.get('maj') else MIN
    mix = np.zeros((2, N)); kbuf = np.zeros((2, N))
    kick_s = kick_soft()
    toms = [tom(118, 0.17), tom(96, 0.15), tom(150, 0.13)]
    congas = [conga_t(215, 0.13), conga_t(160, 0.11)]
    cow = cowbell(); clp = clap_soft(); shk = shaker_s()
    bass_pat = cfg['bass']
    acid_fc = cfg.get('acid_fc', 900)
    kick_times = []
    br0, br1 = cfg.get('br', (int(bars * 0.55), int(bars * 0.55) + 8))     # respiro corto (no breakdown épico)
    intro = cfg.get('intro', 8); outro = cfg.get('outro', 0)
    # caché de notas de bajo por (deg, oct, dur)
    bcache = {}
    lead_phr = cfg.get('lead')          # [(deg, oct, dur_beats)] — frase que espeja el bajo
    voc = np.zeros((2, N)); leads = np.zeros((2, N))
    for bar in range(bars):
        t0 = bar * SPB
        in_br = br0 <= bar < br1
        sparse = bar < intro or bar >= bars - outro
        fc_now = acid_fc * (1.0 + 0.5 * min(1.0, bar / max(1, bars * 0.6)))   # el filtro se abre con la sección
        for step in range(16):
            ts = (t0 + step * S16) / SR
            hum = rng.uniform(-0.004, 0.004)                                   # micro-timing humano
            # kick suave 4/4 (+ ghost en el 'and' del 2)
            if not in_br:
                if step % 4 == 0:
                    mt.place(kbuf, st(kick_s), ts); kick_times.append(ts)
                if step == 6 and cfg.get('ghost', True):
                    mt.place(kbuf, st(kick_s * 0.28), ts)
            # tom loop sincopado (la marca orgánica)
            if not sparse and step in (3, 7, 11, 14):
                ti = (bar + step) % 3
                mt.place(mix, st(toms[ti] * rng.uniform(0.6, 1.0), 0.9 if step % 2 else 1.1), ts + hum)
            # hats acústicos: offbeats + fantasmas
            if not sparse:
                if step % 4 == 2:
                    mt.place(mix, st(hat_ac(rng.uniform(0.03, 0.05), 0.09), 1.06), ts + 0.006)
                elif step % 2 == 1 and rng.random() < cfg.get('hat', 0.75):
                    mt.place(mix, st(hat_ac(rng.uniform(0.012, 0.02), rng.uniform(0.03, 0.055)), 0.94), ts + hum)
            # shaker 1/8 con acento
            if not sparse and step % 2 == 0 and cfg.get('shaker', True):
                mt.place(mix, st(shk * (1.0 if step % 8 == 4 else 0.6), 1.1), ts + 0.008)
            # cowbell juguetón (esporádico)
            if cfg.get('cow') and not sparse and bar % 4 == 2 and step in (7, 13):
                mt.place(mix, st(cow * rng.uniform(0.7, 1.0), 0.85), ts + hum)
            # congas
            if not sparse and step in (5, 13) and bar % 2 == 1:
                mt.place(mix, st(congas[step % 2] * rng.uniform(0.7, 1.0), 1.15), ts - 0.014)
            # clap solo en secciones altas
            if cfg.get('clap') and not sparse and not in_br and step in (4, 12):
                mt.place(mix, st(clp), ts)
            # EL BAJO (sigue sonando en el respiro, filtrado más oscuro)
            for (st_, dg, oc, d16) in bass_pat:
                if st_ == step:
                    key = (dg, oc, d16, in_br, round(fc_now / 150))
                    if key not in bcache:
                        f = note(root, dg, oc - 1, mode)
                        bcache[key] = bass_maccabi(f, d16 * S16 / SR * 1.18, amp=0.58,
                                                   acid_fc=(fc_now * 0.45 if in_br else fc_now),
                                                   acid_amt=cfg.get('acid', 0.5),
                                                   crush_amt=cfg.get('crush', 0.2))
                    if not sparse or bar >= intro - 4:
                        mt.place(mix, st(bcache[key]), ts)
            # stab de tensión (semitono) — la psicodelia
            if cfg.get('tension') and not sparse and bar % 8 in (3, 6) and step == 10:
                mt.place(mix, tension_stab(root, 0.12), ts)
            # vocal chop gateada
            if cfg.get('vocal') and not sparse and not in_br and bar % 4 in (1, 3) and step in (7, 15):
                f = note(root, int(rng.choice([0, 2, 4])), 2, mode)
                mt.place(voc, st(voc_chop(f, 0.14, 0.12, str(rng.choice(['ah', 'oh', 'eh'])))), ts + hum)
        # lead Minimoog: frase de 2 bars espejando el bajo, en la 2ª mitad
        if lead_phr and bar % 4 == 0 and br1 <= bar < bars - outro - 8:
            phr = [(note(root, dg, oc + 1, mode), db * BEAT) for dg, oc, db in lead_phr]
            mt.place(leads, moog_lead(phr, amp=0.15, fc=cfg.get('lead_fc', 2100)), t0 / SR)
    # espacio: delay corto juguetón (1/8 dotted) — poco reverb (club seco)
    if cfg.get('vocal'):
        vw = voc + mt.fbdelay(voc, BEAT * 0.75, fb=0.35, damp=2600) * 0.45
        mix += vw + mt.reverb(vw, 0.9, mix=0.22)
    if lead_phr is not None and np.abs(leads).max() > 0:
        lw = leads + mt.fbdelay(leads, BEAT * 0.5, fb=0.3, damp=3000) * 0.35
        mix += lw + mt.reverb(lw, 0.8, mix=0.18)
    # duck global por kick (bombea el groove)
    duck = mt.duck_env(N, kick_times, depth=0.48, rec=0.30)
    mix[0] *= duck ** 0.5; mix[1] *= duck ** 0.5
    mix += kbuf
    # riser orgánico hacia la salida del respiro
    if br1 < bars:
        mt.place(mix, riser_org(3), (br1 - 3) * SPB / SR)
    if cfg.get('first'):
        fi = 2 * SPB; mix[:, :fi] *= np.linspace(0, 1, fi)
    if cfg.get('last'):
        fo = 10 * SPB; mix[:, -fo:] *= np.linspace(1, 0, fo)
    return mt.softclip(mix, 1.06)

# ---------- patrones de bajo (el hook de cada rola) ----------
PB_ROLL  = [(0,0,0,1.5),(3,0,0,1),(6,0,1,1),(8,0,0,1.5),(11,4,0,1),(14,0,1,1)]      # roller con salto de octava
PB_FUNK  = [(0,0,0,1),(2,0,0,.5),(4,0,1,1),(7,0,0,1),(10,3,0,1),(12,0,1,.5),(14,4,0,1)]  # funk sincopado
PB_BOUNCE= [(0,0,0,2),(4,0,1,1),(6,0,0,1),(10,0,1,1),(12,5,0,2)]                     # bounce indie
PB_SWAY  = [(0,0,0,3),(6,0,0,2),(10,4,0,2),(14,3,0,1)]                               # sway profundo
PB_ACID  = [(0,0,0,1),(3,0,0,1),(6,1,0,1),(8,0,0,1),(11,0,1,1),(13,0,0,.5),(14,1,0,1)]  # serpenteo ácido (2ª menor)

LD_MIRROR = [(0,0,1.5),(4,0,1),(7,0,1.5)]           # espeja el roller
LD_FUNKY  = [(4,0,1),(2,0,1),(0,0,2)]               # respuesta descendente
LD_HIGH   = [(7,1,1),(4,1,1),(2,1,2)]               # arriba, para el pico

A2=110.0; C2=65.41; D2=73.42; E2=82.41; F2=87.31; G2=98.0; Eb2=77.78
SECTIONS = [
 dict(name='PORTAL',    bars=144, root=A2,  bass=PB_SWAY,  hat=0.6,  acid=0.35, acid_fc=700,  intro=12, first=True, shaker=False),
 dict(name='MEZCAL',    bars=152, root=G2,  maj=True, bass=PB_BOUNCE, hat=0.7, acid=0.45, acid_fc=850, cow=True),
 dict(name='CACTUS',    bars=152, root=C2,  bass=PB_ACID,  hat=0.75, acid=0.7,  acid_fc=950,  crush=0.28, tension=True),
 dict(name='COYOTE',    bars=152, root=D2,  maj=True, bass=PB_FUNK, hat=0.8, acid=0.5, acid_fc=900, cow=True, vocal=True),
 dict(name='NEON',      bars=152, root=Eb2, maj=True, bass=PB_BOUNCE, hat=0.8, acid=0.55, acid_fc=1000, clap=True, lead=LD_MIRROR),
 dict(name='SERPIENTE', bars=152, root=F2,  bass=PB_ACID,  hat=0.7,  acid=0.75, acid_fc=880,  crush=0.3, tension=True, vocal=True),
 dict(name='ESPEJISMO', bars=144, root=C2,  maj=True, bass=PB_SWAY, hat=0.55, acid=0.3, acid_fc=750, shaker=False, lead=LD_FUNKY, lead_fc=1700),
 dict(name='VOLTAJE',   bars=152, root=A2,  bass=PB_FUNK,  hat=0.85, acid=0.8,  acid_fc=1100, crush=0.32, clap=True, tension=True),
 dict(name='OBSIDIANA', bars=152, root=F2,  bass=PB_ROLL,  hat=0.75, acid=0.6,  acid_fc=900,  vocal=True, tension=True),
 dict(name='FUEGO',     bars=160, root=A2,  maj=True, bass=PB_ROLL, hat=0.9, acid=0.7, acid_fc=1150, clap=True, cow=True, vocal=True, lead=LD_HIGH),
 dict(name='POLVO',     bars=152, root=G2,  maj=True, bass=PB_FUNK, hat=0.7, acid=0.45, acid_fc=900, vocal=True, lead=LD_FUNKY),
 dict(name='ESTRELLAS', bars=144, root=C2,  maj=True, bass=PB_SWAY, hat=0.5, acid=0.3, acid_fc=760, outro=20, last=True, shaker=False),
]

if __name__ == '__main__':
    only = sys.argv[1] if len(sys.argv) > 1 else None
    os.makedirs(SCR, exist_ok=True); os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    paths = []
    for i, cfg in enumerate(SECTIONS):
        p = os.path.join(SCR, f'{i:02d}.wav'); paths.append(p)
        if only and cfg['name'] != only and os.path.exists(p): continue
        if only and cfg['name'] != only: continue
        if not only and os.path.exists(p): continue
        print(f'  [{i+1:2d}/12] {cfg["name"]} ({cfg["bars"]} bars)…', flush=True)
        x = render_section(cfg)
        x = x / (np.max(np.abs(x)) or 1) * 0.9
        with wave.open(p, 'w') as wf:
            wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
            wf.writeframes((x.T * 32767).astype('<i2').tobytes())
    if only: sys.exit(0)
    # encadenar beat-aligned + master club
    n = len(paths); parts = []
    for i in range(n): parts.append(f'[{i}:a]aformat=channel_layouts=stereo[a{i}]')
    prev = 'a0'
    for i in range(1, n):
        out = 'premix' if i == n - 1 else f'x{i}'
        parts.append(f'[{prev}][a{i}]acrossfade=d={XF_S:.6f}:c1=tri:c2=tri[{out}]'); prev = out
    master = ("highpass=f=24,equalizer=f=60:t=q:w=0.9:g=1.8,equalizer=f=300:t=q:w=1.3:g=-1.5,"
              "equalizer=f=4500:t=q:w=1.1:g=0.6,"
              "acompressor=threshold=-14dB:ratio=2.4:attack=18:release=220:makeup=2.5,"
              "loudnorm=I=-10.5:TP=-1.0:LRA=10,alimiter=level_out=0.97:limit=0.97")
    parts.append(f'[premix]{master}[m]')
    cmd = [FF, '-y']
    for p in paths: cmd += ['-i', p]
    cmd += ['-filter_complex', ';'.join(parts), '-map', '[m]', '-c:a', 'pcm_s16le', OUT_WAV]
    print('Encadenando + master…', flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0: print(r.stderr[-2000:]); raise SystemExit(1)
    raw = subprocess.run([FF, '-v', 'quiet', '-i', OUT_WAV, '-ac', '1', '-ar', '2000', '-f', 'f32le', '-'],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4'); secs = int(len(x) / 2000)
    subprocess.run([FF, '-y', '-v', 'error', '-i', OUT_WAV, '-c:a', 'aac', '-b:a', '160k',
                    '-movflags', '+faststart', M4A], check=True)
    bar_s = SPB / SR
    off = [0.0]
    for i in range(1, n):
        off.append(round(off[-1] + SECTIONS[i - 1]['bars'] * bar_s - XF_S, 1))
    W = 720; seg = max(1, len(x) // W)
    pk = np.abs(x[:seg * W]).reshape(W, seg).max(axis=1); pk = (pk / (pk.max() or 1)).round(3).tolist()
    titles = [s['name'] for s in SECTIONS]
    meta = dict(id='amr-guerrero', title='GUERRERO', kicker='DESERT SET · 0→100', tracks=n, dur=secs,
                titles=titles, offsets=off, file='audio/amr-guerrero.m4a', art='art/amr-guerrero.svg',
                edition=12, peaks=pk, bpm=123, key=None)
    open(os.path.join(HERE, 'guerrero.js'), 'w').write('window.AMR_GUER=' + json.dumps(meta, ensure_ascii=False) + ';')
    print(f'GUERRERO listo: {secs//60}:{secs%60:02d} · {os.path.getsize(M4A)//1024//1024} MB · guerrero.js OK', flush=True)
