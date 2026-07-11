#!/usr/bin/env python3
"""BLOOM — anthem eufórica estilo 'Rapture': arpegio brillante, acordes que levantan, voz sintetizada."""
import os, json, subprocess, wave
import numpy as np, imageio_ffmpeg
import make_tracks as mt

SR = mt.SR
HERE = os.path.dirname(os.path.abspath(__file__))
place, reverb, fbdelay, riser, duck_env = mt.place, mt.reverb, mt.fbdelay, mt.riser, mt.duck_env
mk_pad, mk_pluck, mk_bass, mk_hat, mk_kick = mt.mk_pad, mt.mk_pluck, mt.mk_bass, mt.mk_hat, mt.mk_kick

# Am – F – C – G (i – VI – III – VII): la progresión eufórica
CHORDS = [
    dict(pad=[220, 261.63, 329.63, 440],    arp=[440, 523.25, 659.25, 880],   bass=55.0),   # Am
    dict(pad=[174.61, 220, 261.63, 349.23], arp=[349.23, 440, 523.25, 698.46],bass=43.65),  # F
    dict(pad=[261.63, 329.63, 392, 523.25], arp=[523.25, 659.25, 783.99, 1046.5],bass=65.41),# C
    dict(pad=[196.0, 246.94, 293.66, 392],  arp=[392, 493.88, 587.33, 783.99], bass=49.0),   # G
]
def chord_of(bar): return CHORDS[(bar // 4) % 4]

def vocal_lead(f, dur, amp=0.17):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 0.008 * np.sin(2 * np.pi * 5.0 * t) * np.minimum(1.0, t / 0.35)   # vibrato entra suave
    ph = 2 * np.pi * np.cumsum(f * (1 + vib)) / SR
    tone = (np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.22 * np.sin(3 * ph) + 0.1 * np.sin(4 * ph))
    tone = mt.bandpass(tone, 1150, q=0.8) * 0.65 + tone * 0.7      # formante vocal
    env = np.ones(n); a = int(0.09 * SR); r = int(min(0.3 * SR, n // 3))
    env[:a] = np.linspace(0, 1, a); env[-r:] *= np.linspace(1, 0, r)
    y = tone * env * amp
    return np.vstack([y, y])

def build():
    s = mt.Song(126, 104)
    beat = s.beat
    # --- kick + hats por secciones (drops y builds) ---
    KICK = [1 if i % 4 == 0 else 0 for i in range(16)]
    HATS = [0, 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2]     # open hats en offbeat: euforia
    sec = [(8, 40, 'kh'), (56, 92, 'kh')]
    k, h, _ = mt.render_beat(s, sec, KICK, HATS, {}, {},
                             kick_kw={'f0': 150, 'f1': 48, 'amp': 0.6, 'dur': 0.34}, hat_gain=0.7)
    s.add(k); s.add(h)
    duck = duck_env(s.N, s.kick_times, depth=0.5)

    # --- bass rodante (sigue el acorde) en drops/builds ---
    bass = np.zeros((2, s.N))
    bcache = {}
    def bnote(f):
        if f not in bcache: bcache[f] = mk_bass(f, dur=0.30, amp=0.34)
        return bcache[f]
    def has_bass(bar): return (8 <= bar < 40) or (56 <= bar < 92)
    for bar in range(s.bars):
        if not has_bass(bar): continue
        bf = chord_of(bar)['bass']
        for stp in [0, 2, 4, 6, 8, 10, 12, 14]:          # 8vos rodando
            place(bass, bnote(bf), s.t(bar, stp))
    s.add(bass * duck)

    # --- pads de acorde (bed que evoluciona por bloque de 4 compases) ---
    pads = np.zeros((2, s.N))
    for blk in range(0, s.bars, 4):
        ch = chord_of(blk)
        seg = mk_pad(ch['pad'], 4 * 4 * int(beat * SR) + SR, lfo_hz=0.07, dark=460, bright=1700, amp=0.07)
        place(pads, seg, s.t(blk))
    s.add(pads * duck, [(0, 0.55), (8, 0.8), (16, 1.1), (40, 1.25), (56, 0.9),
                        (64, 1.2), (92, 1.0), (104, 0.4)])

    # --- ARPEGIO brillante (la firma Rapture): 1/16 con pingpong ---
    arp = np.zeros((2, s.N))
    patt = [0, 1, 2, 3, 3, 2, 1, 0, 0, 1, 2, 3, 2, 1, 2, 3]
    def has_arp(bar): return (16 <= bar < 40) or (40 <= bar < 56) or (64 <= bar < 92)
    for bar in range(s.bars):
        if not has_arp(bar): continue
        tones = chord_of(bar)['arp']
        soft = 0.6 if (40 <= bar < 56) else 1.0          # más suave en el break
        for step in range(16):
            f = tones[patt[step]]
            pan = 0.92 if step % 2 else 1.08
            pl = mk_pluck(f, dur=0.34, amp=0.12 * soft, bright=2600)
            place(arp, np.vstack([pl * pan, pl * (2 - pan)]), s.t(bar, step))
    arp = arp + fbdelay(arp, beat * 0.75, fb=0.36, damp=3000) * 0.5
    s.add(arp + reverb(arp, 1.2, damp=3000, mix=0.28))

    # --- VOZ sintetizada: el hook que sube (drops + break) ---
    HOOK = [  # (bar_en_frase, step, freq_relativa_a_A, beats)
        (0, 0, 659.25, 2), (0, 8, 523.25, 2),
        (1, 0, 587.33, 2), (1, 8, 440.0, 2),
        (2, 0, 659.25, 2), (2, 8, 783.99, 2),
        (3, 0, 587.33, 4),
        (4, 0, 880.0, 2), (4, 8, 659.25, 2),
        (5, 0, 523.25, 4),
        (6, 0, 659.25, 2), (6, 8, 783.99, 2),
        (7, 0, 493.88, 2), (7, 8, 587.33, 2),
    ]
    voc = np.zeros((2, s.N))
    def lay_hook(start_bar, amp):
        for pbar, stp, f, bts in HOOK:
            place(voc, vocal_lead(f, bts * beat * 0.96, amp=amp), s.t(start_bar + pbar, stp))
    lay_hook(24, 0.17)          # segunda mitad del drop 1
    lay_hook(44, 0.12)          # break, más suave
    lay_hook(72, 0.19)          # drop 2, más fuerte
    lay_hook(80, 0.19)
    s.add(voc + reverb(voc, 1.6, damp=2600, mix=0.4))

    # --- risers hacia cada drop ---
    place(s.mix, riser(beat * 8, s.N, f0=300, f1=5000, amp=0.06), s.t(8))
    place(s.mix, riser(beat * 8, s.N, f0=300, f1=6000, amp=0.07), s.t(56))
    place(s.mix, riser(beat * 4, s.N, f0=600, f1=7000, amp=0.05), s.t(36))
    return mt.master(s, 'amr-bloom')

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    print('Sintetizando BLOOM…', flush=True)
    wav, dur, peaks = build()
    print(f'  WAV: {wav}  ({dur:.1f}s)', flush=True)
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    m4a = os.path.join(HERE, 'audio', 'amr-bloom.m4a')
    subprocess.run([FF, '-y', '-v', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', m4a], check=True)
    print(f'  M4A: {m4a}', flush=True)
    meta = dict(id='amr-bloom', title='BLOOM', kicker='THE SINGLE', tracks=1,
                dur=round(dur, 1), titles=['BLOOM'], file='audio/amr-bloom.m4a',
                art='art/amr-bloom.svg', edition=30, peaks=peaks, offsets=[0.0], bpm=126, key='A MIN')
    with open(os.path.join(HERE, 'bloom.js'), 'w') as f:
        f.write('window.AMR_BLOOM=' + json.dumps(meta) + ';')
    print('  bloom.js escrito. done', flush=True)
