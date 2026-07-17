#!/usr/bin/env python3
"""FIEBRE — EL SINGLE (~4:50, 126 BPM, La menor). Estructura de CANCIÓN, no de set:
INTRO → GROOVE → BUILD → DROP 1 → BREAKDOWN → BUILD → DROP 2 (contramelodía) → OUTRO.
Detalle por segundo: gancho memorable, risers, impactos, reversos, sweeps, crackle,
silencio real antes de cada drop. Instrumentos del motor v4 (make_hechizo)."""
import os, sys
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, sat_warm, widen, sub_mono, pingpong,
                        stereo_verb, master_file, ffmeter, wav_write, spectrum_pct, fconv)
from make_hechizo import (KICK, hit_conga, hit_bongo, hit_shaker, hit_hat, hit_rim,
                          hit_cincel, kalimba, rhodes, campana, lead_warm, bass_note,
                          supersaw_st, midi_f, deg, NAT, DOR, _saw, drift)

HERE = os.path.dirname(os.path.abspath(__file__))
BPM = 126.0
SPB = int(round(SR * 240.0 / BPM))
S16 = SPB / 16.0
BEAT_S = 60.0 / BPM
SW = dict(bass=0.54, hats=0.57, shaker=0.56, conga=0.55, keys=0.55)
ROOT, SC = 45, NAT                      # La menor
CHORDS = [[45, 52, 60, 64], [41, 48, 57, 60], [48, 55, 64, 67], [43, 50, 58, 62]]  # Am9 F C G

# EL GANCHO — 2 compases, sincopado, contorno cantable (compuesto primero, lección Léger)
HOOK = [(0, 4, 1, 2), (3, 6, 1, 1), (6, 5, 1, 2), (10, 7, 1, 3), (14, 6, 1, 1),
        (16, 4, 1, 2), (19, 6, 1, 1), (22, 8, 1, 2), (26, 7, 1, 2), (29, 5, 1, 3)]
COUNTER = [(2, 9, 1, 2), (8, 8, 1, 2), (18, 9, 1, 2), (24, 11, 1, 3)]   # terceras arriba, a contratiempo

SONG = [('intro', 16), ('groove', 16), ('build', 8), ('drop', 40),
        ('break', 16), ('build2', 8), ('drop2', 32), ('outro', 16)]

def sw16(s, who):
    return s * S16 + (SW[who] - 0.5) * 2 * S16 * (s % 2)

def add(buf, pos, x, g=1.0):
    pos = int(pos)
    if pos < 0: x = x[-pos:]; pos = 0
    end = min(len(buf), pos + len(x))
    if end > pos: buf[pos:end] += x[:end - pos] * g

def riser(bars, rng):
    n = int(bars * SPB)
    t = np.arange(n) / n
    noise = rng.standard_normal(n).astype(np.float32)
    x = hp(noise, 400, 2) * (t ** 2.6).astype(np.float32) * 0.22
    f = 180.0 * (2 ** (t * 2.2))
    x += np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32) * (t ** 3).astype(np.float32) * 0.12
    return x

def downlifter(rng):
    n = int(2 * BEAT_S * SR)
    t = np.arange(n) / n
    f = 600.0 * (0.14 ** t)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5) * 0.4).astype(np.float32)

def impact(rng):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 42 * t) * np.exp(-t / 0.35) * 0.9
    x += lp(rng.standard_normal(n).astype(np.float32), 900, 2) * np.exp(-t / 0.09) * 0.5
    return sat(x.astype(np.float32), 1.6, 0.1)

def revcym(rng):
    h = hit_hat(rng, open_=True)
    n = int(1 * SPB)
    pad = np.zeros(n, np.float32); pad[-len(h):] = h[::-1] if len(h) <= n else h[:n][::-1]
    return pad * np.linspace(0.1, 1.0, n).astype(np.float32) * 0.45

def hit_clap(rng):
    """clap de club: 4 flams de ruido muy juntos + cola corta, banda media-alta."""
    n = int(0.24 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for d in (0.0, 0.007, 0.013, 0.019):                 # los flams del clap
        o = int(d * SR)
        burst = (rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.006))
        if o < n:
            x[o:] += burst[:n - o] * rng.uniform(0.85, 1.0)
    tail = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.055)   # cuerpo/cola del clap
    x = bp(x + tail * 0.4, 1100, 6200, 2)
    return x * 0.55

def hit_hat_fine(rng, open_=False):
    """hat cristalino: agudo, corto, limpio — el 'tss' fino del banger."""
    dec = (0.26 if open_ else 0.026) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * np.exp(-t / dec)
    x = hp(x, rng.uniform(8800, 9600), 2)
    return x * (0.42 if open_ else 0.5) * rng.uniform(0.85, 1.0)

def build():
    rng = np.random.default_rng(77)
    total = sum(b for _, b in SONG) * SPB + 4 * SPB
    kickb = np.zeros(total, np.float32); bassb = np.zeros(total, np.float32)
    drumb = np.zeros(total, np.float32); hookb = np.zeros(total, np.float32)
    fxb = np.zeros(total, np.float32); padL = np.zeros(total, np.float32); padR = np.zeros(total, np.float32)
    kick_pos = []

    # crackle de vinilo — la firma MONUMENTS, todo el track
    ck = np.zeros(total, np.float32)
    for p in rng.integers(0, total - 50, 2600):
        ck[p:p + 3] += rng.uniform(-1, 1)
    fxb += lp(ck, 6000, 2) * 0.012

    def hook_at(base, cutoff, g, octs=0, wide=False, counter=False):
        prev = None
        seq = HOOK + (COUNTER if counter else [])
        for (s, d, o, ln) in sorted(seq):
            m = deg(ROOT, SC, d, o) + 12 * octs
            f = midi_f(m)
            x = lead_warm(prev or f, f, ln * S16 / SR * 1.15, seed=9000 + s + base % 97, cutoff=cutoff)
            add(hookb, base + sw16(s % 16, 'keys') + SPB * (s // 16), x, g)
            if wide and (s % 8 == 0):                    # doble kalimba de brillo en los drops
                add(hookb, base + sw16(s % 16, 'keys') + SPB * (s // 16), kalimba(f * 2, 0.5, rng), g * 0.28)
            prev = f

    pos_bar = 0
    for name, bars in SONG:
        for bar in range(bars):
            gb = pos_bar + bar
            base = gb * SPB
            ch = CHORDS[(gb // 2) % 4]
            in_drop = name in ('drop', 'drop2')
            e = dict(intro=0.35, groove=0.6, build=0.75, drop=0.85, targ=0.5,
                     drop2=0.85, outro=0.4).get(name, 0.5)
            # KICK
            if name not in ('break',) and not (name == 'intro' and bar < 4):
                for beat in range(4):
                    if name.startswith('build') and bar == bars - 1 and beat >= 2: continue
                    add(kickb, base + beat * 4 * S16, KICK, 1.0 if in_drop else 0.85)
                    kick_pos.append(int(base + beat * 4 * S16))
            # BAJO rolling (figura rota cada 8)
            if name in ('groove', 'drop', 'drop2', 'build', 'build2', 'outro') and not (name == 'outro' and bar >= 8):
                fr = midi_f(ch[0] - 12)
                VAR = [[s for s in range(16) if s % 4 != 0], [2, 3, 6, 7, 10, 11, 14, 15], [1, 3, 6, 9, 11, 14]]
                steps = VAR[(gb // 8) % 3]
                fc = 700 + (300 if in_drop else 0)
                for s in steps:
                    if rng.uniform() < 0.1: continue
                    f = fr * (2.0 if (s % 8 == 7 and rng.uniform() < 0.4) else 1.0)
                    add(bassb, base + sw16(s, 'bass') + rng.normal(0, 0.004) * SR,
                        bass_note(f, S16 / SR * 1.7, rng, 'roll', fc), 0.9 if s % 4 == 2 else 0.65)
                if bar % 8 == 7:
                    for k, d in enumerate([0, 2, 3, 4]):
                        add(bassb, base + sw16(12 + k, 'bass'),
                            bass_note(midi_f(deg(ROOT, SC, d, 0) - 12), S16 / SR * 1.5, rng, 'roll', fc * 1.2), 0.75)
            # DRUMS — limpio y fino: CLAP en el backbeat + hats cristalinos + shaker sutil
            if e >= 0.55:
                # CLAP en 2 y 4 (el corazón del groove de club)
                for s in (4, 12):
                    add(drumb, base + sw16(s, 'hats') + rng.normal(0, .003) * SR, hit_clap(rng), e * 0.7)
                if bar % 4 == 3:                                              # ghost clap que empuja
                    add(drumb, base + sw16(14, 'hats'), hit_clap(rng), e * 0.28)
            if e >= 0.5:
                # hats cerrados finos en los offbeats
                for s in (2, 6, 10, 14):
                    add(drumb, base + sw16(s, 'hats') + rng.normal(0, .003) * SR, hit_hat_fine(rng), e * 0.42)
                if in_drop:                                                   # 16ths finos, muy bajitos, en los drops
                    for s in range(16):
                        if s % 4 != 0:
                            add(drumb, base + sw16(s, 'hats'), hit_hat_fine(rng), e * 0.13 * (1.0 if s % 2 else 0.55))
                if bar % 2 == 1:                                              # open hat aireado en el offbeat
                    add(drumb, base + sw16(6, 'hats'), hit_hat_fine(rng, open_=True), e * 0.32)
            # shaker: textura sutil, no protagonista
            if e >= 0.6:
                for s in range(0, 16, 2):
                    add(drumb, base + sw16(s, 'shaker') + rng.normal(0, .003) * SR, hit_shaker(rng), 0.10 * (1.0 if s % 4 == 2 else 0.55))
            # conga: un solo acento cálido por compás, no machaca
            if e >= 0.6 and bar % 2 == 0:
                add(drumb, base + sw16(7, 'conga') + rng.normal(0, .004) * SR, hit_conga(rng, open_=True), e * 0.26)
            # fill fino de fin de frase (rim, no cincel)
            if e >= 0.6 and bar % 8 == 7:
                for k, s in enumerate((12, 13, 14, 15)):
                    add(drumb, base + sw16(s, 'hats'), hit_rim(rng), e * (0.22 + 0.06 * k))
            # EL GANCHO
            if bar % 2 == 0:
                if name == 'intro' and bar >= 8:
                    hook_at(base, 420 + 60 * bar, 0.30)                      # asomándose filtrado
                elif name == 'groove' and bar >= 8:
                    hook_at(base, 900, 0.38)
                elif name == 'drop':
                    hook_at(base, 1700, 0.46, wide=True)
                elif name == 'drop2':
                    hook_at(base, 1900, 0.46, octs=(1 if bar >= 16 else 0), wide=True, counter=True)
                elif name == 'break':
                    hook_at(base, 1400, 0.42)                                 # solo, con reverb enorme después
            # PADS (break y builds) + campana de tensión
            if name in ('break', 'build', 'build2') and bar % 2 == 0:
                durp = int(2 * SPB * 1.05)
                for ni, m in enumerate(ch[1:]):
                    st = supersaw_st(midi_f(m), durp, 0.4, 0.7, seed=gb * 7 + ni)
                    env = np.minimum(1, np.arange(durp) / (0.8 * SR)).astype(np.float32)
                    add(padL, base, st[0] * env, 0.10); add(padR, base, st[1] * env, 0.10)
            if name == 'break' and bar % 4 == 0:
                add(hookb, base, campana(midi_f(deg(ROOT, SC, [0, 4, 2, 4][(bar // 4) % 4], 1)), 3.0, rng), 0.4)
            # EAR CANDY por transición
            if name.startswith('build') and bar == 0:
                add(fxb, base, riser(bars, rng), 0.3)
            if in_drop and bar == 0:
                add(fxb, base, impact(rng), 0.55)
            if in_drop and bar % 8 == 0 and bar > 0:
                swp = bp(rng.standard_normal(int(SPB)).astype(np.float32), 2000, 8000, 2)
                add(fxb, base, swp * np.linspace(0, 0.07, int(SPB)).astype(np.float32) ** 1.5, 1.0)
            if in_drop and bar == bars - 1:
                add(fxb, base + SPB - int(0.1 * SR), downlifter(rng), 1.0)
            if name.startswith('build') and bar == bars - 1:
                add(fxb, base, revcym(rng), 1.0)
        pos_bar += bars

    # SILENCIO real de medio compás antes de cada drop (queda solo el riser/reverso)
    acc = 0
    for name, bars in SONG:
        if name in ('drop', 'drop2'):
            c1 = acc * SPB; c0 = c1 - SPB // 2
            fade = np.linspace(1, 0, c1 - c0).astype(np.float32) ** 0.3
            for bufz in (kickb, bassb, drumb, hookb):
                bufz[c0:c1] *= fade
        acc += bars

    # MEZCLA estéreo (cadena v4)
    from make_hechizo import sidechain_env, _verb_ir
    env = sidechain_env(total, kick_pos, depth=0.5, rel_s=0.10)
    bassb *= env
    drum_st = widen(sat(drumb, 1.1, 0.04), amount=0.7, seed=4)
    hook_st = pingpong(hookb * (env * 0.4 + 0.6), BEAT_S, fb=0.42, mix=0.4, taps=7, damp=3800)
    pads = np.stack([padL, padR]) * (env * 0.4 + 0.6)[None, :]
    verb = np.stack([fconv(pads[0], _verb_ir(2.8, 4600, 11)), fconv(pads[1], _verb_ir(2.8, 4600, 88))])
    music = drum_st * 0.8 + hook_st * 0.85 + (pads + verb) * 0.9 + np.stack([fxb, fxb]) * 0.7
    mm = 0.5 * (music[0] + music[1]); ss = bp(0.5 * (music[0] - music[1]), 220, 11000, 2) * 2.2
    mix = np.stack([mm + ss, mm - ss])
    mix += kickb[None, :] * 1.18 + bassb[None, :] * 1.45
    mix = np.stack([sat(mix[0], 1.12, 0.04), sat(mix[1], 1.12, 0.04)])
    mix = sub_mono(mix, 120.0)
    pk = np.abs(mix).max()
    if pk > 0.90: mix *= 0.90 / pk
    return mix

if __name__ == '__main__':
    print(f'FIEBRE · {sum(b for _, b in SONG)} compases ≈ {sum(b for _, b in SONG) * SPB / SR / 60:.1f} min', flush=True)
    mix = build()
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    raw = os.path.join(HERE, 'masters', 'fiebre-raw.wav')
    final = os.path.join(HERE, 'masters', 'amr-fiebre.wav')
    wav_write(raw, mix); del mix
    hist = master_file(raw, final, target_i=-8.4, ceiling_db=-1.3)
    I, lra, tp = ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}')
    print(final)
