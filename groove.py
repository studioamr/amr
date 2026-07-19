#!/usr/bin/env python3
"""GROOVE — hacer que la percusión suene TOCADA en vez de programada.

EL PROBLEMA QUE ARREGLA (diagnóstico de André, jul 2026: "siento que nos hace
falta mucho para tener el nivel de Keinemusik / Rampa / Adam Ten"):

  Hasta ahora el secuenciador ponía cada golpe así:
      pos = base + s*S16 + rng.normal(0, .0016)*SR
  Eso es RUIDO ALEATORIO alrededor de una rejilla recta. Y el groove no es
  aleatorio — el groove es un humano repitiendo EL MISMO empuje compás tras
  compás. Por eso el jitter suena suelto/descuidado en vez de tocado.

LO QUE SÍ HACE GROOVE, y está aquí:

  1. SWING       los 16avos impares se atrasan de forma CONSISTENTE (54-58%).
                 Consistente es la palabra: mismo atraso siempre, no al azar.
  2. MICROTIMING un desplazamiento fijo POR POSICIÓN dentro del compás, que se
                 repite igual cada compás. Es la "firma" del percusionista.
                 Adelantar = urgencia (el hat que empuja). Atrasar = lo laid-back.
  3. VELOCITY    patrón de intensidad por frase (2 o 4 compases), no por golpe.
                 El acento cae siempre en el mismo lugar de la frase.
  4. FANTASMAS   golpes suaves entre los principales. Es lo que llena el hueco
                 entre el 1 y el 2 y hace que suene a manos, no a caja de ritmos.
  5. DERIVA      una desviación LENTA (no por golpe) que hace que el compás 17
                 no sea idéntico al compás 1. Un humano se cansa y se acelera.

El jitter aleatorio se queda, pero MUY chico (±0.5 ms) y solo encima de todo
lo anterior — el humano tampoco es una máquina perfecta repitiendo su error.
"""
import numpy as np

# ---------------------------------------------------------------- SWING
def swing_offset(step16, amount=0.56):
    """Atraso del 16avo impar. 0.50 = recto, 0.56 = swing suave house,
    0.62 = swing marcado. Devuelve el desplazamiento en fracción de 16avo."""
    if step16 % 2 == 0: return 0.0
    return (amount - 0.5) * 2.0

# ---------------------------------------------------------------- FIRMAS
# Desplazamiento fijo por posición dentro del compás, en fracción de 16avo.
# Negativo = adelanta (empuja). Positivo = atrasa (laid-back).
# Se repite IGUAL cada compás — eso es lo que lo vuelve groove y no ruido.
FEELS = {
    # recto, para cuando quieras la máquina
    'straight': dict(swing=0.50, push=[0.0]*16, ghost=0.0),

    # house de cadera: hats que empujan un pelo, contratiempo atrasado
    'house': dict(swing=0.56,
                  push=[0.00,-0.04, 0.03,-0.02, 0.00,-0.03, 0.04,-0.02,
                        0.00,-0.04, 0.03,-0.02, 0.01,-0.03, 0.05,-0.01],
                  ghost=0.35),

    # afro: percusión adelantada, el "2 y" muy atrás — el balanceo
    'afro':   dict(swing=0.58,
                   push=[0.00,-0.05, 0.06,-0.03, 0.02,-0.04, 0.08,-0.02,
                         0.00,-0.05, 0.05,-0.03, 0.03,-0.04, 0.09,-0.03],
                   ghost=0.55),

    # laid-back: todo un pelín tarde, para lo hipnótico/melódico
    'laid':   dict(swing=0.54,
                   push=[0.00, 0.02, 0.04, 0.03, 0.01, 0.03, 0.05, 0.02,
                         0.00, 0.02, 0.04, 0.03, 0.02, 0.03, 0.06, 0.02],
                   ghost=0.25),
}

# ---------------------------------------------------------------- VELOCITY
# Intensidad por 16avo. El acento vive SIEMPRE en el mismo lugar del compás.
ACCENTS = {
    'straight': [1.0,0.55,0.7,0.55]*4,
    'house':    [1.00,0.42,0.72,0.48, 0.86,0.44,0.76,0.46,
                 0.94,0.42,0.70,0.50, 0.84,0.46,0.80,0.58],
    'afro':     [1.00,0.38,0.80,0.44, 0.72,0.52,0.88,0.40,
                 0.96,0.36,0.76,0.56, 0.68,0.50,0.92,0.62],
    'laid':     [0.94,0.46,0.68,0.50, 0.88,0.44,0.72,0.48,
                 0.90,0.46,0.66,0.52, 0.86,0.48,0.74,0.54],
}

class Groove:
    """El groove de UN instrumento. Se crea una vez y se usa todo el track.

        g = Groove('afro', S16, SR, seed=1)
        pos = g.pos(base, step, bar)      # muestra donde cae el golpe
        vel = g.vel(step, bar)            # 0..1, cuán fuerte pega
        if g.ghost(step, bar, rng): ...   # ¿va un golpe fantasma aquí?
    """
    def __init__(self, feel, s16, sr, seed=0, tight=1.0, drift_bars=16):
        f = FEELS[feel]
        self.feel = feel; self.s16 = s16; self.sr = sr
        self.swing = f['swing']; self.push = f['push']; self.gp = f['ghost']
        self.acc = ACCENTS[feel]
        self.tight = tight                     # 1.0 = fiel al feel, 0 = recto
        rng = np.random.default_rng(1000 + seed)
        # la deriva lenta: el humano se acelera y se frena a lo largo del track
        self.drift = rng.normal(0, 0.012, drift_bars)
        self.jit = 0.0005 * sr                 # ±0.5 ms, el error residual
        self._rng = rng

    def pos(self, base, step, bar):
        """Muestra exacta del golpe: rejilla + swing + firma + deriva + error."""
        s = step % 16
        off = swing_offset(s, self.swing) * 0.5
        off += self.push[s]
        off += self.drift[bar % len(self.drift)]
        off *= self.tight
        return base + (step * self.s16) + off * self.s16 + self._rng.normal(0, self.jit)

    def vel(self, step, bar, phrase=4):
        """Intensidad. El acento se repite por FRASE, no al azar por golpe."""
        v = self.acc[step % 16]
        # la frase respira: el último compás de la frase pega un poco más
        p = (bar % phrase) / max(1, phrase - 1)
        v *= 0.92 + 0.12 * p
        return float(np.clip(v * (0.75 + 0.25 * self.tight), 0.0, 1.0))

    def ghost(self, step, bar, rng, density=1.0):
        """¿Va un golpe fantasma aquí? Solo en 16avos débiles, y con más
        probabilidad conforme avanza la frase — así crece la tensión."""
        s = step % 16
        if s % 2 == 0: return False            # los fuertes no son fantasmas
        p = self.gp * density * (0.6 + 0.4 * ((bar % 4) / 3.0))
        return rng.random() < p

def demo():
    """Compara a ojo la rejilla recta contra el groove, en milisegundos."""
    SR = 44100; BPM = 122.0
    SPB = SR * 240.0 / BPM; S16 = SPB / 16.0
    print(f'{BPM:.0f} BPM · un 16avo = {S16/SR*1000:.1f} ms\n')
    print(f'{"paso":>5} {"recto":>9} {"house":>9} {"afro":>9} {"laid":>9}   (ms desde el 1)')
    gs = {k: Groove(k, S16, SR, seed=3) for k in ('straight','house','afro','laid')}
    for st in range(8):
        row = [f'{(g.pos(0, st, 0))/SR*1000:9.1f}' for g in gs.values()]
        print(f'{st:>5} ' + ' '.join(row))
    print()
    print(f'{"paso":>5} {"vel recto":>10} {"vel house":>10} {"vel afro":>10}')
    for st in range(8):
        print(f'{st:>5} ' + ' '.join(
            f'{gs[k].vel(st,0):10.2f}' for k in ('straight','house','afro')))
    rng = np.random.default_rng(7)
    n = sum(gs['afro'].ghost(st, b, rng) for b in range(8) for st in range(16))
    print(f'\nfantasmas afro en 8 compases: {n} de 128 posiciones')

if __name__ == '__main__':
    demo()
