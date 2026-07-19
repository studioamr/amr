#!/usr/bin/env python3
"""TALLER — construir una canción por etapas, eligiendo entre opciones.

André: "construye toda la lógica para crear una canción de 0-100, para que me des
opciones y vayamos creando juntos y poder terminar la canción."

CÓMO FUNCIONA
  El track se arma en 6 etapas. En cada una se rinden 4 variantes de 8 compases,
  y cada variante suena CON TODO LO YA ELEGIDO debajo — no aislada, porque una
  parte suena distinta sola que en contexto. André escucha, elige, y esa decisión
  queda fija en cancion.json. La siguiente etapa se construye encima.

  Al final, render() arma los 208 compases con todas las decisiones.

POR QUÉ ASÍ
  Del research de Keinemusik: Mathame dijo que la idea salió en 2-3 horas y el
  arreglo y la mezcla tomaron DOS MESES. Rampa hace ~20 versiones antes de volver
  a la primera. Ese es el método real, y sólo funciona si iterar es barato.
  Rendir una rola completa cuesta 90 min; rendir 8 compases cuesta segundos.

REGLAS DEL GÉNERO YA HORNEADAS (medidas, ver memoria afro-house-arreglo)
  · 120 BPM exactos — los tres tracks medibles de Keinemusik están ahí
  · 208 compases = 6:56, casi idéntico a "The Rapture Pt.III"
  · todo cambio de sección en múltiplo de 16
  · ENTRAR ≠ SONAR COMPLETO: cada elemento entra filtrado y se abre en 16-32 comp
  · sin drop grande: rampa lenta con un solo hundimiento
  · el breakdown nunca se vacía — la percusión sigue corriendo
  · máximo 3-4 capas de percusión
  · groove AFRO (elegido por André): swing 57.5%, empuja 12 ms adelante

USO
  python3 taller.py                 → dónde vamos y qué falta
  python3 taller.py bajo            → rinde las 4 opciones de bajo + abre la página
  python3 taller.py bajo pedal      → fija esa opción
  python3 taller.py render          → arma la canción completa con lo elegido
"""
import os, sys, json, glob, subprocess
import numpy as np
import imageio_ffmpeg
from dream_core import SR, wav_write, sat, widen, sub_mono, lp, hp, bp
import kit as K
import af_voices as A
import instrumentos as I
from af_voices import midi_f, deg, MIN
from groove import Groove

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_taller'); os.makedirs(OUT, exist_ok=True)
ESTADO = os.path.join(HERE, 'cancion.json')

BPM = 120.0                       # el tempo exacto de Keinemusik
SPB = int(round(SR * 240.0 / BPM))
S16 = SPB / 16.0
ROOT = 57                         # La (A3) — La menor, la tonalidad más común del sello
FEEL = 'afro'                     # elegido por André

# ══════════════════════════════════════════════════════ LAS OPCIONES
ETAPAS = ['percusion', 'bajo', 'acordes', 'gancho', 'melodia', 'voz']

OPCIONES = {
 'percusion': {
   'base':    'Kick, clap, hats y shaker. Lo esencial, tres capas.',
   'conga':   'Le entra conga y un tom grave marcando el balanceo.',
   'denso':   'Cuatro capas con cabasa y rim — el más ocupado.',
   'seco':    'Sin hats abiertos, todo corto y cerrado. El más hipnótico.'},
 'bajo': {
   'pedal':   'UNA nota sostenida todo el compás. Contención pura, deja aire.',
   'rodante': '16avos rodando con hueco entre notas. El que empuja.',
   'sincopa': 'Sincopado, cae fuera del pulso. El más funky.',
   'sigue':   'Sigue la raíz de cada acorde. El más melódico.'},
 'acordes': {
   'clasico': 'i-VI-III-VII — la progresión del sello (Am-F-C-G).',
   'oscuro':  'i-VII-VI-VII — no resuelve, se queda tenso.',
   'suspenso':'i-iv-VII-III — más movimiento armónico.',
   'drone':   'Dos acordes nada más, 4 compases cada uno. Lo más hipnótico.'},
 'gancho': {
   # ⛔ Se acabaron los sintetizadores. Todo esto son GRABACIONES de instrumentos
   #    reales (VCSL, CC0). André: "cuando te digo videojuego justo a eso me
   #    refiero, esos que tú haces — elimínalos por completo".
   'kalimba':  'Kalimba de Tanzania. Metálica, seca, muy africana.',
   'mbira':    'Mbira de Kenia. Prima de la kalimba, más grave y con más cuerpo.',
   'balafon':  'Balafón — xilófono africano de calabazas. Madera con zumbido.',
   'marimba':  'Marimba. Madera cálida y redonda, el clásico del afro house.',
   'vibrafono':'Vibráfono. Metal con sostén largo, jazzero y flotante.',
   'piano':    'Piano de verdad, grabado. Cuerda percutida.',
   'arpa':     'Arpa. Pulsada, cristalina, el más suave de todos.',
   'campana':  'Campanas y crotales. Puntual, brillante, ceremonial.'},
 'melodia': {
   'llamada': 'Sube y se queda en el aire. Deja la pregunta abierta.',
   'caida':   'Baja y aterriza en la tónica. La más resuelta.',
   'arco':    'Sube y regresa por donde vino. La más redonda.',
   'insiste': 'Machaca una nota y rompe hacia arriba. La más terca.',
   'hueco':   'Casi puro silencio, tres notas. La contención de Keinemusik.',
   'salto':   'Brinca la octava. La más brillante y cantable.',
   'ronda':   'Escalonada, da vueltas sin parar. La más hipnótica.',
   'grito':   'Una sola nota alta y larga que se sostiene.'},
 # ⛔ REGLA DURA DE ANDRÉ (jul 2026): "en voz todas se escuchan horribles,
 # me quedo con ninguna, y asegúrate que nunca vayas a meter algo así en
 # próximas rolas". Las voces del acervo folk de la Library of Congress quedan
 # PROHIBIDAS — no importa cuánto se procesen, el original se sigue oyendo.
 # La única voz aceptable a futuro es la que grabe él mismo.
 'voz': {
   'ninguna': 'Sin voz. Que la percusión y el gancho carguen todo.',
   'propia':  'La voz de André (pendiente: falta que la grabe).'},
}

# ══════════════════════════════════════════════════════ EL GANCHO
# Melodías COMPUESTAS a mano, no generadas. Un gancho tiene FORMA — sube, se
# detiene, cae, deja hueco — y esa forma es lo que se te queda pegado. Antes
# esto tocaba notas del acorde en las posiciones 0, 6 y 10 de cada compás:
# eso es acompañamiento, no melodía.
#   (compás, paso de 16avo, largo en 16avos, grado de la escala)
#   grados en La menor: 0=La 1=Si 2=Do 3=Re 4=Mi 5=Fa 6=Sol  (7+ = octava arriba)
MELODIAS = {
 'llamada': [(0,0,4,0), (0,6,3,2), (0,10,6,4),
             (1,4,8,3)],                                    # sube y deja la pregunta
 'caida':   [(0,0,6,4), (0,8,4,3), (0,12,4,2),
             (1,0,12,0)],                                   # baja y aterriza
 'arco':    [(0,2,3,0), (0,6,3,2), (0,10,5,4),
             (1,2,4,2), (1,8,8,0)],                         # sube y regresa
 'insiste': [(0,0,2,0), (0,4,2,0), (0,8,2,0), (0,12,4,2),
             (1,0,3,0), (1,6,10,4)],                        # machaca y rompe
 'hueco':   [(0,6,8,4),
             (1,2,6,2), (1,12,4,0)],                        # casi puro silencio
 'salto':   [(0,0,3,0), (0,4,3,7), (0,10,5,4),
             (1,0,4,2), (1,6,3,7), (1,12,4,0)],             # octava, el más brillante
 'ronda':   [(0,0,4,2), (0,6,4,3), (0,12,4,4),
             (1,0,4,3), (1,6,4,2), (1,12,4,0)],             # escalonada, hipnótica
 'grito':   [(0,4,10,7),
             (1,0,4,6), (1,8,8,4)],                         # una nota alta larga
}

PROG = {'clasico': [0,5,2,6], 'oscuro': [0,6,5,6],
        'suspenso': [0,3,6,2], 'drone': [0,0,5,5]}

def carga():
    if os.path.exists(ESTADO): return json.load(open(ESTADO))
    return {'titulo': None, 'bpm': int(BPM), 'tono': 'A MIN', 'feel': FEEL, 'elegido': {}}

def guarda(d): json.dump(d, open(ESTADO,'w'), indent=1, ensure_ascii=False)

def acorde(dec, ci):
    p = PROG[dec['elegido'].get('acordes','clasico')]
    g = p[ci % 4]
    return dict(bajo=ROOT + MIN[g%7] - 24,
                tri=[deg(ROOT,g,0,MIN), deg(ROOT,g+2,0,MIN), deg(ROOT,g+4,0,MIN)])

# ══════════════════════════════════════════════════════ VOZ
_VOCES = None
def voces_loc():
    """Chops vocales de la Library of Congress, ya procesados."""
    global _VOCES
    if _VOCES is not None: return _VOCES
    import demo_voz as DV
    fs = sorted(glob.glob(os.path.join(HERE,'_samples','musicbox','one_shots','*.mp3')))
    cand = []
    for f in fs[::11]:
        x = DV.dec(f)
        if len(x) > 2000: cand.append((DV.vocalidad(x), x))
    cand.sort(reverse=True, key=lambda c: c[0])
    _VOCES = [x for _, x in cand[:6]]
    return _VOCES

VOZ_PROHIBIDA = ('chops', 'gate', 'aire')   # las del acervo folk — ver regla arriba

def voz_render(modo, i, dur_s):
    if modo in VOZ_PROHIBIDA:
        raise ValueError(
            f'VOZ BLOQUEADA: "{modo}".\n'
            f'André las rechazó explícitamente y pidió no volver a usarlas. '
            f'La única voz permitida es la que grabe él. Ver VOZ_PROHIBIDA en taller.py.')
    import demo_voz as DV
    vs = voces_loc()
    if not vs: return np.zeros(int(dur_s*SR), np.float32)
    x = vs[i % len(vs)]
    if modo == 'gate':  return DV.procesa(x, semis=-3, largo_s=dur_s, gate_hz=11.0)
    if modo == 'aire':  return DV.procesa(x, semis=-9, largo_s=dur_s*2.2, gate_hz=0)[:int(dur_s*SR)]
    return DV.procesa(x, semis=-5, largo_s=dur_s, gate_hz=0)

# ══════════════════════════════════════════════════════ EL RENDER
def bloque(dec, bars=8, seed=7, abre=1.0):
    """Rinde `bars` compases con TODO lo elegido. `abre` 0..1 = qué tan abiertos
    van los filtros (la regla de 'entrar no es sonar completo')."""
    e = dec['elegido']
    n = bars*SPB + SPB
    B = {k: np.zeros(n, np.float32) for k in
         ('kick','perc','bajo','gancho','vox','pad')}
    rng = np.random.default_rng(seed)
    g = Groove(dec.get('feel',FEEL), S16, SR, bpm=BPM, seed=seed)
    kpos = []

    def add(b, pos, x, gain=1.0):
        pos = int(pos)
        if pos < 0: x = x[-pos:]; pos = 0
        q = min(len(b), pos+len(x))
        if q > pos: b[pos:q] += x[:q-pos]*gain

    perc = e.get('percusion','base')
    for bar in range(bars):
        base = bar*SPB
        c = acorde(dec, bar//2)
        # ---- VIDA DENTRO DE LA SECCIÓN (medido: los compases se parecían 0.98
        #      entre sí, o sea el mismo loop pegado 4 veces). Tres mecanismos:
        prog = bar / max(1, bars-1)          # avance dentro de la sección
        fill = (bar % 8 == 7)                # último compás de cada frase
        respira = (bars > 8 and bar >= bars-2)   # los 2 últimos: se abre hueco
        dens = 0.82 + 0.18*prog              # la densidad crece

        # ---- KICK, siempre recto: es el ancla
        for beat in range(4):
            p = base + beat*4*S16
            add(B['kick'], p, K.vary(K.smp(K.KICK), rng, 0.010, 0.06), 0.95)
            kpos.append(int(p))
        # ---- CLAP
        for s in (4,12):
            add(B['perc'], g.pos(base,s,bar)-0.010*SR,
                K.vary(K.smp(K.CLAP), rng, 0.02, 0.12), 0.40*g.vel(s,bar))
        # ---- HATS
        for s in range(16):
            op = (s%4==2) and perc!='seco'
            sm = K.smp(K.HATO) if op else K.smp(K.HATC)
            if respira and s % 4 != 0: continue      # el hueco antes del cambio
            add(B['perc'], g.pos(base,s,bar), K.vary(sm, rng, 0.03, 0.26),
                g.vel(s,bar)*(0.30 if s%2 else 0.20)*(0.7 if op else 1.0)*dens)
        # ---- SHAKER
        for s in range(2,16,4):
            add(B['perc'], g.pos(base,s,bar), K.vary(K.smp(K.SHAKER), rng, 0.04, 0.28),
                0.26*g.vel(s,bar))
        # ---- capas extra según la opción
        if perc in ('conga','denso'):
            if bar%2==1: add(B['perc'], g.pos(base,10,bar), K.vary(K.smp(K.CONGA_L), rng,0.03,0.2), 0.40)
            if bar%4==2: add(B['perc'], g.pos(base,6,bar),  K.vary(K.smp(K.CONGA_L), rng,0.03,0.2), 0.30)
        if perc=='denso':
            for s in range(3,16,8):
                add(B['perc'], g.pos(base,s,bar), K.vary(K.smp(K.CABASA), rng,0.04,0.3), 0.22)
            if bar%2==0: add(B['perc'], g.pos(base,14,bar), K.vary(K.smp(K.RIM), rng,0.03,0.2), 0.30)
        # ---- FILL al cerrar cada frase de 8 compases
        if fill:
            for k, st16 in enumerate((10, 12, 13, 14, 15)):
                sm = K.smp(K.CONGA_L if k % 2 else K.RIM)
                add(B['perc'], g.pos(base, st16, bar), K.vary(sm, rng, 0.05, 0.2),
                    0.34 + 0.10*k)
            add(B['perc'], base + 15.5*S16, K.vary(K.smp(K.CRASH), rng), 0.20)
        # ---- fantasmas: lo que suena a manos
        for s in range(16):
            if g.ghost(s,bar,rng):
                add(B['perc'], g.pos(base,s,bar), K.vary(K.smp(K.HATC), rng,0.05,0.4),
                    g.ghost_vel(s,bar))

        # ---- BAJO
        modo = e.get('bajo','pedal'); f0 = midi_f(c['bajo'])
        if modo=='pedal':
            add(B['bajo'], base, A.sub(f0, SPB/SR*0.96, rng), 0.9)
        elif modo=='rodante':
            for s in range(16):
                if s%4==3: continue
                add(B['bajo'], base+s*S16, A.sub(f0, (S16/SR)*0.72, rng), 1.0)
        elif modo=='sincopa':
            for s in (0,3,6,10,14):
                add(B['bajo'], base+s*S16, A.sub(f0, (S16/SR)*1.6, rng), 1.0)
        else:                                        # sigue
            for s in (0,8):
                add(B['bajo'], base+s*S16, A.sub(f0, (8*S16/SR)*0.9, rng), 1.0)

        # ---- GANCHO: toca la MELODÍA compuesta, con el timbre elegido.
        #      La frase dura 2 compases y se repite — así se vuelve el gancho.
        gm = e.get('gancho','marimba')
        mel = MELODIAS[e.get('melodia','arco')]
        if bar%2==0:      # colchón armónico, tocado por el MISMO instrumento real
            add(B['pad'], base, I.acorde(gm, [m+12 for m in c['tri']], 2*SPB/SR*0.9, rng), 0.42)
        for (mb, st16, ln, grado) in mel:
            if bar % 2 != mb: continue
            nt = ROOT + 12 + MIN[grado % 7] + 12*(grado // 7)
            dur = ln * S16 / SR
            # GRABACIÓN de instrumento real. Sin sierras, sin FM, sin supersaw.
            v = I.nota(gm, nt, dur, rng)
            add(B['gancho'], g.pos(base, st16, bar), v, 0.9)
        # ---- PAD de fondo, siempre (es el colchón)
        pass   # el colchón ya lo pone el instrumento real, arriba

        # ---- VOZ
        vm = e.get('voz','ninguna')
        if vm!='ninguna':
            add(B['vox'], g.pos(base,0,bar), voz_render(vm, bar, 0.55), 0.9)
            if bar%2==1:
                add(B['vox'], g.pos(base,10,bar), voz_render(vm, bar+1, 0.4), 0.5)

    # ---- sidechain graduado
    def sc(depth, rel):
        env = np.ones(n, np.float32); m = int(rel*4*SR)
        dip = 1.0 - depth*np.exp(-np.arange(m)/(rel*SR)).astype(np.float32)
        for p in kpos:
            q = min(n, p+m)
            if q>p: env[p:q] = np.minimum(env[p:q], dip[:q-p])
        return env
    B['bajo'] *= sc(0.85, 0.105)
    musz = sc(0.32, 0.13); pads = sc(0.20, 0.18)

    # ---- ENTRAR ≠ SONAR COMPLETO: filtro que abre según `abre`
    def filtra(x, cut_min, cut_max):
        # se abre por segmentos a lo largo de la sección: entrar no es sonar
        # completo, y tampoco es abrirse de golpe al primer compás
        if abre >= 0.99 and bars <= 8: return x
        seg = max(1, len(x)//8); out = np.zeros(len(x), np.float32)
        for k in range(8):
            a0, b0 = k*seg, (len(x) if k==7 else (k+1)*seg)
            if a0 >= len(x): break
            loc = abre * (0.80 + 0.20*(k/7))
            out[a0:b0] = lp(x[a0:b0], float(cut_min + (cut_max-cut_min)*min(loc,1.0)), 2)
        return out

    perc_st = widen(hp(B['perc'], 120.0, 2), amount=0.42, seed=seed+3)   # HP 120 (regla del género)
    gan_st  = widen(filtra(B['gancho'], 700, 6000)*musz, amount=0.55, seed=seed+5)
    vox_st  = widen(filtra(B['vox'], 500, 5000)*musz, amount=0.7, seed=seed+7)
    pad_st  = widen(filtra(B['pad'], 500, 3000)*pads, amount=0.62, seed=seed+9)

    mus = perc_st*0.80 + gan_st*0.72 + vox_st*0.85 + pad_st*0.95
    mm = 0.5*(mus[0]+mus[1]); ss = bp(0.5*(mus[0]-mus[1]), 220, 12000, 2)*2.0
    mix = np.stack([mm+ss, mm-ss])
    mix += B['kick'][None,:]*0.92 + B['bajo'][None,:]*0.95
    mix = np.stack([m - bp(m, 250.0, 400.0, 2)*0.29 for m in mix])       # corte de lodo
    mix = np.stack([sat(mix[0],1.05,0.02), sat(mix[1],1.05,0.02)])
    mix = sub_mono(mix, 120.0)
    pk = float(np.abs(mix).max())
    if pk > 1.1: mix *= 1.1/pk
    return mix[:, :bars*SPB]

def enc(x, path):
    x = x*(0.86/max(1e-9, float(np.abs(x).max())))
    w = path.replace('.m4a','.wav'); wav_write(w, x)
    subprocess.run([FF,'-y','-v','error','-i',w,'-c:a','aac_at','-b:a','192k',
                    '-movflags','+faststart',path], check=True)
    os.remove(w)

# ══════════════════════════════════════════════════════ ETAPAS
def rinde_etapa(etapa):
    dec = carga()
    if etapa not in OPCIONES:
        print(f'Etapa desconocida: {etapa}. Son: {", ".join(ETAPAS)}'); return
    print(f'Rindiendo 4 opciones de {etapa.upper()} sobre lo ya elegido…', flush=True)
    hechos = []
    for i,(k,desc) in enumerate(OPCIONES[etapa].items()):
        d2 = json.loads(json.dumps(dec)); d2['elegido'][etapa] = k
        print(f'  … {k}', flush=True)
        enc(bloque(d2, bars=8, seed=11+i*4), os.path.join(OUT, f'{etapa}-{k}.m4a'))
        hechos.append((k, desc))
    pagina(etapa, hechos, dec)
    print(f'\n  http://localhost:4274/_taller/{etapa}.html')

def pagina(etapa, hechos, dec):
    ya = dec['elegido']
    contexto = ' · '.join(f'{k}: <b>{v}</b>' for k,v in ya.items()) or 'nada todavía — esta es la base'
    filas = '\n'.join(
      f'<button onclick="toca({i})"><span class=num>{i+1}</span>'
      f'<span><b>{k}</b><i>{d}</i></span></button>' for i,(k,d) in enumerate(hechos))
    orden = '\n'.join(f'<code>python3 taller.py {etapa} {k}</code>' for k,_ in hechos)
    html = f"""<!doctype html><meta charset=utf-8><title>Taller — {etapa}</title>
<style>
 :root{{--bone:#EDE9E1;--ink:#141210;--violet:#6E5BAE;--dim:#6E675E}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bone);color:var(--ink);
 font:15px/1.55 -apple-system,sans-serif;display:grid;place-items:center;min-height:100vh;padding:32px}}
 .wrap{{width:min(660px,100%)}}
 .kick{{font:600 11px/1 ui-monospace,Menlo,monospace;letter-spacing:3px;color:var(--dim);text-transform:uppercase}}
 h1{{font:400 38px/1.08 Georgia,serif;margin:12px 0 6px;text-transform:capitalize}}
 .sub{{color:var(--dim);margin:0 0 8px}} .ctx{{color:var(--dim);font-size:12.5px;margin:0 0 24px}}
 .grid{{display:grid;gap:10px;margin-bottom:18px}}
 button{{appearance:none;border:1px solid rgba(20,18,16,.22);background:transparent;color:var(--ink);
 border-radius:10px;padding:16px 15px;cursor:pointer;text-align:left;font:inherit;transition:.14s;
 display:grid;grid-template-columns:26px 1fr;gap:13px;width:100%}}
 button:hover{{border-color:var(--violet)}} button.on{{background:var(--violet);border-color:var(--violet);color:#fff}}
 .num{{font:600 12px/1.5 ui-monospace,Menlo,monospace;opacity:.6}}
 button b{{display:block;font:600 13px/1 ui-monospace,Menlo,monospace;letter-spacing:2px;text-transform:uppercase;margin-bottom:5px}}
 button i{{font-style:normal;font-size:12.5px;opacity:.74;line-height:1.45;display:block}}
 .bar{{display:flex;gap:14px;align-items:center;border-top:1px solid rgba(20,18,16,.14);padding-top:16px;
 font:12px ui-monospace,Menlo,monospace;color:var(--dim)}}
 .note{{margin-top:22px;font-size:12.5px;color:var(--dim);border-left:2px solid var(--violet);
 padding-left:14px;line-height:1.7}} code{{display:block;font-size:11.5px;color:var(--ink);opacity:.75}}
</style><div class=wrap>
<div class=kick>Studio AMR · taller · 120 BPM · La menor · groove afro</div>
<h1>{etapa}</h1>
<p class=sub>{len(hechos)} opciones, cada una sonando con todo lo ya elegido debajo.</p>
<p class=ctx>Hasta ahora: {contexto}</p>
<div class=grid>{filas}</div>
<div class=bar><button id=stop style="display:inline-block;width:auto;padding:9px 18px">■ Parar</button>
<label><input type=checkbox id=loop checked> bucle</label><span id=now>—</span></div>
<p class=note>Cuando decidas, corre el comando de la que elegiste y esa queda fija:
{orden}</p>
</div>
<audio id=a preload=none></audio>
<script>
var K={json.dumps([k for k,_ in hechos])}, E='{etapa}';
var a=document.getElementById('a'), cur=-1, bs=document.querySelectorAll('.grid button');
function pinta(){{ bs.forEach(function(b,i){{b.classList.toggle('on', i===cur&&!a.paused);}});
 document.getElementById('now').textContent=(cur<0||a.paused)?'—':K[cur].toUpperCase()+' · en bucle'; }}
function toca(i){{ if(i===cur&&!a.paused){{a.pause();pinta();return;}}
 cur=i; a.loop=document.getElementById('loop').checked; a.src=E+'-'+K[i]+'.m4a';
 a.play().catch(function(){{}}); pinta(); }}
document.getElementById('loop').onchange=function(){{a.loop=this.checked;}};
a.addEventListener('play',pinta); a.addEventListener('pause',pinta); a.addEventListener('ended',pinta);
document.getElementById('stop').onclick=function(){{a.pause();pinta();}};
document.addEventListener('keydown',function(e){{ if(e.key>='1'&&e.key<='9'&&+e.key<=K.length)toca(+e.key-1);
 if(e.key===' '){{e.preventDefault(); a.paused?a.play():a.pause();}} }});
</script>"""
    open(os.path.join(OUT, f'{etapa}.html'),'w').write(html)

def fija(etapa, opcion):
    dec = carga()
    if opcion not in OPCIONES.get(etapa,{}):
        print(f'"{opcion}" no es opción de {etapa}. Son: {", ".join(OPCIONES[etapa])}'); return
    dec['elegido'][etapa] = opcion; guarda(dec)
    print(f'✓ {etapa} = {opcion}')
    falta = [x for x in ETAPAS if x not in dec['elegido']]
    print(f'  siguiente: python3 taller.py {falta[0]}' if falta
          else '  ¡completo! → python3 taller.py render')

def estado():
    dec = carga()
    print(f'CANCIÓN · {dec["bpm"]} BPM · {dec["tono"]} · groove {dec["feel"]}\n')
    for et in ETAPAS:
        v = dec['elegido'].get(et)
        print(f'  {"✓" if v else "·"} {et:11s} {v or "— sin elegir"}')
    falta = [x for x in ETAPAS if x not in dec['elegido']]
    print(f'\n→ python3 taller.py {falta[0]}' if falta else '\n→ python3 taller.py render')

if __name__ == '__main__':
    if len(sys.argv) == 1: estado()
    elif sys.argv[1] == 'render':
        import taller_render; taller_render.main(carga())
    elif len(sys.argv) == 2: rinde_etapa(sys.argv[1])
    else: fija(sys.argv[1], sys.argv[2])
