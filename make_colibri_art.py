#!/usr/bin/env python3
"""Dibujos COLIBRÍ — turquesa tropical iridiscente + coral néctar (fórmula de trazo)."""
import os
A = '#12B3AE'    # turquesa colibrí
AL = '#6FE0D8'   # turquesa claro
CO = '#FF7A6B'   # coral néctar
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
# ALBA — el sol naciente con rayos
ART['alba'] = wrap('gal', f'''
  <path d="M86 132 A34 34 0 0 1 154 132 Z" fill="{A}"/>
  <path d="M120 74 L120 62 M88 86 L80 78 M152 86 L160 78 M62 118 L52 116 M178 118 L188 116" stroke="{CO}" stroke-width="4" stroke-linecap="round"/>
  <rect x="46" y="132" width="148" height="5" rx="2.5" fill="{INK}"/>
  <path d="M78 158 L104 158 M116 158 L142 158" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="66" cy="96" r="2.2" fill="{INK}"/><circle cx="176" cy="100" r="2.4" fill="{INK}"/>
''', gy=126)
# NECTAR — flor de campana con gota
ART['nectar'] = wrap('gne', f'''
  <path d="M120 92 C100 92 92 112 92 126 C92 140 104 148 120 148 C136 148 148 140 148 126 C148 112 140 92 120 92 Z" fill="{CO}"/>
  <path d="M120 148 L120 100" stroke="{INK}" stroke-width="4"/>
  <circle cx="120" cy="86" r="7" fill="{A}"/>
  <path d="M120 158 C116 164 116 170 120 174 C124 170 124 164 120 158 Z" fill="{AL}"/>
  <path d="M92 130 C82 130 78 138 78 146 M148 130 C158 130 162 138 162 146" fill="none" stroke="{A}" stroke-width="4" stroke-linecap="round"/>
  <rect x="46" y="182" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="100" r="2.2" fill="{INK}"/><circle cx="178" cy="118" r="2.4" fill="{INK}"/>
''', gy=130)
# POLEN — partículas flotando en aire
ART['polen'] = wrap('gpo', f'''
  <circle cx="90" cy="100" r="9" fill="{A}"/><circle cx="90" cy="100" r="15" fill="{A}" opacity="0.22"/>
  <circle cx="150" cy="86" r="6" fill="{CO}"/><circle cx="150" cy="86" r="11" fill="{CO}" opacity="0.22"/>
  <circle cx="132" cy="130" r="7" fill="{AL}"/><circle cx="132" cy="130" r="12" fill="{AL}" opacity="0.22"/>
  <circle cx="76" cy="146" r="5" fill="{CO}"/><circle cx="168" cy="140" r="5" fill="{A}"/>
  <circle cx="112" cy="72" r="4" fill="{AL}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="108" r="2.2" fill="{INK}"/><circle cx="184" cy="112" r="2.4" fill="{INK}"/>
''', gy=118)
# VUELO — el colibrí volando (perfil, pico largo, alas)
ART['vuelo'] = wrap('gvu', f'''
  <ellipse cx="122" cy="118" rx="24" ry="15" fill="{A}" transform="rotate(-18 122 118)"/>
  <path d="M104 110 L64 96" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
  <circle cx="132" cy="108" r="4" fill="{INK}"/>
  <path d="M128 132 C138 148 150 154 158 150 M132 128 C146 138 160 138 168 130" fill="none" stroke="{CO}" stroke-width="5" stroke-linecap="round"/>
  <path d="M118 106 C100 92 92 78 96 68 C108 74 120 86 126 100 Z" fill="{AL}"/>
  <path d="M138 128 L150 150 M144 124 L160 142" stroke="{A}" stroke-width="4" stroke-linecap="round" opacity="0.5"/>
  <rect x="46" y="182" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="150" r="2.2" fill="{INK}"/><circle cx="184" cy="90" r="2.4" fill="{INK}"/>
''', gy=118)
# CENOTE — ondas de agua concéntricas + gota
ART['cenote'] = wrap('gce', f'''
  <ellipse cx="120" cy="140" rx="72" ry="26" fill="none" stroke="{INK}" stroke-width="4"/>
  <ellipse cx="120" cy="140" rx="46" ry="16" fill="none" stroke="{A}" stroke-width="4"/>
  <ellipse cx="120" cy="140" rx="22" ry="8" fill="none" stroke="{AL}" stroke-width="3.5"/>
  <path d="M120 88 C116 96 116 104 120 110 C124 104 124 96 120 88 Z" fill="{CO}"/>
  <circle cx="70" cy="90" r="2.2" fill="{INK}"/><circle cx="172" cy="94" r="2.4" fill="{INK}"/>
''', gy=140)
# FIESTA — destellos/confeti (el pico)
ART['fiesta'] = wrap('gfi', f'''
  <path d="M120 70 L126 96 L152 102 L126 108 L120 134 L114 108 L88 102 L114 96 Z" fill="{CO}"/>
  <path d="M74 118 L78 130 L90 134 L78 138 L74 150 L70 138 L58 134 L70 130 Z" fill="{A}"/>
  <path d="M166 116 L170 128 L182 132 L170 136 L166 148 L162 136 L150 132 L162 128 Z" fill="{AL}"/>
  <circle cx="96" cy="80" r="3.5" fill="{A}"/><circle cx="148" cy="150" r="3.5" fill="{CO}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="150" r="2.2" fill="{INK}"/><circle cx="184" cy="90" r="2.4" fill="{INK}"/>
''', gy=116)
# SELVA — hojas de palma
ART['selva'] = wrap('gse', f'''
  <path d="M120 176 L120 96" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
  <path d="M120 108 C96 96 78 98 62 110 C82 116 104 116 120 108 Z" fill="{A}"/>
  <path d="M120 108 C144 96 162 98 178 110 C158 116 136 116 120 108 Z" fill="{AL}"/>
  <path d="M120 132 C100 122 84 124 70 134 C88 140 106 140 120 132 Z" fill="{A}"/>
  <path d="M120 132 C140 122 156 124 170 134 C152 140 134 140 120 132 Z" fill="{AL}"/>
  <circle cx="120" cy="90" r="5" fill="{CO}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="100" r="2.2" fill="{INK}"/><circle cx="184" cy="116" r="2.4" fill="{INK}"/>
''', gy=126)
# NIDO — el nido redondo con huevos
ART['nido'] = wrap('gni', f'''
  <path d="M72 150 A48 30 0 0 0 168 150 Z" fill="{A}"/>
  <path d="M72 150 A48 30 0 0 1 168 150" fill="none" stroke="{INK}" stroke-width="4"/>
  <ellipse cx="106" cy="150" rx="9" ry="11" fill="{AL}"/>
  <ellipse cx="128" cy="152" rx="9" ry="11" fill="{CO}"/>
  <path d="M60 148 C68 142 76 148 84 144 M156 144 C164 148 172 142 180 148" stroke="{INK}" stroke-width="3" stroke-linecap="round" opacity="0.5"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="110" r="2.2" fill="{INK}"/><circle cx="184" cy="120" r="2.4" fill="{INK}"/>
''', gy=140)

os.makedirs('art', exist_ok=True)
for name, svg in ART.items():
    open(f'art/coli-{name}.svg', 'w').write(svg)
    print(f'art/coli-{name}.svg')
print('done')
