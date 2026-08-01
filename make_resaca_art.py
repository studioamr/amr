#!/usr/bin/env python3
"""Arte de RESACA — la ola que se retira y lo que deja.

El nombre tiene las dos lecturas al mismo tiempo: la resaca es el agua que se
regresa Y lo que queda después de la fiesta. El dibujo es exactamente eso: una
ola bold ya yéndose hacia la izquierda, la línea de espuma que marca hasta
dónde llegó, y en la arena las cosas que dejó varadas.

No es una ola rompiendo — es una ola RETIRÁNDOSE. Esa diferencia es el disco.

Estilo de la casa (micelio-hongo, eco-bocina, purpurina-bola): UN objeto en
trazo grueso negro sobre hueso, glow del color del disco, línea de piso,
detalles finos en el acento y dos puntitos.
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TINTA = '#141210'
CORAL = '#C25A4A'          # el acento oscurecido (legible sobre hueso)
CORAL_L = '#F0A08C'        # la espuma iluminada


def svg(w=240):
    rng = np.random.default_rng(23)
    SUELO = 168
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<defs><radialGradient id="rg" cx="38%" cy="44%" r="58%">'
         f'<stop offset="0%" stop-color="{CORAL_L}" stop-opacity="0.42"/>'
         f'<stop offset="55%" stop-color="{CORAL_L}" stop-opacity="0.14"/>'
         f'<stop offset="100%" stop-color="{CORAL_L}" stop-opacity="0"/>'
         f'</radialGradient></defs>',
         f'<ellipse cx="120" cy="206" rx="76" ry="8" fill="{TINTA}" opacity="0.05"/>',
         f'<circle cx="92" cy="108" r="70" fill="url(#rg)"/>']

    # LA OLA, bold, ya retirándose hacia la izquierda: la cresta va cayendo y
    # el cuerpo se adelgaza — no está rompiendo, está regresando.
    p.append(f'<path d="M18,{SUELO} '
             f'C18,120 34,74 72,60 '
             f'C104,48 128,64 132,90 '
             f'C135,110 122,124 106,122 '
             f'C94,120 88,110 92,100 '
             f'L92,100 C86,116 96,132 114,134 '
             f'C140,137 158,116 154,88 '
             f'C150,52 116,30 76,40 '
             f'C34,50 8,104 8,{SUELO} Z" fill="{TINTA}"/>')

    # la espuma sobre la cresta: puntitos claros donde el agua se deshace
    for i in range(14):
        a = rng.uniform(0.15, 0.95)
        x = 20 + a * 130 + rng.uniform(-5, 5)
        y = 150 - math.sin(a * math.pi) * 92 + rng.uniform(-7, 7)
        r = rng.uniform(1.6, 3.6)
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                 f'fill="{CORAL_L}" opacity="{rng.uniform(0.5, 0.95):.2f}"/>')

    # LA LÍNEA DE ESPUMA: hasta dónde llegó el agua. Ondulada, no recta —
    # es una marca en la arena, no una regla.
    pts = []
    for i in range(41):
        t = i / 40.0
        x = 20 + t * 200
        y = SUELO + 4 + math.sin(t * 7.5) * 2.6 + math.sin(t * 21) * 1.1
        pts.append(f'{x:.1f},{y:.1f}')
    p.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{CORAL}" '
             f'stroke-width="3.4" stroke-linecap="round" opacity="0.9"/>')

    # LO QUE DEJÓ VARADO en la arena, del lado que ya se secó
    for i in range(9):
        x = 30 + rng.uniform(0, 180)
        y = SUELO + 12 + rng.uniform(0, 18)
        s = rng.uniform(2.2, 4.6)
        if i % 3 == 0:      # conchas: medio círculo
            p.append(f'<path d="M{x-s:.1f},{y:.1f} a{s:.1f},{s:.1f} 0 0,1 '
                     f'{2*s:.1f},0 Z" fill="{CORAL}" '
                     f'opacity="{rng.uniform(0.45, 0.8):.2f}"/>')
        else:               # guijarros
            p.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{s:.1f}" '
                     f'ry="{s*0.62:.1f}" fill="{CORAL}" '
                     f'opacity="{rng.uniform(0.35, 0.7):.2f}"/>')

    # la línea de suelo = la playa
    p.append(f'<rect x="16" y="{SUELO}" width="208" height="4.5" rx="2.2" '
             f'fill="{TINTA}" opacity="0.82"/>')

    # dos puntitos de acento, como todo el catálogo
    p.append(f'<circle cx="196" cy="58" r="2.4" fill="{TINTA}"/>')
    p.append(f'<circle cx="36" cy="200" r="2.2" fill="{TINTA}"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    t = svg()
    with open(os.path.join(HERE, 'art', 'resaca.svg'), 'w') as f:
        f.write(t)
    print(f'resaca.svg · {len(t)} B')
