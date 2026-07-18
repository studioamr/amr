#!/usr/bin/env python3
"""KIT — samples REALES de hardware (CC0, dominio público) para AMR.

Reemplaza la batería SINTETIZADA (que sonaba a videojuego) por grabaciones de
máquinas reales. André: "los que tú haces luego se escucha como videojuego".

FUENTES (ambas CC0 1.0 Universal — dominio público, uso comercial libre,
sin atribución requerida; se puede vender la música resultante sin problema):
  · MckAudio/MckSamplePacks — TR-808/909/707/606, RD6, DR5, RX5 grabados del
    hardware por el autor con ZOOM U-24, 48kHz/24-bit, normalizados a -1dBFS.
  · Sonic Pi (sonic-pi-net) — 206 samples CC0, incluye ambientes ambi_*.
Los WAV viven en _samples/ (GITIGNORED — solo el audio renderizado se publica)."""
import os
import numpy as np
from dream_core import ffdecode, SR

HERE = os.path.dirname(os.path.abspath(__file__))
MCK = os.path.join(HERE, '_samples', 'MckSamplePacks-main')
AMB = os.path.join(HERE, '_samples', 'sonicpi')
_cache = {}

def smp(path, gain=1.0, norm=True):
    """carga un sample real (cacheado, mono, sin silencio inicial, normalizado)."""
    if path not in _cache:
        x = ffdecode(path, mono=True).astype(np.float32)
        nz = np.nonzero(np.abs(x) > 2e-4)[0]
        if len(nz): x = x[nz[0]:]
        mx = float(np.abs(x).max())
        if norm and mx > 0: x = x / mx
        _cache[path] = np.ascontiguousarray(x)
    return _cache[path] * gain

def vary(x, rng, pitch=0.02, amp=0.12):
    """variación humana por golpe: micro-pitch (resample) + amplitud.
    Evita el 'copy-paste' robótico de repetir el MISMO sample idéntico."""
    g = 1.0 - amp * rng.uniform(0, 1)
    r = 1.0 + pitch * rng.uniform(-1, 1)
    if abs(r - 1.0) < 1e-4: return x * g
    n = int(len(x) / r)
    if n < 8: return x * g
    idx = np.minimum(len(x) - 1, (np.arange(n) * r)).astype(np.int32)
    return x[idx] * g

def M(rel): return os.path.join(MCK, rel)
def A(rel): return os.path.join(AMB, rel)

# ---------------- KIT curado (house/techno clásico: 909 + 808 reales)
KICK    = M('TR8/BD/013_909_AttackBD_2.wav')          # 909 con pegada
KICK808 = M('TR8/BD/008_808_Bass_Drum_Long_2.wav')    # 808 profundo (sub)
CLAP    = M('TR8/PERC/019_909_Hand_Clap.wav')         # el clap 909
CLAP808 = M('TR8/PERC/017_808_Hand_Clap.wav')
SNARE   = M('TR8/SD/006_909_Snare_Drum_2.wav')
HATC    = M('TR8/HATS/010_909_Closed_HiHat_Short.wav')
HATC2   = M('TR8/HATS/002_808_Closed_HiHat.wav')
HATO    = M('TR8/HATS/007_909_Open_HiHat.wav')
SHAKER  = M('DR5/PERC/020_Shaker.wav')
TAMB    = M('DR5/PERC/002_Tambourine.wav')
CABASA  = M('DR5/PERC/021_Cabasa.wav')
RIM     = M('TR8/PERC/008_808_Rim_Shot.wav')
COWBELL = M('TR8/PERC/033_808_Cowbell.wav')
CONGA_L = M('TR8/TOMS/022_808_Low_Conga_Short.wav')
RIDE    = M('DR5/HATS/014_Ride_Cymbal.wav')
CRASH   = M('TR8/HATS/020_909_Crash_Cymbal.wav')
REVCYM  = M('DR5/FX/017_Reverse_Cymbal.wav')
REVCLAP = M('DR5/FX/018_Reverse_Clap.wav')
# ambientes CC0 (Sonic Pi)
AMBI_WOOSH = A('ambi_dark_woosh.flac')
AMBI_SWOOSH= A('ambi_swoosh.flac')
AMBI_DRONE = A('ambi_drone.flac')
AMBI_GLASS = A('ambi_glass_hum.flac')

ALL = dict(KICK=KICK, KICK808=KICK808, CLAP=CLAP, CLAP808=CLAP808, SNARE=SNARE,
           HATC=HATC, HATC2=HATC2, HATO=HATO, SHAKER=SHAKER, TAMB=TAMB, CABASA=CABASA,
           RIM=RIM, COWBELL=COWBELL, CONGA_L=CONGA_L, RIDE=RIDE, CRASH=CRASH,
           REVCYM=REVCYM, REVCLAP=REVCLAP, AMBI_WOOSH=AMBI_WOOSH,
           AMBI_SWOOSH=AMBI_SWOOSH, AMBI_DRONE=AMBI_DRONE, AMBI_GLASS=AMBI_GLASS)

if __name__ == '__main__':
    print('Verificando kit de samples REALES (CC0)…')
    bad = 0
    for k, p in ALL.items():
        if not os.path.exists(p):
            print(f'  ✗ FALTA  {k}: {p}'); bad += 1; continue
        x = smp(p)
        print(f'  ✓ {k:11s} {len(x)/SR:5.2f}s  pico {float(np.abs(x).max()):.2f}  {os.path.basename(p)}')
    print(('OK — kit completo' if not bad else f'{bad} faltantes'))
