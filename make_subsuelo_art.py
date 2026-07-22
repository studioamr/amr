#!/usr/bin/env python3
"""Arte de SUBSUELO — íconos en el estilo de la casa, no escenas atmosféricas.

⚠️ ESTE ARCHIVO SE REHIZO. La primera versión eran escenas de degradado a sangre
(estratos, columnas hexagonales llenando el cuadro, anillos concéntricos).
André: "cambia los dibujos de los subsuelo por algo del estilo". Tenía razón —
el catálogo tiene un ESTILO y esas escenas no eran de él.

EL ESTILO DE LA CASA (ver art/guer-cactus.svg, guer-serpiente.svg, tulum-atlas):
  · fondo transparente (se ve el hueso de la tarjeta)
  · UN objeto icónico, dibujado con trazo grueso negro (#141210, width ~14-15)
  · un glow radial suave del color del disco detrás
  · una sombra elíptica de piso (el objeto está parado en algo)
  · detalles finos en el color de acento (width ~2.6) y dos puntitos negros
Es un grabado, no una fotografía. Cada disco es un objeto reconocible.

LOS TRES OBJETOS DE SUBSUELO (industrial, subterráneo, óxido):
  · portada  = tapa de alcantarilla vista de arriba — el ícono más "subsuelo"
               que existe: lo que pisas todos los días sin mirar
  · BASALTO  = las columnas de basalto (los órganos), la roca del fondo
  · DUCTO    = una rejilla de ventilación, el tiro de aire
"""
import os, math

HERE = os.path.dirname(os.path.abspath(__file__))
TINTA = '#141210'          # el negro cálido del estilo
OXIDO = '#B4501F'
HUESO = '#EAE6DF'


def _glow(idg, cx, cy, r):
    return (f'<defs><radialGradient id="{idg}" cx="50%" cy="50%" r="50%">'
            f'<stop offset="0%" stop-color="{OXIDO}" stop-opacity="0.42"/>'
            f'<stop offset="55%" stop-color="{OXIDO}" stop-opacity="0.14"/>'
            f'<stop offset="100%" stop-color="{OXIDO}" stop-opacity="0"/>'
            f'</radialGradient></defs>'
            f'<ellipse cx="{cx}" cy="212" rx="54" ry="8" fill="{TINTA}" opacity="0.05"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{idg})"/>')


def _dots():
    return (f'<circle cx="60" cy="150" r="2.2" fill="{TINTA}"/>'
            f'<circle cx="186" cy="172" r="2.4" fill="{TINTA}"/>')


def svg_portada(w=240):
    """Tapa de alcantarilla — vista de arriba. Aro grueso, radios, tornillos y
    la ranura de palanca. Lo que pisas sin mirar: la puerta del subsuelo."""
    cx = cy = 120
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         _glow('ssp', cx, cy, 66)]
    # aro exterior grueso
    p.append(f'<circle cx="{cx}" cy="{cy}" r="74" fill="none" stroke="{TINTA}" stroke-width="15"/>')
    # aro interior
    p.append(f'<circle cx="{cx}" cy="{cy}" r="54" fill="none" stroke="{TINTA}" stroke-width="7"/>')
    # radios: 12 costillas gruesas del hub al aro interior
    for k in range(12):
        a = k / 12 * 2 * math.pi
        x1, y1 = cx + math.cos(a) * 16, cy + math.sin(a) * 16
        x2, y2 = cx + math.cos(a) * 50, cy + math.sin(a) * 50
        col = OXIDO if k % 3 == 0 else TINTA
        p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{col}" stroke-width="5" stroke-linecap="round"/>')
    # hub central
    p.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="{TINTA}"/>')
    # tornillos: 8 puntos sobre el aro
    for k in range(8):
        a = k / 8 * 2 * math.pi + 0.39
        p.append(f'<circle cx="{cx+math.cos(a)*64:.1f}" cy="{cy+math.sin(a)*64:.1f}" '
                 f'r="3.4" fill="{TINTA}"/>')
    # ranura de palanca (arriba) en óxido
    p.append(f'<rect x="{cx-11}" y="{cy-72}" width="22" height="9" rx="4.5" fill="{OXIDO}"/>')
    p.append(_dots())
    p.append('</svg>')
    return ''.join(p)


def svg_basalto(w=240):
    """Columnas de basalto — los órganos. Prismas verticales de distinta altura,
    parados juntos, con la cara de arriba encendida en óxido (la roca del fondo,
    el pico del disco)."""
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         _glow('ssb', 120, 128, 60)]
    # cinco columnas: (x, alto). El suelo común queda en y=206.
    cols = [(58, 92), (86, 128), (116, 150), (146, 116), (174, 138)]
    anch = 24
    suelo = 206
    for x, alto in cols:
        top = suelo - alto
        # el fuste
        p.append(f'<rect x="{x}" y="{top}" width="{anch}" height="{alto}" fill="{TINTA}"/>')
        # la cara de arriba: un rombo (hexágono en perspectiva) encendido
        d = anch * 0.34
        cara = f'{x},{top} {x+anch},{top} {x+anch-d:.0f},{top-9} {x+d:.0f},{top-9}'
        p.append(f'<polygon points="{cara}" fill="{OXIDO}"/>')
        # una junta horizontal en el fuste (las columnas se agrietan por tramos)
        jy = top + alto * 0.42
        p.append(f'<line x1="{x}" y1="{jy:.0f}" x2="{x+anch}" y2="{jy:.0f}" '
                 f'stroke="{HUESO}" stroke-width="1.4" opacity="0.35"/>')
    # línea de suelo
    p.append(f'<rect x="46" y="{suelo}" width="150" height="6" rx="3" fill="{OXIDO}"/>')
    p.append(_dots())
    p.append('</svg>')
    return ''.join(p)


def svg_ducto(w=240):
    """Rejilla de ventilación — el tiro de aire. Un aro grueso con persianas
    horizontales; por las rendijas se cuela el óxido, como la luz al fondo del
    tiro."""
    cx = cy = 120
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         _glow('ssd', cx, cy, 62),
         f'<defs><clipPath id="ssdc"><circle cx="{cx}" cy="{cy}" r="58"/></clipPath></defs>']
    # el óxido detrás de las rendijas (la luz colándose)
    p.append(f'<circle cx="{cx}" cy="{cy}" r="58" fill="{OXIDO}" opacity="0.5"/>')
    # las persianas: barras horizontales gruesas, recortadas al círculo
    p.append(f'<g clip-path="url(#ssdc)">')
    y = cy - 52
    while y < cy + 58:
        p.append(f'<rect x="{cx-64}" y="{y:.0f}" width="128" height="12" fill="{TINTA}"/>')
        y += 20
    p.append('</g>')
    # marco grueso
    p.append(f'<circle cx="{cx}" cy="{cy}" r="58" fill="none" stroke="{TINTA}" stroke-width="14"/>')
    # cuatro tornillos del marco
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        p.append(f'<circle cx="{cx+math.cos(a)*58:.1f}" cy="{cy+math.sin(a)*58:.1f}" '
                 f'r="4" fill="{TINTA}"/>')
    p.append(_dots())
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for nombre, gen in [('subsuelo', svg_portada),
                        ('subsuelo-basalto', svg_basalto),
                        ('subsuelo-ducto', svg_ducto)]:
        dst = os.path.join(HERE, 'art', f'{nombre}.svg')
        t = gen()
        with open(dst, 'w') as f:
            f.write(t)
        print(f'{nombre:22s} {len(t)} B')
