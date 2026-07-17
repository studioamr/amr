#!/usr/bin/env python3
"""Dibujos CANTERA — la piedra rosa de Morelia: trazo rosa grueso + tinta + glow."""
import os

A = '#C4756B'    # rosa cantera
AL = '#E2A796'   # rosa claro
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

# BLOQUE — el bloque recién cortado de la veta
ART['bloque'] = wrap('gbl', f'''
  <rect x="76" y="104" width="88" height="64" rx="6" fill="{A}"/>
  <rect x="76" y="104" width="88" height="20" rx="6" fill="{AL}"/>
  <path d="M92 140 L104 140 M116 152 L134 152 M140 132 L152 132" stroke="#8A4A42" stroke-width="4" stroke-linecap="round"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="96" r="2.2" fill="{INK}"/><circle cx="180" cy="120" r="2.4" fill="{INK}"/>
''', gy=138)

# CINCEL — el golpe diagonal y la chispa
ART['cincel'] = wrap('gci', f'''
  <path d="M70 170 L134 106" stroke="{INK}" stroke-width="11" stroke-linecap="round"/>
  <path d="M134 106 L150 90" stroke="{A}" stroke-width="11" stroke-linecap="round"/>
  <circle cx="160" cy="80" r="6" fill="{AL}"/>
  <path d="M170 66 L176 60 M172 84 L180 82 M156 62 L158 54" stroke="{AL}" stroke-width="3.5" stroke-linecap="round"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="100" r="2.2" fill="{INK}"/><circle cx="184" cy="140" r="2.4" fill="{INK}"/>
''', gy=124)

# TALLER — el mazo sobre el bloque, el primer golpe del set
ART['taller'] = wrap('gta', f'''
  <rect x="88" y="140" width="64" height="36" rx="5" fill="{A}"/>
  <path d="M120 128 L120 96" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>
  <rect x="96" y="70" width="48" height="26" rx="7" fill="{INK}"/>
  <path d="M76 120 L66 110 M164 120 L174 110" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="88" r="2.2" fill="{INK}"/><circle cx="182" cy="150" r="2.4" fill="{INK}"/>
''', gy=130)

# CATEDRAL — las dos torres de Morelia, simplificadas
ART['catedral'] = wrap('gca', f'''
  <path d="M84 176 L84 100 L96 82 L108 100 L108 176" fill="{INK}"/>
  <path d="M132 176 L132 100 L144 82 L156 100 L156 176" fill="{INK}"/>
  <path d="M108 176 L108 136 A12 16 0 0 1 132 136 L132 176" fill="{A}"/>
  <circle cx="96" cy="106" r="3.5" fill="{AL}"/>
  <circle cx="144" cy="106" r="3.5" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="92" r="2.2" fill="{INK}"/><circle cx="178" cy="112" r="2.4" fill="{INK}"/>
''', gy=130)

# CAMPANAS — la campana rosa sonando, el pico del set
ART['campanas'] = wrap('gcm', f'''
  <path d="M120 76 C98 76 92 104 88 132 L152 132 C148 104 142 76 120 76 Z" fill="{A}"/>
  <rect x="112" y="66" width="16" height="12" rx="4" fill="{INK}"/>
  <circle cx="120" cy="144" r="8" fill="{INK}"/>
  <path d="M70 106 A54 54 0 0 1 82 82 M170 106 A54 54 0 0 0 158 82" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <path d="M58 122 A70 70 0 0 1 72 92 M182 122 A70 70 0 0 0 168 92" fill="none" stroke="{AL}" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="160" r="2.2" fill="{INK}"/><circle cx="178" cy="156" r="2.4" fill="{INK}"/>
''', gy=116)

# PLAZA — los portales: tres arcos de cantera
ART['plaza'] = wrap('gpl', f'''
  <path d="M60 176 L60 128 A18 18 0 0 1 96 128 L96 176" fill="none" stroke="{A}" stroke-width="9"/>
  <path d="M102 176 L102 128 A18 18 0 0 1 138 128 L138 176" fill="none" stroke="{A}" stroke-width="9"/>
  <path d="M144 176 L144 128 A18 18 0 0 1 180 128 L180 176" fill="none" stroke="{A}" stroke-width="9"/>
  <path d="M54 106 L186 106" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>
  <circle cx="120" cy="156" r="4" fill="{INK}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="86" r="2.2" fill="{INK}"/><circle cx="178" cy="90" r="2.4" fill="{INK}"/>
''', gy=140)

os.makedirs('art', exist_ok=True)
for name, svg in ART.items():
    with open(f'art/cant-{name}.svg', 'w') as f:
        f.write(svg)
    print(f'art/cant-{name}.svg')
print('done')
