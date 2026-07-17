#!/usr/bin/env python3
"""Dibujos MAREA — mismo lenguaje que GUERRERO (tinta + acento + glow), violeta bruma."""
import os

A = '#6E5BAE'    # violeta bruma
AL = '#9D8BD6'   # violeta claro
INK = '#141210'

def wrap(gid, inner, gy=150):
    return f'''<svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="{gid}" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{A}" stop-opacity="0.42"/>
    <stop offset="55%" stop-color="{A}" stop-opacity="0.14"/>
    <stop offset="100%" stop-color="{A}" stop-opacity="0"/>
  </radialGradient></defs>
  <circle cx="120" cy="{gy}" r="52" fill="url(#{gid})"/>
{inner}
</svg>'''

ART = {}

ART['marejada'] = wrap('gma', f'''
  <path d="M60 176 A66 66 0 0 1 126 110 A30 30 0 0 1 156 140 A16 16 0 0 1 140 156 A8 8 0 0 1 132 148" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M84 176 A44 44 0 0 1 118 134" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="76" cy="92" r="2.2" fill="{INK}"/><circle cx="182" cy="108" r="2.4" fill="{INK}"/>
''', gy=134)

ART['serpiente'] = wrap('gse', f'''
  <path d="M48 152 A24 24 0 0 1 96 152 A24 24 0 0 0 144 152 A16 16 0 0 1 162 140" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M60 152 A12 12 0 0 1 84 152" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="167" cy="133" r="9.5" fill="{INK}"/>
  <circle cx="170" cy="130" r="2.2" fill="#EAE6DF"/>
  <path d="M175 127 L185 120" stroke="{AL}" stroke-width="3" stroke-linecap="round"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="66" cy="100" r="2.2" fill="{INK}"/><circle cx="182" cy="164" r="2.4" fill="{INK}"/>
''', gy=140)

ART['brisa'] = wrap('gbr', f'''
  <path d="M52 118 A80 80 0 0 1 148 100 A15 15 0 0 1 146 128" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M62 152 A70 70 0 0 1 150 140" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="166" cy="104" r="3.5" fill="{A}"/>
  <circle cx="170" cy="140" r="2.6" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="88" r="2.2" fill="{INK}"/><circle cx="180" cy="164" r="2.4" fill="{INK}"/>
''', gy=130)

ART['coral'] = wrap('gco', f'''
  <path d="M78 176 A42 42 0 0 1 162 176" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M96 176 A24 24 0 0 1 144 176" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <path d="M120 134 L120 116 M90 146 L79 135 M150 146 L161 135" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
  <circle cx="120" cy="110" r="5" fill="{A}"/>
  <circle cx="75" cy="130" r="4" fill="{AL}"/>
  <circle cx="165" cy="130" r="4" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="96" r="2.2" fill="{INK}"/><circle cx="184" cy="100" r="2.4" fill="{INK}"/>
''', gy=146)

ART['luciernaga'] = wrap('glu', f'''
  <path d="M60 162 A52 52 0 0 1 124 100 A18 18 0 0 1 146 122" fill="none" stroke="{A}" stroke-width="6" stroke-linecap="round" stroke-dasharray="1 13"/>
  <circle cx="150" cy="126" r="8" fill="{A}"/><circle cx="150" cy="126" r="15" fill="{A}" opacity="0.25"/>
  <circle cx="84" cy="108" r="4" fill="{AL}"/><circle cx="84" cy="108" r="8" fill="{AL}" opacity="0.25"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="180" cy="96" r="2.2" fill="{INK}"/><circle cx="64" cy="188" r="0" fill="{INK}"/>
''', gy=126)

ART['cenote'] = wrap('gce', f'''
  <circle cx="120" cy="128" r="42" fill="none" stroke="{A}" stroke-width="9"/>
  <circle cx="120" cy="128" r="24" fill="none" stroke="{INK}" stroke-width="5"/>
  <path d="M120 54 L120 100" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="120" cy="128" r="5" fill="{INK}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="92" r="2.2" fill="{INK}"/><circle cx="180" cy="102" r="2.4" fill="{INK}"/>
''', gy=128)

os.makedirs('art', exist_ok=True)
for name, svg in ART.items():
    with open(f'art/marea-{name}.svg', 'w') as f:
        f.write(svg)
    print(f'art/marea-{name}.svg')
print('done')
