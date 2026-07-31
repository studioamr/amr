#!/usr/bin/env python3
"""Arte de PURPURINA — la bola de espejos que se desarma.

El concepto del disco es la lentejuela del reflector Y lo que queda tirado en el
piso cuando ya se fue todo el mundo. Las dos cosas al mismo tiempo. El dibujo es
exactamente eso: una bola de espejos bold arriba, entera del lado izquierdo, que
del lado derecho empieza a soltar sus espejitos — y abajo, en el piso, los
espejitos ya caídos.

No es "una bola de espejos rota": está EN EL ACTO de desarmarse. La fiesta y su
final en la misma imagen, que es lo que hace el disco.

Estilo de la casa (guer-cactus, tulum-atlas, subsuelo-escalera, micelio-hongo,
eco-bocina): UN objeto en trazo grueso negro sobre hueso, glow del color del
disco, sombra de piso, detalles finos en el acento y dos puntitos.
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TINTA = '#141210'
ORO = '#B98A2E'            # el acento oscurecido (legible sobre hueso)
ORO_L = '#F2D479'          # el destello del reflector


def svg(w=240):
    rng = np.random.default_rng(19)
    CX, CY, R = 118, 104, 52          # la bola
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<defs><radialGradient id="pug" cx="46%" cy="42%" r="56%">'
         f'<stop offset="0%" stop-color="{ORO_L}" stop-opacity="0.46"/>'
         f'<stop offset="55%" stop-color="{ORO_L}" stop-opacity="0.15"/>'
         f'<stop offset="100%" stop-color="{ORO_L}" stop-opacity="0"/>'
         f'</radialGradient>'
         # máscara: la bola está ENTERA a la izquierda y se deshilacha a la
         # derecha. El gradiente de la máscara es literalmente "se está yendo".
         f'<linearGradient id="pumg" x1="0%" y1="0%" x2="100%" y2="0%">'
         f'<stop offset="0%" stop-color="#fff"/>'
         f'<stop offset="46%" stop-color="#fff"/>'
         f'<stop offset="100%" stop-color="#000"/>'
         f'</linearGradient>'
         f'<mask id="pum"><rect width="{w}" height="{w}" fill="url(#pumg)"/></mask>'
         f'</defs>',
         f'<ellipse cx="120" cy="206" rx="76" ry="8" fill="{TINTA}" opacity="0.05"/>',
         f'<circle cx="{CX}" cy="{CY}" r="72" fill="url(#pug)"/>']

    # el cable y la argolla de la que cuelga
    p.append(f'<rect x="{CX-2}" y="16" width="4" height="{CY-R-10}" fill="{TINTA}"/>')
    p.append(f'<circle cx="{CX}" cy="{CY-R-6}" r="6" fill="none" stroke="{TINTA}" '
             f'stroke-width="4"/>')

    # LA BOLA, bold, con la máscara que la deshilacha a la derecha
    p.append(f'<g mask="url(#pum)">')
    p.append(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="{TINTA}"/>')
    # las facetas: cuadritos en rejilla curva, algunos en oro (los que brillan)
    for iy in range(-4, 5):
        yy = CY + iy * 11.5
        ancho = math.sqrt(max(0.0, R*R - (iy*11.5)**2))
        nx = max(1, int(ancho / 11.5))
        for ix in range(-nx, nx + 1):
            xx = CX + ix * 11.5
            if (xx-CX)**2/(R*0.98)**2 + (yy-CY)**2/(R*0.98)**2 > 1:
                continue
            r = rng.random()
            if r < 0.16:
                p.append(f'<rect x="{xx-4.6:.1f}" y="{yy-4.6:.1f}" width="9.2" '
                         f'height="9.2" rx="1.4" fill="{ORO_L}"/>')
            elif r < 0.34:
                p.append(f'<rect x="{xx-4.6:.1f}" y="{yy-4.6:.1f}" width="9.2" '
                         f'height="9.2" rx="1.4" fill="{ORO}" opacity="0.55"/>')
    p.append('</g>')

    # LOS ESPEJITOS QUE SE VAN: salen del borde derecho, girando y cayendo.
    # Se hacen más chicos y más tenues conforme bajan — se están yendo.
    for i in range(11):
        t = i / 10.0
        x = CX + R*0.55 + t * 76 + float(rng.uniform(-6, 6))
        y = CY - 16 + t * t * 96 + float(rng.uniform(-8, 8))
        s = 8.4 * (1 - t * 0.55)
        rot = float(rng.uniform(0, 90))
        col = ORO_L if i % 3 == 0 else ORO
        op = 0.9 - t * 0.35
        p.append(f'<rect x="{-s/2:.1f}" y="{-s/2:.1f}" width="{s:.1f}" '
                 f'height="{s:.1f}" rx="1.2" fill="{col}" opacity="{op:.2f}" '
                 f'transform="translate({x:.1f},{y:.1f}) rotate({rot:.0f})"/>')

    # la línea de piso
    p.append(f'<rect x="26" y="192" width="188" height="5" rx="2.5" fill="{ORO}"/>')

    # LOS QUE YA CAYERON: purpurina en el piso, después de la fiesta
    for i in range(16):
        x = 34 + float(rng.uniform(0, 172))
        y = 198 + float(rng.uniform(0, 12))
        s = float(rng.uniform(3.0, 6.4))
        col = ORO_L if i % 4 == 0 else ORO
        p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{s:.1f}" height="{s*0.6:.1f}" '
                 f'rx="0.8" fill="{col}" opacity="{rng.uniform(0.35, 0.8):.2f}" '
                 f'transform="rotate({rng.uniform(-30,30):.0f} {x:.1f} {y:.1f})"/>')

    # dos puntitos de acento, como todo el catálogo
    p.append(f'<circle cx="44" cy="66" r="2.4" fill="{TINTA}"/>')
    p.append(f'<circle cx="206" cy="150" r="2.2" fill="{TINTA}"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    t = svg()
    with open(os.path.join(HERE, 'art', 'purpurina.svg'), 'w') as f:
        f.write(t)
    print(f'purpurina.svg · {len(t)} B')
