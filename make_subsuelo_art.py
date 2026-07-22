#!/usr/bin/env python3
"""Arte de SUBSUELO — un corte del subsuelo, generado, no dibujado a mano.

POR QUÉ ESTA IMAGEN
  El disco baja ocho niveles: de la banqueta a la roca. Así que la portada no es
  una escena — es un CORTE geológico, como el que hace una excavación cuando
  abre la calle: capas de concreto y tierra apiladas, la varilla expuesta, y
  hasta abajo el basalto, la roca sobre la que se para la ciudad.

  La paleta ES el concepto: óxido sobre concreto. El color del fierro cuando se
  moja, la varilla vista, la luz de sodio de un estacionamiento. Caliente pero
  sucio — nada de neón. Contra el ámbar, el vino, el azul, el jade y el violeta
  del catálogo, este es el disco industrial.

CÓMO ESTÁ HECHO
  Ocho franjas horizontales, una por rola, cada una más oscura que la de arriba
  — como se ve un corte real de suelo, que se va apagando con la profundidad.
  La varilla son líneas verticales que NO son perfectas: se doblan un poco y se
  interrumpen, porque el fierro expuesto está torcido y oxidado, no recién
  puesto. Y sólo BASALTO, el fondo, va encendido en óxido: es el pico del disco
  (por densidad, no por euforia — ver make_subsuelo.py).
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W = 1000

OXIDO = '#B4501F'
CONCRETO = '#2A2724'
CAL = '#D8D2C6'
N = 8                       # ocho niveles


def _lerp(a, b, t):
    def h(c): return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    ca, cb = h(a), h(b)
    return '#%02x%02x%02x' % tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))


def _hex_columns(p, x0, y0, x1, y1, r, rng, base_op=0.12):
    """Rellena un rectángulo con columnas hexagonales de basalto encendidas
    en óxido desde abajo. Es geometría real: la lava al enfriarse se agrieta en
    polígonos de 5-6 lados (la Calzada del Gigante, los órganos de Michoacán)."""
    dx, dy = r * 1.5, r * math.sqrt(3)
    fila = 0; yy = y0 - r
    while yy < y1 + r:
        off = (dx / 2) if fila % 2 else 0.0
        xx = x0 - r
        while xx < x1 + r:
            cx, cy = xx + off, yy
            verts = []
            for a in range(6):
                ang = math.pi / 6 + a * math.pi / 3
                jx = cx + math.cos(ang) * r * (0.9 + 0.12 * rng.random())
                jy = cy + math.sin(ang) * r * (0.9 + 0.12 * rng.random())
                verts.append(f'{jx:.1f},{jy:.1f}')
            t = (cy - y0) / max(1.0, y1 - y0)          # 0 arriba de la roca, 1 al fondo
            op = base_op + 0.6 * t
            p.append(f'<polygon points="{" ".join(verts)}" fill="none" '
                     f'stroke="{OXIDO}" stroke-width="1.1" opacity="{min(0.85,op):.2f}"/>')
            xx += dx
        yy += dy; fila += 1


def svg():
    rng = np.random.default_rng(19)
    corte = W * 0.60                                    # aquí el concreto se vuelve roca
    p = [f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">',
         '<defs><linearGradient id="ssroca" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{OXIDO}" stop-opacity="0.10"/>'
         f'<stop offset="100%" stop-color="{OXIDO}" stop-opacity="0.62"/>'
         '</linearGradient></defs>',
         f'<rect width="{W}" height="{W}" fill="{CAL}"/>']

    # --- arriba: el concreto en estratos que se apagan al bajar ---
    y = 0.0; limites = []
    capas = 6
    for i in range(capas):
        alto = (corte / capas) * (0.82 + 0.30 * i / capas)
        if y + alto > corte: alto = corte - y
        prof = i / (capas - 1)
        base = _lerp('#9A9086', '#3A352F', prof)
        p.append(f'<rect x="0" y="{y:.1f}" width="{W}" height="{alto+1:.1f}" fill="{base}"/>')
        gr = []
        for _ in range(int(50 + 200 * prof)):
            gr.append(f'<circle cx="{rng.uniform(0,W):.0f}" cy="{y+rng.uniform(0,alto):.0f}" '
                      f'r="{rng.uniform(0.6,2.0):.1f}"/>')
        p.append(f'<g fill="#00000026">' + ''.join(gr) + '</g>')
        p.append(f'<line x1="0" y1="{y:.1f}" x2="{W}" y2="{y:.1f}" stroke="{CAL}" '
                 f'stroke-width="1" opacity="0.14"/>')
        limites.append(y); y += alto

    # --- abajo: la roca, columnas de basalto encendidas ---
    p.append(f'<rect x="0" y="{corte:.1f}" width="{W}" height="{W-corte:.1f}" fill="{CONCRETO}"/>')
    p.append(f'<rect x="0" y="{corte:.1f}" width="{W}" height="{W-corte:.1f}" fill="url(#ssroca)"/>')
    _hex_columns(p, 0, corte, W, W, W/16.0, rng)
    # la costura concreto→roca: el filete de óxido más marcado del disco
    p.append(f'<line x1="0" y1="{corte:.1f}" x2="{W}" y2="{corte:.1f}" stroke="{OXIDO}" '
             f'stroke-width="2.6" opacity="0.95"/>')

    # --- la varilla: verticales torcidas, oxidadas, que cruzan el concreto ---
    for k in range(12):
        x0 = W * 0.05 + (W * 0.90) * k / 11 + rng.uniform(-9, 9)
        hasta = rng.uniform(0.55, 1.0) * corte
        seg, yy = [], 0.0
        def cerrar():
            if len(seg) > 1:
                p.append(f'<polyline points="{" ".join(seg)}" fill="none" stroke="{OXIDO}" '
                         f'stroke-width="{rng.uniform(1.6,3.0):.1f}" opacity="{rng.uniform(0.35,0.62):.2f}"/>')
        while yy < hasta:
            if rng.random() > 0.14:
                xx = x0 + math.sin(yy * 0.012 + k) * 7.0
                seg.append(f'{xx:.1f},{yy:.1f}')
            else:
                cerrar(); seg = []
            yy += rng.uniform(22, 62)
        cerrar()

    p.append(f'</svg>')
    return ''.join(p)


def svg_basalto(w=240):
    """BASALTO — la roca del fondo, en columnas.

    El basalto de verdad se enfría en COLUMNAS hexagonales (la Calzada del
    Gigante, los órganos de Michoacán). Es geometría real, no invento: la lava
    al enfriarse se agrieta en polígonos de 5-6 lados. Aquí eso da un mosaico de
    celdas apretadas, encendidas en óxido desde abajo — el fondo del disco."""
    rng = np.random.default_rng(23)
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         '<defs><linearGradient id="bsluz" x1="0" y1="1" x2="0" y2="0">'
         f'<stop offset="0%" stop-color="{OXIDO}" stop-opacity="0.9"/>'
         f'<stop offset="45%" stop-color="{OXIDO}" stop-opacity="0.28"/>'
         f'<stop offset="100%" stop-color="{CONCRETO}" stop-opacity="0"/>'
         '</linearGradient></defs>',
         f'<rect width="{w}" height="{w}" fill="{CONCRETO}"/>',
         f'<rect width="{w}" height="{w}" fill="url(#bsluz)"/>']
    # rejilla hexagonal apretada de columnas
    r = w / 13.0
    dx, dy = r * 1.5, r * math.sqrt(3)
    fila = 0
    yy = -r
    while yy < w + r:
        off = (dx / 2) if fila % 2 else 0.0
        xx = -r
        while xx < w + r:
            cx, cy = xx + off, yy
            verts = []
            for a in range(6):
                ang = math.pi / 6 + a * math.pi / 3
                jx = cx + math.cos(ang) * r * (0.92 + 0.1 * rng.random())
                jy = cy + math.sin(ang) * r * (0.92 + 0.1 * rng.random())
                verts.append(f'{jx:.1f},{jy:.1f}')
            op = 0.10 + 0.55 * (cy / w)               # más encendidas abajo
            p.append(f'<polygon points="{" ".join(verts)}" fill="none" '
                     f'stroke="{OXIDO}" stroke-width="1" opacity="{op:.2f}"/>')
            xx += dx
        yy += dy
        fila += 1
    p.append('</svg>')
    return ''.join(p)


def svg_ducto(w=240):
    """DUCTO — el tiro de aire vertical, visto desde el fondo mirando arriba.

    Un tiro de ventilación se ve como anillos de concreto que se encogen hacia
    un punto de luz allá arriba — la perspectiva de estar hasta abajo mirando la
    salida. El delay de la rola es eso hecho sonido: todo rebota y vuelve tarde,
    encogiéndose. Anillos concéntricos que se cierran hacia un centro claro."""
    rng = np.random.default_rng(29)
    cx = cy = w / 2
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         '<defs><radialGradient id="dcluz" cx="50%" cy="50%" r="50%">'
         f'<stop offset="0%" stop-color="{CAL}" stop-opacity="0.85"/>'
         f'<stop offset="30%" stop-color="{OXIDO}" stop-opacity="0.35"/>'
         f'<stop offset="100%" stop-color="{CONCRETO}" stop-opacity="0"/>'
         '</radialGradient></defs>',
         f'<rect width="{w}" height="{w}" fill="{CONCRETO}"/>']
    # el punto de luz al fondo del tiro
    p.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{w*0.5:.0f}" fill="url(#dcluz)"/>')
    # anillos de concreto que se encogen: cada uno un poco descentrado (el tiro
    # no es perfecto) y con la costura del molde marcada
    for i in range(16):
        r = w * 0.5 * (1.0 - i / 16.0) ** 1.25
        ox = math.sin(i * 0.7) * (2.5 + i * 0.15)
        oy = math.cos(i * 0.9) * (2.5 + i * 0.15)
        op = 0.10 + 0.5 * (i / 16.0)
        p.append(f'<circle cx="{cx+ox:.1f}" cy="{cy+oy:.1f}" r="{r:.1f}" fill="none" '
                 f'stroke="{OXIDO if i%3 else CAL}" stroke-width="{1.4:.1f}" opacity="{op:.2f}"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for nombre, gen in [('subsuelo', svg),
                        ('subsuelo-basalto', svg_basalto),
                        ('subsuelo-ducto', svg_ducto)]:
        dst = os.path.join(HERE, 'art', f'{nombre}.svg')
        t = gen()
        with open(dst, 'w') as f:
            f.write(t)
        print(f'{nombre:22s} {len(t)//1024:4d} KB')
