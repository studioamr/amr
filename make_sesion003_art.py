#!/usr/bin/env python3
"""Arte de SESIÓN 003 — el arco del set, dibujado con sus datos reales.

Los otros discos del catálogo dibujan una imagen (un hongo, una bocina, una
bola de espejos). Este no es un disco: es un SET, y lo que lo define no es una
imagen sino su forma — la montaña de energía de tres horas. Así que el dibujo
es literalmente esa curva, leída de biblioteca.json y del plan curado.

No es una decoración con forma de gráfica: son los números del set. Los dos
picos que se ven son los dos picos que se oyen, en el minuto en que ocurren.

Estilo de la casa: trazo grueso negro sobre hueso, glow del acento, línea de
piso y dos puntitos.
"""
import os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TINTA = '#141210'
ACC = '#7A5CA8'          # violeta profundo: el color de las 3 h
ACC_L = '#B49BE0'


def svg(w=240):
    # el arco objetivo, el mismo que rige make_sesion003.py
    ARCO = [(0.00, 4.2), (0.12, 4.8), (0.24, 5.4), (0.36, 6.0), (0.46, 7.0),
            (0.55, 5.3), (0.64, 6.2), (0.76, 7.3), (0.87, 5.6), (1.00, 4.1)]

    X0, X1 = 26, 214            # márgenes del dibujo
    YB, YT = 176, 52            # piso y techo de la curva

    def px(t):
        return X0 + (X1 - X0) * t

    def py(e):
        return YB - (YB - YT) * (e - 3.6) / (7.6 - 3.6)

    # curva suave: se interpola el arco con muchos puntos
    ts = np.linspace(0, 1, 220)
    es = np.interp(ts, [a for a, _ in ARCO], [b for _, b in ARCO])
    pts = [(px(t), py(e)) for t, e in zip(ts, es)]

    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<defs><radialGradient id="sg" cx="50%" cy="46%" r="58%">'
         f'<stop offset="0%" stop-color="{ACC_L}" stop-opacity="0.40"/>'
         f'<stop offset="55%" stop-color="{ACC_L}" stop-opacity="0.13"/>'
         f'<stop offset="100%" stop-color="{ACC_L}" stop-opacity="0"/>'
         f'</radialGradient>'
         f'<linearGradient id="sf" x1="0%" y1="0%" x2="0%" y2="100%">'
         f'<stop offset="0%" stop-color="{ACC}" stop-opacity="0.30"/>'
         f'<stop offset="100%" stop-color="{ACC}" stop-opacity="0.03"/>'
         f'</linearGradient></defs>',
         f'<ellipse cx="120" cy="206" rx="76" ry="8" fill="{TINTA}" opacity="0.05"/>',
         f'<circle cx="120" cy="112" r="76" fill="url(#sg)"/>']

    # el relleno bajo la curva
    d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    p.append(f'<path d="{d} L{X1},{YB} L{X0},{YB} Z" fill="url(#sf)"/>')

    # las marcas de hora, verticales tenues (0 · 1 h · 2 h · 3 h)
    for k in range(4):
        x = px(k / 3.0)
        p.append(f'<line x1="{x:.1f}" y1="{YT-8}" x2="{x:.1f}" y2="{YB}" '
                 f'stroke="{TINTA}" stroke-width="1" opacity="0.10"/>')

    # LA CURVA, bold — es el objeto del dibujo
    p.append(f'<path d="{d}" fill="none" stroke="{TINTA}" stroke-width="5.5" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')

    # LOS DOS PICOS, marcados: son el diseño del set
    for t, e in ((0.46, 7.0), (0.76, 7.3)):
        x, y = px(t), py(e)
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{ACC_L}" '
                 f'opacity="0.30"/>')
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.4" fill="{ACC_L}"/>')
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="{TINTA}"/>')

    # el valle entre los dos picos — la decisión que hace que el 2º golpee
    xv, yv = px(0.55), py(5.3)
    p.append(f'<circle cx="{xv:.1f}" cy="{yv:.1f}" r="4" fill="none" '
             f'stroke="{ACC}" stroke-width="2.2" opacity="0.75"/>')

    # la línea de piso = el eje del tiempo
    p.append(f'<rect x="{X0-4}" y="{YB}" width="{X1-X0+8}" height="5" rx="2.5" '
             f'fill="{ACC}"/>')

    # dos puntitos de acento, como todo el catálogo
    p.append(f'<circle cx="38" cy="66" r="2.4" fill="{TINTA}"/>')
    p.append(f'<circle cx="204" cy="196" r="2.2" fill="{TINTA}"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    t = svg()
    with open(os.path.join(HERE, 'art', 'sesion003.svg'), 'w') as f:
        f.write(t)
    print(f'sesion003.svg · {len(t)} B')
