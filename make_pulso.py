#!/usr/bin/env python3
"""PULSO — melodic techno estilo Anyma/Afterlife (investigado, 100% original).
125 BPM · La menor · 224 compases = 7:10.
Narrativa: el primer latido de algo que despierta.
Señal → Despertar → Memoria → Trascendencia → Disolución."""
import os, json, subprocess, wave
import numpy as np, imageio_ffmpeg
import make_tracks as mt

SR = mt.SR; rng = mt.rng
HERE = os.path.dirname(os.path.abspath(__file__))
place, reverb, fbdelay, duck_env = mt.place, mt.reverb, mt.fbdelay, mt.duck_env
lowpass, highpass, bandpass, softclip = mt.lowpass, mt.highpass, mt.bandpass, mt.softclip

def st(y, pan=1.0): return np.vstack([y * pan, y * (2 - pan)])

def saw_partials(f, t, K=16):
    y = np.zeros(len(t))
    for k in range(1, K + 1):
        if k * f > 15000: break
        y += np.sin(2 * np.pi * k * f * t) / k
    return y

def saw_from_phase(ph, K=12):
    y = np.zeros(len(ph))
    for k in range(1, K + 1):
        y += np.sin(k * ph) / k
    return y

# ---------- percusión ----------
def snare_hit(amp=0.15):
    n = int(0.09 * SR); t = np.arange(n) / SR
    y = bandpass(rng.standard_normal(n), 950, 0.9) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 60)
    return st(y * np.exp(-t / 0.03) * amp)

def impact_hit(amp=0.5):
    n = int(1.5 * SR); t = np.arange(n) / SR
    f = 58 * (1 + 0.6 * np.exp(-t * 16))
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.5)
    air = highpass(rng.standard_normal(n), 2400) * np.exp(-t / 0.28) * 0.22
    return st((boom + air) * amp)

# ---------- bass (rolling 1/16, la firma) ----------
def sub16(f, amp=0.40):
    n = int(0.100 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.26 * np.sin(4 * np.pi * f * t)
    e = np.ones(n); a = int(0.004 * SR); r = int(0.030 * SR)
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    return st(y * e * amp)

def top16(f, amp=0.15):
    n = int(0.100 * SR); t = np.arange(n) / SR
    y = saw_partials(f * 2, t, 10) + 0.6 * saw_partials(f * 2 * 1.006, t, 8)
    y = highpass(lowpass(y, 950), 92)
    e = np.ones(n); a = int(0.003 * SR); r = int(0.030 * SR)
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    return st(y * e * amp)

# ---------- arpegio (identidad #1) ----------
def arp16(f, amp=0.14, lp=4500, dur=0.16, dec=0.065):
    n = int(dur * SR); t = np.arange(n) / SR
    y = saw_partials(f, t, 14) + 0.55 * saw_partials(f * 1.004, t, 10) + 0.55 * saw_partials(f * 0.996, t, 10)
    y = lowpass(y, lp)
    e = np.exp(-t / dec); a = int(0.002 * SR); e[:a] *= np.linspace(0, 1, a)
    return st(y * e * amp / 2.1)

# ---------- FM shots (drops) ----------
def fm_shot(f, amp=0.2):
    n = int(0.22 * SR); t = np.arange(n) / SR
    mod = np.sin(2 * np.pi * f * 1.01 * t) * 0.7
    y = np.zeros(n)
    for det in (1.0, 1.006, 0.994):
        y += np.sin(2 * np.pi * f * 2 * det * t + 2.2 * mod)
    y = softclip(lowpass(y, 2600), 1.6)
    e = np.exp(-t / 0.08); a = int(0.002 * SR); e[:a] *= np.linspace(0, 1, a)
    return st(y * e * amp / 2.5)

# ---------- mantra robótico (identidad emocional A) ----------
def mantra_syll(f, dur, amp=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    src = saw_partials(f, t, 24) * (1 + 0.22 * np.sin(2 * np.pi * 31 * t))
    v = bandpass(src, 500, 1.1) + 0.8 * bandpass(src, 1080, 1.2) + 0.45 * bandpass(src, 2400, 1.3)
    e = np.ones(n); a = int(0.012 * SR); r = int(min(0.05 * SR, n // 3))
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    return st(lowpass(v, 3400) * e * amp)

MANTRA_SYL = [(0.0, 110.0, 0.22), (0.5, 110.0, 0.20), (1.0, 103.83, 0.18),
              (1.75, 98.0, 0.30), (2.5, 110.0, 0.20), (3.0, 87.31, 0.45)]

# ---------- vocal etérea (identidad emocional B) ----------
def fem_note(f, dur, amp=0.15):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 0.012 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.5)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib)) / SR
    tone = np.sin(ph) + 0.42 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph) + 0.08 * np.sin(4 * ph)
    tone = bandpass(tone, min(f * 2.2, 2200), 0.8) * 0.8 + tone * 0.55
    e = np.ones(n); a = int(0.14 * SR); r = int(min(0.4 * SR, n // 3))
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    y = highpass(tone, 200) * e * amp
    return np.vstack([y * 0.96, y * 1.04])

# frase etérea de 8 compases: E4 A4 | B4 C5 B4 | A4 E4 | C5 B4 A4
FEM_PHRASE = [(0, 0, 329.63, 3), (0, 3, 440.0, 4),
              (2, 0, 493.88, 3), (2, 3, 523.25, 2), (3, 1.5, 493.88, 2.5),
              (4, 0, 440.0, 3), (4, 3, 329.63, 4),
              (6, 0, 523.25, 2), (6, 2, 493.88, 2), (7, 0, 440.0, 3.5)]

# ---------- gated lead (identidad #2 — solo drop 2) ----------
def gated_lead(freqs, secs, beat, amp=0.16):
    n = int(secs * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for fi, f in enumerate(freqs):
        for vi, det in enumerate((1.0, 1.007, 0.993, 1.012, 0.988)):
            mor = 1 + 0.005 * np.sin(2 * np.pi * t / (4 * beat) + vi * 1.3 + fi)
            ph = 2 * np.pi * np.cumsum(f * det * mor) / SR
            y += saw_from_phase(ph, 10) / len(freqs)
    y = lowpass(y, 3600)
    g = (np.sin(2 * np.pi * t / (beat * 0.5)) > 0).astype(float)
    g = lowpass(g, 45) + 0.12
    e = np.ones(n); a = int(0.05 * SR); r = int(min(0.4 * SR, n // 4))
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r)
    y = y * np.clip(g, 0, 1.1) * e * amp / 2.3
    return np.vstack([y * 1.06, y * 0.94])

def choir_gate(freqs, secs, beat, amp=0.07):
    base = mt.mk_pad(freqs, int(secs * SR), lfo_hz=0.07, dark=800, bright=2400, amp=amp)
    n = base.shape[1]; t = np.arange(n) / SR
    g = (np.sin(2 * np.pi * t / (beat * 0.5)) > -0.25).astype(float)
    g = lowpass(g, 55) + 0.12
    return base * np.clip(g, 0, 1.1)

def pitch_riser(bars_len, beat, amp=0.05):
    secs = bars_len * 4 * beat; n = int(secs * SR); t = np.arange(n) / SR
    f = 110 * 2 ** (-1 + t / secs)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.33 * np.sin(3 * ph)
    y = lowpass(y, 1800) * np.linspace(0.12, 1, n) ** 1.5 * amp
    return st(y)

# ---------- armonía: Am(add9) — Fmaj7 — C(add9) — G  (cambio cada 2 compases) ----------
MAIN = [
    dict(root=55.00, pad=[220.00, 261.63, 329.63, 493.88], arp=[220.00, 440.00, 523.25, 659.25], lead=[220.00, 329.63, 440.00, 523.25]),
    dict(root=43.65, pad=[174.61, 220.00, 261.63, 329.63], arp=[174.61, 349.23, 440.00, 523.25], lead=[174.61, 261.63, 349.23, 523.25]),
    dict(root=65.41, pad=[261.63, 293.66, 329.63, 392.00], arp=[261.63, 392.00, 523.25, 659.25], lead=[261.63, 392.00, 523.25, 587.33]),
    dict(root=49.00, pad=[196.00, 246.94, 293.66, 392.00], arp=[196.00, 392.00, 493.88, 587.33], lead=[196.00, 293.66, 392.00, 493.88]),
]
BREAK = [
    [220.00, 261.63, 329.63, 493.88],   # Am(add9)
    [164.81, 196.00, 246.94, 293.66],   # Em7
    [174.61, 220.00, 261.63, 329.63],   # Fmaj7
    [146.83, 174.61, 220.00, 329.63],   # Dm9
]
def mch(bar): return MAIN[(bar // 2) % 4]
def rng_in(bar, spans): return any(a <= bar < b for a, b in spans)

ARP_PAT = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 3, 2]

def build():
    s = mt.Song(125, 224)            # 224 compases @ 125 = 7:10, grid recto
    beat = s.beat
    print('  grid: %.2fs/bar · total %.1fs' % (4 * beat, s.dur), flush=True)

    KICK_ON = [(0, 64), (64, 112), (160, 224)]
    HATS_ON = [(0, 64), (64, 112), (160, 224)]
    BASS_ON = [(16, 64), (64, 112), (160, 208)]
    TOPB_ON = [(32, 64), (64, 112), (160, 208)]

    # --- kick + hats ---
    kick_s = mt.mk_kick(f0=112, f1=52, amp=0.62, dur=0.50)
    kick_hp = highpass(mt.mk_kick(f0=112, f1=52, amp=0.5, dur=0.4), 320)
    ho, hc = mt.mk_hat(True), mt.mk_hat(False)
    drums = np.zeros((2, s.N))
    for bar in range(s.bars):
        if rng_in(bar, KICK_ON):
            for stp in [0, 4, 8, 12]:
                place(drums, kick_s, s.t(bar, stp)); s.kick_times.append(s.t(bar, stp))
        if 152 <= bar < 158:                                  # kick fantasma HP (build 2)
            for stp in [0, 4, 8, 12]:
                place(drums, st(kick_hp * 0.6), s.t(bar, stp))
        if rng_in(bar, HATS_ON):
            lite = bar < 32                                    # intro: percusión mínima
            for stp in range(16):
                if lite and stp % 2 == 0 and stp % 4 != 2: continue
                h = ho if stp % 4 == 2 else hc
                pan = 0.92 if (stp // 2) % 2 else 1.08
                g = 0.62 if stp % 4 == 2 else (0.4 if stp % 2 else 0.26)
                place(drums, st(h * (0.55 if lite else 1.0) * g, pan), s.t(bar, stp))
    # snare rolls (builds)
    for bar, div in [(60, 8), (61, 8), (62, 16), (63, 16)]:
        for k in range(div):
            place(drums, snare_hit(0.10 + 0.05 * k / div), s.t(bar) + k * (4 * beat / div))
    for bar, div in [(156, 8), (157, 16), (158, 16), (159, 32)]:
        for k in range(div):
            place(drums, snare_hit(0.10 + 0.07 * k / div), s.t(bar) + k * (4 * beat / div))
    s.add(drums); del drums
    duck = duck_env(s.N, s.kick_times, depth=0.55, rec=0.32)

    # --- rolling bass 1/16 (sub + top) ---
    bass = np.zeros((2, s.N))
    subc, topc = {}, {}
    for bar in range(s.bars):
        f = mch(bar)['root']
        if rng_in(bar, [(48, 56)]): f = 55.00                  # build 1: A
        if rng_in(bar, [(56, 60)]): f = 43.65                  # → F
        if rng_in(bar, [(60, 64)]): f = 49.00                  # → G (resuelve a Am en el drop)
        if rng_in(bar, BASS_ON):
            if f not in subc: subc[f] = sub16(f)
            for stp in range(16):
                place(bass, subc[f], s.t(bar, stp))
        if rng_in(bar, TOPB_ON):
            if f not in topc: topc[f] = top16(f)
            for stp in range(16):
                place(bass, topc[f], s.t(bar, stp))
    # intro B: sub filtrado más oscuro (LP ya es sine; bajamos ganancia por autom.)
    s.add(bass * duck, [(0, 0.0), (16, 0.55), (32, 0.8), (48, 1.0), (64, 1.15), (96, 1.0),
                        (112, 0.0), (160, 1.2), (200, 1.0), (208, 0.0)])
    del bass

    # --- arpegio (identidad #1): dark → open por crossfade ---
    def render_arp(spans, lp, amp, transpose_at_D=True):
        buf = np.zeros((2, s.N)); cache = {}
        for bar in range(s.bars):
            if not rng_in(bar, spans): continue
            ch = mch(bar)
            tones = ch['arp']
            if transpose_at_D and 88 <= bar < 96:              # drop1 bloque D: al VI (F)
                tones = MAIN[1]['arp']
            for stp in range(16):
                f = tones[ARP_PAT[stp]]
                key = (f, lp)
                if key not in cache: cache[key] = arp16(f, amp, lp)
                pan = 0.9 if stp % 2 else 1.1
                place(buf, cache[key] * [[pan], [2 - pan]], s.t(bar, stp))
        return buf
    arp_dark = render_arp([(32, 64)], 900, 0.13)
    arp_open = render_arp([(48, 96), (148, 160), (160, 208)], 4800, 0.14)
    # crossfade dark→open durante el build (48-64)
    arp = arp_dark * mt.smooth_gain(s.N, [(s.t(0), 1), (s.t(48), 1), (s.t(63), 0.15)]) \
        + arp_open * mt.smooth_gain(s.N, [(s.t(0), 0), (s.t(48), 0.12), (s.t(60), 0.85), (s.t(64), 1),
                                          (s.t(96), 1), (s.t(148), 0.4), (s.t(156), 0.9), (s.t(160), 1),
                                          (s.t(200), 1), (s.t(208), 0)])
    del arp_dark, arp_open
    arp = arp + fbdelay(arp, beat * 0.75, fb=0.22, damp=5000) * 0.5    # delay dotted 1/8
    s.add(arp * duck + reverb(arp, 2.0, damp=4200, mix=0.2) * duck)
    # atmósfera: el tema reversed con reverb larga (intro + breakdown)
    seg = arp[:, int(s.t(64) * SR):int(s.t(72) * SR)]
    atm = np.flip(reverb(seg, 2.8, damp=3000, mix=1.0), axis=1)
    for tt, g in [(s.t(0), 0.5), (s.t(16), 0.6), (s.t(112), 0.4), (s.t(193), 0.5)]:
        place(s.mix, atm * g, tt)
    del arp, seg, atm

    # --- breakdown: tema a mitad de velocidad (1/8) limpio + pads BREAK ---
    half = np.zeros((2, s.N))
    for bar in range(112, 144):
        tones = BREAK[(bar // 2) % 4]
        for k in range(8):
            f = tones[[0, 1, 2, 3, 0, 2, 1, 3][k]] * 2
            nt = arp16(f, 0.11, 2600, dur=0.34, dec=0.16)
            pan = 0.88 if k % 2 else 1.12
            place(half, nt * [[pan], [2 - pan]], s.t(bar) + k * beat / 2)
    half = half + fbdelay(half, beat * 0.75, fb=0.3, damp=3600) * 0.55
    s.add(half * mt.smooth_gain(s.N, [(s.t(112), 0.7), (s.t(132), 1.0), (s.t(136), 0.35), (s.t(144), 0)])
          + reverb(half, 2.4, damp=3000, mix=0.35))
    del half

    # --- pads (3 capas, evolución por automatización) ---
    pads = np.zeros((2, s.N))
    for blk in range(8, s.bars, 2):
        use_break = 112 <= blk < 144
        freqs = BREAK[(blk // 2) % 4] if use_break else mch(blk)['pad']
        secs = 2 * 4 * beat + 0.8
        dark = mt.mk_pad(freqs, int(secs * SR), lfo_hz=0.05, dark=320, bright=900, amp=0.045)
        mid = mt.mk_pad(freqs, int(secs * SR), lfo_hz=0.06, dark=500, bright=1500, amp=0.035)
        air = mt.mk_pad([f * 2 for f in freqs[1:]], int(secs * SR), lfo_hz=0.07, dark=1200, bright=2600, amp=0.02)
        place(pads, dark + mid + air, s.t(blk))
    s.add(pads * duck, [(0, 0.0), (16, 0.5), (32, 0.7), (48, 0.9), (64, 0.55), (96, 0.7),
                        (112, 1.25), (136, 0.5), (140, 0.9), (144, 1.0), (160, 0.8),
                        (192, 0.9), (208, 0.6), (224, 0.2)])
    del pads

    # --- FM shots (drops, en los huecos) ---
    shots = np.zeros((2, s.N))
    for bar in range(s.bars):
        if not (rng_in(bar, [(72, 96)]) or rng_in(bar, [(160, 192)])): continue
        ch = mch(bar)
        if bar % 2 == 1:
            place(shots, fm_shot(ch['arp'][1], 0.19), s.t(bar, 6))
            place(shots, fm_shot(ch['arp'][2], 0.16), s.t(bar, 14))
    shots = shots + fbdelay(shots, beat * 0.5, fb=0.25, damp=2600) * 0.4
    s.add(shots * duck); del shots

    # --- mantra robótico ---
    voc = np.zeros((2, s.N))
    def mantra_at(bar, amp, syls=None):
        for beat_off, f, d in (syls or MANTRA_SYL):
            place(voc, mantra_syll(f, d, amp), s.t(bar) + beat_off * beat)
    mantra_at(40, 0.10)                                        # susurro (muy mojado, ver reverb)
    mantra_at(56, 0.15); mantra_at(58, 0.13)
    for b in (80, 84, 88, 92):                                 # drop1: llamada-respuesta con el arp
        mantra_at(b, 0.15)
    mantra_at(100, 0.08); mantra_at(106, 0.07)                 # eco fantasma (puente)
    mantra_at(156, 0.16, [(0.0, 110.0, 0.22), (0.75, 98.0, 0.25), (1.5, 87.31, 0.5)])
    for b in (168, 176, 184):                                  # drop2 debajo del lead
        mantra_at(b, 0.13)
    voc = voc + fbdelay(voc, beat * 0.75, fb=0.3, damp=2200) * 0.5
    s.add(voc * duck + reverb(voc, 2.6, damp=2400, mix=0.5))
    del voc

    # --- vocal etérea femenina ---
    fem = np.zeros((2, s.N))
    def fem_phrase(start_bar, amp, with_reverse=True):
        for pb, bt, f, bts in FEM_PHRASE:
            note = fem_note(f, bts * beat * 0.97, amp)
            t0 = s.t(start_bar + pb) + bt * beat
            place(fem, note, t0)
            if with_reverse and bt == 0:                       # reverse reverb antes de la frase
                tail = reverb(note, 2.2, damp=2600, mix=1.0)
                rr = np.flip(tail[:, :int(1.4 * SR)], axis=1) * 0.5
                place(fem, rr, max(0.0, t0 - 1.4))
    fem_phrase(120, 0.13)
    fem_phrase(128, 0.15)
    fem_phrase(136, 0.17)                                      # casi a capela (pads bajan)
    fem_phrase(164, 0.12, with_reverse=False)                  # drop 2, encima de todo
    fem_phrase(172, 0.13, with_reverse=False)
    fem_phrase(180, 0.13, with_reverse=False)
    s.add(fem + reverb(fem, 2.6, damp=2800, mix=0.42))
    del fem

    # --- gated lead + choir (SOLO drop 2) ---
    lead = np.zeros((2, s.N))
    for blk in range(160, 192, 2):
        ch = mch(blk)
        seg = gated_lead(ch['lead'], 2 * 4 * beat + 0.4, beat, amp=0.17)
        place(lead, seg, s.t(blk))
    lead[0] = highpass(lead[0], 160); lead[1] = highpass(lead[1], 160)
    grow = mt.smooth_gain(s.N, [(s.t(160), 0.9), (s.t(176), 1.0), (s.t(190), 1.1), (s.t(192), 0)])
    s.add(lead * duck * grow + reverb(lead, 2.4, damp=3200, mix=0.3) * grow)
    del lead
    cho = np.zeros((2, s.N))
    for blk in range(160, 200, 2):
        ch = mch(blk)
        place(cho, choir_gate([f * 2 for f in ch['pad'][:3]], 2 * 4 * beat + 0.5, beat, amp=0.05), s.t(blk))
    s.add(cho * duck * mt.smooth_gain(s.N, [(s.t(160), 0.8), (s.t(192), 1.0), (s.t(200), 0)]))
    del cho

    # --- FX: risers, impacts, downlifter ---
    place(s.mix, mt.riser(beat * 4 * 8, s.N, f0=400, f1=6500, amp=0.055), s.t(56))
    place(s.mix, mt.riser(beat * 4 * 16, s.N, f0=300, f1=7500, amp=0.065), s.t(144))
    place(s.mix, pitch_riser(8, beat, amp=0.05), s.t(152))
    dl = np.flip(mt.riser(beat * 4 * 4, int(beat * 4 * 4 * SR) + 100, f0=500, f1=6000, amp=0.05), axis=1)
    place(s.mix, dl, s.t(96))                                  # downlifter al puente
    place(s.mix, impact_hit(0.45), s.t(64))
    place(s.mix, impact_hit(0.30), s.t(112))
    place(s.mix, impact_hit(0.55), s.t(160))

    # --- LOS SILENCIOS (el medio compás más importante) ---
    for t0, t1 in [(s.t(63, 8), s.t(64)), (s.t(159, 8), s.t(160))]:
        i0, i1 = int(t0 * SR), int(t1 * SR)
        fade = int(0.012 * SR)
        s.mix[:, i0 - fade:i0] *= np.linspace(1, 0, fade)
        s.mix[:, i0:i1] = 0.0
    return mt.master(s, 'amr-pulso')

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    print('Sintetizando PULSO (125 BPM · Am · 224 bars)…', flush=True)
    wav, dur, peaks = build()
    print(f'  WAV: {wav}  ({dur:.1f}s)', flush=True)
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    m4a = os.path.join(HERE, 'audio', 'amr-pulso.m4a')
    subprocess.run([FF, '-y', '-v', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', m4a], check=True)
    print(f'  M4A: {m4a}', flush=True)
    meta = dict(id='amr-pulso', title='PULSO', kicker='THE SINGLE', tracks=1,
                dur=round(dur, 1), titles=['PULSO'], file='audio/amr-pulso.m4a',
                art='art/amr-pulso.svg', edition=20, peaks=peaks, offsets=[0.0], bpm=125, key='A MIN')
    with open(os.path.join(HERE, 'pulso.js'), 'w') as f:
        f.write('window.AMR_PULSO=' + json.dumps(meta) + ';')
    print('  pulso.js escrito. done', flush=True)
