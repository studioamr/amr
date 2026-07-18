#!/usr/bin/env python3
"""PLAYA — set Maccabi House / Burning Man estilo Adam Ten (~26 min, 119 BPM, La menor).
Funk-first: EL RIFF DE BAJO manda, chops de guitarra en el skank, clavinet que
responde, stabs de metales en los arranques de frase, vocales juguetonas, y UN
amanecer emocional en medio del polvo. Arreglo desde CERO (nada de forks):
el groove entra COMPLETO temprano y los drops son por SUSTRACCIÓN.
Uso: python3 make_playa.py POLVO  (una sección)  |  sin args = set completo."""
import os, sys
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, widen, sub_mono, pingpong,
                        master_file, ffmeter, wav_write, spectrum_pct, fconv)
import playa_voices as P
from playa_voices import midi_f, pdeg

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_playa_tmp'); os.makedirs(TMP, exist_ok=True)
BPM = 119.0
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0; BEAT_S = 60.0 / BPM
XF_BARS = 4
SW = dict(bass=0.57, gtr=0.58, hats=0.57, shk=0.56, clav=0.56)
KICK = P.kick_punch()

# riff = (step16 en ciclo de 2 compases [0..31], midi, len16, vel) — EL gancho de cada sección
# chords = ciclo de 4 (2 compases c/u); stabs = acorde de metales de la sección
SECTIONS = [
 dict(name='SALIDA', energy=0.42, shape='rise', bars=72, lead=None,
      chords=[[45,52,57,60],[43,50,55,59],[41,48,53,57],[43,50,55,59]],   # Am G F G
      riff=[(0,33,2,1.0),(6,33,1,.7),(8,45,1,.6),(12,33,2,.85),(16,33,1,.9),(20,31,1,.6),(24,28,2,.8),(28,31,1,.7)],
      stab=[57,60,64]),
 dict(name='POLVO', energy=0.62, shape='wave', bars=104, lead='clav',
      chords=[[45,52,57,60],[45,52,57,60],[41,48,53,57],[43,50,55,59]],
      riff=[(0,33,1,1.0),(3,33,1,.6),(6,36,1,.8),(8,33,2,.9),(14,31,1,.6),(16,33,1,1.0),(19,33,1,.6),(22,40,1,.75),(24,38,2,.85),(30,36,1,.6)],
      stab=[57,60,64]),
 dict(name='CARAVANA', energy=0.8, shape='peak', bars=112, lead='clav',
      chords=[[45,52,57,60],[43,50,55,59],[45,52,57,60],[48,52,55,60]],   # Am G Am C
      riff=[(0,33,2,1.0),(6,45,1,.7),(8,33,1,.85),(10,36,1,.7),(12,38,2,.9),(16,33,2,1.0),(22,45,1,.7),(24,43,1,.8),(26,40,1,.7),(28,38,2,.85)],
      stab=[60,64,67]),
 dict(name='ESPEJISMO', energy=0.66, shape='wave', bars=96, lead='vox',
      chords=[[41,48,53,57],[43,50,55,59],[45,52,57,60],[45,52,57,60]],   # F G Am Am
      riff=[(0,29,2,1.0),(6,29,1,.6),(8,41,1,.7),(12,31,2,.9),(16,33,2,1.0),(22,33,1,.6),(24,45,1,.7),(28,43,1,.75)],
      stab=[57,60,65]),
 dict(name='AMANECER', energy=0.4, shape='valley', bars=88, lead='clav',
      chords=[[45,52,57,60],[41,48,53,57],[48,52,55,60],[43,50,55,59]],   # Am F C G — el amanecer
      riff=[(0,33,3,.9),(8,33,2,.7),(16,29,3,.85),(24,31,2,.7)],
      stab=[57,60,64]),
 dict(name='FUEGO', energy=0.96, shape='peak', bars=128, lead='clav',
      chords=[[45,52,57,60],[43,50,55,59],[41,48,53,57],[43,50,55,59]],
      riff=[(0,33,1,1.0),(2,33,1,.6),(4,36,1,.85),(6,33,1,.6),(8,38,2,.95),(12,36,1,.7),(16,33,1,1.0),(18,33,1,.6),(20,40,1,.85),(24,43,2,.9),(28,45,1,.7),(30,43,1,.6)],
      stab=[60,64,69]),
 dict(name='BAILE', energy=0.78, shape='wave', bars=104, lead='clav',
      chords=[[45,52,57,60],[48,52,55,60],[43,50,55,59],[45,52,57,60]],   # Am C G Am
      riff=[(0,33,2,1.0),(6,33,1,.65),(8,45,1,.7),(10,43,1,.6),(12,40,2,.85),(16,33,2,1.0),(24,38,1,.75),(26,40,1,.7),(28,45,2,.8)],
      stab=[57,60,64]),
 dict(name='HORIZONTE', energy=0.46, shape='outro', bars=72, lead=None,
      chords=[[45,52,57,60],[41,48,53,57],[43,50,55,59],[45,52,57,60]],
      riff=[(0,33,2,.9),(8,45,1,.55),(12,33,2,.8),(16,31,2,.85),(24,28,2,.75)],
      stab=[57,60,64]),
]

# ganchos de lead por sección (step16, grado pent menor, oct, len16) sobre ciclo 2 compases
MOTIFS = dict(
 clav=[(0,0,1,1),(2,2,1,1),(4,3,1,2),(8,2,1,1),(10,1,1,1),(12,0,1,2),(16,0,1,1),(18,2,1,1),(20,4,1,2),(24,3,1,1),(26,2,1,1),(28,1,1,2)],
 wah=[(0,2,1,3),(6,3,1,2),(10,4,1,3),(16,2,1,2),(20,1,1,2),(24,0,1,5)],
 vox=[(0,4,1,2),(4,4,1,1),(6,3,1,2),(12,2,1,3),(16,4,1,2),(20,3,1,1),(22,2,1,2),(26,0,1,4)],
)
ROOT = 45   # La (A2) — todo el set en La menor = 8A del catálogo

def sw(s, who): return s * S16 + (SW[who] - 0.5) * 2 * S16 * (s % 2)

def add(buf, pos, x, g=1.0):
    pos = int(pos)
    if pos < 0: x = x[-pos:]; pos = 0
    end = min(len(buf), pos + len(x))
    if end > pos: buf[pos:end] += x[:end - pos] * g

def plan_blocks(sec):
    """bloques de 8 compases. Distinto a otros discos: el groove COMPLETO entra al
    bloque 2 (Maccabi: la fiesta ya está armada) y los breaks QUITAN piezas."""
    nb = sec['bars'] // 8; e = sec['energy']; shape = sec['shape']; out = []
    for i in range(nb):
        p = i / max(1, nb - 1)
        b = dict(kick=1, bass=1, gtr=1, clav=0.7, brass=0, vox=0, hats=0.7,
                 perc=0.6, pad=0, lead=0, gain=0.9 + 0.1 * min(1, e + 0.2), wind=0)
        if i == 0: b.update(kick=0.0 if shape == 'rise' else 1, bass=1, gtr=0.6, clav=0, hats=0.4, perc=0.3, wind=0.7)
        if p > 0.2: b['brass'] = 1
        if p > 0.3: b['lead'] = 1
        if p > 0.4: b['vox'] = 1
        # EL BREAK POR SUSTRACCIÓN: se van kick+bajo, queda el funk desnudo (gtr+vox)
        if shape in ('wave', 'peak') and 0.5 < p < 0.62:
            b.update(kick=0, bass=0, clav=0.4, brass=0, gain=0.8, wind=0.5, vox=1)
        if shape == 'peak' and p >= 0.62:
            b.update(perc=0.95, hats=0.9, vox=1, brass=1, gain=1.02)
        if shape == 'valley':
            if 0.3 < p < 0.68:                      # EL AMANECER: sin kick/bajo, pads y cielo
                b.update(kick=0, bass=0, gtr=0, clav=0, brass=0, perc=0.12, hats=0.1,
                         pad=1, lead=1, vox=0.5, gain=0.66, wind=1)
            elif p >= 0.68:                          # vuelve el groove con el sol arriba
                b.update(pad=0.5, gain=0.95, vox=1)
            else:
                b.update(pad=0.3)
        if shape == 'rise': b['gain'] = 0.68 + 0.32 * p
        if shape == 'outro':
            b['gain'] = 1.0 - 0.45 * max(0.0, p - 0.35)
            if p > 0.55: b.update(brass=0, lead=0, vox=0, clav=0.3, wind=0.8)
        out.append(b)
    return out

def sidechain(n, kpos, depth=0.4, rel=0.085):
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
    rng = np.random.default_rng(900 + idx * 17)
    bars = sec['bars']; n = bars * SPB + XF_BARS * SPB
    blocks = plan_blocks(sec); chords = sec['chords']
    kickb = np.zeros(n, np.float32); bassb = np.zeros(n, np.float32)
    drumb = np.zeros(n, np.float32); gtrb = np.zeros(n, np.float32)
    clavb = np.zeros(n, np.float32); brassb = np.zeros(n, np.float32)
    voxb = np.zeros(n, np.float32); leadb = np.zeros(n, np.float32)
    padL = np.zeros(n, np.float32); padR = np.zeros(n, np.float32)
    windb = P.wind(n / SR, rng)                     # el polvo siempre está
    kpos = []
    lead_kind = sec['lead']

    for bi, b in enumerate(blocks):
        for bar in range(8):
            gb = bi * 8 + bar
            if gb >= bars: break
            base = gb * SPB
            ch = chords[(gb // 2) % 4]
            cyc = gb % 2                             # posición dentro del ciclo de 2 compases
            last8 = (gb % 8 == 7)
            # KICK 4x4 apretado (respira medio compás antes del arranque de frase)
            if b['kick']:
                for beat in range(4):
                    if last8 and beat == 3 and b['gain'] >= 0.95: continue
                    add(kickb, base + beat * 4 * S16, KICK, 1.0)
                    kpos.append(int(base + beat * 4 * S16))
            # backbeat gordo 2 y 4 + hats swing + shaker
            if b['perc'] >= 0.3:
                for s in (4, 12):
                    add(drumb, base + sw(s, 'hats') + rng.normal(0, .002) * SR, P.snare_fat(rng), b['perc'] * 0.55)
            if b['hats'] > 0:
                for s in range(16):
                    g = (0.5 if s % 2 else 0.28) * b['hats']
                    if s in (6, 14) and rng.uniform() < 0.6:
                        add(drumb, base + sw(s, 'hats'), P.hat_funk(rng, open_=True), g * 0.9)
                    else:
                        add(drumb, base + sw(s, 'hats') + rng.normal(0, .002) * SR, P.hat_funk(rng), g)
                for s in range(0, 16, 2):
                    add(drumb, base + sw(s, 'shk') + rng.normal(0, .003) * SR, P.shk(rng), 0.3 * b['hats'])
            # cencerro/block: el guiño, escaso
            if b['perc'] >= 0.6 and bar % 4 == 2:
                add(drumb, base + sw(10, 'hats'), P.cowb(rng), 0.5)
            if b['perc'] >= 0.8 and bar % 2 == 1:
                add(drumb, base + sw(7, 'shk'), P.block(rng), 0.45)
            # fill de toms al cierre de frase
            if last8 and b['gain'] >= 0.85:
                for k, s in enumerate((12, 13, 14, 15)):
                    add(drumb, base + sw(s, 'shk'), P.tom(200 - 34 * k, rng), 0.4 + 0.1 * k)
            # ===== EL RIFF DE BAJO (la estrella) — ciclo de 2 compases con slides
            if b['bass']:
                prev_f = None
                for (st, m, ln, v) in sec['riff']:
                    if st // 16 != cyc: continue
                    s = st % 16
                    f = midi_f(m - 12)
                    gl = prev_f if (prev_f and rng.uniform() < 0.35) else None
                    add(bassb, base + sw(s, 'bass') + rng.normal(0, .003) * SR,
                        P.bass_rub(f, ln * S16 / SR * 1.7, rng, cutoff=700 + 500 * b['gain'], glide_from=gl), v * 0.95)
                    prev_f = f
            # ===== SKANK de guitarra: chops en contratiempos
            if b['gtr'] > 0:
                pat = (2, 6, 10, 14) if cyc == 0 else (2, 5, 10, 13)
                for s in pat:
                    m = ch[1 + (s // 4) % 3] + 12
                    add(gtrb, base + sw(s, 'gtr') + rng.normal(0, .002) * SR, P.gtr_chop(midi_f(m), rng), b['gtr'] * 0.7)
            # ===== CLAVINET responde al bajo (compás 2 del ciclo)
            if b['clav'] > 0 and cyc == 1:
                for (s, d, o, ln) in ((1, 4, 0, 1), (3, 3, 0, 1), (7, 2, 0, 1), (11, 4, 0, 1)):
                    if rng.uniform() < 0.75:
                        add(clavb, base + sw(s, 'clav'), P.clav(midi_f(pdeg(ROOT, d, o)), rng), b['clav'] * 0.8)
            # ===== STAB de metales al arranque de cada frase de 8
            if b['brass'] and gb % 8 == 0:
                add(brassb, base, P.brass(sec['stab'], 0.34, rng), 0.9)
                add(brassb, base + int(6 * S16), P.brass([m - 2 for m in sec['stab']], 0.22, rng), 0.55)
            # ===== VOX chops juguetones
            if b['vox'] and bar % 2 == 1:
                for s in (0, 3, 8, 11):
                    if rng.uniform() < 0.65:
                        d = int(rng.integers(0, 5))
                        add(voxb, base + sw(s, 'gtr'), P.vox(midi_f(pdeg(57, d)), 0.22, rng, 'aoeui'[s % 5]), 0.55)
            # ===== LEAD (wah / clav-solo / vox-melódico) en pentatónica menor
            if b['lead'] and lead_kind and gb % 2 == 0:
                for (s, d, o, ln) in MOTIFS[lead_kind]:
                    pos = base + int(sw(s % 16, 'clav')) + (SPB if s >= 16 else 0)
                    f = midi_f(pdeg(ROOT + 12, d, o)); dur = ln * S16 / SR * 1.2
                    if lead_kind == 'wah': x = P.lead_wah(f, dur, rng)
                    elif lead_kind == 'clav': x = P.clav(f, rng, dur=min(dur, 0.3))
                    else: x = P.vox(f, min(dur, 0.5), rng, 'aeiou'[(s + d) % 5])
                    add(leadb, pos, x, 0.55)
            # ===== PADS del amanecer
            if b['pad'] > 0.2 and bar % 2 == 0:
                x = P.pad_dust([m + 12 for m in ch[1:]], 2 * SPB / SR * 1.06, rng)
                add(padL, base, x, b['pad']); add(padR, base + int(0.016 * SR), x, b['pad'] * 0.94)

    # ------- buses
    env = sidechain(n, kpos)
    bassb *= env
    drum_st = widen(sat(drumb, 1.1, 0.04), amount=0.55, seed=idx * 3 + 2)
    gtr_st = widen(gtrb * (env * 0.35 + 0.65), amount=0.7, seed=idx * 7 + 1)
    clav_st = pingpong(clavb * (env * 0.3 + 0.7), BEAT_S, fb=0.34, mix=0.3, taps=5, damp=4400)
    brass_st = widen(brassb, amount=0.45, seed=idx + 4)
    vox_st = pingpong(voxb * (env * 0.3 + 0.7), BEAT_S, fb=0.45, mix=0.5, taps=7, damp=4800)
    lead_st = pingpong(leadb, BEAT_S, fb=0.4, mix=0.4, taps=6, damp=4200)
    pads = np.stack([padL, padR]) * (env * 0.4 + 0.6)[None, :]
    verb = np.stack([fconv(pads[0], _verb(2.8, 4600, 21)), fconv(pads[1], _verb(2.8, 4600, 22))])
    wind_st = np.stack([windb, windb[::-1].copy()])
    wgain = np.array([blk['wind'] for blk in plan_blocks(sec)], np.float32)
    wn = wind_st.shape[1]
    wenv = np.repeat(wgain, 8 * SPB)[:wn]
    if len(wenv) < wn: wenv = np.pad(wenv, (0, wn - len(wenv)), constant_values=wenv[-1] if len(wenv) else 0)
    wind_st *= lp(wenv, 1.5, 1)[None, :]
    if wn < n: wind_st = np.pad(wind_st, ((0, 0), (0, n - wn)))
    else: wind_st = wind_st[:, :n]
    music = (drum_st * 0.72 + gtr_st * 0.72 + clav_st * 0.6 + brass_st * 0.8
             + vox_st * 0.55 + lead_st * 0.68 + (pads + verb) * 0.8 + wind_st)
    mm = 0.5 * (music[0] + music[1]); ss = bp(0.5 * (music[0] - music[1]), 220, 11000, 2) * 2.3
    mix = np.stack([mm + ss, mm - ss])
    mix += kickb[None, :] * 1.2                        # SIN bajo (André: el synth sonaba horrible) — el kick lleva el low end
    genv = np.ones(n, np.float32)
    for bi, blk in enumerate(plan_blocks(sec)):
        genv[bi * 8 * SPB:min(n, (bi + 1) * 8 * SPB)] = blk['gain']
    genv = lp(genv, 2.0, 1); mix *= genv[None, :]
    mix = np.stack([sat(mix[0], 1.12, 0.045), sat(mix[1], 1.12, 0.045)])
    mix = sub_mono(mix, 120.0)
    pk = np.abs(mix).max()
    if pk > 0.93: mix *= 0.93 / pk
    return mix

def build(only=None):
    tot = sum(s['bars'] for s in SECTIONS)
    print(f'PLAYA · {len(SECTIONS)} secciones · {tot} compases ≈ {tot * SPB / SR / 60:.0f} min', flush=True)
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
    # afeitado pre-master (soft-clip) para domar transientes picudos de funk → TP controlado
    out = np.stack([sat(out[0] * 1.5, 2.0, 0.04), sat(out[1] * 1.5, 2.0, 0.04)])
    out *= 0.72 / max(1e-9, float(np.abs(out).max()))
    raw = os.path.join(TMP, 'playa-raw.wav'); wav_write(raw, out); del out
    print('  … afeitado + master -10.0 LUFS', flush=True)
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    final = os.path.join(HERE, 'masters', 'amr-playa.wav')
    hist = master_file(raw, final, target_i=-10.0, ceiling_db=-1.5)
    I, lra, tp = ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}'); print(final)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else None)
