#!/usr/bin/env python3
"""IMÁN — AMR SINGLE 002 (~4:20, 126 BPM, La menor). Techno-electro oscuro
estilo Volkoder "She Kisses": bajo PULSANTE que manda, synths CÓSMICOS que
cortan, drums de club, zaps sci-fi. Canción-canción (no set). Arreglo desde
CERO, paleta propia en iman_voices.py."""
import os
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, widen, sub_mono, pingpong,
                        stereo_verb, master_file, ffmeter, wav_write, fconv)
import iman_voices as V
from iman_voices import midi_f

HERE = os.path.dirname(os.path.abspath(__file__))
BPM = 126.0
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0; BEAT_S = 60.0 / BPM
ROOT = 45   # La (A2)

# progresión Am – F – C – G (oscura, tensa), 2 compases c/u
CHORDS = [[45,52,57,60],[41,48,53,57],[48,52,55,60],[43,50,55,59]]
# EL RIFF de bajo pulsante (step16 sobre ciclo de 2 compases [0..31], midi) — sincopado, electro
BRIFF = [0,None,33,33,None,33,45,None, 33,None,33,33,45,None,40,None,
         0,None,33,33,None,36,45,None, 33,None,40,None,43,None,45,45]
# gancho cósmico (step16 en ciclo 2 comp, midi, len16)
HOOK = [(0,69,3),(6,72,2),(10,71,3),(16,69,2),(20,67,2),(22,69,1),(24,72,4)]
HOOK2= [(0,76,2),(4,74,2),(8,72,3),(14,71,1),(16,72,2),(20,69,2),(24,67,4)]

SONG = [('intro',16),('build',8),('drop',36),('break',16),('build2',8),('drop2',36),('outro',16)]

KICK = V.kick_techno()

def add(buf, pos, x, g=1.0):
    pos = int(pos)
    if pos < 0: x = x[-pos:]; pos = 0
    end = min(len(buf), pos + len(x))
    if end > pos: buf[pos:end] += x[:end - pos] * g

def sc_env(n, kpos, depth=0.5, rel=0.11):
    env = np.ones(n, np.float32)
    dip = 1.0 - depth * np.exp(-np.arange(int(rel * 4 * SR)) / (rel * SR)).astype(np.float32)
    for p in kpos:
        e = min(n, p + len(dip))
        if e > p: env[p:e] = np.minimum(env[p:e], dip[:e - p])
    return env

def build():
    rng = np.random.default_rng(126)
    total = sum(b for _, b in SONG) * SPB + 6 * SPB
    kickb = np.zeros(total, np.float32); bassb = np.zeros(total, np.float32)
    drumb = np.zeros(total, np.float32); leadb = np.zeros(total, np.float32)
    stabb = np.zeros(total, np.float32); padL = np.zeros(total, np.float32); padR = np.zeros(total, np.float32)
    fxb = np.zeros(total, np.float32); voxb = np.zeros(total, np.float32); kpos = []
    sw = lambda s: s * S16 + 0.04 * 2 * S16 * (s % 2)      # swing muy leve (electro tight)

    pos_bar = 0
    for name, bars in SONG:
        drop = name in ('drop', 'drop2')
        for bar in range(bars):
            gb = pos_bar + bar
            base = gb * SPB
            ci = (gb // 2) % 4; ch = CHORDS[ci]; cyc = gb % 2
            last = (bar == bars - 1)
            # ---- KICK 4x4 (en drops y build; fuera en el break)
            if name in ('intro', 'drop', 'drop2', 'build', 'build2', 'outro'):
                for beat in range(4):
                    if name == 'build2' and bar >= bars-2 and beat >= 2: continue   # hueco pre-drop
                    add(kickb, base + beat*4*S16, KICK, 0.95 if drop else 0.8)
                    kpos.append(int(base + beat*4*S16))
            # ---- BAJO pulsante (el motor) — solo en drops
            if drop:
                for s in range(16):
                    m = BRIFF[cyc*16 + s]
                    if m is None: continue
                    add(bassb, base + sw(s) + rng.normal(0,.002)*SR,
                        V.bass_stab(midi_f(m), rng), 0.95)
            elif name in ('build','build2'):
                # bajo filtrándose en el build (solo downbeats, cutoff bajo)
                for s in (0,8):
                    add(bassb, base + s*S16, V.bass_throb(midi_f(33), S16/SR*3.5, rng, cutoff=200+180*bar), 0.6)
            # ---- DRUMS de club
            if name != 'break':
                dg = 1.0 if drop else (0.5 if name in ('build','build2') else 0.4)
                add(drumb, base + 4*S16, V.clap(rng), 0.7*dg); add(drumb, base + 12*S16, V.clap(rng), 0.7*dg)
                for s in range(16):
                    if s%2: add(drumb, base + sw(s), V.hat(rng), 0.34*dg)
                    else:   add(drumb, base + sw(s), V.hat(rng), 0.2*dg)
                if drop:
                    for s in (6,14):
                        if rng.uniform()<0.6: add(drumb, base + sw(s), V.hat(rng, open_=True), 0.3)
                    if bar%2==1: add(drumb, base + sw(7), V.rim(rng), 0.5)
                    if bar%4==2: add(drumb, base + sw(10), V.perc_metal(rng, f0=430+rng.uniform(-40,40)), 0.5)
                if last and name in ('build','build2'):                   # snare roll pre-drop
                    for k in range(8):
                        add(drumb, base + (8+k)*S16, V.snare_e(rng), 0.4 + 0.06*k)
            # ---- LEAD cósmico — en drops (y flotando en el break)
            if drop and cyc==0:
                mot = HOOK if name=='drop' else HOOK2
                pf = None
                for (s,m,ln) in mot:
                    add(leadb, base + int(sw(s)), V.cosmic_lead(midi_f(m), ln*S16/SR*1.15, rng, glide_from=pf), 0.5)
                    pf = midi_f(m)
            # ---- STABS de acorde electro en el offbeat de los drops
            if drop and bar%2==0:
                for s in (2,10):
                    add(stabb, base + sw(s), V.stab_synth([ch[1]+12,ch[2]+12,ch[3]+12], 0.18, rng), 0.5)
            # ---- ZAPS sci-fi — acentos al cierre de frase
            if name in ('drop','drop2','build','build2') and (gb%8==7):
                add(fxb, base + 14*S16, V.zap(rng, up=(name=='build' or name=='build2')), 0.7)
            # ---- PADS + VOX robot en el BREAK (atmósfera)
            if name=='break':
                if bar%2==0:
                    x = V.pad_cold([m+12 for m in ch[1:]], 2*SPB/SR*1.05, rng)
                    add(padL, base, x, 0.9); add(padR, base+int(0.02*SR), x, 0.85)
                # lead cósmico flotando
                if cyc==0:
                    pf=None
                    for (s,m,ln) in HOOK:
                        add(leadb, base+int(sw(s)), V.cosmic_lead(midi_f(m-12), ln*S16/SR*1.4, rng, glide_from=pf), 0.42); pf=midi_f(m-12)
                # stab vocal robótico "she kisses" feel
                if bar%4==2:
                    for s in (0,6,10):
                        add(voxb, base+sw(s), V.vox_robot(midi_f(deg_(ROOT+12, s)), 0.3, rng, 'uoea'[s%4]), 0.5)
            # ---- PAD frío suave bajo los drops
            if drop and bar%4==0:
                x = V.pad_cold([m+12 for m in ch[1:3]], 4*SPB/SR, rng)
                add(padL, base, x, 0.28); add(padR, base+int(0.015*SR), x, 0.26)
            # ---- ear candy de transición
            if name=='break' and bar==bars-1:
                add(fxb, base+8*S16, V.downlift(rng), 0.8)
            if drop and bar==0 and gb>0:
                add(fxb, base, V.impact(rng), 0.7)
            if name in ('build','build2'):
                add(fxb, base, V.riser(bars*SPB/SR*0.5, rng) if bar==0 else np.zeros(1,np.float32), 0.0)
        pos_bar += bars

    # riser continuo en los builds
    for name, bars, st in _sections_pos():
        if name in ('build','build2'):
            r = V.riser(bars*SPB/SR, rng); add(fxb, st*SPB, r, 0.5)

    # ---- mezcla
    env = sc_env(total, kpos, depth=0.5)
    bassb *= env
    drum_st = widen(sat(drumb,1.08,0.03), amount=0.5, seed=3)
    lead_st = pingpong(leadb, BEAT_S*0.75, fb=0.42, mix=0.4, taps=6, damp=5200)
    stab_st = pingpong(stabb*(env*0.4+0.6), BEAT_S, fb=0.3, mix=0.3, taps=5, damp=5000)
    vox_st  = pingpong(voxb, BEAT_S*0.5, fb=0.4, mix=0.45, taps=6, damp=4200)
    fx_st   = widen(fxb, amount=0.6, seed=7)
    pads = np.stack([padL, padR]) * (env*0.4+0.6)[None,:]
    music = drum_st*0.72 + lead_st*0.62 + stab_st*0.5 + vox_st*0.5 + fx_st*0.55 + pads*0.6
    mm = 0.5*(music[0]+music[1]); ss = bp(0.5*(music[0]-music[1]), 220, 12000, 2) * 2.2
    mix = np.stack([mm+ss, mm-ss])
    mix += kickb[None,:]*1.2 + bassb[None,:]*1.28
    mix = np.stack([sat(mix[0],1.1,0.04), sat(mix[1],1.1,0.04)])
    mix = sub_mono(mix, 120.0)
    pk = np.abs(mix).max()
    if pk>0.92: mix *= 0.92/pk
    return mix

def deg_(root, s):
    SCALE=[0,2,3,5,7,8,10]; return root + SCALE[s % 7]

def _sections_pos():
    out=[]; p=0
    for name,bars in SONG: out.append((name,bars,p)); p+=bars
    return out

if __name__ == '__main__':
    tb = sum(b for _,b in SONG)
    print(f'IMÁN · {tb} compases ≈ {tb*SPB/SR/60:.1f} min', flush=True)
    mix = build()
    os.makedirs(os.path.join(HERE,'masters'), exist_ok=True)
    raw = os.path.join(HERE,'masters','iman-raw.wav')
    final = os.path.join(HERE,'masters','amr-iman.wav')
    wav_write(raw, mix); del mix
    hist = master_file(raw, final, target_i=-8.0, ceiling_db=-1.2)
    I,lra,tp = ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}')
    print(final)
