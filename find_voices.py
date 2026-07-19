#!/usr/bin/env python3
"""Encuentra las grabaciones con VOZ dentro del pack MusicBox de la Library of Congress.

El pack son 259 pasajes de ~30 s de música folk. Muchos son violín instrumental
(reels, hornpipes) y no sirven. Hay que separar voz de instrumento sin oírlos.

CÓMO: modulación silábica. La voz —hablada o cantada— tiene caídas de amplitud
al ritmo de las sílabas, que en toda lengua humana caen entre 2 y 8 Hz. Un violín
frotado no las tiene: su energía es continua. Así que se mide cuánta energía de
la ENVOLVENTE vive en la banda 2-8 Hz respecto al total.

Se refuerza con dos señales más:
  · presencia en la banda de formantes (300-3400 Hz), donde vive la inteligibilidad
  · caídas profundas de amplitud (silencios entre frases) — el violín no las hace

Uso: python3 find_voices.py            → ranking completo
     python3 find_voices.py 24         → los 24 mejores y arma la página de audición
"""
import os, sys, glob, subprocess
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, '_samples', 'musicbox')
SR = 22050


def decode(path, secs=30):
    raw = subprocess.run([FF, '-v', 'error', '-t', str(secs), '-i', path,
                          '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype='<f4')


def puntua(x):
    """Devuelve (score, detalle). Score alto = más probable que sea voz."""
    if len(x) < SR: return 0.0, {}
    x = x - x.mean()
    pk = float(np.abs(x).max())
    if pk < 1e-4: return 0.0, {}

    # --- envolvente de amplitud a 200 Hz de muestreo
    win = SR // 200
    n = (len(x) // win) * win
    env = np.abs(x[:n]).reshape(-1, win).mean(axis=1)
    env = env / (env.max() + 1e-12)
    fs_env = SR / win                                   # 200 Hz

    # 1) MODULACIÓN SILÁBICA: energía de la envolvente en 2-8 Hz
    e = env - env.mean()
    sp = np.abs(np.fft.rfft(e * np.hanning(len(e))))
    fr = np.fft.rfftfreq(len(e), 1.0 / fs_env)
    banda = sp[(fr >= 2.0) & (fr <= 8.0)].sum()
    total = sp[(fr >= 0.3) & (fr <= 30.0)].sum() + 1e-12
    silabas = float(banda / total)

    # 2) BANDA DE FORMANTES: proporción de energía en 300-3400 Hz
    W = 1 << 12
    acc = np.zeros(W // 2 + 1)
    for i in range(0, len(x) - W, W * 3):
        acc += np.abs(np.fft.rfft(x[i:i + W] * np.hanning(W)))
    f2 = np.fft.rfftfreq(W, 1.0 / SR)
    tot = acc.sum() + 1e-12
    formantes = float(acc[(f2 >= 300) & (f2 <= 3400)].sum() / tot)
    grave = float(acc[f2 < 300].sum() / tot)

    # 3) RESPIRA: fracción del tiempo por debajo del 12% del pico
    #    (huecos entre frases; el violín frotado no los hace)
    respira = float((env < 0.12).mean())

    score = silabas * 2.4 + formantes * 1.0 + min(respira, 0.45) * 1.2
    return score, dict(silabas=silabas, formantes=formantes, grave=grave, respira=respira)


def main():
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    fs = sorted(glob.glob(os.path.join(PACK, 'excerpts', '*.mp3')))
    if not fs:
        print('No encuentro los excerpts. ¿Se descomprimió el pack?'); return
    print(f'Analizando {len(fs)} pasajes en busca de VOZ…', flush=True)
    res = []
    for i, f in enumerate(fs):
        if i % 50 == 0 and i: print(f'  {i}/{len(fs)}', flush=True)
        s, d = puntua(decode(f))
        if s > 0: res.append((s, f, d))
    res.sort(reverse=True, key=lambda r: r[0])

    print(f'\n{"":4s} {"score":>5s} {"sílabas":>7s} {"formant":>7s} {"respira":>7s}  título')
    for i, (s, f, d) in enumerate(res[:max(top, 20)]):
        t = os.path.basename(f).split('_')[0].replace('-', ' ')[:44]
        print(f'{i+1:>3}. {s:5.2f} {d["silabas"]:7.3f} {d["formantes"]:7.3f} {d["respira"]:7.3f}  {t}')

    print(f'\n--- los 8 MENOS probables (deberían ser instrumentales) ---')
    for s, f, d in res[-8:]:
        t = os.path.basename(f).split('_')[0].replace('-', ' ')[:44]
        print(f'     {s:5.2f} {d["silabas"]:7.3f} {d["formantes"]:7.3f} {d["respira"]:7.3f}  {t}')

    if top:
        escribe_pagina(res[:top])


def escribe_pagina(res):
    """Página para audicionar los candidatos y quedarse con los buenos."""
    out = os.path.join(HERE, '_demo', 'voces.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    filas = []
    for i, (s, f, d) in enumerate(res):
        rel = os.path.relpath(f, HERE)
        base = os.path.basename(f)
        titulo = base.split('_')[0].replace('-', ' ')
        filas.append(
            f'<div class=row><div class=n>{i+1:02d}</div>'
            f'<div class=meta><b>{titulo}</b>'
            f'<span>score {s:.2f} · sílabas {d["silabas"]:.3f} · formantes {d["formantes"]:.3f}</span></div>'
            f'<audio controls preload=none src="../{rel}"></audio></div>')
    html = """<!doctype html><meta charset=utf-8><title>AMR — candidatos de voz</title>
<style>
 body{margin:0;background:#EDE9E1;color:#141210;font:14px/1.5 -apple-system,sans-serif;padding:32px}
 .wrap{max-width:820px;margin:0 auto}
 h1{font:400 34px/1.1 Georgia,serif;margin:6px 0 4px}
 .kick{font:600 11px/1 ui-monospace,Menlo,monospace;letter-spacing:3px;color:#6E675E;text-transform:uppercase}
 p.sub{color:#6E675E;max-width:60ch;margin:0 0 24px}
 .row{display:grid;grid-template-columns:34px 1fr 260px;gap:14px;align-items:center;
      padding:11px 0;border-top:1px solid rgba(20,18,16,.12)}
 .n{font:600 12px ui-monospace,Menlo,monospace;color:#6E5BAE}
 .meta b{display:block;font-weight:600}
 .meta span{font:11px ui-monospace,Menlo,monospace;color:#6E675E}
 audio{width:100%;height:32px}
 .note{margin-top:26px;font-size:12.5px;color:#6E675E;border-left:2px solid #6E5BAE;padding-left:14px;line-height:1.65}
</style><div class=wrap>
<div class=kick>Studio AMR · Library of Congress · MusicBox</div>
<h1>Candidatos de voz.</h1>
<p class=sub>Ordenados por un detector de modulación silábica: la voz humana tiene
caídas de amplitud entre 2 y 8 Hz (las sílabas), el violín frotado no. Los de arriba
deberían traer canto; si alguno es instrumental, el detector se equivocó ahí.</p>
""" + '\n'.join(filas) + """
<p class=note><b>Licencia:</b> libre de usar y reusar, incluso comercialmente, sin pedir
permiso. La atribución es recomendada pero no obligatoria. La American Folklife Center
pide que se traten estos materiales con respeto por la cultura de las personas
documentadas — vale la pena hacerle caso aunque no sea obligación legal.</p>
</div>"""
    open(out, 'w').write(html)
    print(f'\nPágina de audición: {out}')
    print('   http://localhost:4274/_demo/voces.html')


if __name__ == '__main__':
    main()
