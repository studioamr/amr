#!/usr/bin/env python3
"""BLOOM — afro / melodic house estilo Black Coffee · Keinemusik ('The Rapture Pt.III').
Percusión orgánica en capas, marimba/kalimba, bajo rodante, piano tierno, voz sin palabras.
Hipnótico y emotivo — sin drops de EDM."""
import os, json, subprocess, wave
import numpy as np, imageio_ffmpeg
import make_tracks as mt

SR = mt.SR; rng = mt.rng
HERE = os.path.dirname(os.path.abspath(__file__))
place, reverb, fbdelay, duck_env = mt.place, mt.reverb, mt.fbdelay, mt.duck_env
lowpass, highpass, bandpass = mt.lowpass, mt.highpass, mt.bandpass

def stereo(y, pan=1.0): return np.vstack([y * pan, y * (2 - pan)])
def pdecay(n, tau, atk=0.002):
    t = np.arange(n) / SR; e = np.exp(-t / tau)
    a = int(atk * SR)
    if a > 0: e[:a] *= np.linspace(0, 1, a)
    return e

# ---------- percusión orgánica ----------
def shaker(amp=0.11, dur=0.055):
    n = int(dur * SR); x = highpass(rng.standard_normal(n), 6500)
    return stereo(x * pdecay(n, 0.018, 0.004) * amp)
def conga(f=200, amp=0.30, dur=0.17, pan=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    pitch = f * (1 + 0.55 * np.exp(-t * 42))
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) + 0.35 * np.sin(4 * np.pi * np.cumsum(pitch) / SR)
    noise = highpass(rng.standard_normal(n), 1400) * np.exp(-t * 55) * 0.28
    return stereo((body * pdecay(n, 0.10, 0.001) + noise) * amp, pan)
def clave(amp=0.16, dur=0.05, pan=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * 2350 * t) * np.exp(-t / 0.012)
    y += highpass(rng.standard_normal(n), 4200) * np.exp(-t * 130) * 0.35
    return stereo(y * amp, pan)

# ---------- melódicos cálidos ----------
def marimba(f, dur=0.42, amp=0.20):
    n = int(dur * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t)
         + 0.5 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 13)   # el parcial 4:1 (madera)
         + 0.22 * np.sin(2 * np.pi * 2 * f * t))
    knock = highpass(rng.standard_normal(n), 2200) * np.exp(-t * 210) * 0.13
    e = np.exp(-t / (dur * 0.5)); a = int(0.003 * SR); e[:a] *= np.linspace(0, 1, a)
    return stereo(lowpass(y * e + knock, 4800) * amp)
def kalimba(f, dur=0.55, amp=0.13):
    n = int(dur * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 11)
         + 0.28 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 17))
    e = np.exp(-t / (dur * 0.4)); a = int(0.002 * SR); e[:a] *= np.linspace(0, 1, a)
    return stereo(y * e * amp)
def epiano(freqs, dur=1.1, amp=0.11):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for f in freqs:
        y += (np.sin(2 * np.pi * f * t) + 0.28 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3)
              + 0.5 * np.sin(2 * np.pi * f * 1.004 * t))
    e = np.exp(-t / (dur * 0.7)); a = int(0.008 * SR); e[:a] *= np.linspace(0, 1, a)
    y = lowpass(y, 3200) * e / max(1, len(freqs)) * amp
    return np.vstack([y * 0.97, y * 1.03])
def vocal(f, dur, amp=0.14):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 0.01 * np.sin(2 * np.pi * 4.6 * t) * np.minimum(1.0, t / 0.4)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib)) / SR
    tone = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.16 * np.sin(3 * ph)
    tone = bandpass(tone, 880, q=0.7) * 0.7 + tone * 0.5           # vocal 'ooh'
    env = np.ones(n); a = int(0.12 * SR); r = int(min(0.35 * SR, n // 3))
    env[:a] = np.linspace(0, 1, a); env[-r:] *= np.linspace(1, 0, r)
    return stereo(tone * env * amp)

# Am – F – C – G, cálido y emotivo
CH = [
    dict(bass=55.0,  pad=[220, 261.63, 329.63],   mar=[440, 523.25, 659.25, 523.25], pno=[220, 261.63, 329.63, 392]),
    dict(bass=43.65, pad=[174.61, 220, 261.63],   mar=[349.23, 440, 523.25, 440],    pno=[174.61, 220, 261.63, 349.23]),
    dict(bass=65.41, pad=[196.0, 261.63, 329.63], mar=[392, 523.25, 659.25, 523.25], pno=[196.0, 261.63, 329.63, 392]),
    dict(bass=49.0,  pad=[196.0, 246.94, 293.66], mar=[392, 493.88, 587.33, 493.88], pno=[196.0, 246.94, 293.66, 392]),
]
def ch(bar): return CH[(bar // 4) % 4]
def rng_in(bar, spans): return any(a <= bar < b for a, b in spans)

def build():
    s = mt.Song(122, 104)
    beat = s.beat

    # --- kick profundo four-on-floor ---
    KICK_ON = [(8, 48), (60, 88), (96, 102)]
    kick_s = mt.mk_kick(f0=125, f1=44, amp=0.6, dur=0.42)
    kk = np.zeros((2, s.N))
    for bar in range(s.bars):
        if not rng_in(bar, KICK_ON): continue
        for st in [0, 4, 8, 12]:
            place(kk, kick_s, s.t(bar, st)); s.kick_times.append(s.t(bar, st))
    s.add(kk)
    duck = duck_env(s.N, s.kick_times, depth=0.55, rec=0.34)

    # --- percusión orgánica (casi siempre; adelgaza en el break) ---
    PERC_ON = [(4, 48), (56, 104)]
    perc = np.zeros((2, s.N))
    for bar in range(s.bars):
        if not rng_in(bar, PERC_ON): continue
        thin = rng_in(bar, [(48, 60)])              # break: sólo shaker suave
        for st in range(16):                        # shaker en 16avos con acentos
            v = 0.13 if st % 4 == 2 else (0.09 if st % 2 else 0.06)
            place(perc, shaker(amp=v * (0.6 if thin else 1.0)), s.t(bar, st))
        if thin: continue
        for st in [2, 6, 10, 14]:                   # open-hat feel: shaker fuerte en offbeat
            place(perc, shaker(amp=0.15, dur=0.09), s.t(bar, st))
        # congas sincopadas (tumbao): hi/lo, paneadas
        for st, f, pan in [(3, 196, 0.8), (6, 330, 1.2), (7, 300, 1.15), (11, 180, 0.85), (14, 330, 1.2)]:
            place(perc, conga(f=f, amp=0.24, pan=pan), s.t(bar, st))
        for st, pan in [(6, 1.25), (14, 0.8)]:      # claves secas
            place(perc, clave(amp=0.12, pan=pan), s.t(bar, st))
    s.add(perc + reverb(perc, 0.9, damp=4500, mix=0.16))

    # --- bajo sub rodante en offbeats (sigue el acorde) ---
    bcache = {}
    def bnote(f):
        if f not in bcache: bcache[f] = mt.mk_bass(f, dur=0.34, amp=0.34)
        return bcache[f]
    bass = np.zeros((2, s.N))
    for bar in range(s.bars):
        if not rng_in(bar, KICK_ON): continue
        bf = ch(bar)['bass']
        for st in [2, 6, 10, 14, 7]:                # 8vos offbeat + una sincopa
            place(bass, bnote(bf), s.t(bar, st))
    s.add(bass * duck)

    # --- pad cálido (bed que evoluciona por bloque) ---
    pads = np.zeros((2, s.N))
    for blk in range(0, s.bars, 4):
        seg = mt.mk_pad([f for f in ch(blk)['pad']] + [ch(blk)['pad'][0] * 2],
                        4 * 4 * int(beat * SR) + SR, lfo_hz=0.05, dark=380, bright=1200, amp=0.06)
        place(pads, seg, s.t(blk))
    s.add(pads * duck, [(0, 0.4), (16, 0.7), (32, 0.95), (48, 1.15), (60, 0.85),
                        (64, 1.1), (88, 0.9), (104, 0.35)])

    # --- MARIMBA: el riff hipnótico (el gancho) ---
    MAR_ON = [(16, 48), (52, 60), (64, 88)]
    MARP = [(0, 0), (3, 1), (6, 2), (8, 1), (11, 3), (14, 2)]
    mar = np.zeros((2, s.N))
    for bar in range(s.bars):
        if not rng_in(bar, MAR_ON): continue
        soft = 0.5 if rng_in(bar, [(52, 60)]) else 1.0
        tones = ch(bar)['mar']
        for st, ti in MARP:
            place(mar, marimba(tones[ti], amp=0.17 * soft), s.t(bar, st))
    mar = mar + fbdelay(mar, beat * 0.75, fb=0.34, damp=3200) * 0.45
    s.add(mar + reverb(mar, 1.2, damp=3200, mix=0.22))

    # --- KALIMBA: contra-melodía brillante en el pico ---
    kal = np.zeros((2, s.N))
    for bar in range(64, 88):
        tones = ch(bar)['mar']
        for st, ti in [(2, 3), (10, 2), (13, 1)]:
            place(kal, kalimba(tones[ti] * 2, amp=0.09), s.t(bar, st))
    kal = kal + fbdelay(kal, beat * 0.5, fb=0.38, damp=4000) * 0.5
    s.add(kal + reverb(kal, 1.4, damp=4000, mix=0.3))

    # --- PIANO tierno (el break emotivo) ---
    pno = np.zeros((2, s.N))
    for bar in range(48, 60):
        for st in [0, 6, 10]:
            place(pno, epiano(ch(bar)['pno'], dur=1.3, amp=0.10), s.t(bar, st))
    s.add(pno + reverb(pno, 1.7, damp=2600, mix=0.42))

    # --- VOZ sin palabras (break + pico) ---
    HOOK = [(0, 0, 659.25, 3), (0, 12, 523.25, 1), (1, 0, 587.33, 2), (1, 8, 440.0, 2),
            (2, 0, 659.25, 2), (2, 8, 783.99, 2), (3, 0, 587.33, 4),
            (4, 0, 523.25, 3), (4, 12, 440.0, 1), (5, 0, 493.88, 4),
            (6, 0, 659.25, 2), (6, 8, 587.33, 2), (7, 0, 523.25, 4)]
    voc = np.zeros((2, s.N))
    def lay(sb, amp):
        for pb, st, f, bts in HOOK:
            place(voc, vocal(f, bts * beat * 0.95, amp=amp), s.t(sb + pb, st))
    lay(52, 0.12)      # break
    lay(72, 0.16)      # pico
    s.add(voc + reverb(voc, 1.8, damp=2400, mix=0.44))

    return mt.master(s, 'amr-bloom')

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    print('Sintetizando BLOOM (afro/melodic house)…', flush=True)
    wav, dur, peaks = build()
    print(f'  WAV: {wav}  ({dur:.1f}s)', flush=True)
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    m4a = os.path.join(HERE, 'audio', 'amr-bloom.m4a')
    subprocess.run([FF, '-y', '-v', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', m4a], check=True)
    print(f'  M4A: {m4a}', flush=True)
    meta = dict(id='amr-bloom', title='BLOOM', kicker='THE SINGLE', tracks=1,
                dur=round(dur, 1), titles=['BLOOM'], file='audio/amr-bloom.m4a',
                art='art/amr-bloom.svg', edition=30, peaks=peaks, offsets=[0.0], bpm=122, key='A MIN')
    with open(os.path.join(HERE, 'bloom.js'), 'w') as f:
        f.write('window.AMR_BLOOM=' + json.dumps(meta) + ';')
    print('  bloom.js escrito. done', flush=True)
