#!/usr/bin/env python3
"""BATUQUE — set tech house con swing brasileño (estilo Volkoder) · 128 BPM · Do mayor (8B).
Groove-first: EL BAJO WONKY manda (rolling en el pocket, sidechain duro), los
VOCAL CHOPS son el gancho (call-response, afinados + vocoder), hats muy
swingueados + congas que serpentean, stabs rítmicos secos, un lead cósmico que
corta en el pico y un comedown melódico (el momento Diynamic/Solomun).
Arreglo desde CERO (nada de forks): builds pacientes con tensión→release, el
'silencio antes del drop', y los 'distintos momentos de la noche' de una EP suya.
Uso: python3 make_batuque.py PAULISTA  (una sección)  |  sin args = set completo."""
import os, sys
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, widen, sub_mono, pingpong,
                        master_file, ffmeter, wav_write, spectrum_pct, fconv)
import batuque_voices as V
from batuque_voices import midi_f, pdeg, MAJP, MINP

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_batuque_tmp'); os.makedirs(TMP, exist_ok=True)
BPM = 128.0
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0; BEAT_S = 60.0 / BPM
XF_BARS = 4
SWING = 0.61                                   # ~61% swing global (empuja el 2do 16vo)
KICK = V.kick_house()
ROOT = 48                                      # Do (C3) — set en Do mayor = 8B (mixea con el catálogo 8A)

# chords = ciclo de 4 (2 compases c/u): voicings en Do mayor / relativo
# bass = patrón rolling en ciclo de 2 compases: (step16 0..31, oct_offset, len16, vel)
# vhook = gancho vocal (step, grado penta, oct, vow) sobre ciclo de 2 compases
SECTIONS = [
 dict(name='ABERTURA', energy=0.42, shape='rise', bars=72,
      chords=[[48,55,60,64],[45,52,57,60],[41,53,57,60],[43,55,59,62]],   # C Am F G
      bass=[(0,0,2,1.0),(6,0,1,.7),(8,1,1,.8),(12,0,2,.9),(16,0,1,.9),(22,0,1,.7),(24,1,2,.8),(30,0,1,.7)],
      stab=[60,64,67], vow=['o','a']),
 dict(name='GAROA', energy=0.60, shape='wave', bars=104,
      chords=[[48,55,60,64],[45,52,57,60],[41,53,57,60],[43,55,59,62]],
      bass=[(0,0,1,1.0),(3,0,1,.6),(6,1,1,.85),(8,0,2,.9),(14,0,1,.6),(16,0,1,1.0),(19,0,1,.6),(22,1,1,.8),(24,0,2,.85),(30,0,1,.6)],
      stab=[60,64,67], vow=['o','a','e']),
 dict(name='PAULISTA', energy=0.84, shape='peak', bars=120,
      chords=[[48,55,60,64],[43,55,59,62],[45,52,57,60],[41,53,57,60]],   # C G Am F
      bass=[(0,0,1,1.0),(2,0,1,.6),(4,1,1,.85),(6,0,1,.6),(8,0,2,.95),(12,1,1,.7),(16,0,1,1.0),(18,0,1,.6),(20,1,1,.85),(24,0,2,.9),(28,1,1,.7),(30,0,1,.6)],
      stab=[60,64,67], vow=['a','o']),
 dict(name='NEON', energy=0.68, shape='wave', bars=104,
      chords=[[45,52,57,60],[41,53,57,60],[48,55,60,64],[43,55,59,62]],   # Am F C G (más sleazy)
      bass=[(0,0,2,1.0),(6,0,1,.65),(8,1,1,.8),(10,0,1,.6),(12,0,2,.9),(16,0,1,1.0),(20,1,1,.75),(24,0,2,.85),(30,0,1,.6)],
      stab=[57,60,64], vow=['e','o']),        # NEON usa más vocoder
 dict(name='MIRANTE', energy=0.38, shape='valley', bars=88,
      chords=[[48,55,60,64],[45,52,57,60],[41,53,57,60],[43,50,55,59]],   # el comedown melódico
      bass=[(0,0,3,.9),(8,0,2,.7),(16,0,3,.85),(24,0,2,.7)],
      stab=[60,64,67], vow=['a','o']),
 dict(name='FAROL', energy=0.97, shape='peak', bars=136,                  # el pico — lead cósmico
      chords=[[48,55,60,64],[43,55,59,62],[45,52,57,60],[41,53,57,60]],
      bass=[(0,0,1,1.0),(2,0,1,.6),(4,1,1,.85),(6,0,1,.6),(8,1,2,.95),(12,0,1,.7),(16,0,1,1.0),(18,1,1,.6),(20,0,1,.85),(24,1,2,.9),(28,0,1,.7),(30,1,1,.6)],
      stab=[60,64,69], vow=['a','o','e']),
 dict(name='BAILE', energy=0.80, shape='wave', bars=112,                  # hands-up
      chords=[[48,55,60,64],[45,52,57,60],[43,55,59,62],[48,55,60,64]],   # C Am G C
      bass=[(0,0,2,1.0),(6,0,1,.65),(8,1,1,.8),(10,1,1,.6),(12,0,2,.85),(16,0,2,1.0),(24,1,1,.75),(26,0,1,.7),(28,1,2,.8)],
      stab=[60,64,67], vow=['o','a']),
 dict(name='AMANHECER', energy=0.46, shape='outro', bars=72,              # el amanecer / mix-out
      chords=[[48,55,60,64],[45,52,57,60],[41,53,57,60],[48,55,60,64]],
      bass=[(0,0,2,.9),(8,1,1,.55),(12,0,2,.8),(16,0,2,.85),(24,0,2,.75)],
      stab=[60,64,67], vow=['a','o']),
]

# gancho vocal repetitivo (step16, grado penta mayor, oct, len16) sobre ciclo de 2 compases
VHOOK = [(2,0,0,1),(5,2,0,1),(8,4,0,2),(12,2,0,1),(16,0,0,1),(19,4,0,1),(22,2,0,2),(28,1,0,1)]
# lead cósmico del pico (grados sobre penta mayor, oct +1)
LEADM = [(0,4,1,3),(6,2,1,2),(10,1,1,2),(16,4,1,2),(20,2,1,2),(24,0,1,4)]

def sw(s, on=True):
    """swing: empuja el 16vo impar hacia adelante."""
    return s * S16 + ((SWING - 0.5) * 2 * S16 if (on and s % 2) else 0.0)

def add(buf, pos, x, g=1.0):
    pos = int(pos)
    if pos < 0: x = x[-pos:]; pos = 0
    end = min(len(buf), pos + len(x))
    if end > pos: buf[pos:end] += x[:end - pos] * g

def plan_blocks(sec):
    """bloques de 8 compases (tech house 'moments of the night'): intro DJ-friendly,
    builds pacientes que suman capas, drop full, y el break por sustracción con
    'silencio antes del drop'. valley = comedown melódico sin kick/bajo."""
    nb = sec['bars'] // 8; e = sec['energy']; shape = sec['shape']; out = []
    for i in range(nb):
        p = i / max(1, nb - 1)
        b = dict(kick=1, bass=1, hats=0.8, shk=0.7, conga=0.7, clap=1, stab=0.6,
                 vox=0, voco=0, lead=0, pad=0, ghost=0.7, gain=0.92 + 0.08 * min(1, e + 0.2),
                 predrop=0)
        if i == 0:                                       # intro DJ-friendly: kick+hats+bajo
            b.update(kick=1 if shape != 'rise' else 0, clap=0, conga=0.3, stab=0, ghost=0.3, hats=0.5)
        if p > 0.18: b['vox'] = 1                        # entra el gancho vocal
        if p > 0.30: b['stab'] = 0.9
        if p > 0.45: b['voco'] = 1
        # THE BREAK por sustracción + el 'silencio antes del drop'
        if shape in ('wave', 'peak') and 0.48 < p < 0.60:
            b.update(kick=0, bass=0, conga=0.3, stab=0.4, clap=0, gain=0.82, vox=1, pad=0.5)
        if shape in ('wave', 'peak') and 0.60 <= p < 0.68:
            b.update(predrop=1)                          # bloque de build → corta antes del drop
        if shape == 'peak' and p >= 0.68:                # el drop grande
            b.update(conga=0.95, hats=0.95, vox=1, voco=1, stab=1.0, gain=1.03,
                     lead=1 if sec['name'] == 'FAROL' else 0)
        if shape == 'valley':                            # MIRANTE: comedown melódico
            if 0.25 < p < 0.72:
                b.update(kick=0, bass=0, conga=0.15, hats=0.12, clap=0, stab=0.3, ghost=0,
                         pad=1, lead=1, vox=0.6, voco=0, gain=0.66)
            elif p >= 0.72:                              # regresa el groove
                b.update(pad=0.4, gain=0.94, vox=1, voco=1)
            else:
                b.update(pad=0.3)
        if shape == 'rise': b['gain'] = 0.70 + 0.30 * p  # warm-up sube
        if shape == 'outro':
            b['gain'] = 1.0 - 0.42 * max(0.0, p - 0.35)
            if p > 0.55: b.update(stab=0, voco=0, lead=0, vox=0.4, conga=0.3, clap=0)
        out.append(b)
    return out

def sidechain(n, kpos, depth=0.55, rel=0.11):
    """pump AUDIBLE (el género lo abraza): dip profundo + release largo ~110ms."""
    env = np.ones(n, np.float32)
    dip = 1.0 - depth * np.exp(-np.arange(int(rel * 4 * SR)) / (rel * SR)).astype(np.float32)
    for p_ in kpos:
        e = min(n, p_ + len(dip))
        if e > p_: env[p_:e] = np.minimum(env[p_:e], dip[:e - p_])
    return env

def _verb(decay, tone, seed):
    m = int(decay * SR); rng = np.random.default_rng(seed)
    ir = rng.standard_normal(m).astype(np.float32) * np.exp(-np.linspace(0, 6.5, m)).astype(np.float32)
    ir = lp(ir, tone, 2); ir /= np.sqrt((ir ** 2).sum()) + 1e-12
    return ir * 0.3

def render_section(sec, idx):
    rng = np.random.default_rng(700 + idx * 23)
    bars = sec['bars']; n = bars * SPB + XF_BARS * SPB
    blocks = plan_blocks(sec); chords = sec['chords']
    kickb = np.zeros(n, np.float32); bassb = np.zeros(n, np.float32)
    drumb = np.zeros(n, np.float32); congab = np.zeros(n, np.float32)
    stabb = np.zeros(n, np.float32); voxb = np.zeros(n, np.float32)
    vocob = np.zeros(n, np.float32); leadb = np.zeros(n, np.float32)
    padL = np.zeros(n, np.float32); padR = np.zeros(n, np.float32)
    kpos = []
    vows = sec['vow']

    for bi, b in enumerate(blocks):
        for bar in range(8):
            gb = bi * 8 + bar
            if gb >= bars: break
            base = gb * SPB
            ch = chords[(gb // 2) % 4]
            root = ch[0]                                  # raíz del acorde (para el bajo)
            cyc = gb % 2
            last8 = (gb % 8 == 7)
            silence = (b['predrop'] and last8)            # medio compás de silencio pre-drop
            # ---- KICK 4x4 (respira en el silencio pre-drop)
            if b['kick'] and not silence:
                for beat in range(4):
                    add(kickb, base + beat * 4 * S16, KICK, 1.0)
                    kpos.append(int(base + beat * 4 * S16))
            elif b['kick'] and silence:
                for beat in (0, 1):                       # solo primera mitad, luego silencio
                    add(kickb, base + beat * 4 * S16, KICK, 1.0)
                    kpos.append(int(base + beat * 4 * S16))
            # ---- CLAP en 2 y 4 (empujado ~18ms antes)
            if b['clap'] and not silence:
                for s in (4, 12):
                    add(drumb, base + sw(s) - 0.018 * SR, V.clap(rng), b['clap'] * 0.7)
            # ---- HATS 16vos swingueados (closed + open offbeat)
            if b['hats'] > 0 and not silence:
                for s in range(16):
                    g = (0.5 if s % 2 else 0.3) * b['hats']
                    op = (s % 4 == 2) and rng.uniform() < 0.7
                    add(drumb, base + sw(s) + rng.normal(0, .002) * SR, V.hat(rng, open_=op), g * (0.85 if op else 1))
            # ---- SHAKER 16vos suave swing
            if b['shk'] > 0 and not silence:
                for s in range(0, 16, 2):
                    add(drumb, base + sw(s) + rng.normal(0, .003) * SR, V.shaker(rng), 0.3 * b['shk'])
            # ---- GHOST snare antes del 3er/7mo kick (empujado por swing)
            if b['ghost'] > 0 and not silence:
                for s in (6, 14):
                    if rng.uniform() < 0.7:
                        add(drumb, base + sw(s), V.snare_ghost(rng), b['ghost'] * 0.5)
            # ---- CONGAS/tumbao que serpentean alrededor del kick
            if b['conga'] > 0 and not silence:
                capat = (2, 6, 11, 14) if cyc == 0 else (3, 6, 10, 15)
                for s in capat:
                    f0 = midi_f(48 if s % 3 else 55)
                    add(congab, base + sw(s) + rng.normal(0, .003) * SR, V.conga(f0, rng), b['conga'] * 0.5)
                if b['conga'] >= 0.9 and bar % 2 == 1:
                    add(congab, base + sw(7), V.rimshot(rng), 0.4)
            # ---- fill de toms al cierre de frase de 8
            if last8 and b['gain'] >= 0.9 and not b['predrop']:
                for k, s in enumerate((12, 13, 14, 15)):
                    add(congab, base + sw(s), V.tom(190 - 30 * k, rng), 0.4 + 0.1 * k)
            # ===== EL BAJO WONKY — rolling en el pocket (raíz del acorde, bounce de octava)
            if b['bass'] and not silence:
                prev = None
                for (st, oo, ln, v) in sec['bass']:
                    if st // 16 != cyc: continue
                    s = st % 16
                    m = root - 12 + 12 * oo                # raíz grave + rebote de octava
                    f = midi_f(m)
                    gl = prev if (prev and rng.uniform() < 0.3) else None
                    wob = 6.4 if sec['shape'] != 'peak' else 9.5
                    add(bassb, base + sw(s) + rng.normal(0, .003) * SR,
                        V.bass_wonky(f, ln * S16 / SR * 1.4, rng, wob_hz=wob,
                                     hi=1300 + 500 * b['gain'], glide_from=gl), v * 0.95)
                    prev = f
            # ===== STABS rítmicos secos (órgano/pluck) en contratiempos
            if b['stab'] > 0 and not silence:
                pat = (2, 6, 10, 14) if cyc == 0 else (3, 7, 11, 14)
                for j, s in enumerate(pat):
                    if rng.uniform() < 0.8:
                        voic = [ch[1] + 12, ch[2] + 12, ch[3] + 12][:2 + (j % 2)]
                        x = V.organ_stab(voic, 0.16, rng) if j % 2 else V.pluck(midi_f(ch[1 + j % 3] + 12), 0.16, rng)
                        add(stabb, base + sw(s), x, b['stab'] * 0.55)
            # ===== VOCAL CHOP hook (repetitivo, call) — el gancho
            if b['vox'] and gb % 2 == 0:
                for (s, d, o, ln) in VHOOK:
                    pos = base + sw(s % 16) + (SPB if s >= 16 else 0)
                    f = midi_f(pdeg(ROOT + 12, d, o, MAJP))
                    add(voxb, pos, V.vox_chop(f, min(ln * S16 / SR * 1.3, 0.26), rng, vows[(s + d) % len(vows)]), 0.6)
            # ===== VOCODER response (contesta el gancho, offbeats)
            if b['voco'] and gb % 2 == 1:
                for s in (4, 10, 20, 26):
                    if rng.uniform() < 0.6:
                        d = int(rng.integers(0, 5))
                        pos = base + sw(s % 16) + (SPB if s >= 16 else 0)
                        add(vocob, pos, V.vox_vocoder(midi_f(pdeg(ROOT + 12, d, 0, MAJP)), 0.15, rng, 'e'), 0.5)
            # ===== LEAD cósmico (solo FAROL en el drop)
            if b['lead'] and gb % 2 == 0:
                for (s, d, o, ln) in LEADM:
                    pos = base + int(sw(s % 16)) + (SPB if s >= 16 else 0)
                    f = midi_f(pdeg(ROOT, d, o, MAJP)); dur = ln * S16 / SR * 1.2
                    add(leadb, pos, V.lead_cosmic(f, dur, rng), 0.5)
            # ===== PADS del comedown (MIRANTE) + supersaw
            if b['pad'] > 0.2 and bar % 2 == 0:
                voic = [m + 12 for m in ch[1:]]
                x = V.saw_chord(voic, 2 * SPB / SR * 1.05, rng) if b['pad'] >= 0.9 else V.pad_warm(voic, 2 * SPB / SR * 1.05, rng)
                add(padL, base, x, b['pad']); add(padR, base + int(0.017 * SR), x, b['pad'] * 0.94)

    # ------- buses
    env = sidechain(n, kpos)
    bassb *= env                                          # el bajo bombea con el kick (audible)
    drum_st = widen(sat(drumb, 1.1, 0.04), amount=0.5, seed=idx * 3 + 2)
    conga_st = widen(congab * (env * 0.4 + 0.6), amount=0.6, seed=idx * 5 + 1)
    stab_st = pingpong(stabb * (env * 0.4 + 0.6), BEAT_S, fb=0.34, mix=0.28, taps=5, damp=4400)
    vox_st = pingpong(voxb * (env * 0.35 + 0.65), BEAT_S, fb=0.4, mix=0.4, taps=6, damp=4600)
    voco_st = pingpong(vocob * (env * 0.35 + 0.65), BEAT_S, fb=0.42, mix=0.45, taps=6, damp=5200)
    lead_st = pingpong(leadb, BEAT_S, fb=0.42, mix=0.42, taps=7, damp=4200)
    pads = np.stack([padL, padR]) * (env * 0.4 + 0.6)[None, :]
    verb = np.stack([fconv(pads[0], _verb(2.6, 4800, 21)), fconv(pads[1], _verb(2.6, 4800, 22))])
    music = (drum_st * 0.74 + conga_st * 0.62 + stab_st * 0.6 + vox_st * 0.6
             + voco_st * 0.5 + lead_st * 0.62 + (pads + verb) * 0.75)
    mm = 0.5 * (music[0] + music[1]); ss = bp(0.5 * (music[0] - music[1]), 220, 11000, 2) * 2.2
    mix = np.stack([mm + ss, mm - ss])
    mix += kickb[None, :] * 1.18 + bassb[None, :] * 1.28  # kick + bajo wonky al centro (low end)
    genv = np.ones(n, np.float32)
    for bi, blk in enumerate(plan_blocks(sec)):
        genv[bi * 8 * SPB:min(n, (bi + 1) * 8 * SPB)] = blk['gain']
    genv = lp(genv, 2.0, 1); mix *= genv[None, :]
    mix = np.stack([sat(mix[0], 1.12, 0.045), sat(mix[1], 1.12, 0.045)])
    mix = sub_mono(mix, 120.0)                             # low end mono
    pk = np.abs(mix).max()
    if pk > 0.93: mix *= 0.93 / pk
    return mix

def _shave(x):
    """afeitado pre-master para transientes tech house (soft-clip + normaliza):
    evita que master_file no converja por inter-sample peaks (lección PLAYA)."""
    x = np.stack([sat(x[0] * 1.5, 2.0, 0.04), sat(x[1] * 1.5, 2.0, 0.04)])
    return x * (0.72 / max(1e-9, float(np.abs(x).max())))

def build(only=None):
    tot = sum(s['bars'] for s in SECTIONS)
    print(f'BATUQUE · {len(SECTIONS)} secciones · {tot} compases ≈ {tot * SPB / SR / 60:.0f} min', flush=True)
    secs = []
    for i, s in enumerate(SECTIONS):
        if only and s['name'] != only: continue
        f = os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        exp = (s['bars'] + XF_BARS) * SPB * 8 + 44
        if not only and os.path.exists(f) and os.path.getsize(f) == exp:
            print(f'  ✓ {s["name"]}', flush=True); secs.append((i, s, f)); continue
        print(f'  … {s["name"]} ({s["bars"]} comp, e={s["energy"]})', flush=True)
        mix = render_section(s, i); wav_write(f, mix); secs.append((i, s, f)); del mix
    if only:
        i, s, f = secs[0]; I, lra, tp = ffmeter(f)
        from dream_core import ffdecode
        print(f'  {s["name"]}: {I} LUFS · LRA {lra} · TP {tp} · {spectrum_pct(ffdecode(f, mono=True))}')
        return
    print('  … crossfades', flush=True)
    xf = XF_BARS * SPB; total = tot * SPB + xf
    out = np.zeros((2, total), np.float32); pos = 0
    for k, (i, s, f) in enumerate(secs):
        from dream_core import ffdecode
        x = ffdecode(f)
        if k > 0: x[:, :xf] *= (np.linspace(0, 1, xf) ** 0.5).astype(np.float32)[None, :]
        a = min(total - pos, x.shape[1]); out[:, pos:pos + a] += x[:, :a]; pos += s['bars'] * SPB; del x
    print('  … afeitado + master -8.5 LUFS', flush=True)
    out = _shave(out)
    raw = os.path.join(TMP, 'batuque-raw.wav'); wav_write(raw, out); del out
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    final = os.path.join(HERE, 'masters', 'amr-batuque.wav')
    hist = master_file(raw, final, target_i=-8.5, ceiling_db=-1.2)
    I, lra, tp = ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}'); print(final)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else None)
