#!/usr/bin/env python3
"""Arma la canción completa con lo elegido en el taller. 208 compases, 6:56.

La estructura NO la inventé: sale de medir los discos de Keinemusik.
"The Rapture Pt.III" son 6:58 ≈ 208 compases a 120 BPM, y 208 = 13×16.

Reglas del género aplicadas aquí (ver memoria afro-house-arreglo):
  · todo cambio de sección cae en múltiplo de 16
  · ⭐ ENTRAR ≠ SONAR COMPLETO: cada sección tiene un valor `abre` 0..1 que
    controla cuánto abren los filtros. Un elemento entra tapado y se revela a
    lo largo de 16-32 compases. La fuente lo llama "la diferencia más grande
    entre el arreglo de afro house y el de house genérico".
  · sin drop grande — la energía es una rampa con UN hundimiento
  · el breakdown NUNCA se vacía: se va el kick, la percusión sigue corriendo
"""
import os, json, subprocess
import numpy as np
import imageio_ffmpeg
from dream_core import (SR, wav_write, sat, master_file, ffmeter, ffdecode,
                        spectrum_pct)
import taller as T

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_taller', 'render'); os.makedirs(TMP, exist_ok=True)

# nombre, compases, cuánto abren los filtros, y qué se apaga
SECCIONES = [
 dict(n='INTRO',      bars=32, abre=0.30, sin=('bajo','gancho','voz')),
 dict(n='ENTRADA',    bars=32, abre=0.55, sin=('voz',)),
 dict(n='GROOVE',     bars=32, abre=0.85, sin=('voz',)),
 dict(n='CUERPO',     bars=32, abre=1.00, sin=()),
 dict(n='BREAKDOWN',  bars=32, abre=0.70, sin=('kick','bajo')),   # la perc SIGUE
 dict(n='CUMBRE',     bars=32, abre=1.00, sin=()),
 dict(n='SALIDA',     bars=16, abre=0.45, sin=('gancho','voz')),
]

def main(dec):
    falta = [e for e in T.ETAPAS if e not in dec['elegido']]
    if falta:
        print(f'Faltan etapas por elegir: {", ".join(falta)}')
        print(f'  → python3 taller.py {falta[0]}')
        return
    tot = sum(s['bars'] for s in SECCIONES)
    print(f'Armando la canción · {tot} compases · {tot*T.SPB/SR/60:.2f} min · '
          f'{dec["bpm"]} BPM {dec["tono"]}', flush=True)
    print('  ' + ' · '.join(f'{k}={v}' for k,v in dec['elegido'].items()), flush=True)

    partes = []
    for i, s in enumerate(SECCIONES):
        print(f'  … {s["n"]:10s} {s["bars"]:>3} comp   filtros {s["abre"]*100:3.0f}%'
              f'{"   sin " + ", ".join(s["sin"]) if s["sin"] else ""}', flush=True)
        d2 = json.loads(json.dumps(dec))
        for q in s['sin']:
            if q in d2['elegido']: d2['elegido'][q] = 'ninguna' if q == 'voz' else d2['elegido'][q]
        x = T.bloque(d2, bars=s['bars'], seed=21 + i*5, abre=s['abre'])
        # apagar buses que esta sección no lleva (el bloque los rinde igual)
        if 'kick' in s['sin'] or 'bajo' in s['sin']:
            # el breakdown se hace quitando el grave, no silenciando todo
            from dream_core import hp
            x = np.stack([hp(x[0], 150.0, 2), hp(x[1], 150.0, 2)]) * 0.88
        partes.append(x)

    print('  … uniendo', flush=True)
    out = np.concatenate(partes, axis=1)
    out = np.stack([sat(out[0],1.10,0.02), sat(out[1],1.10,0.02)])
    out *= 0.90/max(1e-9, float(np.abs(out).max()))

    raw = os.path.join(TMP, 'raw.wav'); wav_write(raw, out); del out
    os.makedirs(os.path.join(HERE,'masters'), exist_ok=True)
    titulo = (dec.get('titulo') or 'taller').lower()
    final = os.path.join(HERE, 'masters', f'amr-{titulo}.wav')
    hist = master_file(raw, final, target_i=-10.4, ceiling_db=-1.0)
    os.remove(raw)
    I, lra, tp = ffmeter(final)
    m4a = os.path.join(HERE, '_taller', f'{titulo}.m4a')
    subprocess.run([FF,'-y','-v','error','-i',final,'-c:a','aac_at','-b:a','256k',
                    '-movflags','+faststart',m4a], check=True)
    print(f'\nMASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}')
    print(f'ESPECTRO: {spectrum_pct(ffdecode(final, mono=True))}')
    print(f'\n  {m4a}')
    print(f'  http://localhost:4274/_taller/{titulo}.m4a')
