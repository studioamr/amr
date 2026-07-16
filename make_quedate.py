#!/usr/bin/env python3
"""QUÉDATE — afro/soulful house en el mundo de The Rapture Pt.III (Keinemusik) y
You Need Me (Black Coffee). 120 BPM · Re menor · 196 compases = 6:32.
Piano tierno al centro + voz femenina cantando la hook "qué-da-te" (3 notas descendentes).
Regla de oro del género: lo que omites importa tanto como lo que pones."""
import os, json, subprocess, wave
import numpy as np, imageio_ffmpeg
import make_tracks as mt

SR = mt.SR; rng = mt.rng
HERE = os.path.dirname(os.path.abspath(__file__))
place, reverb, fbdelay, duck_env = mt.place, mt.reverb, mt.fbdelay, mt.duck_env
lowpass, highpass, bandpass, softclip = mt.lowpass, mt.highpass, mt.bandpass, mt.softclip

def st(y, pan=1.0): return np.vstack([y * pan, y * (2 - pan)])

# ---------- percusión (poca, suave, humana) ----------
def kick_deep(amp=0.58):
    """kick profundo SIN click (Black Coffee): redondo, suave."""
    n = int(0.42 * SR); t = np.arange(n) / SR
    f = 44 + 52 * np.exp(-t * 26)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR)
    y = lowpass(y, 2200)
    e = np.exp(-t / 0.16); a = int(0.004 * SR); e[:a] *= np.linspace(0, 1, a)
    return st(y * e * amp)

def tom_low(f0=128, amp=0.16):
    """tom suave — el loop debajo del kick, la marca Black Coffee."""
    n = int(0.16 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.35 * np.exp(-t * 40))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.2 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    y = highpass(y, 82)
    e = np.exp(-t / 0.06); a = int(0.003 * SR); e[:a] *= np.linspace(0, 1, a)
    return st(y * e * amp)

def shaker(amp=0.08, dur=0.05):
    n = int(dur * SR); t = np.arange(n) / SR
    y = highpass(rng.standard_normal(n), 7000)
    e = np.exp(-t / 0.017); a = int(0.006 * SR); e[:a] *= np.linspace(0, 1, a)
    return st(y * e * amp)

def conga(f=190, amp=0.14, pan=1.0):
    """conga tonal LIMPIA (nada de ruido turbio)."""
    n = int(0.13 * SR); t = np.arange(n) / SR
    f_t = f * (1 + 0.28 * np.exp(-t * 55))
    y = np.sin(2 * np.pi * np.cumsum(f_t) / SR) + 0.18 * np.sin(4 * np.pi * np.cumsum(f_t) / SR)
    e = np.exp(-t / 0.05); a = int(0.002 * SR); e[:a] *= np.linspace(0, 1, a)
    return st(lowpass(y, 2400) * e * amp, pan)

def rim(amp=0.07, pan=1.0):
    """rimshot/woodblock suave (el backbeat del género — nada de claps)."""
    n = int(0.05 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * 810 * t) * np.exp(-t / 0.010) + bandpass(rng.standard_normal(n), 2600, 1.4) * np.exp(-t / 0.007) * 0.5
    return st(y * amp, pan)

def tick(amp=0.045, pan=1.0):
    """tick agudo del polirritmo 3-contra-4 (el motor hipnótico, casi subliminal)."""
    n = int(0.03 * SR); t = np.arange(n) / SR
    y = bandpass(rng.standard_normal(n), 3400, 2.2) * np.exp(-t / 0.006)
    return st(y * amp, pan)

# ---------- bajo (3-3-2, redondo, con huecos) ----------
def bass_note(f, dur=0.24, amp=0.34):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t) + 0.05 * np.sin(6 * np.pi * f * t)
    y = lowpass(y, 320)
    e = np.ones(n); a = int(0.006 * SR); r = int(0.07 * SR)
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    return st(y * e * amp)

def sub_hold(f, secs, amp=0.10):
    n = int(secs * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t)
    e = np.ones(n); a = int(0.10 * SR); r = int(0.20 * SR)
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    return st(y * e * amp)

# ---------- piano acústico (el centro emocional) ----------
_PIANO_CACHE = {}
def piano_note(f, dur=1.6, amp=0.15):
    key = (round(f, 1), round(dur, 2))
    if key in _PIANO_CACHE: return _PIANO_CACHE[key] * (amp / 0.15)
    n = int(dur * SR); t = np.arange(n) / SR
    B = 0.00022                                     # inarmonicidad de cuerda real
    y = np.zeros(n)
    for k in range(1, 13):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 9000: break
        dk = 0.9 / (1 + 0.5 * (k - 1))              # agudos decaen más rápido
        for det in (1.0, 1.0012):                   # dos cuerdas
            y += np.sin(2 * np.pi * fk * det * t + rng.uniform(0, 6.28)) * np.exp(-t / (dur * dk)) / (k ** 1.4)
    hammer = bandpass(rng.standard_normal(n), min(f * 5, 4200), 1.2) * np.exp(-t / 0.010) * 0.4
    e = np.ones(n); a = int(0.002 * SR); r = int(min(0.25 * SR, n // 4))
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    out = st(lowpass(y + hammer, 5200) * e * 0.15 / 1.7)
    _PIANO_CACHE[key] = out
    return out * (amp / 0.15)

# ---------- voz femenina que CANTA (portamento + formantes + vibrato) ----------
FORMANTS = {'ah': (800, 1150, 2900), 'eh': (610, 1900, 2600),
            'oh': (450, 800, 2830), 'oo': (350, 800, 2700)}

def sing(seq, amp=0.16, breath=0.05):
    """seq: [(freq, dur_s, 'ah'|'eh'|'oh'|'oo')] — UNA frase continua con glides."""
    total = sum(d for _, d, _ in seq)
    n = int(total * SR); t = np.arange(n) / SR
    fcurve = np.zeros(n); pos = 0
    prev_f = seq[0][0]
    segs = []
    for f, d, vw in seq:
        m = int(d * SR); g = min(int(0.075 * SR), m // 3)
        fcurve[pos:pos + g] = np.linspace(prev_f, f, g)          # portamento
        fcurve[pos + g:pos + m] = f
        segs.append((pos, m, vw)); prev_f = f; pos += m
    fcurve[pos:] = prev_f
    vib = 0.009 * np.sin(2 * np.pi * 5.3 * t)
    vibgate = np.zeros(n)                                        # vibrato entra tarde en cada nota
    for p, m, _ in segs:
        L = np.arange(m) / SR
        vibgate[p:p + m] = np.clip((L - 0.30) / 0.25, 0, 1)
    ph = 2 * np.pi * np.cumsum(fcurve * (1 + vib * vibgate)) / SR
    src = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.33 * np.sin(3 * ph) + 0.24 * np.sin(4 * ph) + 0.18 * np.sin(5 * ph) + 0.12 * np.sin(6 * ph)
    out = np.zeros(n)
    for p, m, vw in segs:                                        # formantes por sílaba
        F1, F2, F3 = FORMANTS[vw]
        seg = src[max(0, p - 200):p + m]
        v = bandpass(seg, F1, 1.0) + 0.7 * bandpass(seg, F2, 1.1) + 0.32 * bandpass(seg, F3, 1.3) + seg * 0.16
        out[p:p + m] += v[-m:]
    out += highpass(rng.standard_normal(n), 5200) * breath * 0.4  # aire
    e = np.ones(n); a = int(0.09 * SR); r = int(min(0.30 * SR, n // 4))
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    y = highpass(out, 210) * e * amp
    return np.vstack([y * 0.97, y * 1.03])

# ---------- armonía (You Need Me): B♭maj7 – Am7 – Dm9 – C  (1 compás cada uno) ----------
PIANO_CH = [
    [116.54, 174.61, 220.00, 293.66, 349.23],   # B♭maj7  (Bb2 F3 A3 D4 F4)
    [110.00, 164.81, 196.00, 261.63, 329.63],   # Am7     (A2 E3 G3 C4 E4)
    [146.83, 220.00, 261.63, 329.63, 392.00],   # Dm9     (D3 A3 C4 E4 G4)
    [130.81, 196.00, 246.94, 329.63, 392.00],   # Cmaj    (C3 G3 B3 E4 G4)
]
BASS_ROOT = [58.27, 55.00, 73.42, 65.41]        # Bb1 A1 D2 C2
def ch(bar): return (bar % 4)
def rng_in(bar, spans): return any(a <= bar < b for a, b in spans)

# hook "qué-da-te" (3 sílabas, intervalo descendente) — sobre el compás de Dm
HOOK = [(523.25, 0.34, 'eh'), (440.00, 0.34, 'ah'), (349.23, 0.95, 'eh')]          # C5 A4 F4
HOOK_LOW = [(261.63, 0.36, 'oh'), (220.00, 0.36, 'oh'), (174.61, 1.0, 'oo')]       # respuesta grave (pitched-down)
# línea completa del breakdown (spotlight) — centro C4-C5, clímax D5, melisma al cierre
BREAK_LINES = [
    [(440.00, 0.7, 'ah'), (523.25, 0.5, 'eh'), (587.33, 1.3, 'ah'), (523.25, 0.4, 'eh'), (587.33, 0.6, 'ah')],
    [(523.25, 0.5, 'eh'), (440.00, 0.5, 'ah'), (392.00, 0.8, 'oh'), (349.23, 0.9, 'oo')],
    [(349.23, 0.5, 'oh'), (392.00, 0.5, 'ah'), (440.00, 1.6, 'eh'), (392.00, 0.35, 'ah'), (440.00, 0.55, 'eh')],
    [(392.00, 0.4, 'ah'), (349.23, 0.4, 'eh'), (329.63, 0.5, 'ah'), (293.66, 1.4, 'oo'), (329.63, 0.3, 'oh'), (293.66, 0.6, 'oo')],
]

def build():
    s = mt.Song(120, 196)                       # 196 compases @120 = 6:32, bar = 2.0s
    beat = s.beat
    print('  grid: %.2fs/bar · total %.1fs' % (4 * beat, s.dur), flush=True)

    KICK_ON  = [(0, 96), (128, 176)]            # breakdown 96-128 sin kick; outro sin kick desde 176
    PERC1_ON = [(16, 96), (120, 176)]           # shaker + toms
    PERC2_ON = [(32, 96), (128, 168)]           # congas + ticks + rim
    BASS_ON  = [(16, 96), (100, 120), (128, 176)]

    # --- kick + ghost + tom loop ---
    kd = kick_deep(); tomA, tomB = tom_low(122, 0.13), tom_low(98, 0.11)
    drums = np.zeros((2, s.N))
    for bar in range(s.bars):
        if rng_in(bar, KICK_ON):
            for stp in [0, 4, 8, 12]:
                place(drums, kd, s.t(bar, stp)); s.kick_times.append(s.t(bar, stp))
            place(drums, kd * 0.32, s.t(bar, 6))                       # ghost kick ("and" del 2)
        if rng_in(bar, PERC1_ON):
            place(drums, tomA, s.t(bar, 3) + 0.006)                    # tom loop (swing propio)
            place(drums, tomB, s.t(bar, 10) + 0.010)
            place(drums, tomA * 0.7, s.t(bar, 14) + 0.006)
    s.add(drums); del drums
    duck = duck_env(s.N, s.kick_times, depth=0.42, rec=0.26)

    # --- percusión de manos (poca, humana) ---
    perc = np.zeros((2, s.N))
    for bar in range(s.bars):
        if rng_in(bar, PERC1_ON):
            for k, stp in enumerate([2, 6, 10, 14]):                   # shaker offbeat 1/8
                g = 1.0 if k % 2 == 0 else 0.72
                place(perc, shaker(0.085 * g), s.t(bar, stp) + 0.009)
        if rng_in(bar, PERC2_ON):
            place(perc, conga(228, 0.13, 0.86), s.t(bar, 4) - 0.018)   # congas ANTES del beat
            place(perc, conga(172, 0.11, 1.14), s.t(bar, 12) - 0.020)
            if bar % 2 == 1:
                place(perc, conga(228, 0.08, 0.86), s.t(bar, 15) - 0.012)
            place(perc, rim(0.055, 1.1), s.t(bar, 8) + 0.004)          # backbeat suave (rim, no clap)
            for stp in [0, 3, 6, 9, 12, 15]:                           # 3-contra-4, casi subliminal
                place(perc, tick(0.038, 0.92 if stp % 2 else 1.08), s.t(bar, stp) + 0.004)
    s.add(perc * duck); del perc

    # --- bajo 3-3-2 con huecos + sub sostenido ---
    bass = np.zeros((2, s.N)); bc = {}
    for bar in range(s.bars):
        if not rng_in(bar, BASS_ON): continue
        f = BASS_ROOT[ch(bar)]
        if f not in bc: bc[f] = bass_note(f)
        full = bar >= 32
        for stp in ([0, 3, 6, 8, 11, 14] if full else [0, 6, 8, 14]):  # 3-3-2
            g = 1.0 if stp in (0, 8) else 0.85
            place(bass, bc[f] * g, s.t(bar, stp))
        place(bass, sub_hold(f / 2 if f > 60 else f, 4 * beat * 0.94, 0.085), s.t(bar))
    s.add(bass * duck, [(0, 0), (16, 0.7), (32, 1.0), (96, 0.8), (100, 0.55),
                        (120, 0.8), (128, 1.05), (168, 0.9), (176, 0)])
    del bass

    # --- PIANO (You Need Me: entra desde el compás 1, delicado) ---
    pno = np.zeros((2, s.N))
    for bar in range(s.bars):
        freqs = PIANO_CH[ch(bar)]
        # downbeat: acorde (roll suave de 12 ms entre notas)
        for i, f in enumerate(freqs):
            place(pno, piano_note(f, 2.2, 0.13), s.t(bar) + i * 0.013)
        # repique sincopado en el "and" del 3 (solo tríada alta), no en el intro
        if 16 <= bar and bar % 2 == 0:
            for i, f in enumerate(freqs[2:]):
                place(pno, piano_note(f, 1.1, 0.085), s.t(bar, 10) + i * 0.011)
    s.add(pno * duck * 0.9 + reverb(pno, 1.6, damp=3800, mix=0.22))
    del pno

    # --- piano improvisado (frases tiernas arriba — la firma Rapture) ---
    MEL = {  # frases por sección: (bar, [(beat, freq, dur)])
        40: [(0.0, 587.33, 0.8), (1.0, 523.25, 0.8), (2.0, 440.00, 1.6)],
        56: [(0.5, 698.46, 0.6), (1.5, 587.33, 0.6), (2.5, 523.25, 1.3)],
        72: [(0.0, 523.25, 0.7), (1.0, 587.33, 0.7), (2.0, 698.46, 1.7)],
        88: [(0.0, 440.00, 0.6), (1.0, 392.00, 0.6), (2.0, 349.23, 1.8)],
        100: [(0.0, 587.33, 1.0), (1.5, 523.25, 1.0), (3.0, 440.00, 1.0)],
        104: [(0.5, 523.25, 0.8), (2.0, 440.00, 0.8), (3.0, 392.00, 1.0)],
        108: [(0.0, 440.00, 0.9), (1.5, 349.23, 0.9), (3.0, 329.63, 1.0)],
        140: [(0.0, 698.46, 0.7), (1.0, 587.33, 0.7), (2.0, 523.25, 1.6)],
        156: [(0.5, 587.33, 0.7), (1.5, 523.25, 0.7), (2.5, 440.00, 1.5)],
        180: [(0.0, 523.25, 1.2), (2.0, 440.00, 1.8)],
        186: [(0.0, 349.23, 1.2), (2.0, 293.66, 2.4)],
        190: [(0.0, 293.66, 3.6)],
    }
    imp = np.zeros((2, s.N))
    for bar, notes in MEL.items():
        for bt, f, d in notes:
            place(imp, piano_note(f, d + 0.7, 0.15), s.t(bar) + bt * beat)
    s.add(imp * 0.95 + reverb(imp, 2.2, damp=3400, mix=0.32))
    del imp

    # --- pads cálidos muy sutiles ---
    pads = np.zeros((2, s.N))
    for blk in range(16, s.bars - 4):
        if blk % 4 == 0:
            freqs = [f * 2 for f in PIANO_CH[ch(blk)][1:4]]
            secs = 4 * 4 * beat + 1.0
            place(pads, mt.mk_pad(freqs, int(secs * SR), lfo_hz=0.05, dark=380, bright=1100, amp=0.030), s.t(blk))
    s.add(pads * duck, [(0, 0), (16, 0.5), (48, 0.8), (96, 1.15), (128, 0.9), (176, 0.7), (196, 0.2)])
    del pads

    # --- VOZ ---
    voc = np.zeros((2, s.N))
    hook_s = sing(HOOK, 0.16)
    hook_soft = sing(HOOK, 0.11)
    hook_low = sing(HOOK_LOW, 0.10)
    chop = sing([(440.0, 0.30, 'eh')], 0.09)
    # fragmentos chopeados (offbeat, como percusión) desde el 3er bloque
    for bar in range(40, 96, 8):
        place(voc, chop, s.t(bar + 1, 6))
        place(voc, chop * 0.8, s.t(bar + 5, 14))
    # hook en el groove: cada 4 compases, en el compás de Dm (ch==2)
    for bar in range(48, 96, 4):
        if ch(bar + 2) == 2:
            place(voc, hook_s, s.t(bar + 2) + 0.5 * beat)
    for bar in range(64, 96, 8):                                        # respuesta grave (call-response)
        place(voc, hook_low, s.t(bar + 3) + 0.5 * beat)
    # BREAKDOWN spotlight (104-120): la línea completa
    for i, line in enumerate(BREAK_LINES):
        place(voc, sing(line, 0.17), s.t(104 + i * 4) + 0.5 * beat)
    # clímax (128-168): hook + respuesta + coros
    for bar in range(128, 168, 4):
        if ch(bar + 2) == 2:
            place(voc, hook_s, s.t(bar + 2) + 0.5 * beat)
    for bar in range(132, 168, 8):
        place(voc, hook_low, s.t(bar + 3) + 0.5 * beat)
    for bar in range(144, 160, 4):                                      # segunda línea arriba
        place(voc, sing(BREAK_LINES[(bar // 4) % 2], 0.10), s.t(bar) + 0.5 * beat)
    # outro: ecos de la hook
    place(voc, hook_soft, s.t(170) + 0.5 * beat)
    place(voc, hook_soft * 0.7, s.t(178) + 0.5 * beat)
    throws = fbdelay(voc, beat * 1.0, fb=0.22, damp=2800) * 0.35        # delay 1/4 (throws)
    s.add(voc + throws + reverb(voc, 2.4, damp=3000, mix=0.30))
    del voc, throws

    # --- coros góspel (acordes de voz, solo breakdown→clímax) ---
    cho = np.zeros((2, s.N))
    for bar in range(112, 168, 4):
        freqs = PIANO_CH[ch(bar)][2:5]
        for i, f in enumerate(freqs):
            nt = sing([(f, 4 * beat * 0.92, 'oo' if i != 1 else 'oh')], 0.045)
            place(cho, nt, s.t(bar) + i * 0.03)
    s.add(cho * duck + reverb(cho, 2.8, damp=2600, mix=0.5))
    del cho

    # --- transiciones suaves (sin risers EDM): la marea del género ---
    place(s.mix, mt.riser(beat * 8, s.N, f0=300, f1=2400, amp=0.018), s.t(92))
    place(s.mix, mt.riser(beat * 8, s.N, f0=300, f1=2600, amp=0.022), s.t(124))
    return mt.master(s, 'amr-quedate')

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    print('Sintetizando QUÉDATE (120 BPM · Dm · 196 bars)…', flush=True)
    wav, dur, peaks = build()
    print(f'  WAV: {wav}  ({dur:.1f}s)', flush=True)
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    m4a = os.path.join(HERE, 'audio', 'amr-quedate.m4a')
    subprocess.run([FF, '-y', '-v', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', m4a], check=True)
    print(f'  M4A: {m4a}', flush=True)
    meta = dict(id='amr-quedate', title='QUÉDATE', kicker='THE SINGLE', tracks=1,
                dur=round(dur, 1), titles=['QUÉDATE'], file='audio/amr-quedate.m4a',
                art='art/amr-quedate.svg', edition=20, peaks=peaks, offsets=[0.0], bpm=120, key='D MIN')
    with open(os.path.join(HERE, 'quedate.js'), 'w') as f:
        f.write('window.AMR_QUEDATE=' + json.dumps(meta) + ';')
    print('  quedate.js escrito. done', flush=True)
