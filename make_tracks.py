#!/usr/bin/env python3
# AMR — motor de síntesis del EP "MONUMENTS" (5 rolas, ADN sonoro de PLINTH).
# Correr con /usr/local/bin/python3 (numpy). Renderiza WAV masters -> m4a (afconvert)
# y exporta tracks.js con metadata + peaks de waveform para el player.
import numpy as np, wave, subprocess, os, json, math

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(41)

# ---------- helpers DSP (sin scipy: filtros via FFT, ecos via serie geométrica) ----------
def st(x):
    return np.vstack([x, x]) if x.ndim == 1 else x

def fft_filt(x, curve):
    if x.ndim == 2:
        return np.vstack([fft_filt(x[0], curve), fft_filt(x[1], curve)])
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * curve(f), len(x))

def lowpass(x, fc, order=2):
    return fft_filt(x, lambda f: 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order)))

def highpass(x, fc, order=2):
    return fft_filt(x, lambda f: (f / fc) ** order / np.sqrt(1.0 + (f / fc) ** (2 * order)))

def bandpass(x, fc, q=1.0):
    bw = fc / q
    return fft_filt(x, lambda f: np.exp(-0.5 * ((f - fc) / (bw / 2.355)) ** 2))

def fbdelay(x, time_s, fb=0.42, damp=1800, pingpong=True):
    """Delay con feedback y filtro en el loop (ecos sucesivos, LTI exacto)."""
    x = st(x)
    N = x.shape[1]
    D = int(time_s * SR)
    out = np.zeros_like(x)
    e = x.copy()
    k = 1
    while k * D < N and k < 12:
        e = lowpass(e, damp) * fb
        if np.max(np.abs(e)) < 1e-4: break
        seg = e[:, : N - k * D]
        if pingpong and k % 2 == 1:
            out[0, k * D:] += seg[1] * 1.15
            out[1, k * D:] += seg[0] * 0.85
        else:
            out[:, k * D:] += seg
        k += 1
    return out

def comb(x, D, g):
    N = len(x)
    out = np.zeros_like(x)
    k = 1
    while g ** k > 0.001 and k * D < N:
        out[k * D:] += (g ** k) * x[: N - k * D]
        k += 1
    return out

def reverb(x, size=1.0, damp=3200, mix=1.0):
    """Schroeder barato: 4 combs por canal (afinaciones L/R distintas = ancho)."""
    x = st(x)
    xd = lowpass(x, damp)
    tunL = (0.0297, 0.0371, 0.0411, 0.0437)
    tunR = (0.0313, 0.0356, 0.0402, 0.0451)
    L = sum(comb(xd[0], int(SR * t * size), 0.72 + 0.015 * i) for i, t in enumerate(tunL)) / 4
    R = sum(comb(xd[1], int(SR * t * size), 0.72 + 0.015 * i) for i, t in enumerate(tunR)) / 4
    return np.vstack([L, R]) * mix

def env_exp(n, decay):
    return np.exp(-np.linspace(0, 1, n) * decay)

def place(canvas, sample, t):
    sample = st(sample)
    i = int(t * SR)
    if i >= canvas.shape[1]: return
    n = min(sample.shape[1], canvas.shape[1] - i)
    canvas[:, i:i + n] += sample[:, :n]

def softclip(x, drive=1.15):
    return np.tanh(x * drive) / math.tanh(drive)

def smooth_gain(N, points, sr=SR):
    """Automatización de volumen: [(bar_time_s, gain), ...] con rampas suaves."""
    g = np.zeros(N)
    ts = [int(p[0] * sr) for p in points]
    vs = [p[1] for p in points]
    for i in range(len(points) - 1):
        a, b = ts[i], min(ts[i + 1], N)
        if a >= N: break
        g[a:b] = np.linspace(vs[i], vs[i + 1], max(b - a, 1))
    g[ts[-1]:] = vs[-1]
    return g

# ---------- instrumentos (ADN plinth.html) ----------
def mk_kick(f0=140, f1=46, amp=0.52, dur=0.34):
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f1 + (f0 - f1) * np.exp(-t * 26)
    ph = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(ph) * env_exp(n, 9) * amp
    click = highpass(rng.standard_normal(int(0.012 * SR)), 3000) * env_exp(int(0.012 * SR), 14) * 0.12
    body[: len(click)] += click
    return body

def mk_hat(open_=False):
    d = 0.16 if open_ else 0.055
    n = int(d * SR)
    x = highpass(rng.standard_normal(n), 8200) * env_exp(n, 6 if open_ else 11)
    return x * (0.30 if open_ else 0.22)

def mk_bass(f, dur=0.36, amp=0.34):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tri = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t))
    x = lowpass(tri + 0.18 * np.sin(2 * np.pi * f * 2 * t), 240)
    e = np.minimum(np.linspace(0, 1, n) * 40, 1) * env_exp(n, 6.5)
    return x * e * amp

def mk_stab(freqs, dur=0.30, bp=920, q=1.1, amp=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    L = np.zeros(n); R = np.zeros(n)
    for i, f in enumerate(freqs):
        dt = (5 if i % 2 else -5) / 1200
        L += ((2 * ((f * (1 + dt) * t) % 1) - 1))
        R += ((2 * ((f * (1 - dt) * t) % 1) - 1))
    x = np.vstack([L, R]) / len(freqs)
    x = bandpass(x, bp, q)
    e = np.minimum(np.linspace(0, 1, n) * 90, 1) * env_exp(n, 8)
    return x * e * amp

def mk_pluck(f, dur=0.5, amp=0.2, bright=1400):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2 * t) + 0.12 * np.sin(2 * np.pi * f * 3 * t)
    x = lowpass(x, bright)
    e = np.minimum(np.linspace(0, 1, n) * 200, 1) * env_exp(n, 7)
    return x * e * amp

def mk_pad(freqs, N, lfo_hz=0.05, dark=380, bright=1250, amp=0.062):
    """Saws desafinados L/R + crossfade oscuro/brillante con LFO = 'respiración'."""
    t = np.arange(N) / SR
    L = np.zeros(N); R = np.zeros(N)
    for i, f in enumerate(freqs):
        det = (6 if i % 2 else -6) / 1200
        L += 2 * ((f * (1 + det) * t + rng.random()) % 1) - 1
        R += 2 * ((f * (1 - det) * t + rng.random()) % 1) - 1
    x = np.vstack([L, R]) / len(freqs)
    xd = lowpass(x, dark); xb = lowpass(x, bright)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * lfo_hz * t + rng.random() * 6)
    return (xd * (1 - lfo) + xb * lfo) * amp

def mk_drone(f0, N, amp=0.30):
    """El drone del reel de ALTAR: fundamental + armónicos, respiración 0.14 Hz."""
    t = np.arange(N) / SR
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.14 * t)
    d = (0.5 * np.sin(2 * np.pi * f0 * t) + 0.28 * np.sin(2 * np.pi * f0 * 1.5 * t)
         + 0.16 * np.sin(2 * np.pi * f0 * 2 * t) + 0.09 * np.sin(2 * np.pi * f0 * 3 * t + 0.7))
    x = d * (0.35 + 0.35 * lfo) * amp
    wid = lowpass(rng.standard_normal(N), 300) * 0.012
    return np.vstack([x + wid, x - wid])

def vinyl_bed(N, crackle_rate=9.0, hiss=0.006, amp=1.0):
    """Polvo de vinilo: ticks Poisson + hiss + rumble 33rpm (la aguja es la marca)."""
    out = np.zeros((2, N))
    for ch in range(2):
        n_ticks = int(crackle_rate * N / SR)
        idx = rng.integers(0, N - 400, n_ticks)
        amps = rng.exponential(0.05, n_ticks) * rng.choice([1, -1], n_ticks)
        tick = env_exp(120, 9)
        for i, a in zip(idx, amps):
            out[ch, i:i + 120] += np.clip(a, -0.35, 0.35) * tick
        out[ch] += lowpass(rng.standard_normal(N), 2800) * hiss
    out = lowpass(out, 6500)
    t = np.arange(N) / SR
    rumble = np.sin(2 * np.pi * 0.55 * t) * np.sin(2 * np.pi * 29 * t) * 0.012
    return (out + rumble) * amp

def needle_drop(N_bed):
    """Golpe de aguja + ráfaga de crackle al inicio."""
    n = int(1.1 * SR)
    x = np.zeros((2, n))
    t = np.arange(int(0.25 * SR)) / SR
    thump = np.sin(2 * np.pi * (60 * np.exp(-t * 12) + 24) * t) * env_exp(len(t), 7) * 0.35
    x[:, 2000:2000 + len(thump)] += thump
    burst = vinyl_bed(n, crackle_rate=40, hiss=0.012)
    x += burst * np.linspace(1.4, 0.5, n)
    return x

def riser(dur, N, f0=400, f1=4000, amp=0.05):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    sweep = np.linspace(0, 1, n) ** 2
    blocks = 24; out = np.zeros(n)
    for b in range(blocks):
        a, bb = b * n // blocks, (b + 1) * n // blocks
        fc = f0 + (f1 - f0) * sweep[a]
        out[a:bb] = bandpass(x[a:bb], fc, 1.2)
    return st(out * np.linspace(0.1, 1, n) ** 1.5 * amp)

def duck_env(N, kick_times, depth=0.62, rec=0.42):
    g = np.ones(N)
    L = int(rec * SR)
    dip = 1 - depth * np.exp(-np.linspace(0, 1, L) * 6)
    for t in kick_times:
        i = int(t * SR)
        if i >= N: continue
        n = min(L, N - i)
        g[i:i + n] = np.minimum(g[i:i + n], dip[:n])
    return g

# ---------- secuenciador ----------
class Song:
    def __init__(self, bpm, bars, swing=0.0):
        self.bpm = bpm; self.bars = bars
        self.beat = 60.0 / bpm
        self.s16 = self.beat / 4
        self.dur = bars * 4 * self.beat
        self.N = int(self.dur * SR)
        self.mix = np.zeros((2, self.N))
        self.kick_times = []
        self.swing = swing
    def t(self, bar, step=0):
        sw = self.s16 * self.swing if step % 2 == 1 else 0
        return bar * 4 * self.beat + step * self.s16 + sw
    def add(self, x, gain_pts=None):
        x = st(x)
        n = min(x.shape[1], self.N)
        if gain_pts:
            g = smooth_gain(self.N, [(self.t(b), v) for b, v in gain_pts])[:n]
            self.mix[:, :n] += x[:, :n] * g
        else:
            self.mix[:, :n] += x[:, :n]

def render_beat(song, sec, kick_pat, hat_pat, bass_pat, bass_notes,
                kick_kw=None, hat_gain=1.0):
    """sec: lista de (bar_ini, bar_fin, capas_activas) — 'k','h','b'"""
    kick_s = mk_kick(**(kick_kw or {}))
    hat_c = mk_hat(False); hat_o = mk_hat(True)
    kicks = np.zeros((2, song.N)); hats = np.zeros((2, song.N)); bass = np.zeros((2, song.N))
    bass_cache = {f: mk_bass(f) for f in set(bass_notes.values())}
    for bar in range(song.bars):
        layers = ''
        for a, b, l in sec:
            if a <= bar < b: layers = l; break
        for step in range(16):
            tt = song.t(bar, step)
            if 'k' in layers and kick_pat[step]:
                place(kicks, kick_s, tt); song.kick_times.append(tt)
            if 'h' in layers and hat_pat[step]:
                h = hat_o if hat_pat[step] == 2 else hat_c
                pan = 0.9 if (step // 2) % 2 else 1.1
                place(hats, np.vstack([h * pan, h * (2 - pan)]) * hat_gain, tt)
            if 'b' in layers and step in bass_pat:
                place(bass, bass_cache[bass_notes[bass_pat[step]]], tt)
    return kicks, hats, bass

def master(song, out_name, extra_intro_bed=True):
    x = song.mix
    # bed de vinilo siempre presente — más fuerte al inicio y final
    bed = vinyl_bed(song.N)
    bed_g = smooth_gain(song.N, [(0, 1.0), (int(4 * 4 * song.beat * 0), 1.0)])
    fade_bars = 4 * 4 * song.beat
    bed_auto = np.interp(np.arange(song.N),
                         [0, int(fade_bars * SR), song.N - int(fade_bars * SR), song.N - 1],
                         [1.0, 0.45, 0.45, 1.1])
    x = x + bed * bed_auto * 0.9
    x[:, :int(1.1 * SR)] += needle_drop(song.N) * 0.9
    # fades globales
    fi = int(0.15 * SR); fo = int(2.2 * SR)
    x[:, :fi] *= np.linspace(0, 1, fi)
    x[:, -fo:] *= np.linspace(1, 0, fo)
    x = softclip(x, 1.12)
    x = x / np.max(np.abs(x)) * 0.89
    path = os.path.join(HERE, 'masters', out_name + '.wav')
    data = (x.T * 32767).astype('<i2')
    with wave.open(path, 'w') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(data.tobytes())
    # peaks para el waveform del player
    W = 720
    seg = song.N // W
    mono = np.abs(x).mean(axis=0)[: seg * W].reshape(W, seg)
    peaks = mono.max(axis=1)
    peaks = (peaks / peaks.max()).round(3).tolist()
    return path, song.dur, peaks

# ---------- ROLAS ----------
def track_plinth():
    """AMR-001 PLINTH — 118 BPM, La menor. La rola original, ahora completa."""
    s = Song(118, 88)
    KICK = [1 if i % 4 == 0 else 0 for i in range(16)]
    HATS = [0, 1, 0, 1, 2, 1, 0, 1, 0, 1, 0, 1, 2, 1, 0, 1]
    BASSP = {0: 'A', 6: 'A', 10: 'E', 14: 'G'}
    NOTES = {'A': 55.0, 'E': 41.2, 'G': 49.0}
    sec = [(8, 24, 'kb'), (24, 48, 'khb'), (56, 76, 'khb'), (76, 82, 'kb')]
    k, h, b = render_beat(s, sec, KICK, HATS, BASSP, NOTES)
    s.add(k); s.add(h); s.add(b)
    duck = duck_env(s.N, s.kick_times)
    pad = mk_pad([110, 164.81, 220, 329.63], s.N) * duck
    s.add(pad, [(0, 0.0), (4, 0.9), (24, 0.9), (26, 1.15), (48, 1.3), (56, 1.0), (82, 1.2), (88, 0.6)])
    # stabs Am7 con delay pingpong a 3/4 (el sonido plinth)
    stabs = np.zeros((2, s.N))
    stab_s = mk_stab([220, 261.63, 329.63, 392])
    for bar in range(24, 76):
        if bar % 2 == 1: place(stabs, stab_s, s.t(bar, 6))
        if bar % 4 == 2: place(stabs, stab_s, s.t(bar, 14))
    stabs = stabs + fbdelay(stabs, s.beat * 0.75, fb=0.42, damp=1800) * 0.6
    s.add(stabs)
    # motivo en el break: E5-C5-A4 plucks espaciados
    mot = np.zeros((2, s.N))
    seqn = [(48, 0, 659.26), (49, 8, 523.25), (50, 4, 440.0), (52, 0, 659.26), (53, 8, 523.25), (54, 4, 440.0)]
    for bar, stp, f in seqn:
        place(mot, mk_pluck(f, amp=0.17), s.t(bar, stp))
    mot = mot + fbdelay(mot, s.beat * 0.75, fb=0.5, damp=2200) * 0.7
    s.add(mot + reverb(mot, 1.3, mix=0.5))
    place(s.mix, riser(s.beat * 8, s.N, amp=0.05), s.t(54))
    return master(s, 'amr-001-plinth')

def track_monolith():
    """AMR-002 MONOLITH — 112 BPM, Fa menor. Más oscura, más pesada, más lenta."""
    s = Song(112, 84)
    KICK = [1 if i % 4 == 0 else 0 for i in range(16)]
    HATS = [0, 0, 0, 1, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 1]
    BASSP = {0: 'F', 7: 'F', 10: 'Ab', 12: 'C'}
    NOTES = {'F': 43.65, 'Ab': 51.91, 'C': 65.41}
    sec = [(8, 20, 'kb'), (20, 44, 'khb'), (52, 72, 'khb'), (72, 78, 'kb')]
    k, h, b = render_beat(s, sec, KICK, HATS, BASSP, NOTES,
                          kick_kw={'f0': 120, 'f1': 42, 'amp': 0.56, 'dur': 0.4}, hat_gain=0.8)
    s.add(k); s.add(h); s.add(b)
    duck = duck_env(s.N, s.kick_times, depth=0.7)
    pad = mk_pad([87.31, 130.81, 207.65, 311.13], s.N, lfo_hz=0.04, dark=300, bright=900, amp=0.07) * duck
    s.add(pad, [(0, 0.0), (5, 1.0), (44, 1.35), (52, 1.0), (78, 1.15), (84, 0.5)])
    # stab oscuro Fm — golpe lento cada 2 compases, delay largo
    stabs = np.zeros((2, s.N))
    stab_s = mk_stab([174.61, 207.65, 261.63, 311.13], dur=0.5, bp=620, q=1.0, amp=0.17)
    for bar in range(20, 72):
        if bar % 2 == 0: place(stabs, stab_s, s.t(bar, 8))
    stabs = stabs + fbdelay(stabs, s.beat * 1.0, fb=0.5, damp=1200) * 0.7
    s.add(stabs + reverb(stabs, 1.6, damp=2000, mix=0.4))
    # campana grave distante en el break (monolito resonando)
    bell = np.zeros((2, s.N))
    for bar, f in [(44, 349.23), (46, 311.13), (48, 261.63), (50, 349.23)]:
        place(bell, mk_pluck(f, dur=1.2, amp=0.13, bright=900), s.t(bar, 0))
    s.add(bell + reverb(bell, 1.8, damp=1800, mix=0.7))
    return master(s, 'amr-002-monolith')

def track_vessel():
    """AMR-003 VESSEL — 122 BPM, Do menor. La melódica: arpegio que corre con delay."""
    s = Song(122, 92, swing=0.12)
    KICK = [1 if i % 4 == 0 else 0 for i in range(16)]
    HATS = [0, 1, 0, 1, 2, 1, 0, 1, 0, 1, 0, 1, 2, 1, 0, 1]
    BASSP = {0: 'C', 3: 'C', 6: 'Eb', 10: 'C', 14: 'G'}
    NOTES = {'C': 65.41, 'Eb': 77.78, 'G': 49.0}
    sec = [(8, 24, 'kb'), (24, 52, 'khb'), (60, 82, 'khb'), (82, 86, 'kb')]
    k, h, b = render_beat(s, sec, KICK, HATS, BASSP, NOTES, kick_kw={'amp': 0.5})
    s.add(k); s.add(h); s.add(b)
    duck = duck_env(s.N, s.kick_times, depth=0.55)
    pad = mk_pad([130.81, 196.0, 233.08, 311.13], s.N, lfo_hz=0.06, dark=420, bright=1500, amp=0.06) * duck
    s.add(pad, [(0, 0.0), (4, 0.85), (52, 1.25), (60, 0.95), (86, 1.1), (92, 0.5)])
    # arpegio Cm7: la melodía que te lleva — corre en corcheas con delay
    arp = np.zeros((2, s.N))
    seq = [261.63, 311.13, 392.0, 466.16, 523.25, 466.16, 392.0, 311.13]
    for bar in range(16, 84):
        if bar in range(52, 56): continue
        dens = 8 if bar >= 24 else 4
        for j in range(dens):
            stp = j * (16 // dens)
            f = seq[(bar * dens + j) % 8]
            g = 0.55 if bar < 24 else (1.0 if bar < 60 else 0.85)
            place(arp, mk_pluck(f, dur=0.32, amp=0.12 * g, bright=1900), s.t(bar, stp))
    arp = arp * duck
    arp = arp + fbdelay(arp, s.beat * 0.75, fb=0.45, damp=2400) * 0.55
    s.add(arp + reverb(arp, 1.1, mix=0.35))
    # voz del vessel: nota larga en el break
    br = np.zeros((2, s.N))
    for bar, f in [(52, 523.25), (54, 466.16), (56, 392.0), (58, 466.16)]:
        place(br, mk_pluck(f, dur=1.6, amp=0.15, bright=1100), s.t(bar, 0))
    s.add(br + reverb(br, 1.5, mix=0.6))
    return master(s, 'amr-003-vessel')

def track_strata():
    """AMR-004 STRATA — 116 BPM, Re menor. Dub techno: el acorde es la estrella."""
    s = Song(116, 88)
    KICK = [1 if i % 4 == 0 else 0 for i in range(16)]
    HATS = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 2, 0]
    BASSP = {0: 'D', 8: 'D', 11: 'A', 14: 'C'}
    NOTES = {'D': 36.71, 'A': 55.0, 'C': 65.41}
    sec = [(8, 20, 'kb'), (20, 46, 'khb'), (54, 78, 'khb'), (78, 84, 'kb')]
    k, h, b = render_beat(s, sec, KICK, HATS, BASSP, NOTES,
                          kick_kw={'f0': 130, 'f1': 44, 'amp': 0.54}, hat_gain=0.7)
    s.add(k); s.add(h); s.add(b)
    duck = duck_env(s.N, s.kick_times, depth=0.6)
    # skank dub: Dm9 en contratiempos, delay eterno filtrado — capas geológicas
    sk = np.zeros((2, s.N))
    chord = mk_stab([146.83, 174.61, 220.0, 261.63, 329.63], dur=0.42, bp=780, q=0.9, amp=0.15)
    for bar in range(12, 82):
        place(sk, chord, s.t(bar, 4))
        if bar % 2 == 1: place(sk, chord, s.t(bar, 12))
    sk = sk * duck
    sk = sk + fbdelay(sk, s.beat * 0.75, fb=0.58, damp=1400) * 0.85
    s.add(sk + reverb(sk, 1.7, damp=2400, mix=0.5),
          [(0, 0.6), (20, 1.0), (46, 1.3), (54, 1.0), (84, 1.1), (88, 0.5)])
    pad = mk_pad([73.42, 110.0, 146.83, 220.0], s.N, lfo_hz=0.045, dark=260, bright=800, amp=0.065) * duck
    s.add(pad, [(0, 0.0), (6, 0.9), (46, 1.2), (54, 0.85), (84, 1.0), (88, 0.4)])
    return master(s, 'amr-004-strata')

def track_ghost():
    """AMR-005 GHOST — sin beat. El drone del reveal de ALTAR, expandido a pieza completa."""
    s = Song(70, 56)  # ~3:12 a 70bpm
    drone = mk_drone(41.2, s.N, amp=0.34)
    s.add(drone, [(0, 0.0), (4, 1.0), (40, 1.15), (52, 0.9), (56, 0.0)])
    # aire filtrado (el 'air' del reel)
    air = lowpass(rng.standard_normal(s.N), 900) * 0.05
    airg = 0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * np.arange(s.N) / SR + 2)
    s.add(st(air) * airg, [(0, 0.4), (20, 1.0), (56, 0.3)])
    # pulso grave cada 2 compases (el latido del reel, cada ~3.4s)
    pulse = np.zeros((2, s.N))
    pk = mk_kick(f0=52, f1=44, amp=0.4, dur=0.5)
    for bar in range(4, 52, 2):
        place(pulse, pk, s.t(bar, 0))
    s.add(pulse)
    # campanas fantasma: Mi menor flotando lejos
    bells = np.zeros((2, s.N))
    freqs = [329.63, 392.0, 493.88, 659.26, 587.33]
    bar = 8
    bi = 0
    while bar < 50:
        f = freqs[bi % len(freqs)]
        place(bells, mk_pluck(f, dur=2.0, amp=0.10, bright=800), s.t(bar, int(rng.integers(0, 8))))
        bar += int(rng.integers(2, 5)); bi += 1
    bells = bells + fbdelay(bells, 0.9, fb=0.55, damp=1600) * 0.8
    s.add(bells + reverb(bells, 2.0, damp=1600, mix=0.9))
    # pad muy tenue Em arriba
    pad = mk_pad([82.41, 123.47, 164.81, 246.94], s.N, lfo_hz=0.03, dark=240, bright=700, amp=0.05)
    s.add(pad, [(0, 0.0), (12, 0.8), (44, 1.0), (56, 0.0)])
    return master(s, 'amr-005-ghost')

# ---------- render ----------
TRACKS = [
    dict(id='amr-001-plinth',   n=1, title='TINTO',   key='A MINOR',  bpm=118, edition=12, fn=track_plinth,
         desc='The original. Sub bass on A1, dust on the needle, chords that answer two bars late.'),
    dict(id='amr-002-monolith', n=2, title='BARRICA', key='F MINOR',  bpm=112, edition=8,  fn=track_monolith,
         desc='Slower, heavier, darker. One chord every two bars, struck like stone.'),
    dict(id='amr-003-vessel',   n=3, title='COSECHA',   key='C MINOR',  bpm=122, edition=12, fn=track_vessel,
         desc='The melodic one. An arpeggio poured in circles until the vessel overflows.'),
    dict(id='amr-004-strata',   n=4, title='RESERVA',   key='D MINOR',  bpm=116, edition=10, fn=track_strata,
         desc='Dub techno in geological layers. The chord echoes until it becomes sediment.'),
    dict(id='amr-005-ghost',    n=5, title='POSO',    key='E MINOR',  bpm=0,   edition=8,  fn=track_ghost,
         desc='No drums. The 41 Hz drone breathing under everything, finally alone.'),
]

if __name__ == '__main__':
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    meta = []
    for tr in TRACKS:
        if only and only not in tr['id']:
            continue
        print(f"— {tr['title']} …", flush=True)
        path, dur, peaks = tr['fn']()
        m4a = os.path.join(HERE, 'audio', tr['id'] + '.m4a')
        subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '192000', path, m4a],
                       check=True, capture_output=True)
        print(f"   {dur:.1f}s  wav={os.path.getsize(path)//1024//1024}MB  m4a={os.path.getsize(m4a)//1024}KB")
        meta.append(dict(id=tr['id'], n=tr['n'], title=tr['title'], key=tr['key'], bpm=tr['bpm'],
                         edition=tr['edition'], dur=round(dur, 1), desc=tr['desc'],
                         file='audio/' + tr['id'] + '.m4a', art='art/' + tr['id'] + '.svg',
                         peaks=peaks))
    if not only:
        with open(os.path.join(HERE, 'tracks.js'), 'w') as f:
            f.write('window.AMR_TRACKS=' + json.dumps(meta) + ';\n')
        print('tracks.js OK')
    print('LISTO')
