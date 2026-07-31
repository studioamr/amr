#!/usr/bin/env python3
"""Portada de PURPURINA para SoundCloud = el mismo dibujo del catálogo
(make_purpurina_art.py) a resolución de portada, sobre el hueso de la casa.

Se porta el SVG a PIL con el MISMO rng seed (19) para que las facetas, los
espejitos que caen y la purpurina del piso queden idénticos al ícono del
catálogo — es el mismo dibujo, sólo más grande, no una reinterpretación.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

SC = 7                      # 240 unidades svg × 7 = 1680 px
W = 240 * SC
HUESO = (234, 230, 223)
TINTA = (20, 18, 16)
ORO = (185, 138, 46)
ORO_L = (242, 212, 121)

CX, CY, R = 118, 104, 52


def S(v):
    return v * SC


def main():
    base = Image.new('RGB', (W, W), HUESO)
    ov = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    rng = np.random.default_rng(19)      # mismo seed que el SVG

    # sombra de piso
    d.ellipse([S(120 - 76), S(206 - 8), S(120 + 76), S(206 + 8)], fill=TINTA + (13,))

    # glow dorado detrás de la bola
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float64)
    dist = np.hypot(xx - S(CX), yy - S(CY)) / S(72)
    a = np.clip(1 - dist, 0, 1) ** 1.5 * 117
    glow = Image.fromarray(a.astype(np.uint8), 'L')
    solid = Image.new('RGBA', (W, W), ORO_L + (255,))
    ov = Image.alpha_composite(ov, Image.composite(
        solid, Image.new('RGBA', (W, W), (0, 0, 0, 0)), glow))
    d = ImageDraw.Draw(ov)

    # cable y argolla
    d.rectangle([S(CX - 2), S(16), S(CX + 2), S(CY - R - 10)], fill=TINTA + (255,))
    d.ellipse([S(CX - 6), S(CY - R - 12), S(CX + 6), S(CY - R)],
              outline=TINTA + (255,), width=int(S(4)))

    # LA BOLA en su propia capa, para poder aplicarle la máscara que la
    # deshilacha hacia la derecha (igual que el linearGradient del SVG)
    bola = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    db = ImageDraw.Draw(bola)
    db.ellipse([S(CX - R), S(CY - R), S(CX + R), S(CY + R)], fill=TINTA + (255,))
    for iy in range(-4, 5):
        yy_ = CY + iy * 11.5
        ancho = math.sqrt(max(0.0, R * R - (iy * 11.5) ** 2))
        nx = max(1, int(ancho / 11.5))
        for ix in range(-nx, nx + 1):
            xx_ = CX + ix * 11.5
            if (xx_ - CX) ** 2 / (R * .98) ** 2 + (yy_ - CY) ** 2 / (R * .98) ** 2 > 1:
                continue
            r = rng.random()
            if r < 0.16:
                db.rounded_rectangle([S(xx_ - 4.6), S(yy_ - 4.6), S(xx_ + 4.6),
                                      S(yy_ + 4.6)], radius=int(S(1.4)), fill=ORO_L + (255,))
            elif r < 0.34:
                db.rounded_rectangle([S(xx_ - 4.6), S(yy_ - 4.6), S(xx_ + 4.6),
                                      S(yy_ + 4.6)], radius=int(S(1.4)), fill=ORO + (140,))

    # máscara horizontal: opaca hasta 46 %, se desvanece hacia la derecha
    grad = np.zeros((W, W), dtype=np.uint8)
    col = np.clip((1.0 - (np.arange(W) / W - 0.46) / 0.54), 0, 1) * 255
    grad[:, :] = col.astype(np.uint8)[None, :]
    bola.putalpha(Image.fromarray(
        (np.array(bola.split()[3]) * (grad / 255.0)).astype(np.uint8), 'L'))
    ov = Image.alpha_composite(ov, bola)
    d = ImageDraw.Draw(ov)

    # LOS ESPEJITOS QUE SE VAN: salen del borde derecho, girando y cayendo
    for i in range(11):
        t = i / 10.0
        x = CX + R * 0.55 + t * 76 + float(rng.uniform(-6, 6))
        y = CY - 16 + t * t * 96 + float(rng.uniform(-8, 8))
        s = 8.4 * (1 - t * 0.55)
        rot = float(rng.uniform(0, 90))
        colr = ORO_L if i % 3 == 0 else ORO
        op = int((0.9 - t * 0.35) * 255)
        chip = Image.new('RGBA', (int(S(s * 1.6)),) * 2, (0, 0, 0, 0))
        ImageDraw.Draw(chip).rounded_rectangle(
            [S(s * 0.3), S(s * 0.3), S(s * 1.3), S(s * 1.3)],
            radius=int(S(1.2)), fill=colr + (op,))
        chip = chip.rotate(rot, resample=Image.BICUBIC)
        ov.alpha_composite(chip, (int(S(x) - chip.width / 2), int(S(y) - chip.height / 2)))
    d = ImageDraw.Draw(ov)

    # línea de piso
    d.rounded_rectangle([S(26), S(192), S(214), S(197)], radius=int(S(2.5)),
                        fill=ORO + (255,))

    # LA PURPURINA YA CAÍDA
    for i in range(16):
        x = 34 + float(rng.uniform(0, 172))
        y = 198 + float(rng.uniform(0, 12))
        s = float(rng.uniform(3.0, 6.4))
        colr = ORO_L if i % 4 == 0 else ORO
        op = int(float(rng.uniform(0.35, 0.8)) * 255)
        rot = float(rng.uniform(-30, 30))
        chip = Image.new('RGBA', (int(S(s * 2)),) * 2, (0, 0, 0, 0))
        ImageDraw.Draw(chip).rounded_rectangle(
            [S(s * 0.5), S(s * 0.5), S(s * 1.5), S(s * 1.1)],
            radius=int(S(0.8)), fill=colr + (op,))
        chip = chip.rotate(rot, resample=Image.BICUBIC)
        ov.alpha_composite(chip, (int(S(x)), int(S(y))))
    d = ImageDraw.Draw(ov)

    # dos puntitos de acento, como todo el catálogo
    d.ellipse([S(44 - 2.4), S(66 - 2.4), S(44 + 2.4), S(66 + 2.4)], fill=TINTA + (255,))
    d.ellipse([S(206 - 2.2), S(150 - 2.2), S(206 + 2.2), S(150 + 2.2)], fill=TINTA + (255,))

    out = Image.alpha_composite(base.convert('RGBA'), ov).convert('RGB')
    dst = 'art/purpurina-cover.png'
    out.save(dst, 'PNG')
    import os
    print(f'{dst} · {out.size} · {os.path.getsize(dst)//1024} KB')


if __name__ == '__main__':
    main()
