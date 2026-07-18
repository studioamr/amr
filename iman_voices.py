#!/usr/bin/env python3
"""IMÁN — paleta techno-electro oscura estilo Volkoder "She Kisses".
Bajo PULSANTE ("throbbing") punchy y con grit, synths CÓSMICOS que cortan
(saws resonantes con glide y LFO), drums de club, zaps sci-fi, atmósfera fría.
Paleta propia — nada compartido. NADA de bajo chicloso: aquí es electro tight."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

# ---------------------------------------------------------------- drums de club
def kick_techno():
    """kick techno profundo y con pegada — clic + cuerpo + cola controlada."""
    n = int(0.42 * SR); t = np.arange(n) / SR
    f = 48.0 + 90.0 * np.exp(-t / 0.012)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    clic = np.exp(-t / 0.0025) * np.sin(2 * np.pi * 1700 * t)
    x = sat(body.astype(np.float32), 1.5, 0.05) + 0.35 * clic.astype(np.float32)
    return lp(x, 3600, 2) * 0.9

def clap(rng):
    """clap electro: 3 flams de ruido + cola."""
    n = int(0.2 * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for d in (0.0, 0.008, 0.016):
        off = int(d * SR)
        env = np.exp(-(t) / 0.012)
        seg = (rng.standard_normal(n).astype(np.float32) * env)
        x[off:] += seg[:n - off]
    tail = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.09) * 0.5
    return bp((x + tail), 1100, 6500, 2) * 0.6

def snare_e(rng):
    n = int(0.16 * SR); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 210 * t) * np.exp(-t / 0.03)
    nz = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.06)
    return sat((tone * 0.5 + bp(nz, 1400, 8000, 2) * 0.9).astype(np.float32) * 0.7, 1.3, 0.08)

def hat(rng, open_=False):
    dec = (0.16 if open_ else 0.022) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32)
    x += 0.4 * np.sign(np.sin(2 * np.pi * 8200 * t)).astype(np.float32)   # metálico
    x *= np.exp(-t / dec)
    return hp(x, 8200, 2) * (0.26 if open_ else 0.34) * rng.uniform(0.85, 1.0)

def rim(rng):
    n = int(0.05 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * rng.uniform(1500, 1700) * t) * np.exp(-t / 0.008)
    return bp(x.astype(np.float32), 900, 4000, 2) * 0.5

def perc_metal(rng, f0=430):
    """percusión metálica inarmónica — el toque industrial."""
    n = int(0.18 * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for r in (1.0, 1.71, 2.43, 3.17):
        x += np.sin(2 * np.pi * f0 * r * t).astype(np.float32) * (1.0 / r)
    x *= np.exp(-t / 0.05)
    return bp(sat(x * 0.4, 1.3, 0.1), 800, 7000, 2) * 0.4

# ---------------------------------------------------------------- EL BAJO (la estrella, pero LIMPIO)
def bass_throb(f, dur, rng, cutoff=520, drive=1.7):
    """bajo electro PULSANTE: 2 saws detune + sub, LP con envolvente, gate en 16vos
    (throb), grit por saturación. Mono, tight, agresivo — NADA chicloso."""
    n = max(8, int(dur * SR)); t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    saw1 = 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    saw2 = 2 * (((ph * 2 ** (7 / 1200)) / (2 * np.pi)) % 1.0) - 1     # detune +7c = reese leve
    sub = np.sin(ph)
    x = (saw1 * 0.5 + saw2 * 0.4 + sub * 0.7).astype(np.float32)
    # envolvente de filtro: abre en el ataque y cierra (movimiento)
    fenv = cutoff * (1.0 + 1.4 * np.exp(-t / 0.035))
    seg = max(1, n // 5); out = np.zeros(n, np.float32)
    for k in range(5):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        c = float(fenv[min(n - 1, (a + b_) // 2)])
        out[a:b_] = lp(x[a:b_], c, 2)
    amp = np.minimum(1.0, t / 0.004) * np.exp(-np.maximum(0.0, t - dur * 0.55) / 0.06)
    out = sat(out * amp.astype(np.float32), drive, 0.06)
    return sat_warm(out) * 0.85

def bass_stab(f, rng):
    """stab de bajo corto y percusivo para los patrones sincopados."""
    return bass_throb(f, 0.13, rng, cutoff=620, drive=2.0)

# ---------------------------------------------------------------- synths CÓSMICOS
def cosmic_lead(f, dur, rng, glide_from=None):
    """lead cósmico: 3 saws detune por filtro RESONANTE con LFO + glide — corta la mezcla."""
    n = int(dur * SR); t = np.arange(n) / SR
    if glide_from:
        fr = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.06)
    else:
        fr = f * np.ones(n, np.float32)
    vib = 2.0 ** (7.0 * np.sin(2 * np.pi * 5.5 * t + rng.uniform(0, 6)) / 1200)
    x = np.zeros(n, np.float32)
    for det in (-11, 0, 12):
        fv = fr * 2 ** (det / 1200) * vib
        ph = 2 * np.pi * np.cumsum(fv) / SR + rng.uniform(0, 6)
        x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.32
    # filtro resonante con LFO (el barrido cósmico)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t / max(0.1, dur) * 4 + rng.uniform(0, 6))
    seg = max(1, n // 10); out = np.zeros(n, np.float32)
    for k in range(10):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        c = 500 + 4500 * float(lfo[min(n - 1, (a + b_) // 2)]) ** 2
        band = bp(x[a:b_], c * 0.55, c * 1.5, 2)                        # banda estrecha = resonancia
        out[a:b_] = x[a:b_] * 0.4 + band * 1.3
    env = np.minimum(1.0, t / 0.015) * np.exp(-np.maximum(0.0, t - dur * 0.8) / 0.14)
    return sat(out * env.astype(np.float32), 1.3, 0.08) * 0.5

def zap(rng, up=False):
    """zap/laser sci-fi que corta — barrido de pitch rápido."""
    n = int(0.22 * SR); t = np.arange(n) / SR
    prog = t / (n / SR)
    f = (400 + 3000 * prog) if up else (3400 - 3000 * prog)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    env = np.exp(-t / 0.06)
    return sat(bp(x * env, 600, 9000, 2), 1.4, 0.1) * 0.4

def stab_synth(ms, dur, rng):
    """stab de acorde electro — saws cortos con filtro-ataque, bien apretado."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-8, 7):
            fv = f * 2 ** (det / 1200)
            ph = 2 * np.pi * fv * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.28
    br = np.minimum(1.0, t / 0.02)
    env = np.minimum(1.0, t / 0.006) * np.exp(-np.maximum(0.0, t - dur * 0.4) / 0.05)
    x = lp(x, 900, 2) + hp(x, 900, 2) * br.astype(np.float32)
    return sat(lp(x * env.astype(np.float32), 7000, 2) * 0.4, 1.3, 0.1)

def pad_cold(ms, dur, rng):
    """pad frío/espacial: saws muy filtrados con batido — la atmósfera."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-9, 0, 8):
            fv = f * 2 ** (det / 1200)
            ph = 2 * np.pi * fv * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.14
    env = np.minimum(1.0, t / 1.0) * np.minimum(1.0, np.maximum(0.0, dur - t) / 1.1)
    return lp(x * env.astype(np.float32), 1700, 2) * 0.42

def vox_robot(f, dur, rng, vow='u'):
    """stab vocal robótico/vocoder — frío, corta como los synths."""
    F = dict(a=((760, 1.0), (1200, 0.5)), o=((520, 1.0), (920, 0.5)),
             u=((360, 1.0), (920, 0.4)), e=((540, 1.0), (2000, 0.4)))[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    src = np.zeros(n, np.float32)
    for h in range(1, 14):
        src += (np.sin(h * ph) / h).astype(np.float32)
    env = np.minimum(1.0, t / 0.01) * np.exp(-np.maximum(0.0, t - dur * 0.5) / 0.06)
    src = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * env.astype(np.float32)  # saw = más robótico
    out = sum(bp(src, fq * 0.9, fq * 1.1, 2) * g for fq, g in F)
    ring = np.sin(2 * np.pi * 90 * t)                                   # ring-mod leve = grit robótico
    return sat((out * (0.7 + 0.3 * ring)).astype(np.float32) * 0.6, 1.3, 0.09)

def riser(dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    nz = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32); seg = max(1, n // 24)
    for k in range(24):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        p = float(prog[min(n - 1, (a + b_) // 2)])
        out[a:b_] = bp(nz[a:b_], 200 + 6000 * p ** 2, 500 + 9000 * p ** 2, 2)
    return (out * (prog ** 1.5)).astype(np.float32) * 0.4

def downlift(rng):
    n = int(0.5 * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    f = 900 * (1 - prog) + 60
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t / 0.28)).astype(np.float32) * 0.5

def impact(rng):
    n = int(1.2 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (60 + 40 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.4)
    nz = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.5)
    return (sat(boom.astype(np.float32), 1.3, 0.05) + bp(nz, 200, 4000, 2) * 0.5) * 0.6

if __name__ == '__main__':
    from dream_core import wav_write, spectrum_pct
    rng = np.random.default_rng(5)
    bpm = 126; spb = int(SR * 240 / bpm); s16 = spb / 16
    n = spb * 2; mix = np.zeros(n, np.float32)
    def put(buf, pos, x, g=1.0):
        pos = int(pos); e = min(len(buf), pos + len(x))
        if e > pos: buf[pos:e] += x[:e - pos] * g
    K = kick_techno()
    for bar in range(2):
        base = bar * spb
        for b in range(4): put(mix, base + b * 4 * s16, K)
        put(mix, base + 4 * s16, clap(rng), 0.7); put(mix, base + 12 * s16, clap(rng), 0.7)
        for s in range(16): put(mix, base + s * s16, hat(rng), 0.4 if s % 2 else 0.24)
        # bajo pulsante sincopado
        pat = [(0, 33), (3, 33), (6, 33), (8, 45), (10, 33), (11, 33), (14, 40)]
        for st, m in pat:
            put(mix, base + st * s16, bass_stab(midi_f(m - 12), rng), 0.9)
    put(mix, 0, cosmic_lead(midi_f(69), 0.9, rng), 0.6)
    put(mix, spb + 8 * s16, zap(rng), 0.7)
    mix /= max(1e-9, np.abs(mix).max())
    wav_write('_test_iman.wav', np.stack([mix, mix]))
    print('IMÁN groove:', {k: round(v, 1) for k, v in spectrum_pct(mix).items()})
    print('_test_iman.wav listo')
