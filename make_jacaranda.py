#!/usr/bin/env python3
"""JACARANDA — set melodic techno cinemático (124 BPM, La menor) con BATERÍA REAL.

La diferencia con todo lo anterior: kick, clap, hats, percusión, crashes y FX
NO son sintetizados — son samples de hardware real (TR-909/808/707, DR5, RX5,
CC0 dominio público) vía kit.py, con variación por golpe (micro-pitch+amplitud)
para que no suene a copy-paste. Solo lo melódico se sintetiza (mt_voices.py).

8 movimientos con el arco Anyma/Afterlife, contados como la FLORACIÓN de una
jacaranda (la narrativa que André tenía en el set JACARANDA): semilla (ambiental
SIN kick) → brote (sube) → rama → sombra (motor hipnótico) → flor (breakdown +
drop en MAYOR: el árbol abre) → abril (cumbre de la temporada) → pétalos (clímax,
la lluvia violeta) → primavera (comedown). Bajo LIMPIO, dinámica ANCHA.
Uso: python3 make_jacaranda.py RAMA (una sección) | sin args = set completo."""
import os, sys
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, widen, sub_mono, pingpong,
                        master_file, ffmeter, wav_write, spectrum_pct, ffdecode)
import kit as K
import mt_voices as V
from mt_voices import midi_f, deg, MIN, MAJ

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_jacaranda_tmp'); os.makedirs(TMP, exist_ok=True)
BPM = 124.0
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0; BEAT = 60.0 / BPM
XF = 4
ROOT = 57                       # La (A3) — La menor = 8A (mixea con DELIRIO/GUERRERO)

SECTIONS = [
 dict(name='SEMILLA',   shape='amb',    bars=48,  maj=False),
 dict(name='BROTE',    shape='rise',   bars=88,  maj=False),
 dict(name='RAMA',    shape='wave',   bars=96,  maj=False),
 dict(name='SOMBRA',     shape='drive',  bars=96,  maj=False),
 dict(name='FLOR',    shape='jacaranday', bars=96,  maj=True),
 dict(name='ABRIL', shape='peak',   bars=88,  maj=False),
 dict(name='PETALOS',     shape='peak2',  bars=104, maj=True),
 dict(name='PRIMAVERA',    shape='outro',  bars=56,  maj=False),
]

def chords(sec):
    sc = MAJ if sec['maj'] else MIN
    prog = [(0,0),(5,0),(3,0),(4,0)] if sec['maj'] else [(0,0),(5,0),(2,0),(6,0)]
    out = []
    for d,o in prog:
        tri = [deg(ROOT,d,o,sc), deg(ROOT,d+2,o,sc), deg(ROOT,d+4,o,sc)]
        out.append([ROOT + sc[d%7] + 12*(d//7) - 24] + tri)   # [bass_root(grave), t1,t2,t3]
    return out

def plan(shape, p):
    b = dict(kick=1, bass=1, hats=0.7, clap=1, perc=0.4, lead=0, stab=0, pad=0.4,
             piano=0, vox=0, amb=0, gain=1.0, pre=0, filt=1.0, crash=0)
    if shape=='amb':
        b.update(kick=0,bass=0,hats=0,clap=0,perc=0,pad=1,amb=1,vox=0.5 if p>0.45 else 0,
                 gain=0.5+0.34*p, filt=0.4+0.5*p)
    elif shape=='rise':
        b.update(hats=0.3+0.4*p, clap=1 if p>0.35 else 0, perc=0.3, pad=0.5, amb=0.5*(1-p),
                 lead=0.4 if p>0.6 else 0, gain=0.7+0.28*p, filt=0.45+0.5*p,
                 crash=1 if p<0.06 else 0)
        if p>0.88: b.update(pre=1)
    elif shape=='wave':
        b.update(lead=0.9, stab=0.6, vox=1, pad=0.6, perc=0.5, gain=1.0, crash=1 if p<0.06 else 0)
        if 0.5<p<0.62: b.update(kick=0,bass=0,clap=0,pad=0.9,vox=1,gain=0.76)
    elif shape=='drive':
        b.update(lead=0.8, stab=0.9, pad=0.5, perc=0.6, vox=0.4, gain=1.02, crash=1 if p<0.06 else 0)
    elif shape=='jacaranday':
        if p<0.55:
            b.update(kick=0,bass=0,clap=0,hats=0.08,perc=0.05,pad=1,vox=1,piano=0.6,amb=0.5,
                     lead=0.5 if p>0.3 else 0, gain=0.6, filt=0.55)
        elif p<0.6:
            b.update(kick=0,bass=0,clap=0,hats=0,perc=0,pad=0.7,vox=0.6,pre=1,gain=0.7)
        else:
            b.update(lead=1.0, stab=0.8, pad=0.8, vox=0.8, perc=0.7, gain=1.05, crash=1 if p<0.64 else 0)
    elif shape=='peak':
        b.update(lead=1.0, stab=1.0, vox=0.9, pad=0.7, perc=0.8, hats=0.9, gain=1.05,
                 crash=1 if p<0.06 else 0)
    elif shape=='peak2':
        if 0.34<p<0.45:
            b.update(kick=0,bass=0,clap=0,pad=1,vox=1,pre=1,gain=0.8)
        else:
            b.update(lead=1.0, stab=1.0, vox=1, pad=0.8, perc=0.9, hats=0.95, gain=1.08,
                     crash=1 if (p<0.06 or 0.45<=p<0.5) else 0)
    elif shape=='outro':
        b.update(gain=1.0-0.5*max(0,p-0.25), lead=0.5*(1-p), stab=0, perc=0.4*(1-p),
                 pad=0.8, piano=0.7, vox=0.7, amb=0.6*p, kick=1 if p<0.55 else 0,
                 clap=1 if p<0.5 else 0, filt=1.0-0.4*max(0,p-0.4))
    return b

def sc_env(n, kpos, depth=0.5, rel=0.12):
    e = np.ones(n, np.float32)
    dip = 1.0 - depth*np.exp(-np.arange(int(rel*4*SR))/(rel*SR)).astype(np.float32)
    for p_ in kpos:
        q = min(n, p_+len(dip))
        if q>p_: e[p_:q] = np.minimum(e[p_:q], dip[:q-p_])
    return e

def render_section(sec, idx):
    rng = np.random.default_rng(800 + idx*37)
    bars = sec['bars']; n = bars*SPB + XF*SPB
    ch = chords(sec); shape = sec['shape']; nb = bars//8
    drum = np.zeros(n, np.float32); kickb = np.zeros(n, np.float32); bassb = np.zeros(n, np.float32)
    leadb = np.zeros(n, np.float32); stabb = np.zeros(n, np.float32)
    padL = np.zeros(n, np.float32); padR = np.zeros(n, np.float32)
    voxb = np.zeros(n, np.float32); pianob = np.zeros(n, np.float32); ambb = np.zeros(n, np.float32)
    kpos = []
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
            last=(gb%8==7); silent=(b['pre'] and last)
            # ---- AMBIENTE real (drone/glass)
            if b['amb']>0 and gb%8==0:
                a = K.smp(K.AMBI_DRONE if (gb//8)%2==0 else K.AMBI_GLASS)
                add(ambb, base, np.tile(a, int(np.ceil(8*SPB/len(a))))[:8*SPB], b['amb']*0.35)
            # ---- CRASH real al arranque de sección
            if b['crash'] and bar==0 and gb%8==0:
                add(drum, base, K.vary(K.smp(K.CRASH), rng), 0.5)
            # ---- KICK 909 REAL 4x4
            if b['kick'] and not silent:
                for beat in range(4):
                    add(kickb, base+beat*4*S16, K.vary(K.smp(K.KICK), rng, 0.012, 0.08), 0.95)
                    kpos.append(int(base+beat*4*S16))
            # ---- CLAP 909 REAL en 2 y 4
            if b['clap'] and not silent:
                for s in (4,12):
                    add(drum, base+s*S16-0.012*SR, K.vary(K.smp(K.CLAP), rng, 0.02, 0.15), b['clap']*0.42)
            # ---- HATS 909 REALES (16vos + open en contratiempo)
            if b['hats']>0 and not silent:
                for s in range(16):
                    op=(s%4==2)
                    sm = K.smp(K.HATO) if op else K.smp(K.HATC)
                    add(drum, base+s*S16+rng.normal(0,.0018)*SR, K.vary(sm, rng, 0.03, 0.3),
                        (0.34 if s%2 else 0.22)*b['hats']*(0.75 if op else 1))
            # ---- PERCUSIÓN real (shaker, cabasa, rim, conga)
            if b['perc']>0 and not silent:
                for s in range(2,16,4):
                    add(drum, base+s*S16+rng.normal(0,.003)*SR, K.vary(K.smp(K.SHAKER), rng, 0.04, 0.3), b['perc']*0.3)
                if bar%2==1:
                    add(drum, base+10*S16, K.vary(K.smp(K.RIM), rng, 0.03, 0.2), b['perc']*0.4)
                if b['perc']>=0.6 and bar%4==2:
                    add(drum, base+6*S16, K.vary(K.smp(K.CONGA_L), rng, 0.03, 0.2), b['perc']*0.45)
                if b['perc']>=0.8 and bar%4==3:
                    add(drum, base+14*S16, K.vary(K.smp(K.CABASA), rng, 0.04, 0.3), b['perc']*0.3)
            # ---- FX REAL antes del drop (reverse cymbal + reverse clap)
            if last and b['pre']:
                rc = K.smp(K.REVCYM)
                add(drum, base+8*SPB//8*0 + (SPB - len(rc)) if len(rc)<SPB else base, rc, 0.55)
                add(drum, base+int(12*S16), K.smp(K.REVCLAP), 0.4)
            # ---- BAJO LIMPIO rolling (deja vacía la 1a semicorchea del beat)
            if b['bass'] and not silent:
                for s in range(16):
                    if s%4==0: continue
                    add(bassb, base+s*S16+rng.normal(0,.002)*SR,
                        V.bass(midi_f(root), 0.9*S16/SR, rng, cutoff=360+230*b['filt']), 0.85)
            # ---- LEAD gated (frases de 2 compases con huecos)
            if b['lead']>0 and gb%2==0:
                for (s,d,ln) in [(0,0,3),(6,2,2),(10,4,3),(16,1,2),(22,3,4)]:
                    pos=base+int(s*S16)+(SPB if s>=16 else 0)
                    f=midi_f(deg(ROOT, d, 1, MAJ if sec['maj'] else MIN))
                    add(leadb, pos, V.lead(f, ln*S16/SR*1.15, rng, gate_hz=BPM/60*2,
                                           cut=1600+1400*b['filt']), b['lead']*0.5)
            # ---- STABS FM en los huecos
            if b['stab']>0 and not silent:
                for s in ((12,13,14,15) if cyc==1 else (4,5)):
                    if rng.uniform()<0.7:
                        add(stabb, base+s*S16, V.stab(midi_f(deg(ROOT,int(rng.integers(0,5)),1)), 0.13, rng), b['stab']*0.42)
            # ---- PADS
            if b['pad']>0.2 and gb%2==0:
                x=V.pad([c[1]+12, c[3]+12], 2*SPB/SR*1.04, rng)
                add(padL, base, x, b['pad']); add(padR, base+int(0.02*SR), x, b['pad']*0.92)
            if b['piano']>0 and gb%4==0:
                add(pianob, base, V.piano([c[1],c[2],c[3]], 2*SPB/SR, rng), b['piano'])
            # ---- VOZ-musa ELIMINADA (André: suena a trompeta chillona / globo desinflándose).
            # Los tonos con filtros de formante + vibrato le suenan a chillido — mismo
            # problema que el lead 'wah' de PLAYA. NO volver a usar formantes sostenidos.
            if False and b['vox']>0 and gb%4==0:
                add(voxb, base, V.vox(midi_f(deg(ROOT,(gb//4)%5,1)), 2*SPB/SR*0.9, rng, 'aou'[(gb//4)%3]), b['vox']*0.5)
    # ---- buses
    env = sc_env(n, kpos)
    bassb *= env
    drum_st = widen(drum, amount=0.45, seed=idx*3+2)
    lead_st = pingpong(leadb*(env*0.5+0.5), BEAT, fb=0.42, mix=0.4, taps=7, damp=5200)
    stab_st = pingpong(stabb*(env*0.5+0.5), BEAT, fb=0.36, mix=0.34, taps=5, damp=6000)
    vox_st  = pingpong(voxb*(env*0.5+0.5), BEAT, fb=0.4, mix=0.42, taps=6, damp=5000)
    pads = np.stack([padL,padR])*(env*0.5+0.5)[None,:]
    piano_st = np.stack([pianob,pianob]); amb_st = np.stack([ambb, ambb[::-1].copy()])
    music = (drum_st*0.82 + lead_st*0.7 + stab_st*0.5 + pads*0.86           # SIN voz-musa
             + piano_st*0.56 + amb_st*0.55)
    mm=0.5*(music[0]+music[1]); ss=bp(0.5*(music[0]-music[1]), 200, 12000, 2)*2.1
    mix=np.stack([mm+ss, mm-ss])
    mix += kickb[None,:]*1.15 + bassb[None,:]*0.78
    genv=np.ones(n,np.float32)
    for bi,blk in enumerate(blocks):
        genv[bi*8*SPB:min(n,(bi+1)*8*SPB)]=blk['gain']
    genv=lp(genv,2.0,1)**1.5; mix*=genv[None,:]
    mix=np.stack([sat(mix[0],1.04,0.02), sat(mix[1],1.04,0.02)])   # muy suave
    mix=sub_mono(mix,120.0)
    pk=np.abs(mix).max()
    if pk>1.5: mix*=1.5/pk
    return mix

def _shave(x):
    x=np.stack([sat(x[0],1.3,0.02), sat(x[1],1.3,0.02)])
    return x*(0.90/max(1e-9,float(np.abs(x).max())))

def build(only=None):
    tot=sum(s['bars'] for s in SECTIONS)
    print(f'JACARANDA · {len(SECTIONS)} movimientos · {tot} compases ≈ {tot*SPB/SR/60:.0f} min · FLORACIÓN', flush=True)
    secs=[]
    for i,s in enumerate(SECTIONS):
        if only and s['name']!=only: continue
        f=os.path.join(TMP, f'sec-{i:02d}-{s["name"].lower()}.wav')
        if not only and os.path.exists(f):
            print(f'  ✓ {s["name"]}', flush=True); secs.append((i,s,f)); continue
        print(f'  … {s["name"]} ({s["bars"]} comp, {s["shape"]})', flush=True)
        mix=render_section(s,i); wav_write(f,mix); secs.append((i,s,f)); del mix
    if only:
        i,s,f=secs[0]; I,lra,tp=ffmeter(f)
        print(f'  {s["name"]}: {I} LUFS · LRA {lra} · TP {tp} · {spectrum_pct(ffdecode(f,mono=True))}')
        return
    print('  … crossfades', flush=True)
    xf=XF*SPB; total=tot*SPB+xf
    out=np.zeros((2,total),np.float32); pos=0
    for k,(i,s,f) in enumerate(secs):
        x=ffdecode(f)
        if k>0: x[:,:xf]*=(np.linspace(0,1,xf)**0.5).astype(np.float32)[None,:]
        a=min(total-pos,x.shape[1]); out[:,pos:pos+a]+=x[:,:a]; pos+=s['bars']*SPB; del x
    print('  … afeitado suave + master -10.5 (dinámico)', flush=True)
    out=_shave(out)
    raw=os.path.join(TMP,'jacaranda-raw.wav'); wav_write(raw,out); del out
    os.makedirs(os.path.join(HERE,'masters'),exist_ok=True)
    final=os.path.join(HERE,'masters','amr-jacaranda.wav')
    hist=master_file(raw, final, target_i=-10.5, ceiling_db=-1.2)
    I,lra,tp=ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}'); print(final)

if __name__=='__main__':
    build(sys.argv[1] if len(sys.argv)>1 else None)
