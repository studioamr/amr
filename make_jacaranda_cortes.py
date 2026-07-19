#!/usr/bin/env python3
"""Cortes sueltos de JACARANDA — dos rolas para escuchar sin bajarse el set entero.

Se sacan del MASTER del set, no de los originales de Gemini: así el corte suena
idéntico a como suena dentro de la mezcla. Los límites caen en compás exacto
(2.000 s a 120 BPM) y con medio segundo de fundido en cada punta, porque un
corte a hueso truena.
"""
import os, json, subprocess
from dream_core import FF

HERE = os.path.dirname(os.path.abspath(__file__))
SET = os.path.join(HERE, '_jacaranda', '_tmp', 'jacaranda-set.wav')

# cuáles y por qué: FULGOR es la floración a contraluz; LETANÍA es la de la
# repetición. Los límites se recalcularon al volver EPIFANÍA al set — los de
# antes apuntaban a otras rolas.
CORTES = [
    ('fulgor',  320.0,  480.0),
    ('letania', 480.0,  630.0),
]

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    for nom, ini, fin in CORTES:
        dur = fin - ini
        dst = os.path.join(HERE, 'audio', f'amr-jacaranda-cut-{nom}.m4a')
        subprocess.run([
            FF, '-y', '-v', 'error', '-ss', f'{ini}', '-t', f'{dur}', '-i', SET,
            '-af', f'afade=t=in:st=0:d=0.5,afade=t=out:st={dur-0.5}:d=0.5,'
                   'aformat=sample_fmts=fltp:sample_rates=44100',
            '-c:a', 'aac_at', '-b:a', '192k', '-movflags', '+faststart', dst],
            check=True, capture_output=True)
        print(f'{nom:12s} {ini:6.1f}–{fin:6.1f}s  {dur:5.1f}s  '
              f'{os.path.getsize(dst)//1024} KB')
