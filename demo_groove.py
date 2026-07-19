#!/usr/bin/env python3
"""A/B audible del groove: el mismo patrón, la misma batería real, 4 formas de tocarlo.

  compases  1-8   VIEJO   rejilla recta + jitter gaussiano (lo que hacíamos)
  compases  9-16  HOUSE   swing 56%, firma de empuje, velocity por frase
  compases 17-24  AFRO    swing 58%, más balanceo, fantasmas densos
  compases 25-32  LAID    todo un pelo atrás

Mismo kit, mismas notas, mismo master. Lo único que cambia es CÓMO se toca.
Salida: _demo/groove-ab.m4a
"""
import os, subprocess
import numpy as np
import imageio_ffmpeg
from dream_core import SR, wav_write, sat, widen, sub_mono
import kit as K
from groove import Groove

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_demo'); os.makedirs(OUT, exist_ok=True)
BPM = 122.0
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0
BARS = 8

def bloque(modo, seed):
    """8 compases del MISMO patrón, tocados según el modo."""
    n = BARS * SPB + SPB
    kick = np.zeros(n, np.float32); perc = np.zeros(n, np.float32)
    rng = np.random.default_rng(seed)
    g = None if modo == 'viejo' else Groove(modo, S16, SR, bpm=BPM, seed=seed)

    def add(buf, pos, x, gain):
        pos = int(pos)
        if pos < 0: x = x[-pos:]; pos = 0
        e = min(len(buf), pos + len(x))
        if e > pos: buf[pos:e] += x[:e - pos] * gain

    for bar in range(BARS):
        base = bar * SPB
        # KICK 4x4 — siempre recto, es el ancla (así se hace de verdad)
        for beat in range(4):
            add(kick, base + beat * 4 * S16,
                K.vary(K.smp(K.KICK), rng, 0.010, 0.06), 0.95)
        # CLAP en 2 y 4
        for s in (4, 12):
            pos = (base + s * S16 - 0.010 * SR) if g is None else (g.pos(base, s, bar) - 0.010 * SR)
            v = 1.0 if g is None else g.vel(s, bar)
            add(perc, pos, K.vary(K.smp(K.CLAP), rng, 0.02, 0.12), 0.44 * v)
        # HATS en 16avos — AQUÍ es donde se oye el groove
        for s in range(16):
            op = (s % 4 == 2)
            sm = K.smp(K.HATO) if op else K.smp(K.HATC)
            if g is None:
                pos = base + s * S16 + rng.normal(0, .0016) * SR
                v = 0.32 if s % 2 else 0.20
            else:
                pos = g.pos(base, s, bar)
                v = g.vel(s, bar) * (0.34 if s % 2 else 0.24)
            add(perc, pos, K.vary(sm, rng, 0.03, 0.26), v * (0.7 if op else 1.0))
        # SHAKER + CONGA
        for s in range(2, 16, 4):
            pos = (base + s * S16 + rng.normal(0, .003) * SR) if g is None else g.pos(base, s, bar)
            v = 1.0 if g is None else g.vel(s, bar)
            add(perc, pos, K.vary(K.smp(K.SHAKER), rng, 0.04, 0.28), 0.30 * v)
        if bar % 2 == 1:
            pos = (base + 10 * S16) if g is None else g.pos(base, 10, bar)
            add(perc, pos, K.vary(K.smp(K.CONGA_L), rng, 0.03, 0.2), 0.42)
        # FANTASMAS — sólo existen con groove. Es lo que suena a manos.
        if g is not None:
            for s in range(16):
                if g.ghost(s, bar, rng):
                    add(perc, g.pos(base, s, bar),
                        K.vary(K.smp(K.HATC), rng, 0.05, 0.4), g.ghost_vel(s, bar) * 0.5)
                    if s % 4 == 3 and rng.random() < 0.35:
                        add(perc, g.pos(base, s, bar),
                            K.vary(K.smp(K.RIM), rng, 0.04, 0.3), 0.13)

    st = widen(perc, amount=0.42, seed=seed)
    mix = st * 0.9 + kick[None, :] * 0.95
    mix = np.stack([sat(mix[0], 1.05, 0.02), sat(mix[1], 1.05, 0.02)])
    return sub_mono(mix, 120.0)[:, :BARS * SPB]

if __name__ == '__main__':
    print(f'A/B de groove · {BPM:.0f} BPM · batería REAL (909/808/DR5)', flush=True)
    partes = []
    for i, modo in enumerate(('viejo', 'house', 'afro', 'laid')):
        print(f'  … {modo}', flush=True)
        partes.append(bloque(modo, 40 + i * 11))
    x = np.concatenate(partes, axis=1)
    x *= 0.86 / max(1e-9, float(np.abs(x).max()))
    wav = os.path.join(OUT, 'groove-ab.wav'); wav_write(wav, x)
    m4a = os.path.join(OUT, 'groove-ab.m4a')
    subprocess.run([FF, '-y', '-v', 'error', '-i', wav, '-c:a', 'aac_at', '-b:a', '192k',
                    '-movflags', '+faststart', m4a], check=True)
    os.remove(wav)
    dur = x.shape[1] / SR
    print(f'\n{m4a}')
    print(f'{dur:.0f}s · cada bloque {BARS*SPB/SR:.0f}s')
    print(f'  0:00  VIEJO  rejilla recta + jitter (lo que hacíamos)')
    print(f'  0:{int(BARS*SPB/SR):02d}  HOUSE  swing 56% + firma + fantasmas')
    print(f'  0:{int(2*BARS*SPB/SR):02d}  AFRO   swing 58%, el balanceo')
    print(f'  0:{int(3*BARS*SPB/SR):02d}  LAID   todo un pelo atrás')
