#!/usr/bin/env python3
"""Cortes sueltos de PURPURINA — dos rolas para oír sin bajarse el set entero.

Salen del MASTER del set (no de los originales de Gemini), así el corte suena
igual que dentro de la mezcla. Límites en compás exacto y medio segundo de
fundido en cada punta, que un corte a hueso truena.

Cuáles y por qué: VESTIDOR es la apertura y es la rara del disco — no tiene
bombo casi hasta el final, es la única que se puede oír sola sin que se sienta
que le falta la pista. SALÓN es lo contrario: el momento más físico, la pista
llena. Los dos extremos del disco en dos cortes.

Los tiempos salen de los offsets MEDIDOS del set (purpurina.js), corridos hacia
adentro para no arrancar a media transición:
    VESTIDOR  0.0 → 167.0     SALÓN  470.4 → 631.7
"""
import os, subprocess
from dream_core import FF

HERE = os.path.dirname(os.path.abspath(__file__))
SET = os.path.join(HERE, '_purpurina', '_tmp', 'purpurina-set.wav')

CORTES = [
    ('vestidor',   1.0, 166.0),
    ('salon',    471.0, 631.0),
]

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    for nom, ini, fin in CORTES:
        dur = fin - ini
        dst = os.path.join(HERE, 'audio', f'amr-purpurina-cut-{nom}.m4a')
        subprocess.run([
            FF, '-y', '-v', 'error', '-ss', f'{ini}', '-t', f'{dur}', '-i', SET,
            '-af', f'afade=t=in:st=0:d=0.5,afade=t=out:st={dur-0.5}:d=0.5,'
                   'aformat=sample_fmts=fltp:sample_rates=44100',
            '-c:a', 'aac_at', '-b:a', '192k', '-movflags', '+faststart', dst],
            check=True, capture_output=True)
        print(f'{nom:10s} {ini:6.1f}–{fin:6.1f}s  {dur:5.1f}s  '
              f'{os.path.getsize(dst)//1024} KB')
