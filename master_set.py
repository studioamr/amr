#!/usr/bin/env python3
# AMR — masteriza THE SET (EQ + glue + loudness) y regenera m4a + peaks + set.js + portada.
# No re-mezcla: parte del WAV master ya crossfadeado. Corre con /usr/local/bin/python3.
import os, subprocess, json, re, wave
import numpy as np, imageio_ffmpeg
import make_set

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
WAV = os.path.join(HERE, 'masters', 'amr-set-the-set.wav')
MWAV = os.path.join(HERE, 'masters', 'amr-set-mastered.wav')
M4A = os.path.join(HERE, 'audio', 'amr-set-the-set.m4a')

# cadena de mastering: limpieza sub + curva EQ + glue compresor + loudness club + limitador
CHAIN = (
    "highpass=f=24,"                                             # quita rumble sub-audible
    "equalizer=f=55:t=q:w=0.9:g=1.5,"                            # peso de sub
    "equalizer=f=200:t=q:w=1.4:g=-2,"                            # despeja el barro
    "equalizer=f=3000:t=q:w=1.2:g=1,"                            # presencia
    "equalizer=f=9000:t=h:w=0.7:g=2.5,"                          # aire
    "acompressor=threshold=-15dB:ratio=2.2:attack=25:release=260:makeup=2.5,"  # glue del bus
    "loudnorm=I=-10:TP=-1.0:LRA=11,"                             # loudness de club, caliente
    "alimiter=level_in=1:level_out=0.97:limit=0.97:attack=5:release=60"        # techo seguro
)

def sec_of(wavpath):
    info = subprocess.run([FF, '-i', wavpath], capture_output=True, text=True).stderr
    m = re.search(r'Duration: (\d+):(\d+):(\d+)', info)
    return int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) if m else 0

if __name__ == '__main__':
    print('Masterizando el set (EQ + glue + loudness)…', flush=True)
    r = subprocess.run([FF, '-y', '-i', WAV, '-af', CHAIN, '-c:a', 'pcm_s16le', MWAV],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print('ERROR:\n', r.stderr[-2500:]); raise SystemExit(1)
    secs = sec_of(MWAV)
    print(f'master WAV: {secs//60}:{secs%60:02d}  ({os.path.getsize(MWAV)//1024//1024} MB)')
    # m4a web 128k desde el master
    subprocess.run([FF, '-y', '-i', MWAV, '-c:a', 'aac', '-b:a', '128k', M4A], capture_output=True)
    print(f'm4a: {os.path.getsize(M4A)//1024//1024} MB')
    # peaks del master
    w = wave.open(MWAV); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float).reshape(-1, 2).mean(axis=1)
    W = 720; seg = len(x)//W
    pk = np.abs(x[:seg*W]).reshape(W, seg).max(axis=1)
    pk = (pk/pk.max()).round(3).tolist()
    # conservar titles/tracks del set.js actual
    meta = json.loads(open(os.path.join(HERE, 'set.js')).read().split('=', 1)[1].rstrip(';\n'))
    meta['peaks'] = pk; meta['dur'] = secs
    with open(os.path.join(HERE, 'set.js'), 'w') as f:
        f.write('window.AMR_SET=' + json.dumps(meta) + ';\n')
    print('set.js actualizado (peaks masterizados)')
    make_set.make_cover(pk, meta['tracks'], secs)
    print('portada vinilo regenerada')
    print('LISTO')
