#!/usr/bin/env python3
"""Arte de los dos cortes de PURPURINA — cada rola con su propio dibujo.

No se reusa el ícono del disco: cada corte es una rola distinta y merece su
imagen. Los dos son los extremos del disco, y los dibujos lo dicen:

  VESTIDOR — el espejo de camerino con sus focos alrededor. Estás sola frente
             al espejo antes de salir. Un foco está apagado: el detalle que
             hace que sea un camerino de verdad y no un ícono de camerino.
  SALÓN    — el piso de baile ajedrezado en perspectiva, con el haz de luz
             cayendo encima. Nadie dibujado: la pista es el personaje.

Estilo de la casa (micelio-hongo, eco-bocina, purpurina-bola): UN objeto en
trazo grueso negro sobre hueso, glow del color del disco, sombra de piso,
detalles finos en el acento y dos puntitos.
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TINTA = '#141210'
ORO = '#B98A2E'
ORO_L = '#F2D479'


def cab(w, gx, gy, gr):
    """Cabecera común: defs del glow y la sombra de piso."""
    return [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
            f'<defs><radialGradient id="g" cx="50%" cy="45%" r="55%">'
            f'<stop offset="0%" stop-color="{ORO_L}" stop-opacity="0.44"/>'
            f'<stop offset="55%" stop-color="{ORO_L}" stop-opacity="0.15"/>'
            f'<stop offset="100%" stop-color="{ORO_L}" stop-opacity="0"/>'
            f'</radialGradient></defs>',
            f'<ellipse cx="120" cy="208" rx="72" ry="8" fill="{TINTA}" opacity="0.05"/>',
            f'<circle cx="{gx}" cy="{gy}" r="{gr}" fill="url(#g)"/>']


def svg_vestidor(w=240):
    """El espejo de camerino: marco bold, focos alrededor, uno fundido."""
    p = cab(w, 120, 104, 70)
    X0, Y0, X1, Y1 = 62, 46, 178, 168      # el marco exterior

    # el marco, bold
    p.append(f'<rect x="{X0}" y="{Y0}" width="{X1-X0}" height="{Y1-Y0}" rx="8" '
             f'fill="{TINTA}"/>')
    # el cristal, hueco (se ve el hueso de la tarjeta = el espejo vacío)
    p.append(f'<rect x="{X0+20}" y="{Y0+20}" width="{X1-X0-40}" '
             f'height="{Y1-Y0-40}" rx="3" fill="#EAE6DF"/>')
    # el reflejo: dos franjas diagonales tenues sobre el cristal
    p.append(f'<path d="M{X0+26},{Y1-26} L{X0+62},{Y0+26} L{X0+76},{Y0+26} '
             f'L{X0+40},{Y1-26} Z" fill="{ORO}" opacity="0.13"/>')
    p.append(f'<path d="M{X0+58},{Y1-26} L{X0+94},{Y0+26} L{X0+101},{Y0+26} '
             f'L{X0+65},{Y1-26} Z" fill="{ORO}" opacity="0.09"/>')

    # LOS FOCOS alrededor del marco. El nº 7 va apagado (sin relleno claro):
    # un camerino real siempre tiene un foco fundido.
    focos = []
    for k in range(5):                      # arriba
        focos.append((X0 + 10 + k * 24, Y0 + 10))
    for k in range(4):                      # abajo
        focos.append((X0 + 22 + k * 24, Y1 - 10))
    for k in range(3):                      # laterales
        focos.append((X0 + 10, Y0 + 40 + k * 30))
        focos.append((X1 - 10, Y0 + 40 + k * 30))
    for i, (fx, fy) in enumerate(focos):
        if i == 7:                          # el fundido
            p.append(f'<circle cx="{fx}" cy="{fy}" r="5" fill="none" '
                     f'stroke="{ORO}" stroke-width="1.8" opacity="0.5"/>')
        else:
            p.append(f'<circle cx="{fx}" cy="{fy}" r="6.5" fill="{ORO_L}" '
                     f'opacity="0.28"/>')
            p.append(f'<circle cx="{fx}" cy="{fy}" r="4.2" fill="{ORO_L}"/>')

    # la repisa del tocador
    p.append(f'<rect x="46" y="176" width="148" height="6" rx="3" fill="{ORO}"/>')
    p.append(f'<circle cx="52" cy="72" r="2.4" fill="{TINTA}"/>')
    p.append(f'<circle cx="192" cy="192" r="2.2" fill="{TINTA}"/>')
    p.append('</svg>')
    return ''.join(p)


def svg_salon(w=240):
    """El piso de baile ajedrezado en perspectiva, con el haz cayendo encima."""
    p = cab(w, 120, 92, 66)

    # EL HAZ DE LUZ: un cono desde arriba, abierto hacia el piso
    p.append(f'<path d="M108,20 L132,20 L186,150 L54,150 Z" fill="{ORO_L}" '
             f'opacity="0.17"/>')
    p.append(f'<path d="M113,20 L127,20 L156,150 L84,150 Z" fill="{ORO_L}" '
             f'opacity="0.15"/>')
    # el reflector del que sale
    p.append(f'<rect x="102" y="14" width="36" height="14" rx="4" fill="{TINTA}"/>')

    # EL PISO en perspectiva: 6 columnas × 4 filas, se angostan hacia el fondo.
    # Las filas de atrás son más cortas y más juntas = profundidad.
    FIL = [(150, 190, 30), (150, 178, 46), (150, 168, 60), (150, 160, 72)]
    y = 150
    alturas = [40, 26, 18, 12]
    anchos = [190, 150, 118, 94]
    for r, (h, an) in enumerate(zip(alturas, anchos)):
        y2 = y - h if r else 150
        yy = 150 - sum(alturas[:r]) - (h if False else 0)
    # se dibuja de adelante (abajo, grande) hacia atrás (arriba, chico)
    ytop = 150
    for r in range(4):
        h = alturas[r]
        an = anchos[r]
        y0 = ytop - h
        cols = 6
        cw = an / cols
        for c in range(cols):
            if (r + c) % 2:
                continue                      # el ajedrez: sólo los alternos
            x0 = 120 - an / 2 + c * cw
            an2 = anchos[r + 1] if r + 1 < 4 else anchos[3] * 0.86
            cw2 = an2 / cols
            x0b = 120 - an2 / 2 + c * cw2
            p.append(f'<path d="M{x0:.1f},{ytop:.1f} L{x0+cw:.1f},{ytop:.1f} '
                     f'L{x0b+cw2:.1f},{y0:.1f} L{x0b:.1f},{y0:.1f} Z" '
                     f'fill="{TINTA}" opacity="{0.92 - r*0.16:.2f}"/>')
        ytop = y0

    # el borde del piso al frente
    p.append(f'<rect x="24" y="150" width="192" height="5" rx="2.5" fill="{ORO}"/>')

    # purpurina suelta en el piso, poquita — ya empezó a caer
    rng = np.random.default_rng(5)
    for i in range(9):
        x = 34 + float(rng.uniform(0, 172))
        yv = 158 + float(rng.uniform(0, 14))
        s = float(rng.uniform(3.0, 5.6))
        col = ORO_L if i % 3 == 0 else ORO
        p.append(f'<rect x="{x:.1f}" y="{yv:.1f}" width="{s:.1f}" '
                 f'height="{s*0.6:.1f}" rx="0.8" fill="{col}" '
                 f'opacity="{rng.uniform(0.4,0.8):.2f}" '
                 f'transform="rotate({rng.uniform(-30,30):.0f} {x:.1f} {yv:.1f})"/>')

    p.append(f'<circle cx="42" cy="60" r="2.4" fill="{TINTA}"/>')
    p.append(f'<circle cx="200" cy="184" r="2.2" fill="{TINTA}"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for nom, fn in (('vestidor', svg_vestidor), ('salon', svg_salon)):
        t = fn()
        dst = os.path.join(HERE, 'art', f'purpurina-{nom}.svg')
        with open(dst, 'w') as f:
            f.write(t)
        print(f'purpurina-{nom}.svg · {len(t)} B')
