#!/usr/bin/env python3
"""Arte de ECO — la bocina y sus ecos, en el estilo de la casa.

El single de dub. El concepto es que en dub el eco no es un efecto que le pones
encima a la rola: el eco ES el arreglo. Entonces el dibujo es literalmente eso —
una bocina de sound system y, a su derecha, ELLA MISMA repetida cada vez más
chica y más tenue. Lo que ves repetido es el instrumento.

Estilo de la casa (guer-cactus, tulum-atlas, subsuelo-escalera, micelio-hongo):
UN objeto en trazo grueso negro sobre hueso, glow del color del disco, sombra de
piso, detalles finos en el acento y dos puntitos.

Color: ámbar de válvula. El dub se hizo en cuartos llenos de amplificadores de
bulbos y máquinas de cinta calientes — y no estaba usado en el catálogo
(naranja, rojo, azul, verde, violeta, óxido, turquesa ya estaban tomados).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TINTA = '#141210'
AMBAR = '#9A6B1E'          # el acento oscurecido (legible sobre hueso)
AMBAR_L = '#E8B24C'        # el brillo


def svg(w=240):
    """La caja de sound system a la izquierda y sus ecos abriéndose a la derecha.

    La primera versión la puse descentrada, con los ecos como bocinas fantasma
    encogidas — sobre hueso se leían como manchas grises, no como repeticiones,
    y el gabinete parecía un corchete. Aquí el eco se dibuja como lo que se oye:
    ARCOS que salen del cono, cada uno más abierto, más delgado y más tenue,
    igual que un delay pierde nivel en cada repetición.
    """
    CX_BOX = 74          # centro de la caja
    CY = 116             # eje óptico de todo el dibujo
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<defs><radialGradient id="ecg" cx="30%" cy="48%" r="58%">'
         f'<stop offset="0%" stop-color="{AMBAR_L}" stop-opacity="0.42"/>'
         f'<stop offset="55%" stop-color="{AMBAR_L}" stop-opacity="0.14"/>'
         f'<stop offset="100%" stop-color="{AMBAR_L}" stop-opacity="0"/>'
         f'</radialGradient></defs>',
         f'<ellipse cx="120" cy="206" rx="74" ry="8" fill="{TINTA}" opacity="0.05"/>',
         f'<circle cx="{CX_BOX}" cy="{CY}" r="66" fill="url(#ecg)"/>']

    # LOS ECOS: arcos concéntricos que se abren hacia la derecha.
    # Cada repetición: más lejos, más delgada, más tenue. Eso es un delay.
    for i in range(5):
        r = 58 + i * 26
        gr = 0.52 - i * 0.03                      # qué tanto abre el arco
        x0 = CX_BOX + r * (1 - gr * 0.55)
        p.append(f'<path d="M{x0:.0f},{CY - r*gr:.0f} Q{CX_BOX + r:.0f},{CY} '
                 f'{x0:.0f},{CY + r*gr:.0f}" fill="none" stroke="{AMBAR}" '
                 f'stroke-width="{5.0 - i*0.8:.1f}" opacity="{0.62 - i*0.11:.2f}" '
                 f'stroke-linecap="round"/>')

    # LA CAJA: rectángulo bold vertical, con esquinas suaves. Es un bafle.
    p.append(f'<rect x="{CX_BOX-46}" y="{CY-64}" width="92" height="128" rx="7" '
             f'fill="{TINTA}"/>')

    # el cono grande: aro de suspensión ámbar + dust cap brillante al centro
    p.append(f'<circle cx="{CX_BOX}" cy="{CY+10}" r="33" fill="{AMBAR}" opacity="0.34"/>')
    p.append(f'<circle cx="{CX_BOX}" cy="{CY+10}" r="13" fill="{AMBAR_L}"/>')
    # el tweeter chico arriba, para que se lea sound-system y no un solo bocinón
    p.append(f'<circle cx="{CX_BOX}" cy="{CY-42}" r="9" fill="{AMBAR}" opacity="0.34"/>')
    p.append(f'<circle cx="{CX_BOX}" cy="{CY-42}" r="3.6" fill="{AMBAR_L}"/>')

    # línea de piso — cruza por debajo de la caja Y de los ecos, los amarra
    p.append(f'<rect x="24" y="192" width="176" height="5" rx="2.5" fill="{AMBAR}"/>')

    # dos puntitos de acento, como todo el catálogo
    p.append(f'<circle cx="205" cy="58" r="2.4" fill="{TINTA}"/>')
    p.append(f'<circle cx="40" cy="214" r="2.2" fill="{TINTA}"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    t = svg()
    with open(os.path.join(HERE, 'art', 'eco.svg'), 'w') as f:
        f.write(t)
    print(f'eco.svg · {len(t)} B')
