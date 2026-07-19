#!/usr/bin/env python3
"""INSTRUMENTOS — sampler de instrumentos REALES. El fin de los sintetizadores.

André, tres veces y cada vez más claro:
  "los que tú haces luego se escucha como videojuego"
  "cuando te digo videojuego justo a eso me refiero, esos que tú haces"
  "elimínalos por completo y empieza a descargar cosas de calidad"

Esto lo cumple. Toda nota melódica sale ahora de una GRABACIÓN de un instrumento
de verdad (VCSL, CC0 1.0 verificado leyendo su LICENSE), no de sumar sierras.

CÓMO FUNCIONA
  VCSL nombra cada archivo con su nota adentro:
      Mbira6_Normal_MainSpirit_B2_k8_vl3_rr2.wav
                              ^^ nota  ^^^ capa de velocity  ^^^ round-robin
  Se escanea la carpeta, se saca la nota de cada nombre, y se arma un mapa
  instrumento → {nota MIDI: [archivos]}. Al pedir una nota:
    · si existe grabada, se usa TAL CUAL (cero procesamiento)
    · si no, se toma la MÁS CERCANA y se resamplea el mínimo necesario
  Nunca se estira más de 4 semitonos: más allá el timbre se deforma y vuelve a
  sonar a sintetizador, que es justo lo que estamos matando.

  Los round-robin y las capas de velocity se eligen al azar por golpe — así dos
  notas iguales seguidas NO son el mismo archivo, que es el "copy-paste
  robótico" que ya habíamos arreglado en la batería con kit.vary().
"""
import os, re, glob, random
import numpy as np
from dream_core import SR, ffdecode

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, '_samples', 'vcsl')

# nota en el nombre: _C4_ · _F#3_ · _Bb2_ · _A-1_
_RE = re.compile(r'_([A-G])([#b]?)(-?\d)[_.]')
_PC = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}

def _midi(nombre):
    m = _RE.search(nombre)
    if not m: return None
    p, alt, octa = m.group(1), m.group(2), int(m.group(3))
    v = _PC[p] + (1 if alt=='#' else -1 if alt=='b' else 0)
    return 12*(octa+1) + v            # C4 = 60, como el estándar

# ---- catálogo curado: nombre corto → cómo reconocerlo en la ruta
CATALOGO = {
 'kalimba':   ('kalimba',),
 'mbira':     ('mbira',),
 'balafon':   ('balafon',),
 'marimba':   ('marimba',),
 'vibrafono': ('vibraphone',),
 'glocken':   ('glockenspiel',),
 'xilofono':  ('xylophone',),
 'celesta':   ('celesta',),
 'arpa':      ('harp',),
 'piano':     ('piano',),
 'organo':    ('organ',),
 'guitarra':  ('guitar',),
 'campana':   ('bell', 'chime', 'crotale'),
 'cuenco':    ('singing bowl', 'bowl'),
 'gong':      ('gong', 'tam-tam'),
 'flauta':    ('flute', 'recorder', 'ocarina', 'pan pipe'),
 'contrabajo':('contrabass', 'double bass'),
}

_MAPA = None      # instrumento → {midi: [rutas]}
_CACHE = {}       # ruta → audio decodificado

def mapa():
    global _MAPA
    if _MAPA is not None: return _MAPA
    _MAPA = {}
    if not os.path.isdir(RAIZ): return _MAPA
    for f in glob.glob(os.path.join(RAIZ, '**', '*.wav'), recursive=True):
        n = _midi(os.path.basename(f))
        if n is None: continue
        low = f.lower()
        for inst, claves in CATALOGO.items():
            if any(c in low for c in claves):
                _MAPA.setdefault(inst, {}).setdefault(n, []).append(f)
                break
    return _MAPA

def hay(inst):
    return inst in mapa() and len(mapa()[inst]) > 0

def instrumentos():
    """Los que de verdad quedaron utilizables, con su rango."""
    out = []
    for k, v in sorted(mapa().items()):
        if not v: continue
        ns = sorted(v)
        out.append((k, len(ns), ns[0], ns[-1], sum(len(x) for x in v.values())))
    return out

def _carga(ruta):
    if ruta not in _CACHE:
        if len(_CACHE) > 220: _CACHE.clear()          # techo de memoria
        x = ffdecode(ruta, mono=True).astype(np.float32)
        nz = np.nonzero(np.abs(x) > 1.5e-4)[0]
        if len(nz): x = x[nz[0]:]
        m = float(np.abs(x).max())
        _CACHE[ruta] = (x/m if m > 0 else x)
    return _CACHE[ruta]

MAX_ESTIRA = 4        # semitonos. Más allá el timbre se deforma y vuelve a sonar sintético.

def nota(inst, midi, dur=None, rng=None, gain=1.0):
    """Devuelve la nota tocada por el instrumento REAL. dur en segundos (None = completa)."""
    M = mapa().get(inst)
    if not M: return np.zeros(int((dur or 0.3)*SR), np.float32)
    rng = rng or np.random
    disp = sorted(M)
    cerca = min(disp, key=lambda n: abs(n - midi))
    if abs(cerca - midi) > MAX_ESTIRA:                # fuera de rango: se transporta por octavas
        while midi - cerca > MAX_ESTIRA:  midi -= 12
        while cerca - midi > MAX_ESTIRA:  midi += 12
        cerca = min(disp, key=lambda n: abs(n - midi))
    x = _carga(rng.choice(M[cerca]))                  # round-robin al azar
    semis = midi - cerca
    if semis != 0:                                    # resample mínimo
        r = 2.0 ** (semis/12.0)
        n = int(len(x)/r)
        if n > 8:
            idx = np.minimum(len(x)-1, (np.arange(n)*r)).astype(np.int32)
            x = x[idx]
    if dur is not None:
        n = int(dur*SR)
        if len(x) > n:
            x = x[:n].copy()
            f = min(int(0.012*SR), n//4)              # fade para no cortar seco
            if f > 2: x[-f:] *= np.linspace(1, 0, f).astype(np.float32)
        elif len(x) < n:
            x = np.concatenate([x, np.zeros(n-len(x), np.float32)])
    return x * gain

def acorde(inst, midis, dur=None, rng=None, gain=1.0, spread=0.012):
    """Varias notas con un rasgueo mínimo entre ellas — como lo tocaría una mano."""
    rng = rng or np.random
    voces = [nota(inst, m, dur, rng, gain) for m in midis]
    n = max(len(v) for v in voces) + int(spread*SR*len(midis))
    out = np.zeros(n, np.float32)
    for i, v in enumerate(voces):
        o = int(i*spread*SR)
        out[o:o+len(v)] += v
    return out / max(1.0, len(midis)**0.5)

if __name__ == '__main__':
    M = mapa()
    if not M:
        print(f'No hay samples en {RAIZ}. ¿Corrió bajar_libreria.py?'); raise SystemExit
    print(f'INSTRUMENTOS REALES disponibles (VCSL, CC0)\n')
    print(f'  {"instrumento":12s} {"notas":>5s} {"rango":>12s} {"archivos":>8s}')
    tot = 0
    for k, nn, lo, hi, arch in instrumentos():
        nom = lambda m: ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][m%12]+str(m//12-1)
        print(f'  {k:12s} {nn:5d} {nom(lo)+"–"+nom(hi):>12s} {arch:8d}')
        tot += arch
    print(f'\n  {len(M)} instrumentos · {tot} grabaciones')
    print('\nPrueba: una nota de cada uno…')
    rng = np.random.default_rng(1)
    for k, *_ in instrumentos():
        x = nota(k, 60, 0.6, rng)
        ok = np.isfinite(x).all() and float(np.abs(x).max()) > 1e-4
        print(f'  {"✓" if ok else "✗"} {k:12s} pico {float(np.abs(x).max()):.2f}')
