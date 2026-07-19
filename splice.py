#!/usr/bin/env python3
"""SPLICE — índice de la librería de André. Material profesional, ya en su disco.

André: "tengo hasta splice con sonidos, estoy lleno de sonidos en ableton".
Y tenía razón: 302 packs, 2.1 GB. Esto es mejor que TODO lo que se bajó hoy —
son samples producidos profesionalmente, y la suscripción de Splice los licencia
para uso comercial del suscriptor, que es exactamente el caso (él vende vinilos).

Packs que importan para lo que estamos haciendo:
  Afro House & Vocals · Afro Vocal House · Afro House Yethu
  Air - Progressive Melodic House · Atmospheric Techno
  ANNA's Deconstruct (Resident Advisor) · Ambient Textures

EL PROBLEMA QUE RESUELVE ESTE ARCHIVO: 395 audios repartidos en 302 carpetas no
sirven de nada si no puedes encontrar "un loop de percusión afro a 120 BPM en La
menor". Splice codifica BPM y tonalidad EN EL NOMBRE del archivo, con formatos
inconsistentes entre packs. Esto los normaliza y los deja buscables.

  python3 splice.py                    → resumen de la librería
  python3 splice.py vocal              → todo lo vocal
  python3 splice.py perc --bpm 120     → percusión cerca de 120 BPM
  python3 splice.py --key Amin         → todo en La menor
"""
import os, re, sys, glob, json
import numpy as np

RAIZ = os.path.expanduser('~/Splice/sounds/packs')
HERE = os.path.dirname(os.path.abspath(__file__))
INDICE = os.path.join(HERE, '_samples', 'splice-indice.json')

# ── BPM: "120bpm", "_128_", "-124-", "120 BPM"
_BPM = [re.compile(r'(\d{2,3})\s*[_\- ]?bpm', re.I),
        re.compile(r'bpm[_\- ]?(\d{2,3})', re.I),
        re.compile(r'[_\-](\d{2,3})[_\-]')]
# ── tonalidad: "Amin", "Cmi", "F#maj", "_Dm_", "Abmin"
_KEY = re.compile(r'[_\- ]([A-G][#b]?)\s*(min|maj|m|M|mi|ma)?[_\-. ]', re.I)

CATS = {
 'kick':   ('kick','bd_','bassdrum'),
 'clap':   ('clap','snap'),
 'snare':  ('snare','sd_','rimshot','rim_'),
 'hat':    ('hat','hihat','hh_','shaker','tamb','cabasa'),
 'perc':   ('perc','conga','bongo','djembe','tabla','clave','woodblock','tom_','cowbell'),
 'drumloop':('drum_loop','drumloop','beat_','full_loop','groove','top_loop','breakbeat'),
 'bass':   ('bass','sub_','808'),
 'vocal':  ('vocal','vox','chant','choir','acapella','adlib','spoken','sigh','whisper','dialogue'),
 'chord':  ('chord','stab','keys','piano','rhodes','organ'),
 'lead':   ('lead','arp','pluck','melody','synth'),
 'pad':    ('pad','atmo','texture','drone','ambient','string'),
 'fx':     ('fx','riser','impact','sweep','downlifter','uplifter','noise','foley','reverse'),
}

def _bpm(n):
    for r in _BPM:
        m = r.search(n)
        if m:
            v = int(m.group(1))
            if 60 <= v <= 200: return v
    return None

def _key(n):
    m = _KEY.search(n)
    if not m: return None
    nota, modo = m.group(1).upper(), (m.group(2) or '').lower()
    if modo in ('min','m','mi'): modo = 'min'
    elif modo in ('maj','ma'):   modo = 'maj'
    else: return None                      # sin modo explícito es demasiado ambiguo
    return f'{nota}{modo}'

def _cat(ruta):
    l = ruta.lower()
    for c, claves in CATS.items():
        if any(k in l for k in claves): return c
    return 'otro'

def construye():
    if not os.path.isdir(RAIZ): return []
    out = []
    for f in glob.glob(os.path.join(RAIZ, '**', '*.*'), recursive=True):
        if not f.lower().endswith(('.wav','.aif','.aiff','.mp3','.flac')): continue
        base = os.path.basename(f)
        rel = os.path.relpath(f, RAIZ)
        out.append(dict(ruta=f, pack=rel.split(os.sep)[0], nombre=base,
                        cat=_cat(rel), bpm=_bpm(base), key=_key(base),
                        loop=('loop' in base.lower() or 'loop' in rel.lower()),
                        mb=round(os.path.getsize(f)/1048576, 2)))
    os.makedirs(os.path.dirname(INDICE), exist_ok=True)
    json.dump(out, open(INDICE,'w'))
    return out

def indice():
    if os.path.exists(INDICE):
        try: return json.load(open(INDICE))
        except Exception: pass
    return construye()

def busca(cat=None, bpm=None, key=None, loop=None, tol=6, texto=None):
    """Busca en la librería. bpm con tolerancia; también acepta mitad/doble tempo."""
    r = indice()
    if cat:   r = [x for x in r if x['cat'] == cat]
    if loop is not None: r = [x for x in r if x['loop'] == loop]
    if key:   r = [x for x in r if x['key'] == key]
    if texto: r = [x for x in r if texto.lower() in x['nombre'].lower()
                                or texto.lower() in x['pack'].lower()]
    if bpm:
        def cerca(v):
            if v is None: return False
            return min(abs(v-bpm), abs(v-bpm*2), abs(v-bpm/2)) <= tol
        r = [x for x in r if cerca(x['bpm'])]
    return r

def resumen():
    r = indice()
    print(f'LIBRERÍA SPLICE · {len(r)} archivos · '
          f'{len(set(x["pack"] for x in r))} packs · {sum(x["mb"] for x in r)/1024:.2f} GB\n')
    print(f'  {"categoría":10s} {"total":>5s} {"loops":>6s} {"c/BPM":>6s} {"c/tono":>7s}')
    for c in list(CATS) + ['otro']:
        v = [x for x in r if x['cat'] == c]
        if not v: continue
        print(f'  {c:10s} {len(v):5d} {sum(1 for x in v if x["loop"]):6d} '
              f'{sum(1 for x in v if x["bpm"]):6d} {sum(1 for x in v if x["key"]):7d}')
    bp = [x['bpm'] for x in r if x['bpm']]
    if bp:
        print(f'\n  BPM detectados: {min(bp)}–{max(bp)} · mediana {int(np.median(bp))}')
    ks = {}
    for x in r:
        if x['key']: ks[x['key']] = ks.get(x['key'],0)+1
    if ks:
        print('  tonalidades: ' + ' · '.join(f'{k}({v})' for k,v in
              sorted(ks.items(), key=lambda a:-a[1])[:8]))
    print('\n  Packs con más material útil:')
    pk = {}
    for x in r:
        if x['cat'] != 'otro': pk[x['pack']] = pk.get(x['pack'],0)+1
    for p,n in sorted(pk.items(), key=lambda a:-a[1])[:10]:
        print(f'    {n:3d}  {p[:58]}')

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: resumen(); raise SystemExit
    cat = a[0] if not a[0].startswith('--') else None
    bpm = int(a[a.index('--bpm')+1]) if '--bpm' in a else None
    key = a[a.index('--key')+1] if '--key' in a else None
    txt = a[a.index('--txt')+1] if '--txt' in a else None
    r = busca(cat=cat, bpm=bpm, key=key, texto=txt)
    print(f'{len(r)} resultados\n')
    for x in r[:40]:
        print(f'  {x["cat"]:9s} {str(x["bpm"] or "—"):>4s} {str(x["key"] or "—"):>6s} '
              f'{"loop" if x["loop"] else "shot":4s}  {x["nombre"][:58]}')
        print(f'            {x["pack"][:70]}')
