#!/usr/bin/env python3
"""Arte de JACARANDA — la lluvia de pétalos, generada, no dibujada a mano.

POR QUÉ ESTA IMAGEN
  El jacarandá no interesa como árbol: interesa como EVENTO. Pone violeta una
  ciudad entera durante tres semanas y se acaba. Y lo que la gente recuerda no
  es el árbol — es la calle cubierta, los pétalos cayendo encima de los coches,
  pisar violeta.

  Por eso la portada no dibuja un árbol. Dibuja **lo que cae**: miles de pétalos
  en el aire, densos arriba donde está la copa y amontonándose abajo hasta
  volverse alfombra.

CÓMO ESTÁ HECHA
  Un pétalo que cae NO baja derecho. Es ancho y ligero, así que el aire lo hace
  voltearse y planear de lado — el movimiento se llama *tumbling* y es por eso
  que un pétalo tarda tanto en llegar al suelo comparado con una piedra. Aquí
  eso se aproxima con dos cosas:
    · un campo de flujo suave con deriva hacia abajo (el viento y la gravedad)
    · un ángulo PROPIO por pétalo, sin relación con su vecino, porque cada uno
      va girando por su cuenta
  Eso último es lo que distingue esta imagen de la bandada que tenía antes el
  disco: los pájaros se ALINEAN con sus vecinos, los pétalos NO. Misma máquina,
  regla opuesta, y se lee distinto de inmediato.
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W = 1000

# La paleta del jacarandá: violeta profundo con un lila que brilla. Son los
# mismos tonos que ya usaba el disco viejo — cambia la música, no el color.
VIOLETA = '#463A73'
LILA = '#9D8BD6'
HUESO = '#EAE6DF'


def campo(x, y):
    """Deriva del aire en (x,y): baja siempre, con corrientes laterales suaves."""
    u = (math.sin(y * 0.0062 + 0.7) * 0.85 + math.cos(x * 0.0041 + 2.2) * 0.42
         + math.sin(y * 0.0135) * 0.28)
    v = 1.55 + math.sin(x * 0.0057 + 1.1) * 0.22      # ← siempre hacia abajo
    n = math.hypot(u, v) or 1.0
    return u / n, v / n


def petalos(n=2600, seed=41):
    """Suelta pétalos y los deja caer por el campo.

    Devuelve (x, y, ángulo propio, peso). El ángulo NO sale del campo: cada
    pétalo gira por su cuenta mientras planea. Esa es la diferencia entre esto
    y una bandada."""
    rng = np.random.default_rng(seed)
    out = []
    intentos = 0
    while len(out) < n and intentos < n * 40:
        intentos += 1
        x = float(rng.uniform(-W * 0.05, W * 1.05))
        y = float(rng.uniform(-W * 0.05, W * 0.98))
        # densidad: mucha arriba (la copa), se abre al caer, se junta abajo
        t = max(0.0, min(1.0, y / W))
        copa = math.exp(-((t - 0.10) / 0.30) ** 2)         # la copa, arriba
        suelo = math.exp(-((t - 0.955) / 0.055) ** 2) * 1.15  # la alfombra, abajo
        aire = 0.30 * math.exp(-((t - 0.5) / 0.40) ** 2)   # los que van cayendo
        d = min(1.0, copa + suelo + aire)
        if rng.random() > d:
            continue
        for _ in range(int(rng.integers(2, 9))):
            u, v = campo(x, y)
            x += u * 8.0
            y += v * 8.0
        if not (-W * 0.06 < x < W * 1.06 and -W * 0.06 < y < W * 1.02):
            continue
        out.append((x, y, float(rng.uniform(0, 180)), d))
    return out


def svg():
    ps = petalos()
    p = [f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">',
         # ⚠️ El recorte no es opcional. Los pétalos se siembran FUERA del marco
         # a propósito, para que no se vea la orilla de donde salen — pero sin
         # clip se pintan encima del marco y se desbordan de la portada.
         f'<defs><clipPath id="jcmarco"><rect width="{W}" height="{W}"/></clipPath>',
         '<linearGradient id="jcaire" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{LILA}" stop-opacity="0.20"/>'
         f'<stop offset="55%" stop-color="{LILA}" stop-opacity="0.05"/>'
         f'<stop offset="100%" stop-color="{VIOLETA}" stop-opacity="0.14"/>'
         '</linearGradient></defs>',
         f'<rect width="{W}" height="{W}" fill="{HUESO}"/>',
         f'<rect width="{W}" height="{W}" fill="url(#jcaire)"/>',
         '<g clip-path="url(#jcmarco)">']

    rng = np.random.default_rng(7)
    cuerpo = []
    for x, y, a, d in ps:
        # el pétalo del jacarandá es una campanita: más ancho que largo
        L = (3.2 + 5.0 * d) * (0.55 + 1.0 * float(rng.random()))
        # los de abajo van más oscuros: llevan días ahí y ya se pisaron
        prof = min(1.0, y / W)
        col = VIOLETA if (prof > 0.72 or rng.random() < 0.34) else LILA
        cuerpo.append(
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({a:.0f})">'
            f'<ellipse rx="{L:.1f}" ry="{L*0.62:.2f}" fill="{col}" '
            f'opacity="{0.28+0.60*d:.2f}"/></g>')
    p.append(''.join(cuerpo))
    p.append('</g>')

    # la línea de la banqueta: donde la alfombra se acaba
    p.append(f'<line x1="{W*0.06:.0f}" y1="{W*0.875:.0f}" x2="{W*0.94:.0f}" '
             f'y2="{W*0.875:.0f}" stroke="{VIOLETA}" stroke-width="1.8" opacity="0.4"/>')
    # marcas de las 8 rolas, la 5ª (EPIFANÍA) encendida: es el pico del disco
    for i in range(8):
        cx = W * 0.10 + (W * 0.80) * (i + 0.5) / 8.0
        col = LILA if i == 4 else VIOLETA
        op = '1' if i == 4 else '0.5'
        p.append(f'<line x1="{cx:.1f}" y1="{W*0.875:.0f}" x2="{cx:.1f}" '
                 f'y2="{W*0.899:.0f}" stroke="{col}" stroke-width="2.4" opacity="{op}"/>')
    p.append('</svg>')
    return ''.join(p)


def svg_fulgor(w=240):
    """FULGOR — la copa vista desde abajo, a contraluz.

    Es el pico del disco, y el pico del jacarandá es un instante muy concreto:
    estás debajo del árbol, miras para arriba, y el sol pasa POR las flores. El
    violeta deja de ser color y se vuelve luz. Por eso aquí el fondo es claro
    (el cielo) y las flores son la masa oscura — al revés que la portada.
    """
    rng = np.random.default_rng(13)
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         '<defs><radialGradient id="fgsol" cx="46%" cy="40%" r="46%">'
         '<stop offset="0%" stop-color="#FFF6E4"/>'
         f'<stop offset="55%" stop-color="{LILA}" stop-opacity="0.55"/>'
         f'<stop offset="100%" stop-color="{VIOLETA}" stop-opacity="0.30"/>'
         '</radialGradient></defs>',
         f'<rect width="{w}" height="{w}" fill="{HUESO}"/>',
         f'<rect width="{w}" height="{w}" fill="url(#fgsol)"/>']

    # las ramas: salen del borde hacia adentro, adelgazando como ramas de verdad
    def rama(x, y, ang, largo, grosor, prof=0):
        if largo < 4 or grosor < 0.35:
            return
        x2 = x + math.cos(ang) * largo
        y2 = y + math.sin(ang) * largo
        p.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{VIOLETA}" stroke-width="{grosor:.2f}" '
                 f'stroke-linecap="round" opacity="{0.30+0.45*min(1,prof/3):.2f}"/>')
        # racimos de flor colgando de las puntas
        if prof >= 2:
            for _ in range(int(rng.integers(3, 9))):
                fx = x2 + rng.uniform(-largo * 0.4, largo * 0.4)
                fy = y2 + rng.uniform(-largo * 0.3, largo * 0.5)
                r = rng.uniform(1.1, 3.0)
                p.append(f'<ellipse cx="{fx:.1f}" cy="{fy:.1f}" rx="{r:.2f}" '
                         f'ry="{r*0.66:.2f}" fill="{VIOLETA}" '
                         f'opacity="{rng.uniform(0.30,0.80):.2f}"/>')
        for _ in range(2):
            rama(x2, y2, ang + rng.uniform(-0.75, 0.75), largo * rng.uniform(0.52, 0.74),
                 grosor * 0.62, prof + 1)

    for k in range(9):
        ang = k / 9.0 * 2 * math.pi + rng.uniform(-0.2, 0.2)
        x0 = w * 0.5 + math.cos(ang) * w * 0.62
        y0 = w * 0.5 + math.sin(ang) * w * 0.62
        rama(x0, y0, math.atan2(w * 0.5 - y0, w * 0.5 - x0) + rng.uniform(-0.3, 0.3),
             w * 0.17, 2.6)
    p.append('</svg>')
    return ''.join(p)


def svg_letania(w=240):
    """LETANÍA — miles de flores idénticas repitiendo hasta volverse una sola.

    Una letanía es la misma frase dicha muchas veces hasta que deja de ser
    frase. El dibujo hace exactamente eso: una sola forma, repetida en rejilla,
    con variaciones tan chicas que de lejos se lee como textura y no como
    flores. De cerca vuelven a ser flores. Ese ir y venir ES la rola.
    """
    rng = np.random.default_rng(29)
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{w}" height="{w}" fill="{HUESO}"/>']
    paso = w / 17.0
    for fila in range(19):
        for col in range(19):
            # la rejilla se desfasa un poco fila con fila: no es cuadrícula
            cx = (col + (0.5 if fila % 2 else 0.0)) * paso + rng.uniform(-1.6, 1.6)
            cy = fila * paso * 0.86 + rng.uniform(-1.6, 1.6)
            if not (-paso < cx < w + paso and -paso < cy < w + paso):
                continue
            # se apaga hacia las orillas para que el centro mande
            d = math.hypot((cx - w / 2) / (w * 0.62), (cy - w / 2) / (w * 0.62))
            op = max(0.0, 0.88 - d * 0.78) * rng.uniform(0.72, 1.0)
            if op < 0.05:
                continue
            r = paso * rng.uniform(0.20, 0.30)
            ang = rng.uniform(0, 360)
            col_f = LILA if rng.random() < 0.30 else VIOLETA
            # la flor: cinco lóbulos, como la campana del jacarandá
            g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({ang:.0f})" '
                 f'fill="{col_f}" opacity="{op:.2f}">']
            for k in range(5):
                a = k / 5.0 * 2 * math.pi
                g.append(f'<ellipse cx="{math.cos(a)*r*0.52:.2f}" '
                         f'cy="{math.sin(a)*r*0.52:.2f}" rx="{r*0.46:.2f}" '
                         f'ry="{r*0.34:.2f}" transform="rotate({math.degrees(a):.0f} '
                         f'{math.cos(a)*r*0.52:.2f} {math.sin(a)*r*0.52:.2f})"/>')
            g.append('</g>')
            p.append(''.join(g))
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for nombre, gen in [('jacaranda', svg),
                        ('jacaranda-fulgor', svg_fulgor),
                        ('jacaranda-letania', svg_letania)]:
        dst = os.path.join(HERE, 'art', f'{nombre}.svg')
        s = gen()
        with open(dst, 'w') as f:
            f.write(s)
        print(f'{nombre:22s} {len(s)//1024:4d} KB')
