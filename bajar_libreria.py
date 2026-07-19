#!/usr/bin/env python3
"""Baja la librería de INSTRUMENTOS REALES. Cero síntesis.

André: "cuando te digo videojuego justo a eso me refiero, esos que tú haces —
elimínalos por completo y empieza a descargar cosas de calidad".

Tiene razón y es el mismo salto que ya funcionó una vez: cuando cambiamos la
batería sintetizada por samples de hardware real, los medios pasaron de 10-20%
a 43% y dejó de sonar a videojuego. Esto hace lo mismo con TODO lo demás.

QUÉ SE BAJA — VCSL (Versilian Community Sample Library), CC0 1.0 verificado
leyendo su archivo LICENSE. Grabaciones de instrumentos de verdad. No se baja
el repo completo (5.8 GB, no cabe): se piden los archivos uno por uno desde
raw.githubusercontent, solo las familias que sirven.

RESTRICCIÓN QUE NO SE RELAJA: André VENDE la música, así que solo entra
material CC0 / dominio público con licencia verificada. Nada de "royalty free"
ambiguo, nada de packs de vendedor.
"""
import os, sys, json, time, subprocess
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, '_samples', 'vcsl')
RAW = 'https://raw.githubusercontent.com/sgossner/VCSL/master/'
API = 'https://api.github.com/repos/sgossner/VCSL/git/trees/master?recursive=1'

# familia → qué palabras buscar en la ruta, y para qué sirve en la rola
FAMILIAS = {
 'perc-mano':  (('conga','bongo','djembe','darbuka','cajon','frame drum','tambourine',
                 'shaker','cabasa','guiro','clave','woodblock','agogo','cowbell',
                 'castanet','maraca','udu','talking drum','handclap','hand clap'),
                'percusión de mano — el groove orgánico'),
 'melodicos':  (('kalimba','mbira','balafon','marimba','vibraphone','glockenspiel',
                 'xylophone','celesta','crotale'),
                'láminas y maderas — reemplazan el "sintetizador de videojuego"'),
 'cuerdas':    (('harp','guitar','ukulele','mandolin','banjo','dulcimer','zither'),
                'cuerdas pulsadas — texturas y arpegios'),
 'teclas':     (('piano','rhodes','wurlitzer','clavinet','harpsichord','organ'),
                'teclas reales — acordes con cuerpo'),
 'graves':     (('contrabass','double bass','bass guitar','tuba','bassoon'),
                'graves acústicos — alternativa al sub sintetizado'),
 'aire':       (('flute','clarinet','ocarina','recorder','pan pipe','whistle',
                 'melodica','accordion','harmonica'),
                'vientos — capas de aire y melodías'),
 'metal':      (('gong','tam-tam','cymbal','bell','chime','triangle','singing bowl',
                 'anvil','bell tree'),
                'metales — impactos, colas y atmósferas'),
}

def arbol():
    req = urllib.request.Request(API, headers={'User-Agent':'amr-studio'})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    return [(t['path'], t.get('size',0)) for t in d['tree']
            if t['path'].lower().endswith('.wav')]

def clasifica(paths):
    out = {k: [] for k in FAMILIAS}
    for p, sz in paths:
        l = p.lower()
        for fam, (claves, _) in FAMILIAS.items():
            if any(c in l for c in claves):
                out[fam].append((p, sz)); break
    return out

def baja(paths, tope_mb):
    """Descarga hasta agotar el tope. Devuelve (bajados, MB)."""
    n = 0; mb = 0.0
    for p, sz in paths:
        if mb > tope_mb: break
        dst = os.path.join(DEST, p)
        if os.path.exists(dst): continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        url = RAW + urllib.parse.quote(p)
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(dst,'wb') as f:
                data = r.read(); f.write(data)
            n += 1; mb += len(data)/1048576
        except Exception as ex:
            print(f'    ! {p[:60]}: {ex}', flush=True)
    return n, mb

def libre_gb():
    s = os.statvfs(HERE)
    return s.f_bavail * s.f_frsize / (1024**3)

if __name__ == '__main__':
    reserva = 0.6                                   # GB que NO se tocan (para renderizar)
    presupuesto = max(0.0, libre_gb() - reserva)
    print(f'Libre {libre_gb():.2f} GB · reservo {reserva} GB para renderizar '
          f'· presupuesto {presupuesto:.2f} GB\n', flush=True)
    print('Pidiendo el índice de VCSL…', flush=True)
    paths = arbol()
    fam = clasifica(paths)
    print(f'{len(paths)} wavs en el repo · {sum(len(v) for v in fam.values())} útiles\n')
    print(f'{"familia":12s} {"wavs":>5s} {"MB":>7s}  para qué')
    for k,(_, desc) in FAMILIAS.items():
        v = fam[k]
        print(f'  {k:10s} {len(v):5d} {sum(s for _,s in v)/1048576:7.1f}  {desc}')

    # reparto: la percusión y los melódicos primero, que es lo que urge
    ORDEN = ['perc-mano','melodicos','teclas','cuerdas','graves','metal','aire']
    PESO  = {'perc-mano':.30,'melodicos':.24,'teclas':.16,'cuerdas':.12,
             'graves':.08,'metal':.06,'aire':.04}
    print(f'\nBajando…', flush=True)
    tot_n = 0; tot_mb = 0.0
    for k in ORDEN:
        if libre_gb() < reserva + 0.1:
            print(f'  ! disco al límite, paro aquí'); break
        tope = presupuesto * 1024 * PESO[k]
        n, mb = baja(fam[k], tope)
        tot_n += n; tot_mb += mb
        print(f'  {k:10s} {n:4d} archivos · {mb:7.1f} MB', flush=True)
    print(f'\nTOTAL {tot_n} archivos · {tot_mb/1024:.2f} GB · quedan {libre_gb():.2f} GB libres')
    print(f'{DEST}')
