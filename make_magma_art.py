#!/usr/bin/env python3
"""Dibujos MAGMA — lava sobre grid futurista: trazo grueso lava + circuitos + tinta."""
import os

A = '#E04E1A'    # lava
AL = '#FF8A4C'   # lava brillante
INK = '#141210'

def wrap(gid, inner, gy=140):
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

# CIRCUITO — traza de circuito con nodos, la corriente arranca
ART['circuito'] = wrap('gci', f'''
  <path d="M52 156 L88 156 L88 112 L136 112 L136 148 L172 148" fill="none" stroke="{A}" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>
  <path d="M64 130 L100 130 L100 92 L124 92" fill="none" stroke="{AL}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="52" cy="156" r="6.5" fill="{INK}"/>
  <circle cx="172" cy="148" r="6.5" fill="{A}"/>
  <circle cx="124" cy="92" r="4" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="88" r="2.2" fill="{INK}"/><circle cx="182" cy="106" r="2.4" fill="{INK}"/>
''', gy=132)

# NUCLEO — el reactor: anillo de tinta, centro fundido, órbita
ART['nucleo'] = wrap('gnu', f'''
  <circle cx="120" cy="126" r="42" fill="none" stroke="{INK}" stroke-width="5"/>
  <circle cx="120" cy="126" r="19" fill="{A}"/>
  <circle cx="120" cy="126" r="8" fill="{AL}"/>
  <circle cx="120" cy="126" r="30" fill="none" stroke="{AL}" stroke-width="2.5" stroke-dasharray="3 10"/>
  <circle cx="156" cy="102" r="5" fill="{A}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="92" r="2.2" fill="{INK}"/><circle cx="180" cy="150" r="2.4" fill="{INK}"/>
''', gy=126)

# FOTON — el pulso de luz cruzando el grid
ART['foton'] = wrap('gfo', f'''
  <path d="M54 150 L118 108" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M62 164 L106 136" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="138" cy="96" r="11" fill="{A}"/>
  <circle cx="138" cy="96" r="19" fill="{A}" opacity="0.25"/>
  <circle cx="160" cy="82" r="4" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="66" cy="96" r="2.2" fill="{INK}"/><circle cx="180" cy="140" r="2.4" fill="{INK}"/>
''', gy=120)

# CRATER — la boca del volcán respirando calor, sin erupción
ART['crater'] = wrap('gcr', f'''
  <path d="M96 108 L74 176 M144 108 L166 176" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>
  <path d="M96 108 L144 108" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M104 92 C110 84 130 84 136 92" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <path d="M110 76 C114 71 126 71 130 76" fill="none" stroke="{AL}" stroke-width="3" stroke-linecap="round" opacity="0.6"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="100" r="2.2" fill="{INK}"/><circle cx="182" cy="118" r="2.4" fill="{INK}"/>
''', gy=120)

# ERUPCION — el pico del set: la columna revienta
ART['erupcion'] = wrap('ger', f'''
  <path d="M98 112 L72 176 M142 112 L168 176" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>
  <path d="M120 128 L120 62" fill="none" stroke="{A}" stroke-width="10" stroke-linecap="round"/>
  <path d="M120 84 L100 58 M120 84 L140 58" fill="none" stroke="{A}" stroke-width="7" stroke-linecap="round"/>
  <circle cx="94" cy="48" r="4.5" fill="{AL}"/>
  <circle cx="146" cy="48" r="4.5" fill="{AL}"/>
  <circle cx="120" cy="50" r="3.5" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="120" r="2.2" fill="{INK}"/><circle cx="184" cy="132" r="2.4" fill="{INK}"/>
''', gy=110)

# RIO — el río de lava serpenteando a casa
ART['rio'] = wrap('gri', f'''
  <path d="M50 108 A22 22 0 0 1 94 108 A22 22 0 0 0 138 108 A22 22 0 0 1 182 108" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M62 144 A18 18 0 0 1 98 144 A18 18 0 0 0 134 144 A18 18 0 0 1 170 144" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="182" cy="108" r="5.5" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="86" r="2.2" fill="{INK}"/><circle cx="178" cy="164" r="2.4" fill="{INK}"/>
''', gy=126)

os.makedirs('art', exist_ok=True)
for name, svg in ART.items():
    with open(f'art/magma-{name}.svg', 'w') as f:
        f.write(svg)
    print(f'art/magma-{name}.svg')
print('done')
