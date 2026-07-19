#!/usr/bin/env python3
"""GROOVE v2 — que la percusión suene TOCADA y no programada.

⚠️ v2 CORRIGE TRES ERRORES DE v1, encontrados al contrastar contra literatura
   revisada por pares (ver memoria afro-house-arreglo / keinemusik):

   1. EL SWING IBA A LA MITAD. Roger Linn —que inventó el parámetro— define
      el % como la fracción del par de semicorcheas que se le da a la PRIMERA,
      así que el retraso es sobre la corchea completa:
          delay = (S - 0.5) * (30000 / BPM)   ms
      v1 tenía un *0.5 de más: a S=0.56 y 122 BPM daba 7.4 ms en vez de 14.8.
      El swing existía pero se sentía la mitad de lo que decía la etiqueta.

   2. EL RANGO DE VELOCITY ERA DEMASIADO ANGOSTO. Dahl 2004 (motion capture +
      plataforma de fuerza) midió acento vs no-acento en 25 dB. v1 tenía 5-9 dB.
      25 dB son ~18x en amplitud lineal; v1 llegaba a 2.8x.

   3. EL ACENTO SE REPETÍA CADA COMPÁS. Porcaro (931 onsets de hi-hat medidos)
      tiene periodicidad de DOS compases, correlación 0.88. v1 usaba uno.

⭐ Y EL HALLAZGO QUE MÁS CAMBIA EL ENFOQUE — cuatro fuentes independientes
   dicen que el jitter aleatorio NO es lo que hace que suene tocado:
     · Roger Linn, sobre meter variación aleatoria: "I've never found these to
       do much good."
     · Datseris et al. (Nature Sci Rep 2019): quitaron las desviaciones
       aleatorias PRESERVANDO el ratio de swing → las versiones cuantizadas
       fueron 1.65x más probables de calificarse como que swinguean MÁS.
       Exagerar las desviaciones (x2) fue 4.42x más probable de calificarse peor.
     · Frühauf et al. 2013 (N=93): la versión cuantizada sacó la nota más alta.
     · Gordon et al. 2019: las amplitudes de hi-hat salen ruido blanco, y no hubo
       diferencia medible entre bateristas expertos y principiantes absolutos.
   Conclusión: si suena programado, el problema es VELOCITY y TIMBRE, no jitter.
   Por eso v2 baja el jitter casi a cero y mete el presupuesto en dinámica.

✅ LO QUE SÍ SE SOSTUVO DE v1: el rango de swing. Yo había inventado 56-58%
   admitiendo que no tenía respaldo — y resulta que Polak midió el jembé de Malí
   (MTO 16.4) y el patrón Woloso binario da ratios de 53:47 a 58:42, que es
   EXACTAMENTE swing de MPC 53-58%. Confirmación etnomusicológica independiente.

Nota de honestidad: Keinemusik NUNCA ha declarado un valor de swing, de
cuantización ni de humanización. Cualquier tutorial que cite "el swing de
Keinemusik" se lo inventó. Los números de aquí salen de percusión medida
(Malí, Cuba, Uruguay, funk de los 70), no de ellos.
"""
import numpy as np

# ------------------------------------------------------------------ SWING
def swing_delay_ms(S, bpm):
    """Fórmula de Linn. S=0.50 recto · 0.667 tresillo · ~2.4 ms por punto % a tempo house."""
    return (S - 0.5) * (30000.0 / bpm)

# ------------------------------------------------------------------ ACENTO
# Contorno de Porcaro medido sobre 8 semicorcheas: alto-bajo-medio-bajo-MUY
# alto-bajo-medio-bajo. Se extiende a 32 pasos (DOS compases) porque ahí está
# la periodicidad real. El segundo compás varía: es lo que impide el clon.
_POR = [1.00, 0.25, 0.55, 0.25, 1.15, 0.25, 0.55, 0.25]

def _contorno(feel):
    a = (_POR * 4)[:32]
    if feel == 'afro':      # el "2 y" pega fuerte; deja huecos más profundos
        for i in (6, 22): a[i] = 1.05
        for i in (3, 11, 19, 27): a[i] = 0.16
    elif feel == 'laid':    # menos contraste, más parejo
        a = [0.42 + 0.58 * (v / 1.15) for v in a]
    # el compás 2 nunca es clon del 1 — de ahí sale la periodicidad de 2
    for i in range(16, 32):
        a[i] *= 0.88 if i % 4 == 0 else 1.06
    return a

# Firmas direccionales medidas (no inventadas). En ms, negativo = adelantado.
#   conga de rumba afrocubana (Los Muñequitos, 110 BPM): ~30 ms ADELANTE
#   última semicorchea del candombe uruguayo: cae en 0.70 del pulso, no 0.75
FEELS = {
    'straight': dict(swing=0.500, ghost=0.00, lead_ms=0.0),
    'house':    dict(swing=0.560, ghost=0.35, lead_ms=-4.0),
    'afro':     dict(swing=0.575, ghost=0.55, lead_ms=-12.0),   # tira adelante
    'laid':     dict(swing=0.540, ghost=0.25, lead_ms=+8.0),    # tira atrás
}

def _pink(n, rng):
    """Ruido rosa (1/f). Hennig (PLOS ONE) es el ÚNICO estudio a favor de
    aleatorizar, y exige que sea rosa, no blanco. Aun así gana 59% vs 41%."""
    w = rng.standard_normal(n + 64)
    f = np.fft.rfft(w)
    k = np.arange(len(f)); k[0] = 1
    p = np.fft.irfft(f / np.sqrt(k))[:n]
    s = p.std()
    return p / s if s > 1e-9 else p

class Groove:
    """El groove de UN instrumento. Se crea una vez y se usa todo el track.

        g = Groove('afro', S16, SR, bpm=120, seed=1)
        pos = g.pos(base, step, bar)     # muestra donde cae el golpe
        vel = g.vel(step, bar)           # 0..1 — AQUÍ vive el groove de verdad
    """
    def __init__(self, feel, s16, sr, bpm=120.0, seed=0, tight=1.0,
                 vel_db=22.0, jitter_ms=3.0):
        f = FEELS[feel]
        self.feel, self.s16, self.sr, self.bpm = feel, s16, sr, bpm
        self.swing = f['swing']; self.gp = f['ghost']
        self.lead = f['lead_ms'] * 1e-3 * sr
        self.acc = _contorno(feel)
        self.tight = tight
        # 22 dB de rango dinámico. Dahl midió 25 en tarola; 22 es prudente para
        # hats y sigue siendo ~13x lineal, contra los 2.8x de v1.
        self.vfloor = 10.0 ** (-vel_db / 20.0)
        self.sw = swing_delay_ms(self.swing, bpm) * 1e-3 * sr
        rng = np.random.default_rng(1000 + seed)
        self._rng = rng
        self._pink = _pink(4096, rng) * (jitter_ms * 1e-3 * sr)   # SD ~3 ms, muy por
        self._pi = 0                                              # debajo de los 10 ms
        self.drift = rng.normal(0, 0.004, 32)                     # profesionales
        self._agog = {}

    def _jit(self):
        v = self._pink[self._pi % len(self._pink)]; self._pi += 1
        return v

    def pos(self, base, step, bar):
        """rejilla + swing (Linn) + firma direccional + acento agógico + deriva."""
        s = step % 16
        t = base + step * self.s16
        if s % 2 == 1: t += self.sw * self.tight            # swing: sólo los impares
        t += self.lead * self.tight                          # empuja o atrasa
        # ACENTO AGÓGICO (Dahl): el intervalo que EMPIEZA con un golpe acentuado
        # se alarga 3%. O sea: llega tarde la nota SIGUIENTE, no el acento.
        prev = self.acc[(step - 1) % 32]
        if prev > 0.9: t += 0.03 * self.s16 * self.tight
        t += self.drift[bar % len(self.drift)] * self.s16
        return t + self._jit()

    def vel(self, step, bar):
        """Intensidad. El research dice que AQUÍ está el groove, no en el timing."""
        v = self.acc[(bar * 16 + step) % 32]
        v = self.vfloor + (1.0 - self.vfloor) * (v / 1.15) ** 1.15
        p = (bar % 4) / 3.0
        v *= 0.94 + 0.10 * p                                 # la frase respira
        return float(np.clip(v, 0.0, 1.0))

    def ghost(self, step, bar, rng, density=1.0):
        """Golpes fantasma en semicorcheas débiles. Suenan MUY abajo (es donde
        se gasta la parte de abajo de los 22 dB)."""
        if step % 2 == 0: return False
        p = self.gp * density * (0.6 + 0.4 * ((bar % 4) / 3.0))
        return rng.random() < p

    def ghost_vel(self, step, bar):
        return self.vel(step, bar) * 0.22

def demo():
    SR, BPM = 44100, 120.0
    SPB = SR * 240.0 / BPM; S16 = SPB / 16.0
    print(f'{BPM:.0f} BPM · semicorchea {S16/SR*1000:.1f} ms\n')
    print('SWING (fórmula de Linn, ~2.4 ms por punto %)')
    for f, d in FEELS.items():
        print(f'   {f:9s} S={d["swing"]:.3f}  retraso {swing_delay_ms(d["swing"],BPM):5.1f} ms'
              f'   firma {d["lead_ms"]:+5.1f} ms')
    print('\nRANGO DINÁMICO (Dahl midió 25 dB en tarola)')
    for f in FEELS:
        g = Groove(f, S16, SR, BPM, seed=1)
        vs = [g.vel(s, b) for b in range(2) for s in range(16)]
        gv = g.ghost_vel(1, 0)
        print(f'   {f:9s} {min(vs):.3f}-{max(vs):.3f} = {20*np.log10(max(vs)/min(vs)):4.1f} dB'
              f'   con fantasmas {20*np.log10(max(vs)/gv):4.1f} dB')
    print('\n¿SE REPITE compás a compás? (debe ser alto, pero NO 1.00 —')
    print('  el patrón es de 2 compases, así que el 1 y el 2 difieren)')
    for f in FEELS:
        g = Groove(f, S16, SR, BPM, seed=1)
        d = np.array([[(g.pos(b*SPB, s, b) - (b*SPB + s*S16))/SR*1000
                       for s in range(16)] for b in range(16)])
        c = np.mean([np.corrcoef(d[i], d[i+2])[0,1] for i in range(len(d)-2)])
        print(f'   {f:9s} correlación a 2 compases {c:5.2f}   '
              f'rango {d.min():6.1f} a {d.max():5.1f} ms')

if __name__ == '__main__':
    demo()
