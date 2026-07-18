#!/usr/bin/env python3
"""Auditoría técnica del catálogo Studio AMR — números duros, sin opinión.

Streaming: procesa en bloques de 30 s con memoria plana (un set de 3 h son 476 M
de muestras; cargarlo entero y hacerle una FFT reventaba el swap).

Mide: LUFS-I (BS.1770 con gating doble), LRA, sample peak, crest, BPM, tonalidad,
ancho estéreo, evolución (¿loop o desarrollo?), densidad de transientes y balance
espectral en 6 bandas.
"""
import os, subprocess, json, sys
import numpy as np, imageio_ffmpeg
from numpy.lib.stride_tricks import sliding_window_view

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
CHUNK_S = 30           # bloque de análisis == unidad de "evolución"
WIN = 1 << 15          # ventana FFT espectral (32768 ≈ 0.74 s)
EHOP = 256             # hop de la envolvente de energía
EFPS = SR / EHOP

BANDS = [('sub', 20, 60), ('bass', 60, 150), ('lowmid', 150, 500),
         ('mid', 500, 2000), ('himid', 2000, 6000), ('air', 6000, 16000)]
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def stream(path, chunk_s=CHUNK_S):
    """Saca audio de ffmpeg en trozos; nunca tiene el track entero en RAM."""
    cmd = [FF, '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    nb = chunk_s * SR * 2 * 4
    try:
        while True:
            raw = p.stdout.read(nb)
            if not raw:
                break
            x = np.frombuffer(raw, dtype='<f4')
            n = len(x) // 2
            if n < SR // 10:
                break
            yield np.ascontiguousarray(x[:n * 2].reshape(-1, 2).T)
    finally:
        p.stdout.close()
        p.wait()


def kweight(x, sr=SR):
    """K-weighting BS.1770 (aprox. por FFT): shelf alto +4 dB + highpass RLB 38 Hz."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / sr)
    g = np.ones_like(f)
    g[f > 1500] = 10 ** (4 / 20)
    tr = (f >= 1000) & (f <= 1500)
    if tr.any():
        g[tr] = np.linspace(1, 10 ** (4 / 20), tr.sum())
    hp = f < 38
    g[hp] *= (f[hp] / 38) ** 2
    return np.fft.irfft(X * g, n)


def band_split(mag, fr):
    tot = mag.sum() or 1
    return {n: mag[(fr >= a) & (fr < b)].sum() / tot for n, a, b in BANDS}


def ac_lag(on, lag):
    """Autocorrelación en UN lag. np.correlate(on,on,'full') es O(n²) y con 1.8 M
    muestras nunca termina — sólo necesito lags < 220."""
    if lag <= 0 or lag >= len(on):
        return 0.0
    return float(np.dot(on[:-lag], on[lag:]))


def bpm_est(on, lo=100, hi=136):
    if len(on) < 2000:
        return None
    cache, best = {}, (-1e30, None)
    for bpm in np.arange(lo, hi + .5, .25):
        lag = int(round(EFPS * 60 / bpm))
        for L in (lag, 2 * lag):
            if L not in cache:
                cache[L] = ac_lag(on, L)
        sc = cache[lag] + 0.5 * cache[2 * lag]
        if sc > best[0]:
            best = (sc, float(bpm))
    return best[1]


def audit(path, label):
    if not os.path.exists(path):
        return None

    nsamp = 0
    peak = 0.0
    sq_mono = 0.0
    eL = eR = eLR = 0.0
    em = es = 0.0
    lblocks = []
    spec_acc = np.zeros(WIN // 2 + 1)
    spec_n = 0
    chroma = np.zeros(12)
    evo_specs = []
    env_parts = []
    carry = np.zeros(0, dtype=np.float32)

    fr = np.fft.rfftfreq(WIN, 1 / SR)
    hann = np.hanning(WIN)
    pc_mask = (fr > 55) & (fr < 2000)
    pc_idx = (np.round(12 * np.log2(fr[pc_mask] / 440.0) + 69).astype(int)) % 12

    for xs in stream(path):
        L, R = xs[0].astype(np.float64), xs[1].astype(np.float64)
        mono = (L + R) / 2
        n = len(mono)
        nsamp += n
        peak = max(peak, float(np.abs(xs).max()))
        sq_mono += float((mono ** 2).sum())
        eL += float((L ** 2).sum()); eR += float((R ** 2).sum())
        eLR += float((L * R).sum())
        m = (L + R) / 2; s = (L - R) / 2
        em += float((m ** 2).sum()); es += float((s ** 2).sum())

        # --- LUFS: bloques de 400 ms cada 100 ms, K-weighted, potencia L+R (no mezcla a mono)
        kL, kR = kweight(L), kweight(R)
        w, h = int(0.4 * SR), int(0.1 * SR)
        if n >= w:
            zL = (sliding_window_view(kL, w)[::h] ** 2).mean(axis=1)
            zR = (sliding_window_view(kR, w)[::h] ** 2).mean(axis=1)
            z = zL + zR
            z = z[z > 1e-12]
            if len(z):
                lblocks.append(-0.691 + 10 * np.log10(z))

        # --- espectro + croma: varias ventanas repartidas en el bloque
        if n >= WIN:
            starts = np.linspace(0, n - WIN, min(8, max(1, n // WIN)), dtype=int)
            for i, st in enumerate(starts):
                mag = np.abs(np.fft.rfft(mono[st:st + WIN] * hann))
                spec_acc += mag; spec_n += 1
                np.add.at(chroma, pc_idx, mag[pc_mask])
                if i == 0:
                    evo_specs.append(mag / (mag.sum() or 1))

        # --- envolvente de energía (frames no solapados; sin índices gigantes)
        e = np.concatenate([carry, mono.astype(np.float32)])
        nf = len(e) // EHOP
        if nf:
            env_parts.append((e[:nf * EHOP].reshape(-1, EHOP) ** 2).mean(axis=1))
        carry = e[nf * EHOP:]

    if not nsamp:
        return None

    dur = nsamp / SR
    rms = np.sqrt(sq_mono / nsamp)
    crest = round(float(peak / (rms + 1e-12)), 2)

    # LUFS-I con gating absoluto (-70) + relativo (-10 LU)
    lufs = lra = None
    if lblocks:
        l = np.concatenate(lblocks)
        l = l[l > -70]
        if len(l):
            thr = -0.691 + 10 * np.log10(np.mean(10 ** ((l + 0.691) / 10))) - 10
            lg = l[l > thr]
            if len(lg):
                lufs = round(float(-0.691 + 10 * np.log10(np.mean(10 ** ((lg + 0.691) / 10)))), 1)
                if len(lg) > 10:
                    lra = round(float(np.percentile(lg, 95) - np.percentile(lg, 10)), 1)

    spec = {}
    if spec_n:
        spec = {k: round(v * 100, 1) for k, v in band_split(spec_acc / spec_n, fr).items()}

    key = None
    if chroma.sum() > 0:
        c = chroma / chroma.sum()
        best = (-9, '')
        for i in range(12):
            for prof, tag in ((MAJ, 'maj'), (MIN, 'min')):
                r = np.corrcoef(np.roll(c, -i), prof)[0, 1]
                if r > best[0]:
                    best = (r, f'{NOTES[i]} {tag}')
        key = best[1]

    evol = None
    if len(evo_specs) >= 3:
        S = np.array(evo_specs)
        evol = round(float(np.mean([np.corrcoef(S[i], S[i + 1])[0, 1] for i in range(len(S) - 1)])), 3)

    bpm = hits = None
    if env_parts:
        E = np.concatenate(env_parts)
        on = np.maximum(0, np.diff(E)); on = on - on.mean()
        bpm = bpm_est(on)
        thr = on.mean() + 2.2 * on.std()
        pk = (on > thr) & (on > np.roll(on, 1)) & (on > np.roll(on, -1))
        hits = round(float(pk.sum() / dur), 2)

    # correlación L/R y ancho, por sumas acumuladas (corrcoef sobre 476 M muestras = 7 GB)
    corr = round(float(eLR / (np.sqrt(eL * eR) + 1e-12)), 3)
    width = round(float(es / (em + 1e-12)), 3)

    return dict(track=label, dur=round(dur, 1), lufs=lufs, lra=lra,
                peak_db=round(float(20 * np.log10(peak + 1e-9)), 2), crest=crest,
                bpm=bpm, key=key, width=width, corr=corr, evol=evol,
                hits_s=hits, spec=spec)


TARGETS = [
    ('audio/amr-monuments-side.m4a', 'MONUMENTS (EP)'),
    ('audio/amr-set-the-set.m4a', 'SESIÓN 001'),
    ('audio/amr-tulum.m4a', 'DELIRIO'),
    ('audio/amr-guerrero.m4a', 'GUERRERO'),
    ('audio/amr-jacaranda.m4a', 'JACARANDA'),
    ('audio/amr-playa.m4a', 'PLAYA'),
    ('audio/amr-oraculo.m4a', 'ORÁCULO'),
    ('audio/amr-fiebre.m4a', 'FIEBRE'),
    ('audio/amr-iman.m4a', 'IMÁN'),
    ('audio/amr-ficcion.m4a', 'FICCIÓN'),
    ('set-src/06 - Aura.mp3', '[REF] Aura'),
    ('set-src/10 - Rosablanca.mp3', '[REF] Rosablanca'),
    ('set-src/05 - wish you were here remake.mp3', '[REF] wish-you-were'),
]

if __name__ == '__main__':
    out = []
    for p, lab in TARGETS:
        full = os.path.join(HERE, p)
        print(f'  … {lab}', flush=True)
        try:
            r = audit(full, lab)
        except Exception as e:
            print(f'      ! falló: {e}', flush=True)
            continue
        if r:
            out.append(r)
            print(f'      lufs={r["lufs"]} bpm={r["bpm"]} evol={r["evol"]} '
                  f'bass={r["spec"].get("bass")} air={r["spec"].get("air")}', flush=True)

    json.dump(out, open(os.path.join(HERE, '_audit.json'), 'w'), indent=1, ensure_ascii=False)

    print('\n' + '=' * 118)
    print(f"{'TRACK':26s} {'DUR':>6s} {'LUFS':>6s} {'LRA':>5s} {'PEAK':>6s} {'CREST':>5s} "
          f"{'BPM':>6s} {'KEY':>7s} {'WIDTH':>5s} {'CORR':>5s} {'EVOL':>5s} {'HIT/s':>5s}")
    print('-' * 118)
    for r in out:
        print(f"{r['track']:26s} {r['dur']:6.0f} {str(r['lufs']):>6s} {str(r['lra']):>5s} "
              f"{r['peak_db']:6.2f} {r['crest']:5.2f} {str(r['bpm']):>6s} {str(r['key']):>7s} "
              f"{r['width']:5.3f} {r['corr']:5.2f} {str(r['evol']):>5s} {str(r['hits_s']):>5s}")

    print('\n' + '=' * 118)
    print(f"{'TRACK':26s} {'sub':>6s} {'bass':>6s} {'lowmid':>7s} {'mid':>6s} {'himid':>6s} {'air':>6s}")
    print('-' * 118)
    for r in out:
        s = r['spec']
        print(f"{r['track']:26s} {s.get('sub',0):6.1f} {s.get('bass',0):6.1f} {s.get('lowmid',0):7.1f} "
              f"{s.get('mid',0):6.1f} {s.get('himid',0):6.1f} {s.get('air',0):6.1f}")
