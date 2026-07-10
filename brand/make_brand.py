#!/usr/bin/env python3
# AMR — foto de perfil (1000x1000) + banner (2480x520) estilo PLINTH/MONUMENTS.
# Rasteriza con qlmanage. Fuentes del sistema (Georgia / Courier New) para nitidez garantizada.
import os, math, subprocess

BONE='#EAE6DF'; BONE2='#e0dad1'; INK='#141210'; AMBER='#A62D3E'; MUT='#6E675E'; NIGHT='#16130f'
HERE=os.path.dirname(os.path.abspath(__file__))

def grooves(cx, cy, r0, r1, step, color, op):
    out=[]
    r=r0
    i=0
    while r<=r1:
        o=op*(0.5 if i%2 else 1.0)
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{color}" stroke-width="1.1" opacity="{o:.2f}"/>')
        r+=step; i+=1
    return ''.join(out)

# ---------------- AVATAR 1000x1000 (un vinilo AMR) ----------------
def avatar():
    W=1000; cx=cy=500; R=496
    s=[f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">']
    s.append('<defs>')
    s.append('<radialGradient id="disc" cx="42%" cy="38%" r="75%">'
             '<stop offset="0%" stop-color="#221d18"/><stop offset="55%" stop-color="#18140f"/>'
             '<stop offset="100%" stop-color="#0e0b08"/></radialGradient>')
    s.append('<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1">'
             '<stop offset="0%" stop-color="#ffffff" stop-opacity="0.10"/>'
             '<stop offset="38%" stop-color="#ffffff" stop-opacity="0"/>'
             '<stop offset="62%" stop-color="#ffffff" stop-opacity="0"/>'
             '<stop offset="100%" stop-color="#ffffff" stop-opacity="0.05"/></linearGradient>')
    s.append('<radialGradient id="lblg" cx="50%" cy="50%" r="50%">'
             f'<stop offset="0%" stop-color="#C24C5C"/><stop offset="100%" stop-color="{AMBER}"/></radialGradient>')
    s.append('</defs>')
    # fondo hueso (por si el recorte deja un aro)
    s.append(f'<rect width="{W}" height="{W}" fill="{BONE}"/>')
    # disco
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#disc)"/>')
    # surcos
    s.append(grooves(cx, cy, 210, R-6, 6.5, '#3a332b', 0.55))
    # brillo diagonal
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#sheen)"/>')
    # anillo de separación label
    s.append(f'<circle cx="{cx}" cy="{cy}" r="200" fill="none" stroke="#0c0a07" stroke-width="6"/>')
    # etiqueta ámbar
    s.append(f'<circle cx="{cx}" cy="{cy}" r="192" fill="url(#lblg)"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="192" fill="none" stroke="#7d1f2e" stroke-width="2"/>')
    # arco superior mono
    s.append(f'<path id="arcTop" d="M {cx-150} {cy} A 150 150 0 0 1 {cx+150} {cy}" fill="none"/>')
    s.append('<text font-family="Courier New, monospace" font-size="27" font-weight="bold" letter-spacing="7" '
             f'fill="{INK}" opacity="0.85"><textPath href="#arcTop" startOffset="50%" text-anchor="middle">MONUMENTS</textPath></text>')
    # AMR grande serif
    s.append(f'<text x="{cx}" y="{cy+38}" font-family="Georgia, serif" font-weight="bold" font-size="150" '
             f'letter-spacing="4" fill="{INK}" text-anchor="middle">AMR</text>')
    # arco inferior mono
    s.append(f'<path id="arcBot" d="M {cx-150} {cy} A 150 150 0 0 0 {cx+150} {cy}" fill="none"/>')
    s.append('<text font-family="Courier New, monospace" font-size="23" letter-spacing="6" '
             f'fill="{INK}" opacity="0.7"><textPath href="#arcBot" startOffset="50%" text-anchor="middle">FIVE RECORDS</textPath></text>')
    # hoyo central
    s.append(f'<circle cx="{cx}" cy="{cy}" r="21" fill="{BONE}"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="21" fill="none" stroke="#00000030" stroke-width="2"/>')
    s.append('</svg>')
    return ''.join(s)

# ---- monumentos abstractos raros, estilo blueprint MONUMENTS (tinta temblorosa + halo ámbar) ----
def mono_obelisk(x, s):
    return (f'<rect x="{x-22*s:.0f}" y="{92}" width="{44*s:.0f}" height="{300*s:.0f}" rx="{6*s:.0f}" '
            f'fill="{INK}" transform="rotate(-4 {x} 240)"/>')
def mono_sphere(x, y, s):
    ink=f'<circle cx="{x}" cy="{y+70*s:.0f}" r="{9*s:.0f}" fill="{INK}"/>'  # núcleo
    ink+=f'<rect x="{x-40*s:.0f}" y="{y+120*s:.0f}" width="{80*s:.0f}" height="{26*s:.0f}" rx="4" fill="{INK}"/>'  # pedestal
    return ink
def mono_strata(x, y, s):
    out=''
    ws=[120,104,80,58];
    for i,w in enumerate(ws):
        yy=y+ (len(ws)-1-i)*30*s
        fill = AMBER if i==1 else INK
        out+=f'<rect x="{x-w*s/2:.0f}" y="{yy:.0f}" width="{w*s:.0f}" height="{24*s:.0f}" rx="4" fill="{fill}"/>'
    return out
def mono_vessel(x, y, s):
    d=(f'M {x-34*s:.0f} {y-40*s:.0f} '
       f'C {x-34*s:.0f} {y+2*s:.0f} {x-54*s:.0f} {y+22*s:.0f} {x-54*s:.0f} {y+70*s:.0f} '
       f'C {x-54*s:.0f} {y+118*s:.0f} {x-30*s:.0f} {y+140*s:.0f} {x} {y+140*s:.0f} '
       f'C {x+30*s:.0f} {y+140*s:.0f} {x+54*s:.0f} {y+118*s:.0f} {x+54*s:.0f} {y+70*s:.0f} '
       f'C {x+54*s:.0f} {y+22*s:.0f} {x+34*s:.0f} {y+2*s:.0f} {x+34*s:.0f} {y-40*s:.0f} Z')
    return f'<path d="{d}" fill="{INK}"/>'
def mono_monolith(x, y, s):
    out=f'<rect x="{x-26*s:.0f}" y="{y-150*s:.0f}" width="{52*s:.0f}" height="{300*s:.0f}" rx="6" fill="{INK}"/>'
    out+=f'<rect x="{x-34*s:.0f}" y="{y-4*s:.0f}" width="{68*s:.0f}" height="{10*s:.0f}" fill="{AMBER}"/>'
    return out
def mono_prism(x, y, s):
    return f'<path d="M {x} {y-70*s:.0f} L {x+62*s:.0f} {y+70*s:.0f} L {x-62*s:.0f} {y+70*s:.0f} Z" fill="{INK}"/>'
def mono_arch(x, y, s):
    r=90*s
    d=f'M {x-r:.0f} {y+r:.0f} L {x-r:.0f} {y:.0f} A {r:.0f} {r:.0f} 0 0 1 {x+r:.0f} {y:.0f} L {x+r:.0f} {y+r:.0f}'
    out=f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{14*s:.0f}" stroke-linecap="round" stroke-dasharray="{2*s:.0f} {26*s:.0f}"/>'
    out+=f'<circle cx="{x}" cy="{y+18*s:.0f}" r="{16*s:.0f}" fill="{AMBER}"/>'
    return out
def mono_moon(x, y, s):
    r=70*s
    return (f'<circle cx="{x}" cy="{y}" r="{r:.0f}" fill="{INK}"/>'
            f'<circle cx="{x+26*s:.0f}" cy="{y-8*s:.0f}" r="{r:.0f}" fill="{BONE}"/>')
def mono_column(x, y, s):
    out=''
    for i in range(5):
        out+=f'<rect x="{x-24*s:.0f}" y="{y-140*s+ i*58*s:.0f}" width="{48*s:.0f}" height="{46*s:.0f}" rx="4" fill="{INK}"/>'
    return out

# ---------------- BANNER 2480x520 — friso de monumentos abstractos ----------------
def banner():
    W=2480; H=520
    s=[f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    s.append('<defs>')
    s.append('<radialGradient id="orb" cx="42%" cy="40%" r="62%">'
             f'<stop offset="0%" stop-color="#C24C5C"/><stop offset="100%" stop-color="{AMBER}"/></radialGradient>')
    # halo difuso via degradado (nítido a cualquier resolución, sin filtro)
    s.append('<radialGradient id="halosoft" cx="50%" cy="50%" r="50%">'
             f'<stop offset="0%" stop-color="{AMBER}" stop-opacity="0.45"/>'
             f'<stop offset="55%" stop-color="{AMBER}" stop-opacity="0.14"/>'
             f'<stop offset="100%" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>')
    s.append('</defs>')

    # papel hueso
    s.append(f'<rect width="{W}" height="{H}" fill="{BONE}"/>')
    cx = W/2

    # ---- HALOS ámbar difusos (degradado, no blur) detrás de algunos monumentos ----
    halos = [(360,180,150),(770,235,120),(1700,215,135),(2230,180,155),(cx,250,300)]
    for hx,hy,hr in halos:
        s.append(f'<circle cx="{hx}" cy="{hy}" r="{hr}" fill="url(#halosoft)"/>')

    # ---- monumentos raros de fondo (formas limpias, HD) ----
    s.append('<g opacity="0.92">')
    s.append(mono_obelisk(150, 1.05))
    s.append(mono_sphere(360, 110, 1.15))
    s.append(mono_strata(560, 250, 1.15))
    s.append(mono_arch(770, 200, 1.15))
    s.append(mono_column(2350, 250, 1.0))
    s.append(mono_moon(2210, 170, 1.15))
    s.append(mono_prism(2050, 250, 1.1))
    s.append(mono_monolith(1880, 250, 1.05))
    s.append(mono_vessel(1700, 190, 1.1))
    s.append('</g>')

    # esferas ámbar sólidas (núcleos PLINTH) encima de sus halos
    for ox,oy,orr in [(360,180,30),(2230,180,30)]:
        s.append(f'<circle cx="{ox}" cy="{oy}" r="{orr}" fill="url(#orb)"/>')
        s.append(f'<circle cx="{ox}" cy="{oy}" r="{orr*0.4:.0f}" fill="{INK}"/>')

    # ---- puntitos de tinta dispersos (firma blueprint) ----
    import random
    random.seed(9)
    for _ in range(70):
        gx = random.uniform(40, W-40); gy = random.uniform(30, H-30)
        if abs(gx-cx) < 300 and 150 < gy < 360:  # despeja el wordmark
            continue
        s.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{random.uniform(1.4,4.5):.1f}" fill="{INK}" opacity="{random.uniform(0.5,0.9):.2f}"/>')

    # ---- placa hueso semitransparente para asentar el wordmark ----
    s.append(f'<rect x="{cx-330}" y="212" width="660" height="150" fill="{BONE}" opacity="0.72"/>')

    # ---- wordmark AMR + tagline ----
    s.append(f'<text x="{cx}" y="300" font-family="Georgia, serif" font-weight="bold" font-size="118" '
             f'letter-spacing="14" fill="{INK}" text-anchor="middle">AMR</text>')
    s.append(f'<line x1="{cx-150}" y1="322" x2="{cx+150}" y2="322" stroke="{AMBER}" stroke-width="3"/>')
    s.append(f'<text x="{cx}" y="352" font-family="Courier New, monospace" font-size="19" letter-spacing="8" '
             f'fill="{MUT}" text-anchor="middle">MONUMENTS<tspan fill="{AMBER}">  ·  </tspan>FIVE RECORDS<tspan fill="{AMBER}">  ·  </tspan>ONE SOUND</text>')

    # ---- esquinas mono ----
    s.append(f'<text x="70" y="60" font-family="Courier New, monospace" font-size="24" letter-spacing="6" fill="{MUT}">AMR — MORELIA, MX</text>')
    s.append(f'<text x="{W-70}" y="60" font-family="Courier New, monospace" font-size="24" letter-spacing="6" fill="{AMBER}" text-anchor="end">EST. MMXXVI</text>')
    s.append('</svg>')
    return ''.join(s)

def raster(name, svg, out_w, out_h, ss=3):
    """Rasteriza con supersampling ss× via qlmanage y baja a out_w×out_h con LANCZOS.
    qlmanage mete el SVG en un lienzo cuadrado (preserveAspectRatio meet); recortamos la banda."""
    from PIL import Image
    svgp=os.path.join(HERE, name+'.svg'); open(svgp,'w').write(svg)
    N = out_w*ss
    subprocess.run(['qlmanage','-t','-s',str(N),'-o',HERE,svgp], capture_output=True)
    raw=os.path.join(HERE, name+'.svg.png')
    im=Image.open(raw).convert('RGB')
    Wc,Hc=im.size  # cuadrado NxN
    band_h=round(Wc*out_h/out_w)
    y0=round((Hc-band_h)/2)
    im=im.crop((0,y0,Wc,y0+band_h)).resize((out_w,out_h), Image.LANCZOS)
    dst=os.path.join(HERE, name+'.png'); im.save(dst); os.remove(raw)
    return dst

if __name__=='__main__':
    a=raster('amr-avatar', avatar(), 1000, 1000, ss=3)
    b=raster('amr-banner', banner(), 2480, 520, ss=3)
    for p in (a,b):
        r=subprocess.run(['sips','-g','pixelWidth','-g','pixelHeight',p], capture_output=True, text=True).stdout
        dims=' '.join(x.split(':')[-1].strip() for x in r.strip().splitlines() if 'pixel' in x)
        print(os.path.basename(p), dims, os.path.getsize(p)//1024,'KB')
