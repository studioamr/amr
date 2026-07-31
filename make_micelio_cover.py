#!/usr/bin/env python3
"""Portada de MICELIO para SoundCloud = el mismo dibujo default del hongo
(make_micelio_art.py), a resolución de portada. Nada de cielo nocturno ni
texto encima — el ícono del catálogo tal cual: hongo tinta bold sobre hueso,
glow, sombra de piso, red de micelio, dos puntitos.

Se porta el SVG a PIL curva por curva (mismas bezier, mismo rng seed=37) para
que sea EL MISMO dibujo, no una reinterpretación — sólo más grande."""
import math
import numpy as np
from PIL import Image, ImageDraw

SC = 7                    # 240 unidades svg × 7 = 1680px
W = 240 * SC
HUESO = (234, 230, 223)   # --bone del sitio
TINTA = (20, 18, 16)      # --ink del sitio
TURQ = (18, 112, 122)
TURQ_L = (94, 212, 222)


def bez_cubic(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3*mt**2*t * p1[0] + 3*mt*t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3*mt**2*t * p1[1] + 3*mt*t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def bez_quad(p0, p1, p2, n=16):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**2 * p0[0] + 2*mt*t * p1[0] + t**2 * p2[0]
        y = mt**2 * p0[1] + 2*mt*t * p1[1] + t**2 * p2[1]
        pts.append((x, y))
    return pts


def S(pt):
    return (pt[0] * SC, pt[1] * SC)


def main():
    base = Image.new('RGB', (W, W), HUESO)
    ov = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # sombra de piso
    cx, cy, rx, ry = 120, 212, 56, 8
    d.ellipse([S((cx - rx, cy - ry)), S((cx + rx, cy + ry))], fill=TINTA + (13,))

    # glow turquesa detrás del sombrero (radial, como el radialGradient del svg)
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float64)
    gcx, gcy = S((120, 94))
    gr = 66 * SC
    dist = np.hypot(xx - gcx, yy - gcy) / gr
    a = np.clip(1 - dist, 0, 1) ** 1.4 * 107
    glow_mask = Image.fromarray(a.astype(np.uint8), 'L')
    glow_solid = Image.new('RGBA', (W, W), TURQ_L + (255,))
    ov = Image.alpha_composite(ov, Image.composite(glow_solid, Image.new('RGBA', (W, W), (0, 0, 0, 0)), glow_mask))
    d = ImageDraw.Draw(ov)

    # el sombrero: domo bold (dos bezier cúbicas, igual que el path del svg)
    dome = bez_cubic((70, 112), (70, 72), (96, 56), (120, 56)) + \
        bez_cubic((120, 56), (144, 56), (170, 72), (170, 112))
    d.polygon([S(p) for p in dome], fill=TINTA + (255,))

    # motas
    for cx_, cy_, r_ in [(101, 84, 5), (129, 73, 4), (143, 94, 4.5)]:
        d.ellipse([S((cx_ - r_, cy_ - r_)), S((cx_ + r_, cy_ + r_))], fill=TURQ_L + (217,))

    # laminillas
    for k in range(6):
        x = 80 + k * 16
        d.line([S((x, 112)), S((x, 119))], fill=TURQ + (255,), width=max(1, int(2.6 * SC)))

    # tallo
    d.rectangle([S((110, 112)), S((130, 148))], fill=TINTA + (255,))

    # línea de suelo
    d.rounded_rectangle([S((56, 148)), S((184, 153))], radius=int(2.5 * SC), fill=TURQ + (255,))

    # EL MICELIO: red recursiva bajo tierra — mismo rng seed que el svg original,
    # así el árbol de ramas sale idéntico, no una reinterpretación al azar
    rng = np.random.default_rng(37)

    def rama(x, y, ang, largo, prof=0):
        if largo < 6 or prof > 3:
            r2 = 1.8
            d.ellipse([S((x - r2, y - r2)), S((x + r2, y + r2))], fill=TURQ_L + (230,))
            return
        x2 = x + math.sin(ang) * largo
        y2 = y + math.cos(ang) * largo * 0.75
        xm = x + math.sin(ang) * largo * 0.5
        ym = y + math.cos(ang) * largo * 0.45
        pts = [S(p) for p in bez_quad((x, y), (xm, ym), (x2, y2))]
        op = int((0.75 - prof * 0.12) * 255)
        wd = max(1, int(max(1.2, 3.2 - prof) * SC))
        d.line(pts, fill=TURQ + (op,), width=wd, joint='curve')
        for dd in (-0.55, 0.5):
            rama(x2, y2, ang + dd * float(rng.uniform(0.7, 1.3)),
                 largo * float(rng.uniform(0.55, 0.72)), prof + 1)

    for a in (-0.9, -0.35, 0.3, 0.85):
        rama(120 + a * 8, 153, a, 30)

    # dos puntitos de acento, como todo el catálogo
    d.ellipse([S((60 - 2.2, 96 - 2.2)), S((60 + 2.2, 96 + 2.2))], fill=TINTA + (255,))
    d.ellipse([S((184 - 2.4, 130 - 2.4)), S((184 + 2.4, 130 + 2.4))], fill=TINTA + (255,))

    out = Image.alpha_composite(base.convert('RGBA'), ov).convert('RGB')
    dst = 'art/micelio-cover.png'
    out.save(dst, 'PNG')
    import os
    print(f'{dst} · {out.size} · {os.path.getsize(dst)//1024} KB')


if __name__ == '__main__':
    main()
