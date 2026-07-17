#!/usr/bin/env python3
"""Dibujos ELLA — el disco dedicado a una mujer: trazo rosa grueso + tinta + glow."""
import os

A = '#C4756B'    # rosa
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

# NOMBRE — la carta con su nombre adentro
ART['nombre'] = wrap('gno', f'''
  <rect x="72" y="108" width="96" height="62" rx="6" fill="none" stroke="{INK}" stroke-width="6"/>
  <path d="M74 112 L120 146 L166 112" fill="none" stroke="{A}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="120" cy="90" r="6" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="96" r="2.2" fill="{INK}"/><circle cx="180" cy="124" r="2.4" fill="{INK}"/>
''', gy=138)

# RISA — su risa: dos arcos que suben y chispas
ART['risa'] = wrap('gri', f'''
  <path d="M76 128 A44 44 0 0 0 164 128" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M92 112 A28 28 0 0 0 148 112" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="70" cy="104" r="4" fill="{AL}"/>
  <circle cx="170" cy="104" r="4" fill="{AL}"/>
  <circle cx="120" cy="76" r="3" fill="{A}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="150" r="2.2" fill="{INK}"/><circle cx="182" cy="146" r="2.4" fill="{INK}"/>
''', gy=120)

# BAILE — los dos bailando, inclinados uno hacia el otro
ART['baile'] = wrap('gba', f'''
  <ellipse cx="120" cy="206" rx="46" ry="7" fill="{INK}" opacity="0.05"/>
  <circle cx="103" cy="84" r="11" fill="{INK}"/>
  <path d="M103 96 C99 124 100 152 96 186 L110 186 C112 156 112 128 112 108 Z" fill="{INK}"/>
  <circle cx="140" cy="88" r="10" fill="{INK}"/>
  <path d="M140 99 C144 126 142 154 148 186 L131 186 C130 156 130 130 130 110 Z" fill="{INK}"/>
  <path d="M112 118 C120 112 124 112 130 118" fill="none" stroke="{A}" stroke-width="5" stroke-linecap="round"/>
  <circle cx="121" cy="112" r="4.5" fill="{A}"/>
  <path d="M74 96 L66 88 M170 100 L178 92" stroke="{AL}" stroke-width="3.5" stroke-linecap="round"/>
''', gy=130)

# SILENCIO — la luna sobre los dos puntos, el silencio compartido
ART['silencio'] = wrap('gsi', f'''
  <path d="M138 68 A38 38 0 1 0 138 136 A30 30 0 1 1 138 68 Z" fill="{A}"/>
  <circle cx="104" cy="164" r="5" fill="{INK}"/>
  <circle cx="128" cy="164" r="5" fill="{INK}"/>
  <circle cx="168" cy="84" r="2.6" fill="{AL}"/>
  <circle cx="80" cy="76" r="2.2" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="120" r="2.2" fill="{INK}"/><circle cx="182" cy="140" r="2.4" fill="{INK}"/>
''', gy=120)

# CAMPANAS — la campana de boda sonando: el pico
ART['campanas'] = wrap('gcm', f'''
  <path d="M120 76 C98 76 92 104 88 132 L152 132 C148 104 142 76 120 76 Z" fill="{A}"/>
  <rect x="112" y="66" width="16" height="12" rx="4" fill="{INK}"/>
  <circle cx="120" cy="144" r="8" fill="{INK}"/>
  <path d="M70 106 A54 54 0 0 1 82 82 M170 106 A54 54 0 0 0 158 82" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <path d="M58 122 A70 70 0 0 1 72 92 M182 122 A70 70 0 0 0 168 92" fill="none" stroke="{AL}" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="160" r="2.2" fill="{INK}"/><circle cx="178" cy="156" r="2.4" fill="{INK}"/>
''', gy=116)

# AMANECER — despertar junto a ella: el sol saliendo
ART['amanecer'] = wrap('gam', f'''
  <path d="M86 132 A34 34 0 0 1 154 132 Z" fill="{A}"/>
  <path d="M120 74 L120 62 M88 86 L80 78 M152 86 L160 78" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <rect x="46" y="130" width="148" height="5" rx="2.5" fill="{INK}"/>
  <path d="M78 158 L102 158 M116 158 L142 158" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <path d="M92 180 L112 180 M126 180 L148 180" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="70" cy="94" r="2.2" fill="{INK}"/><circle cx="174" cy="100" r="2.4" fill="{INK}"/>
''', gy=126)

os.makedirs('art', exist_ok=True)
for name, svg in ART.items():
    with open(f'art/ella-{name}.svg', 'w') as f:
        f.write(svg)
    print(f'art/ella-{name}.svg')
print('done')
