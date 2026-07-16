#!/usr/bin/env python3
"""Genera tomas de producto (packshots) del vinilo saliendo de su funda, por lanzamiento."""
import os

def grooves(cx, cy, r0, r1, step=7):
    out = []
    r = r0
    i = 0
    while r < r1:
        op = 0.5 if i % 2 == 0 else 0.25
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="#2a241d" stroke-width="1.1" opacity="{op}"/>')
        r += step
        i += 1
    return "".join(out)

def shot(accent, accent_lt, title, sub, edition, num, mark_svg, tsize=58):
    W, H = 1600, 1200
    # funda (jacket) — cuadrada, ligeramente rotada
    jx, jy, js = 250, 300, 620
    jcx, jcy = jx + js/2, jy + js/2
    # disco — detrás, sale por la derecha
    dcx, dcy, dr = 1080, 600, 300
    lbl = 108  # radio etiqueta
    return f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#F2EEE7"/><stop offset="60%" stop-color="#EAE4DA"/><stop offset="100%" stop-color="#DED7CB"/>
    </linearGradient>
    <radialGradient id="disc" cx="40%" cy="36%" r="72%">
      <stop offset="0%" stop-color="#25201a"/><stop offset="55%" stop-color="#161209"/><stop offset="100%" stop-color="#0b0906"/>
    </radialGradient>
    <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fff" stop-opacity="0.12"/><stop offset="42%" stop-color="#fff" stop-opacity="0"/>
      <stop offset="60%" stop-color="#fff" stop-opacity="0"/><stop offset="100%" stop-color="#fff" stop-opacity="0.06"/>
    </linearGradient>
    <radialGradient id="lblg" cx="46%" cy="40%" r="60%">
      <stop offset="0%" stop-color="{accent_lt}"/><stop offset="100%" stop-color="{accent}"/>
    </radialGradient>
    <linearGradient id="jacket" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0%" stop-color="#F6F2EB"/><stop offset="100%" stop-color="#E7E0D4"/>
    </linearGradient>
    <radialGradient id="vig" cx="50%" cy="46%" r="70%">
      <stop offset="0%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity="0.06"/>
    </radialGradient>
  </defs>

  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#vig)"/>

  <!-- sombra del disco -->
  <ellipse cx="{dcx}" cy="{dcy+dr+30}" rx="{dr*0.86:.0f}" ry="26" fill="#14120f" opacity="0.10"/>

  <!-- DISCO (detrás de la funda) -->
  <g>
    <circle cx="{dcx}" cy="{dcy}" r="{dr}" fill="url(#disc)"/>
    {grooves(dcx, dcy, lbl+22, dr-8)}
    <circle cx="{dcx}" cy="{dcy}" r="{dr}" fill="url(#sheen)"/>
    <circle cx="{dcx}" cy="{dcy}" r="{lbl+6}" fill="none" stroke="#0b0906" stroke-width="4"/>
    <circle cx="{dcx}" cy="{dcy}" r="{lbl}" fill="url(#lblg)"/>
    <circle cx="{dcx}" cy="{dcy}" r="{lbl}" fill="none" stroke="#000" stroke-opacity="0.25" stroke-width="1.5"/>
    <text x="{dcx}" y="{dcy-16}" font-family="'IBM Plex Mono',monospace" font-size="15" letter-spacing="3" fill="#EAE6DF" text-anchor="middle" opacity="0.9">STUDIO AMR</text>
    <text x="{dcx}" y="{dcy+12}" font-family="Georgia,serif" font-weight="bold" font-size="26" fill="#EAE6DF" text-anchor="middle">{title[:9]}</text>
    <text x="{dcx}" y="{dcy+34}" font-family="'IBM Plex Mono',monospace" font-size="12" letter-spacing="2" fill="#EAE6DF" text-anchor="middle" opacity="0.8">45 RPM</text>
    <circle cx="{dcx}" cy="{dcy}" r="7" fill="#EAE6DF"/>
  </g>

  <!-- sombra de la funda -->
  <ellipse cx="{jcx-10}" cy="{jy+js+34}" rx="{js*0.52:.0f}" ry="30" fill="#14120f" opacity="0.12"/>

  <!-- FUNDA impresa (jacket) -->
  <g transform="rotate(-4 {jcx} {jcy})">
    <rect x="{jx}" y="{jy}" width="{js}" height="{js}" rx="8" fill="url(#jacket)" stroke="#141210" stroke-opacity="0.12" stroke-width="2"/>
    <rect x="{jx}" y="{jy}" width="{js}" height="{js}" rx="8" fill="none" stroke="#141210" stroke-opacity="0.06" stroke-width="10" transform="translate(0,0)"/>
    <!-- borde interior tipo apertura de funda a la derecha -->
    <line x1="{jx+js-2}" y1="{jy+18}" x2="{jx+js-2}" y2="{jy+js-18}" stroke="#141210" stroke-opacity="0.10" stroke-width="3"/>
    <text x="{jx+38}" y="{jy+66}" font-family="'IBM Plex Mono',monospace" font-size="20" letter-spacing="6" fill="#6E675E">STUDIO AMR</text>
    <text x="{jx+js-38}" y="{jy+66}" font-family="'IBM Plex Mono',monospace" font-size="20" letter-spacing="6" fill="{accent}" text-anchor="end">MMXXVI</text>
    <!-- marca / dibujo -->
    <g transform="translate({jx+js/2-120} {jy+120}) scale(1.0)">{mark_svg}</g>
    <text x="{jcx}" y="{jy+js-96}" font-family="Georgia,serif" font-weight="bold" font-size="{tsize}" letter-spacing="1" fill="#141210" text-anchor="middle">{title}</text>
    <text x="{jcx}" y="{jy+js-58}" font-family="'IBM Plex Mono',monospace" font-size="15" letter-spacing="4" fill="{accent}" text-anchor="middle">{sub}</text>
    <text x="{jcx}" y="{jy+js-32}" font-family="'IBM Plex Mono',monospace" font-size="12" letter-spacing="3" fill="#6E675E" text-anchor="middle">EDITION OF {edition} · NUMBERED BY HAND</text>
  </g>

  <!-- etiqueta de número escrita a mano (kraft) -->
  <g transform="rotate(6 1330 980)">
    <rect x="1180" y="930" width="300" height="120" rx="4" fill="#DcCfb6" stroke="#141210" stroke-opacity="0.18" stroke-width="1.5"/>
    <circle cx="1205" cy="990" r="7" fill="none" stroke="#141210" stroke-opacity="0.35" stroke-width="2"/>
    <text x="1250" y="978" font-family="'IBM Plex Mono',monospace" font-size="16" letter-spacing="3" fill="#6E675E">HAND-NUMBERED</text>
    <text x="1250" y="1022" font-family="Georgia,serif" font-weight="bold" font-size="34" fill="#141210">No {num} / {edition}</text>
  </g>
</svg>'''

MONO_MARK = '<rect x="96" y="20" width="48" height="150" rx="5" fill="#141210"/><rect x="90" y="86" width="60" height="4" fill="#C96F2B"/>'
SUN_MARK  = '<circle cx="120" cy="96" r="46" fill="#2E6FB0" opacity="0.25"/><circle cx="120" cy="96" r="30" fill="#2E6FB0"/><rect x="60" y="150" width="120" height="7" rx="3" fill="#141210"/><rect x="74" y="166" width="92" height="6" rx="3" fill="#141210" opacity="0.6"/>'
ARCS_MARK = '<circle cx="120" cy="150" r="12" fill="#A62D3E"/>' + "".join(f'<path d="M {120-40-i*16} 150 A {40+i*16} {40+i*16} 0 0 1 {120+40+i*16} 150" fill="none" stroke="#A62D3E" stroke-width="{3-i*0.4:.1f}" opacity="{0.7-i*0.13:.2f}"/>' for i in range(4))

QUEDATE_MARK = '<circle cx="104" cy="86" r="13" fill="#141210"/><path d="M92 180 C88 152 90 128 96 112 C99 103 110 104 111 114 C112 134 110 158 108 180 Z" fill="#141210"/><path d="M111 122 C124 116 138 112 152 112" fill="none" stroke="#141210" stroke-width="7" stroke-linecap="round"/><circle cx="160" cy="110" r="6.5" fill="#2F8C77"/><path d="M160 110 C170 104 180 100 190 98" fill="none" stroke="#2F8C77" stroke-width="3" stroke-linecap="round" stroke-dasharray="2 8"/>'

TRI_MARK = '<circle cx="70" cy="100" r="34" fill="#141210"/><circle cx="70" cy="100" r="12" fill="#C96F2B"/><circle cx="120" cy="100" r="34" fill="#141210"/><circle cx="120" cy="100" r="12" fill="#A62D3E"/><circle cx="170" cy="100" r="34" fill="#141210"/><circle cx="170" cy="100" r="12" fill="#2E6FB0"/>'

SHOTS = [
    dict(id='megaset',   accent='#C96F2B', accent_lt='#e0954f', title='MEGA SET',  sub='ALL THREE RECORDS · 3H37', edition=10, num='02', mark=TRI_MARK, tsize=54),
    dict(id='monuments', accent='#C96F2B', accent_lt='#e0954f', title='MONUMENTS', sub='THE EP · 5 CUTS',   edition=50, num='07', mark=MONO_MARK, tsize=50),
    dict(id='tulum',     accent='#2E6FB0', accent_lt='#5B9BD5', title='DELIRIO',   sub='IN SYNC · 16 CUTS',  edition=15, num='04', mark=SUN_MARK,  tsize=54),
    dict(id='sesion',    accent='#A62D3E', accent_lt='#c8495e', title='SESIÓN 001',sub='THE SET · 19 CUTS',  edition=25, num='11', mark=ARCS_MARK, tsize=52),
]

os.makedirs('art/shots', exist_ok=True)
for s in SHOTS:
    svg = shot(s['accent'], s['accent_lt'], s['title'], s['sub'], s['edition'], s['num'], s['mark'], s['tsize'])
    with open(f"art/shots/shot-{s['id']}.svg", 'w') as f:
        f.write(svg)
    print(f"art/shots/shot-{s['id']}.svg")
print("done")
