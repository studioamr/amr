#!/usr/bin/env python3
"""ORÁCULO — set melodic techno cinemático sci-fi (estilo Anyma / Afterlife).
Réplica de cómo Anyma construye un set (investigado): intro cinemático SIN kick,
BPM que SUBE 122→126 (no salta), keys menores con giro a MAYOR relativa en los
dos picos, largos builds filtrados, breakdown con 'silencio antes del drop', el
lead supersaw GATED, stabs FM, voz-musa + narración robótica, y MUCHO efecto.
8 movimientos = el arco emocional Génesis→Pulso→Musa→Descenso→Vacío(drop mayor)→
Himno→Corazón(clímax)→Humano(comedown). Bajo LIMPIO, máster dinámico (no muro).
Uso: python3 make_oraculo.py MUSA (una sección) | sin args = set completo."""
import os, sys
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, widen, sub_mono, pingpong,
                        master_file, ffmeter, wav_write, spectrum_pct, ffdecode)
import anyma_voices as V
from anyma_voices import midi_f

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_oraculo_tmp'); os.makedirs(TMP, exist_ok=True)
XF_BARS = 4
KICK = V.kick_mt()

# escalas
MIN = [0, 2, 3, 5, 7, 8, 10]     # menor natural
MAJ = [0, 2, 4, 5, 7, 9, 11]     # mayor (para los picos)
def deg(root, d, o=0, scale=MIN): return root + scale[d % 7] + 12 * (d // 7 + o)

# cada movimiento: nombre, bpm, root(midi de la tónica media), major?, shape, bars,
# chords = 4 acordes (grados de tónica) — se construyen tríadas en la escala
SECTIONS = [
 dict(name='GENESIS',  bpm=122, root=55, maj=False, shape='amb',   bars=44),   # Sol menor, útero cinemático
 dict(name='PULSO',    bpm=122, root=55, maj=False, shape='rise',  bars=88),   # entra kick + sub filtrado
 dict(name='MUSA',     bpm=123, root=53, maj=False, shape='wave',  bars=96),   # Fa menor, la voz-musa
 dict(name='DESCENSO', bpm=124, root=52, maj=False, shape='drive', bars=96),   # Mi menor, hipnótico oscuro
 dict(name='VACIO',    bpm=125, root=52, maj=True,  shape='valley',bars=96),   # breakdown → DROP en mayor
 dict(name='HIMNO',    bpm=126, root=56, maj=False, shape='peak',  bars=88),   # Lab menor, anthem
 dict(name='CORAZON',  bpm=126, root=55, maj=True,  shape='peak2', bars=104),  # clímax, giro a mayor
 dict(name='HUMANO',   bpm=126, root=55, maj=False, shape='outro', bars=56),   # comedown, pads+piano+voz
]

def chords_of(sec):
    r = sec['root']; sc = MAJ if sec['maj'] else MIN
    if sec['maj']:  # I  vi  IV  V  (lift euforico)
        prog = [(0,0),(5,0),(3,0),(4,0)]
    else:           # i  VI  III VII (melodic techno menor)
        prog = [(0,0),(5,0),(2,0),(6,0)]
    out = []
    for d, o in prog:
        tri = [deg(r, d, o, sc), deg(r, d+2, o, sc), deg(r, d+4, o, sc)]
        out.append([r + sc[d % 7] + 12*(d//7) - 12] + tri)   # [bass_root, t1,t2,t3]
    return out

def plan(shape, p):
    """gains/flags por bloque de 8 compases según shape y posición p (0..1)."""
    b = dict(kick=1, bass=1, hats=0.7, clap=1, perc=0.4, lead=0, fm=0, pad=0.4,
             piano=0, muse=0, robot=0, drone=0, gain=1.0, predrop=0, filt=1.0)
    if shape == 'amb':      # intro cinemático SIN kick
        b.update(kick=0, bass=0, hats=0, clap=0, perc=0, pad=1, drone=1, robot=0.6 if p<0.5 else 0,
                 muse=0.4 if p>0.5 else 0, gain=0.5+0.35*p, filt=0.4+0.5*p)
    elif shape == 'rise':   # entra el groove, filtro abriendo
        b.update(hats=0.3+0.4*p, clap=1 if p>0.4 else 0, perc=0.3, pad=0.5, lead=0.4 if p>0.6 else 0,
                 drone=0.5*(1-p), gain=0.7+0.28*p, filt=0.45+0.5*p, muse=0.3 if p>0.7 else 0)
        if p>0.88: b.update(predrop=1)
    elif shape == 'wave':   # la musa canta
        b.update(lead=0.9, fm=0.7, muse=1, pad=0.6, perc=0.5, gain=1.0)
        if 0.5<p<0.62: b.update(kick=0, bass=0, clap=0, muse=1, pad=0.9, gain=0.78, predrop=0)   # respiro
    elif shape == 'drive':  # hipnótico oscuro
        b.update(lead=0.8, fm=0.9, pad=0.5, perc=0.6, muse=0.4, gain=1.02, filt=0.9)
    elif shape == 'valley': # breakdown → drop en mayor
        if p<0.55:          # strip: pads + voz, sin kick (silencio antes del drop)
            b.update(kick=0, bass=0, clap=0, hats=0.1, perc=0.05, pad=1, muse=1, piano=0.6,
                     lead=0.5 if p>0.3 else 0, gain=0.62, filt=0.6, drone=0.4)
        elif p<0.6:
            b.update(kick=0, bass=0, clap=0, hats=0, perc=0, pad=0.7, muse=0.6, predrop=1, gain=0.7)
        else:               # DROP euforico en mayor
            b.update(lead=1.0, fm=0.8, pad=0.8, muse=0.8, perc=0.7, gain=1.05, filt=1.0)
    elif shape == 'peak':   # anthem
        b.update(lead=1.0, fm=1.0, muse=0.9, pad=0.7, perc=0.8, hats=0.9, gain=1.05, filt=1.0)
    elif shape == 'peak2':  # clímax
        if 0.35<p<0.46:     # último respiro + riser antes del drop más grande
            b.update(kick=0, bass=0, clap=0, pad=1, muse=1, predrop=1, gain=0.82)
        else:
            b.update(lead=1.0, fm=1.0, muse=1, pad=0.8, perc=0.9, hats=0.95, gain=1.08, filt=1.0)
    elif shape == 'outro':  # comedown
        b.update(gain=1.0-0.5*max(0,p-0.25), lead=0.5*(1-p), fm=0, perc=0.4*(1-p),
                 pad=0.8, piano=0.7, muse=0.7, robot=0.5 if p>0.6 else 0, drone=0.5*p,
                 kick=1 if p<0.55 else 0, clap=1 if p<0.5 else 0, filt=1.0-0.4*max(0,p-0.4))
    return b

def sidechain(n, kpos, depth=0.5, rel=0.12):
    env = np.ones(n, np.float32)
    dip = 1.0 - depth*np.exp(-np.arange(int(rel*4*SR))/(rel*SR)).astype(np.float32)
    for p_ in kpos:
        e = min(n, p_+len(dip))
        if e>p_: env[p_:e] = np.minimum(env[p_:e], dip[:e-p_])
    return env

def render_section(sec, idx):
    rng = np.random.default_rng(500 + idx*29)
    bpm = sec['bpm']; SPB = int(round(SR*240.0/bpm)); S16 = SPB/16.0; BEAT = 60.0/bpm
    bars = sec['bars']; n = bars*SPB + XF_BARS*SPB
    ch = chords_of(sec); shape = sec['shape']; nb = bars//8
    kickb=np.zeros(n,np.float32); bassb=np.zeros(n,np.float32); drumb=np.zeros(n,np.float32)
    leadb=np.zeros(n,np.float32); fmb=np.zeros(n,np.float32); padL=np.zeros(n,np.float32)
    padR=np.zeros(n,np.float32); voxb=np.zeros(n,np.float32); pianob=np.zeros(n,np.float32)
    droneb=np.zeros(n,np.float32); kpos=[]
    gate_hz = bpm/60.0*2                                    # gate en 1/8 (stutter)
    def add(buf,pos,x,g=1.0):
        pos=int(pos)
        if pos<0: x=x[-pos:]; pos=0
        e=min(len(buf),pos+len(x))
        if e>pos: buf[pos:e]+=x[:e-pos]*g
    blocks=[plan(shape, i/max(1,nb-1)) for i in range(nb)]
    for bi,b in enumerate(blocks):
        for bar in range(8):
            gb=bi*8+bar
            if gb>=bars: break
            base=gb*SPB; c=ch[(gb//2)%4]; root=c[0]; cyc=gb%2
            last=(gb%8==7); silent=(b['predrop'] and last)
            if b['drone']>0 and bar==0 and gb%4==0:
                add(droneb, base, V.drone(4*SPB/SR, [root, c[2]], rng), b['drone'])
            if b['kick'] and not silent:
                for beat in range(4):
                    add(kickb, base+beat*4*S16, KICK); kpos.append(int(base+beat*4*S16))
            if b['clap'] and not silent:
                for s in (4,12): add(drumb, base+s*S16-0.014*SR, V.clap(rng), b['clap']*0.6)
            if b['hats']>0 and not silent:
                for s in range(16):
                    op=(s%4==2)
                    add(drumb, base+s*S16+rng.normal(0,.002)*SR, V.hat(rng,open_=op), (0.4 if s%2 else 0.26)*b['hats']*(0.8 if op else 1))
            if b['perc']>0 and not silent and bar%2==1:
                add(drumb, base+10*S16, V.perc_metal(rng, 480+idx*20), b['perc']*0.5)
                add(drumb, base+6*S16, V.shaker(rng), b['perc']*0.4)
            # BAJO limpio rolling 16vos (deja vacía la 1a semicorchea de cada beat)
            if b['bass'] and not silent:
                for s in range(16):
                    if s%4==0: continue
                    add(bassb, base+s*S16+rng.normal(0,.002)*SR, V.bass_mt(midi_f(root-12), 0.9*S16/SR, rng, cutoff=380+240*b['filt']), 0.85)
            # LEAD supersaw gated — frases de 2 compases con huecos (call/response)
            if b['lead']>0 and gb%2==0:
                mel=[(0,0,3),(6,2,2),(10,4,3),(16,1,2),(22,3,4)]
                for (s,d,ln) in mel:
                    pos=base+int(s*S16)+(SPB if s>=16 else 0)
                    f=midi_f(deg(sec['root'], d, 1, MAJ if sec['maj'] else MIN))
                    add(leadb, pos, V.lead_gated(f, ln*S16/SR*1.15, rng, gate_hz=gate_hz, cut=1600+1400*b['filt']), b['lead']*0.5)
            # STABS FM en los huecos
            if b['fm']>0 and not silent:
                for s in (12,13,14,15) if cyc==1 else (4,5):
                    if rng.uniform()<0.7:
                        add(fmb, base+s*S16, V.fm_stab(midi_f(deg(sec['root'], int(rng.integers(0,5)), 1)), 0.13, rng), b['fm']*0.45)
            # PADS cinemáticos (2 notas)
            if b['pad']>0.2 and gb%2==0:
                x=V.pad_cine([c[1]+12, c[3]+12], 2*SPB/SR*1.04, rng)
                add(padL, base, x, b['pad']); add(padR, base+int(0.02*SR), x, b['pad']*0.92)
            # PIANO glue
            if b['piano']>0 and gb%4==0:
                add(pianob, base, V.piano_glue([c[1], c[2], c[3]], 2*SPB/SR, rng), b['piano'])
            # VOZ-musa (frases largas etéreas)
            if b['muse']>0 and gb%4==0:
                add(voxb, base, V.vox_muse(midi_f(deg(sec['root'], (gb//4)%5, 1)), 2*SPB/SR*0.9, rng, 'aou'[(gb//4)%3]), b['muse']*0.5)
            # NARRACIÓN robótica (intro/outro)
            if b['robot']>0 and gb%4==2:
                add(voxb, base, V.vox_robot(midi_f(deg(sec['root'], 0, 0)), 1.4*SPB/SR, rng, 'oe'[(gb//4)%2]), b['robot']*0.5)
            # FX de sección
            if last and b['predrop']:
                add(leadb, base, V.riser(4*BEAT, rng), 0.9)
                if shape in ('valley','peak2'): add(kickb, base+4*4*S16, V.impact(rng), 0.9)
            if gb==0 and shape in ('rise','drive'): add(leadb, 0, V.revswell(2*BEAT, rng), 0.7)
    # ------- buses (MUCHO espacio; ya vienen con reverb interno)
    env=sidechain(n,kpos)
    bassb*=env
    drum_st=widen(drumb, amount=0.45, seed=idx*3+2)
    lead_st=pingpong(leadb*(env*0.5+0.5), BEAT, fb=0.42, mix=0.4, taps=7, damp=5200)
    fm_st=pingpong(fmb*(env*0.5+0.5), BEAT, fb=0.36, mix=0.34, taps=5, damp=6000)
    vox_st=pingpong(voxb*(env*0.5+0.5), BEAT, fb=0.4, mix=0.42, taps=6, damp=5000)
    pads=np.stack([padL,padR])*(env*0.5+0.5)[None,:]
    piano_st=np.stack([pianob,pianob]); drone_st=np.stack([droneb, droneb[::-1].copy()])
    music=(drum_st*0.68 + lead_st*0.76 + fm_st*0.56 + vox_st*0.6 + (pads)*0.88 + piano_st*0.56 + drone_st*0.64)
    mm=0.5*(music[0]+music[1]); ss=bp(0.5*(music[0]-music[1]), 200, 12000, 2)*2.2
    mix=np.stack([mm+ss, mm-ss])
    mix += kickb[None,:]*1.16 + bassb[None,:]*0.78          # bajo limpio, menos denso (no bass-heavy)
    genv=np.ones(n,np.float32)
    for bi,blk in enumerate(blocks):
        genv[bi*8*SPB:min(n,(bi+1)*8*SPB)]=blk['gain']
    genv=lp(genv,2.0,1)**1.5; mix*=genv[None,:]             # macro-dinámica ancha
    mix=np.stack([sat(mix[0],1.05,0.03), sat(mix[1],1.05,0.03)])
    mix=sub_mono(mix,120.0)
    pk=np.abs(mix).max()
    if pk>1.5: mix*=1.5/pk                                  # no normalizar cada sección
    return mix, SPB

def _shave(x):
    x=np.stack([sat(x[0],1.3,0.02), sat(x[1],1.3,0.02)])
    return x*(0.90/max(1e-9, float(np.abs(x).max())))

def build(only=None):
    tot=sum(s['bars'] for s in SECTIONS)
    approx=sum(s['bars']*int(round(SR*240.0/s['bpm'])) for s in SECTIONS)/SR/60
    print(f'ORÁCULO · {len(SECTIONS)} movimientos · {tot} compases ≈ {approx:.0f} min', flush=True)
    secs=[]
    for i,s in enumerate(SECTIONS):
        if only and s['name']!=only: continue
        f=os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        if not only and os.path.exists(f):
            print(f'  ✓ {s["name"]}', flush=True); secs.append((i,s,f)); continue
        print(f'  … {s["name"]} ({s["bars"]} comp, {s["bpm"]} BPM, {s["shape"]})', flush=True)
        mix,_=render_section(s,i); wav_write(f,mix); secs.append((i,s,f)); del mix
    if only:
        i,s,f=secs[0]; I,lra,tp=ffmeter(f)
        print(f'  {s["name"]}: {I} LUFS · LRA {lra} · TP {tp} · {spectrum_pct(ffdecode(f,mono=True))}')
        return
    print('  … crossfades', flush=True)
    parts=[];
    for k,(i,s,f) in enumerate(secs):
        x=ffdecode(f)
        xf=XF_BARS*int(round(SR*240.0/s['bpm']))
        if k>0: x[:, :xf]*=(np.linspace(0,1,xf)**0.5).astype(np.float32)[None,:]
        keep=s['bars']*int(round(SR*240.0/s['bpm']))
        parts.append((x, keep));
    total=sum(keep for _,keep in parts)+XF_BARS*int(round(SR*240.0/SECTIONS[-1]['bpm']))
    out=np.zeros((2,total),np.float32); pos=0
    for x,keep in parts:
        a=min(total-pos, x.shape[1]); out[:,pos:pos+a]+=x[:,:a]; pos+=keep; del x
    print('  … afeitado suave + master -10.5 (dinámico, mucho FX)', flush=True)
    out=_shave(out)
    raw=os.path.join(TMP,'oraculo-raw.wav'); wav_write(raw,out); del out
    os.makedirs(os.path.join(HERE,'masters'),exist_ok=True)
    final=os.path.join(HERE,'masters','amr-oraculo.wav')
    hist=master_file(raw, final, target_i=-10.5, ceiling_db=-1.2)
    I,lra,tp=ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}'); print(final)

if __name__=='__main__':
    build(sys.argv[1] if len(sys.argv)>1 else None)
