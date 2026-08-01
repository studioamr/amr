#!/usr/bin/env python3
"""Parte la SESIÓN 003 en tres actos que sí se pueden publicar.

POR QUÉ POR PARTES
  El set completo pesa 211 MB y GitHub rechaza cualquier archivo de más de
  100 MB — no es una preferencia, es un límite duro que hace fallar el push.
  Tres actos de ~61 min a 160k dan ~73 MB cada uno y entran con margen.

DÓNDE CORTA
  NO a los 61 minutos exactos: eso caería a media rola. Corta en el offset de
  pieza más cercano al tercio, que es donde el set ya cambia de tema — así cada
  acto abre y cierra en una transición real y no en un tajo.

  Además los actos coinciden con la forma del set, que fue diseñada en dos
  picos con un valle en medio:
      ACTO I   la subida y el primer pico
      ACTO II  el valle y la reconstrucción
      ACTO III el segundo pico y el descenso
"""
import os, json, re, subprocess
from dream_core import FF, ffmeter

HERE = os.path.dirname(os.path.abspath(__file__))
SET = os.path.join(HERE, '_sesion003', '_tmp', 'sesion003.wav')
AUDIO = os.path.join(HERE, 'audio')
N_PARTES = 3
BITRATE = '160k'
LIMITE_MB = 100

ACTOS = [
    ('i',   'ACTO I',   'La subida y el primer pico'),
    ('ii',  'ACTO II',  'El valle, y la reconstrucción'),
    ('iii', 'ACTO III', 'El segundo pico y el descenso'),
]


def trim_medido(src, ini, dur, dst):
    """Codifica midiendo el true peak del AAC real y bajando hasta cumplir —
    el mismo lazo del set completo: el códec sobrepasa y hay que medirlo."""
    trim = 0.0
    for _ in range(4):
        subprocess.run([
            FF, '-y', '-v', 'error', '-ss', f'{ini}', '-t', f'{dur}', '-i', src,
            '-af', f'volume={trim:.2f}dB,'
                   f'afade=t=in:st=0:d=1.5,afade=t=out:st={dur-2.0}:d=2.0,'
                   'aformat=sample_fmts=fltp:sample_rates=44100',
            '-c:a', 'aac_at', '-b:a', BITRATE, '-movflags', '+faststart', dst],
            check=True, capture_output=True)
        _, _, tp = ffmeter(dst)
        if tp <= -1.2:
            return trim, tp
        trim += (-1.5 - tp)
    return trim, tp


if __name__ == '__main__':
    js = open(os.path.join(HERE, 'sesion003.js')).read()
    meta = json.loads(js.split('=', 1)[1].rstrip(';\n '))
    offs = meta['offsets']
    total = meta['dur']

    # los dos puntos de corte: el offset de pieza más cercano a cada tercio
    cortes = [0.0]
    for k in (1, 2):
        ideal = total * k / N_PARTES
        cortes.append(min(offs, key=lambda o: abs(o - ideal)))
    cortes.append(total)

    print(f'set {total/60:.1f} min · cortando en offsets de pieza reales\n')
    partes = []
    for i, (slug, titulo, desc) in enumerate(ACTOS):
        ini, fin = cortes[i], cortes[i + 1]
        dur = fin - ini
        dst = os.path.join(AUDIO, f'amr-sesion003-{slug}.m4a')
        trim, tp = trim_medido(SET, ini, dur, dst)
        mb = os.path.getsize(dst) / 1024 / 1024
        I, lra, _ = ffmeter(dst)
        ok = 'OK' if mb < LIMITE_MB else f'¡PASA DE {LIMITE_MB} MB!'
        print(f'{titulo:9s} {ini/60:6.1f}–{fin/60:6.1f} min  {dur/60:5.1f} min  '
              f'{mb:6.1f} MB  {I:6.1f} LUFS  TP {tp:+.1f}  {ok}')
        partes.append(dict(slug=slug, title=titulo, desc=desc,
                           dur=round(dur, 1), ini=round(ini, 1),
                           file=f'audio/amr-sesion003-{slug}.m4a',
                           mb=round(mb, 1)))

    with open(os.path.join(HERE, 'sesion003-partes.json'), 'w') as f:
        json.dump(partes, f, indent=1, ensure_ascii=False)
    print(f'\ntotal publicable: {sum(p["mb"] for p in partes):.0f} MB en '
          f'{len(partes)} archivos (ninguno pasa de {LIMITE_MB} MB)')
