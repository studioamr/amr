#!/usr/bin/env python3
"""Arte de MICELIO — el hongo y su red, en el estilo de la casa.

El single místico de flautas y agua. El concepto es el micelio: la red de los
hongos bajo el suelo del bosque — el hongo es solo la parte visible, la red de
abajo es el organismo de verdad. El dibujo cuenta exactamente eso: un hongo bold
arriba de la línea de suelo, y debajo la red ramificándose en turquesa, con
nodos que brillan (hay hongos que de verdad son bioluminiscentes — foxfire).

Estilo de la casa (guer-cactus, tulum-atlas, subsuelo-escalera): UN objeto en
trazo grueso negro sobre hueso, glow del color del disco, sombra de piso,
detalles finos en el acento y dos puntitos.
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TINTA = '#141210'
TURQ = '#12707A'           # el acento oscurecido (legible sobre hueso)
TURQ_L = '#5ED4DE'         # el brillo


def svg(w=240):
    rng = np.random.default_rng(37)
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<defs><radialGradient id="mcg" cx="50%" cy="42%" r="52%">'
         f'<stop offset="0%" stop-color="{TURQ_L}" stop-opacity="0.42"/>'
         f'<stop offset="55%" stop-color="{TURQ_L}" stop-opacity="0.14"/>'
         f'<stop offset="100%" stop-color="{TURQ_L}" stop-opacity="0"/>'
         f'</radialGradient></defs>',
         f'<ellipse cx="120" cy="212" rx="56" ry="8" fill="{TINTA}" opacity="0.05"/>',
         f'<circle cx="120" cy="100" r="64" fill="url(#mcg)"/>']

    # el sombrero: domo bold
    p.append(f'<path d="M70,112 C70,72 96,56 120,56 C144,56 170,72 170,112 '
             f'L70,112 Z" fill="{TINTA}"/>')
    # motas del sombrero (psicodélico, sobrio): tres, en turquesa claro
    for cx, cy, r in [(101, 84, 5), (129, 73, 4), (143, 94, 4.5)]:
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{TURQ_L}" opacity="0.85"/>')
    # laminillas: rayitas bajo el borde del sombrero
    for k in range(6):
        x = 80 + k * 16
        p.append(f'<line x1="{x}" y1="112" x2="{x}" y2="119" stroke="{TURQ}" '
                 f'stroke-width="2.6" stroke-linecap="round"/>')
    # el tallo, hasta el suelo
    p.append(f'<path d="M110,112 L110,148 L130,148 L130,112 Z" fill="{TINTA}"/>')

    # la línea de suelo — el hongo arriba, el organismo real abajo
    p.append(f'<rect x="56" y="148" width="128" height="5" rx="2.5" fill="{TURQ}"/>')

    # EL MICELIO: la red ramificándose bajo el suelo, con nodos que brillan
    def rama(x, y, ang, largo, prof=0):
        if largo < 6 or prof > 3:
            p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="1.8" fill="{TURQ_L}" opacity="0.9"/>')
            return
        x2 = x + math.sin(ang) * largo
        y2 = y + math.cos(ang) * largo * 0.75
        p.append(f'<path d="M{x:.0f},{y:.0f} Q{x + math.sin(ang)*largo*0.5:.0f},'
                 f'{y + math.cos(ang)*largo*0.45:.0f} {x2:.0f},{y2:.0f}" fill="none" '
                 f'stroke="{TURQ}" stroke-width="{max(1.2, 3.2-prof):.1f}" '
                 f'opacity="{0.75 - prof*0.12:.2f}" stroke-linecap="round"/>')
        for d in (-0.55, 0.5):
            rama(x2, y2, ang + d * float(rng.uniform(0.7, 1.3)),
                 largo * float(rng.uniform(0.55, 0.72)), prof + 1)

    for a in (-0.9, -0.35, 0.3, 0.85):
        rama(120 + a * 8, 153, a, 30)

    # dos puntitos de acento, como todo el catálogo
    p.append(f'<circle cx="60" cy="96" r="2.2" fill="{TINTA}"/>')
    p.append(f'<circle cx="184" cy="130" r="2.4" fill="{TINTA}"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    t = svg()
    with open(os.path.join(HERE, 'art', 'micelio.svg'), 'w') as f:
        f.write(t)
    print(f'micelio.svg · {len(t)} B')
