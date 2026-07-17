#!/usr/bin/env python3
"""COLIBRÍ — set luminoso tropical estilo Polo & Pan (~36 min, 118 BPM, MAYOR).
French touch psicodélico: arpegios brillantes con delay ping-pong, marimba, flauta,
vocal chops alegres, bajo funky, batería house suave. Nada oscuro — todo color.
Uso: python3 make_colibri.py NECTAR  (una sección)  |  sin args = set completo."""
import os, sys
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, sat_warm, widen, sub_mono, pingpong,
                        stereo_verb, master_file, ffmeter, wav_write, spectrum_pct, fconv)
import colibri_voices as V
from colibri_voices import midi_f, deg, MAJ, LYD, MIX

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_colibri_tmp'); os.makedirs(TMP, exist_ok=True)
BPM = 120.0                                # sweet spot house de Polo & Pan (research)
PENT = [0, 2, 4, 7, 9]                      # pentatónica mayor — melodías cantabile/tropicales
def pdeg(root, d, o=0): return root + PENT[d % 5] + 12 * (d // 5 + o)
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0; BEAT_S = 60.0 / BPM
XF_BARS = 4
SW = dict(bass=0.56, hats=0.58, shaker=0.57, arp=0.55, keys=0.55)
KICK = V.hit_kick_soft()

# secciones = el viaje del colibrí, todas en tonalidades brillantes
# arp = patrón de arpegio (grados sobre el acorde), motif = gancho de flauta/vocal (step16, grado, oct, len)
# voicings [fund, n2, n3, n4] con el gesto IV→iv (subdominante mayor→menor, el color firma)
SECTIONS = [
 dict(name='ALBA', root=48, sc=MAJ, energy=0.40, shape='rise', bars=80, lead='flauta',
      chords=[[48,52,55,59],[53,57,60,64],[53,56,60,63],[48,52,55,59]],   # I IV iv I
      motif=[(0,2,1,4),(8,1,1,3),(16,2,1,2),(20,3,1,6)]),
 dict(name='NECTAR', root=48, sc=MAJ, energy=0.58, shape='wave', bars=112, lead='vocal',
      chords=[[48,52,55,59],[45,52,55,60],[53,57,60,64],[53,56,60,63]],   # I vi IV iv
      motif=[(0,0,1,2),(3,1,1,2),(6,2,1,3),(12,1,1,2),(16,2,1,2),(20,4,1,4)]),
 dict(name='POLEN', root=50, sc=MAJ, energy=0.66, shape='wave', bars=112, lead='marimba',
      chords=[[50,54,57,61],[45,49,52,57],[55,59,62,66],[55,58,62,65]],   # I V IV iv
      motif=[(0,2,1,1),(2,3,1,1),(4,4,1,2),(8,2,1,2),(12,1,1,3),(16,2,1,1),(18,3,1,1),(20,5,1,4)]),
 dict(name='VUELO', root=45, sc=MAJ, energy=0.82, shape='peak', bars=128, lead='vocal',
      chords=[[45,49,52,56],[50,54,57,61],[50,53,57,60],[52,56,59,64]],   # I IV iv V
      motif=[(0,2,1,1),(2,2,1,1),(4,3,1,2),(7,4,1,2),(10,2,1,2),(16,1,1,1),(18,2,1,1),(20,4,1,3),(26,3,1,4)]),
 dict(name='CENOTE', root=52, sc=MAJ, energy=0.50, shape='valley', bars=96, lead='glocken',
      chords=[[52,56,59,66],[45,49,52,56],[45,48,52,55],[52,56,59,66]],   # I IV iv I
      motif=[(0,2,1,6),(12,1,1,4),(16,0,1,8)]),
 dict(name='FIESTA', root=48, sc=MIX, energy=0.94, shape='peak', bars=136, lead='vocal',
      chords=[[48,52,55,59],[46,50,53,58],[53,57,60,64],[53,56,60,63]],   # I bVII IV iv
      motif=[(0,2,1,1),(2,2,1,1),(4,3,1,2),(7,2,1,2),(10,1,1,2),(16,2,1,1),(18,2,1,1),(20,4,1,3),(24,3,1,2),(28,2,1,4)]),
 dict(name='SELVA', root=43, sc=MIX, energy=0.72, shape='wave', bars=112, lead='flauta',
      chords=[[55,59,62,65],[53,57,60,65],[48,52,55,59],[48,51,55,58]],   # I bVII IV iv
      motif=[(0,2,1,3),(6,3,1,2),(10,2,1,2),(16,1,1,3),(22,2,1,5)]),
 dict(name='NIDO', root=48, sc=MAJ, energy=0.44, shape='outro', bars=80, lead='marimba',
      chords=[[48,52,55,62],[53,57,60,64],[53,56,60,63],[48,52,55,59]],   # I IV iv I
      motif=[(0,2,1,6),(12,1,1,4),(16,0,1,8)]),
]

def sw(s, who): return s * S16 + (SW[who] - 0.5) * 2 * S16 * (s % 2)

def add(buf, pos, x, g=1.0):
    pos = int(pos)
    if pos < 0: x = x[-pos:]; pos = 0
    end = min(len(buf), pos + len(x))
    if end > pos: buf[pos:end] += x[:end - pos] * g

def plan_blocks(sec):
    nb = sec['bars'] // 8; e = sec['energy']; shape = sec['shape']; out = []
    for i in range(nb):
        p = i / max(1, nb - 1)
        b = dict(kick=1, bass=1, arp=1, marimba=1, lead=0, perc=0.5, hats=0.6, pad=0.5,
                 gain=1.0, dly=0.2, voc=0)
        if i == 0: b.update(bass=0, perc=0.2, hats=0.3, marimba=0.4, arp=0.6)
        if i == 1: b.update(perc=0.35, marimba=0.7)
        if p > 0.25: b['lead'] = 1
        if p > 0.35 and sec['lead'] == 'vocal': b['voc'] = 1
        b['dly'] = 0.15 + 0.2 * p
        if shape == 'valley' and 0.4 < p < 0.68:
            b.update(kick=0, bass=0, gain=0.62, perc=0.15, hats=0.15, pad=0.9, arp=0.5, lead=1)
        if shape == 'wave' and 0.48 < p < 0.6:
            b.update(bass=0, gain=0.82, perc=0.3)
        if shape == 'rise': b['gain'] = 0.72 + 0.28 * p
        if shape == 'peak':
            if 0.34 < p < 0.48: b.update(kick=0, bass=0, gain=0.66, pad=0.85, voc=1)
            elif p >= 0.48: b.update(perc=0.9, hats=0.85, voc=1, gain=1.0)
        if shape == 'outro':
            b['gain'] = 1.0 - 0.5 * max(0.0, p - 0.4)
            if p > 0.6: b.update(lead=0, arp=0.5, perc=0.2)
        out.append(b)
    return out

def sidechain(n, kpos, depth=0.34, rel=0.09):
    env = np.ones(n, np.float32)
    dip = 1.0 - depth * np.exp(-np.arange(int(rel * 4 * SR)) / (rel * SR)).astype(np.float32)
    for p in kpos:
        e = min(n, p + len(dip))
        if e > p: env[p:e] = np.minimum(env[p:e], dip[:e - p])
    return env

def _verb(decay, tone, seed):
    m = int(decay * SR); rng = np.random.default_rng(seed)
    ir = rng.standard_normal(m).astype(np.float32) * np.exp(-np.linspace(0, 6.5, m)).astype(np.float32)
    ir = lp(ir, tone, 2); ir /= np.sqrt((ir ** 2).sum()) + 1e-12
    return ir * 0.3

def render_section(sec, idx):
    rng = np.random.default_rng(500 + idx * 13)
    bars = sec['bars']; n = bars * SPB + XF_BARS * SPB
    blocks = plan_blocks(sec); root, sc, chords = sec['root'], sec['sc'], sec['chords']
    kickb = np.zeros(n, np.float32); bassb = np.zeros(n, np.float32)
    percb = np.zeros(n, np.float32); arpb = np.zeros(n, np.float32)
    leadb = np.zeros(n, np.float32); vocb = np.zeros(n, np.float32)
    marb = np.zeros(n, np.float32); padL = np.zeros(n, np.float32); padR = np.zeros(n, np.float32)
    glob = np.zeros(n, np.float32); kpos = []

    # NATURALEZA (el "viaje"): agua toda la sección de fondo; pájaros en intro/valle
    natL = V.water(n / SR, rng); natR = V.water(n / SR, np.random.default_rng(idx * 31 + 1))
    if sec['shape'] in ('rise', 'valley', 'outro') or idx == 0:
        b_ = V.birds(min(24.0, n / SR), rng)
        natL[:len(b_)] += b_; natR[:len(b_)] += V.birds(min(24.0, n / SR), rng)

    # patrón de arpegio: sube-baja sobre las notas del acorde (marca French touch)
    ARP = [0, 1, 2, 3, 2, 1, 3, 2, 0, 1, 2, 3, 2, 3, 1, 2]
    for bi, b in enumerate(blocks):
        for bar in range(8):
            gb = bi * 8 + bar
            if gb >= bars: break
            base = gb * SPB
            ch = chords[(gb // 2) % len(chords)]
            last16 = (gb % 16 == 15)
            # kick suave 4x4 (respira al fin de frase)
            if b['kick'] and not (sec['shape'] == 'rise' and gb < 4):
                for beat in range(4):
                    if last16 and beat >= 2 and (gb // 16) % 2 == 1: continue
                    add(kickb, base + beat * 4 * S16, KICK, 1.0); kpos.append(int(base + beat * 4 * S16))
            # bajo funky (notas root/5/octava con groove, no rolling denso)
            if b['bass']:
                fr = midi_f(ch[0] - 24)
                pat = [(0, 1.0), (3, 0.6), (6, 0.85), (10, 0.7), (11, 0.5), (14, 0.8)]
                if (gb // 8) % 2: pat = [(0, 1.0), (4, 0.7), (6, 0.85), (10, 0.6), (13, 0.8), (14, 0.5)]
                for s, v in pat:
                    f = fr * (2.0 if v < 0.6 and rng.uniform() < 0.4 else 1.0)
                    add(bassb, base + sw(s, 'bass') + rng.normal(0, .004) * SR,
                        V.bass_funk(f, S16 / SR * 2.2, rng, cutoff=800 + 400 * b['gain']), v * 0.9)
            # ARPEGIO brillante en 16ths (el corazón del sonido)
            if b['arp'] > 0:
                for s in range(16):
                    if rng.uniform() < 0.06: continue
                    d = ARP[s]
                    m = ch[1 + d % 3] + 12 * (d // 3)
                    add(arpb, base + sw(s, 'arp'), V.arp_note(midi_f(m), S16 / SR * 1.4, rng),
                        b['arp'] * (0.5 if s % 2 else 0.35))
            # MARIMBA: acordes rasgueados en el offbeat
            if b['marimba'] > 0 and bar % 2 == 0:
                for k, m in enumerate(ch[1:]):
                    add(marb, base + int(4 * S16 + k * 0.01 * SR),
                        V.marimba(midi_f(m), 0.5, rng), b['marimba'] * 0.4)
                    add(marb, base + int(12 * S16 + k * 0.01 * SR),
                        V.marimba(midi_f(m), 0.45, rng), b['marimba'] * 0.32)
            # PERCUSIÓN suave: clap backbeat + shaker + tamb + conga acento
            pg = b['perc']
            if pg >= 0.4:
                for s in (4, 12):
                    add(percb, base + sw(s, 'hats') + rng.normal(0, .003) * SR, V.hit_clap_soft(rng), pg * 0.6)
                for s in range(0, 16, 2):
                    add(percb, base + sw(s, 'shaker') + rng.normal(0, .003) * SR, V.hit_shaker_s(rng), 0.12 * (1 if s % 4 == 2 else 0.6))
                if bar % 2 == 1:
                    add(percb, base + sw(6, 'hats'), V.hit_tamb(rng), pg * 0.35)
                if bar % 4 == 2:
                    add(percb, base + sw(7, 'shaker'), V.hit_conga_s(rng, open_=True), pg * 0.4)
                if last16:
                    for k, s in enumerate((12, 13, 14, 15)):
                        add(percb, base + sw(s, 'shaker'), V.hit_conga_s(rng, f0=180 + 30 * k, open_=(k == 3)), pg * (0.3 + 0.08 * k))
            if b['hats'] > 0:
                for s in (2, 6, 10, 14):
                    add(percb, base + sw(s, 'hats') + rng.normal(0, .003) * SR, V.hit_shaker_s(rng), b['hats'] * 0.2)
            # PADS cálidos
            if b['pad'] > 0.4 and bar % 2 == 0:
                durp = int(2 * SPB * 1.05)
                for m in ch[1:]:
                    x = V.flauta(midi_f(m), durp / SR, rng, air=0.15)   # pad de "aire de flauta"
                    env = np.minimum(1, np.arange(len(x)) / (0.9 * SR)).astype(np.float32)
                    add(padL, base, x * env, b['pad'] * 0.12); add(padR, base, x[::-1] * env, b['pad'] * 0.12)
            # GLOCKEN de acento en downbeats fuertes
            if b['gain'] >= 0.9 and bar % 4 == 0:
                add(glob, base, V.glocken(midi_f(deg(root, sc, [0, 4, 2][(bar // 4) % 3], 2)), 1.2, rng), 0.3)
            # EL GANCHO (flauta / vocal / marimba / glocken) — en PENTATÓNICA, cantabile
            if b['lead'] and gb % 2 == 0:
                for (s, d, o, ln) in sec['motif']:
                    m = pdeg(root, d, o + 1)
                    f = midi_f(m); dur = ln * S16 / SR * 1.15
                    pos = base + int(sw(s % 16, 'keys')) + (SPB if s >= 16 else 0)
                    if sec['lead'] == 'flauta': x = V.flauta(f, dur, rng)
                    elif sec['lead'] == 'marimba': x = V.marimba(f, min(dur, 0.6), rng)
                    elif sec['lead'] == 'glocken': x = V.glocken(f, min(dur, 1.4), rng)
                    else: x = V.vocal_la(f, dur, rng, 'aeiou'[(s + d) % 5])
                    add(leadb, pos, x, 0.5)
            # VOCAL CHOPS rítmicos (¡ah! ¡ah!) — la alegría Polo & Pan
            if b['voc'] and bar % 2 == 1:
                for s in (0, 4, 6, 10, 12):
                    if rng.uniform() < 0.7:
                        d = int(rng.integers(0, 5)); m = deg(root, sc, d, 2)
                        add(vocb, base + sw(s, 'arp'), V.vocal_la(midi_f(m), 0.28, rng, 'aaeio'[s % 5]), 0.4)

    # buses → estéreo con delays ping-pong (French touch)
    env = sidechain(n, kpos)
    bassb *= env
    perc_st = widen(sat(percb, 1.1, 0.04), amount=0.6, seed=idx * 3 + 1)
    arp_st = pingpong(arpb * (env * 0.4 + 0.6), BEAT_S, fb=0.45, mix=0.5, taps=8, damp=5200)  # arpegio delayado, brillante
    lead_st = pingpong(leadb, BEAT_S, fb=0.4, mix=0.42, taps=6, damp=4200)
    voc_st = pingpong(vocb * (env * 0.4 + 0.6), BEAT_S, fb=0.5, mix=0.55, taps=8, damp=4600)
    mar_st = widen(marb, amount=0.5, seed=idx * 5 + 2)
    glo_st = widen(glob, amount=0.7, seed=idx + 9)
    pads = np.stack([padL, padR]) * (env * 0.4 + 0.6)[None, :]
    verb = np.stack([fconv(pads[0], _verb(2.6, 5200, 11)), fconv(pads[1], _verb(2.6, 5200, 88))])
    nat = np.stack([natL, natR]) * 0.5                     # agua + pájaros, suave de fondo
    music = (perc_st * 0.7 + arp_st * 0.6 + lead_st * 0.75 + voc_st * 0.55
             + mar_st * 0.6 + glo_st * 0.4 + (pads + verb) * 0.7 + nat)
    # ancho lateral banda-limitada
    mm = 0.5 * (music[0] + music[1]); ss = bp(0.5 * (music[0] - music[1]), 200, 12000, 2) * 2.4
    mix = np.stack([mm + ss, mm - ss])
    mix += kickb[None, :] * 1.12 + bassb[None, :] * 1.35
    # macro-dinámica por bloque
    genv = np.ones(n, np.float32)
    for bi, b in enumerate(blocks):
        genv[bi * 8 * SPB:min(n, (bi + 1) * 8 * SPB)] = b['gain']
    genv = lp(genv, 2.0, 1); mix *= genv[None, :]
    mix = np.stack([sat(mix[0], 1.12, 0.04), sat(mix[1], 1.12, 0.04)])
    mix = sub_mono(mix, 120.0)
    pk = np.abs(mix).max()
    if pk > 0.93: mix *= 0.93 / pk
    return mix

def build(only=None):
    tot = sum(s['bars'] for s in SECTIONS)
    print(f'COLIBRÍ · {len(SECTIONS)} secciones · {tot} compases ≈ {tot * SPB / SR / 60:.0f} min', flush=True)
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
    raw = os.path.join(TMP, 'colibri-raw.wav'); wav_write(raw, out); del out
    print('  … master -8.5 LUFS', flush=True)
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    final = os.path.join(HERE, 'masters', 'amr-colibri.wav')
    hist = master_file(raw, final, target_i=-8.5, ceiling_db=-1.2)
    I, lra, tp = ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}'); print(final)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else None)
