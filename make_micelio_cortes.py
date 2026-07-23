#!/usr/bin/env python3
"""Cortes sueltos de MICELIO — dos rolas para oír sin bajarse el set entero.

Salen del MASTER del set (no de los originales de Gemini), así el corte suena
igual que dentro de la mezcla. Límites en compás exacto y medio segundo de
fundido en cada punta, que un corte a hueso truena.
"""
import os, subprocess
from dream_core import FF

HERE = os.path.dirname(os.path.abspath(__file__))
SET = os.path.join(HERE, '_micelio', '_tmp', 'micelio-set.wav')

# cuáles y por qué: MICELIO es el pico del disco (la red se enciende bajo tus
# pies); RAUDAL es la del agua, el momento más líquido y juguetón. Los tiempos
# salen de los offsets medidos del set.
CORTES = [
    ('micelio', 630.0,  788.0),
    ('raudal',  314.0,  472.0),
]

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    for nom, ini, fin in CORTES:
        dur = fin - ini
        dst = os.path.join(HERE, 'audio', f'amr-micelio-cut-{nom}.m4a')
        subprocess.run([
            FF, '-y', '-v', 'error', '-ss', f'{ini}', '-t', f'{dur}', '-i', SET,
            '-af', f'afade=t=in:st=0:d=0.5,afade=t=out:st={dur-0.5}:d=0.5,'
                   'aformat=sample_fmts=fltp:sample_rates=44100',
            '-c:a', 'aac_at', '-b:a', '192k', '-movflags', '+faststart', dst],
            check=True, capture_output=True)
        print(f'{nom:10s} {ini:6.1f}–{fin:6.1f}s  {dur:5.1f}s  {os.path.getsize(dst)//1024} KB')
