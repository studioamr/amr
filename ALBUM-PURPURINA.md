# PURPURINA — 8 rolas · minimal techno con alma de pop sueco

**AMR · 126 BPM · oro purpurina sobre azul noche**

## DE DÓNDE VIENE (y el límite, dicho claro)

André puso "Super Trouper" y pidió un set minimal techno con ese sabor.

**No se hacen versiones de esas canciones.** Esas melodías tienen dueño y no
entran aquí ni citadas ni "parecidas a propósito". Lo que sí se puede tomar —
porque es color, no propiedad — es la ESCUELA:

- tonalidades **mayores brillantes** con una tristeza abajo (la euforia-triste
  escandinava: suena feliz y te deja un nudo)
- melodías de sintetizador **cantables**, que se sienten himno sin voz
- **arpegios** que giran como bola de espejos
- progresiones que **suben** y te levantan el pecho
- brillo de salón de baile, lentejuela, luz de reflector

Eso traducido a minimal techno: repetición hipnótica, pocos elementos, mucho
espacio — pero con corazón de pop. **Minimal que te hace sentir algo**, que es
lo raro del género.

## POR QUÉ "PURPURINA"

Es la lentejuela y el reflector, pero también lo que queda tirado en el piso
cuando ya se fue todo el mundo. Esas dos cosas al mismo tiempo SON el disco:
la fiesta y la melancolía en la misma rola. Y va con los títulos de una palabra
en español del catálogo (MICELIO, SUBSUELO, JACARANDA, OFRENDA, ECO).

## LA IDENTIDAD

| | |
|---|---|
| color | **oro purpurina `#D9A441`** sobre **azul noche `#1B2450`** |
| acento claro | `#F2D479` (el destello del reflector) |
| formato | GLITTER 12″ · edición de 8 |
| tempo | 126 BPM (mezclable con el catálogo) |
| arte | una bola de espejos que se desarma — las lentejuelas cayendo |

## EL ARCO — ocho momentos de una noche de salón

| # | rola | qué es |
|---|------|--------|
| 01 | VESTIDOR | antes de salir; el arpegio solo, sin bombo |
| 02 | REFLECTOR | se prende la luz; entra el groove |
| 03 | LENTEJUELA | brillo puro, el arpegio gira |
| 04 | SALÓN | la pista llena; lo más físico |
| 05 | PURPURINA | **el pico** — la melodía-himno, mayor y brillante |
| 06 | ESPEJOS | la bola gira, la melodía se fragmenta |
| 07 | ÚLTIMA | la última canción de la noche; agridulce |
| 08 | CONFETI | prenden las luces, el piso lleno de brillos, te vas |

## MATERIAL MEDIDO (31-jul-2026)

Seis archivos generados en Gemini. `Porcelain_and_Light` resultó ser **el mismo
archivo** que `01-VESTIDOR` (2:55, 125.165 BPM, Mi menor — métricas idénticas),
así que son **6 rolas únicas, no 7**.

| archivo | largo | BPM real | tono | juez |
|---|---|---|---|---|
| 01-VESTIDOR (Porcelain_and_Light) | 2:55 | 125.165 | Mi menor | ✅ |
| Before_The_Curtains_Close | 2:51 | 124.945 | **Fa# MAYOR** (r .83) | ✅ |
| Light_Through_Glass | 2:56 | 124.945 | **La# MAYOR** (r .71) | ✅ |
| Sunlight_On_A_Closed_Door | 2:59 | 124.970 | Sol# menor / Mi mayor (empate .78) | ✅ |
| Keys_Left_on_the_Table | 2:47 | **120.530** | Fa# menor | ✅ tras REPISA |
| Before_the_Light_Returns | 2:51 | 124.960 | Sol menor | ❌ **descartada** |

### Lo que dicen los números

- **Cinco de seis caen en 124.9–125.2 BPM.** Regalo: el set se arma casi sin
  estirar. La rara es Keys (120.5), que sí hay que llevar a 125.
- **Before_the_Light_Returns no se salva.** El barrido probó 24 combinaciones de
  repisa (f0 2000–3500 Hz × +1.5 a +6.5 dB) y **ninguna** cruza el mínimo de
  centroide. Está apagada de origen; forzarla más sonaría artificial. Se
  descarta — no se mete una rola rota a un disco por completar el número.
- **Keys necesitó +6.5 dB @ 2000 Hz**, casi el doble que cualquier rola de
  MICELIO (+3.5/+4.0). Quedó aprobada (centroide 1953) pero es la corrección más
  agresiva del catálogo; si suena rara al escucharla, se regenera y ya.
- **Sí hay material mayor**: Before_The_Curtains_Close (Fa# mayor, r=.83) es el
  mejor candidato a PICO, y Light_Through_Glass (La# mayor) el segundo.

### Dos lecciones de método

1. **Mi centroide ≠ el del juez.** El barrido daba 1006/1133 Hz y el juez
   1345/1387 para los mismos archivos. El barrido sirve para ORDENAR opciones;
   quien dictamina es juez.py sobre el archivo ya corregido.
2. **La repisa sube nivel y rompe el true peak.** Normalizar el pico de muestra
   a 0.98 dejó el TP en −0.1 dBTP (el juez pide ≤ −1). Hay que bajar midiendo el
   true peak en un lazo — el mismo tropiezo que con el m4a de ECO.

### Segunda tanda (SALÓN y CONFETI)

| archivo | largo | BPM real | tono | juez |
|---|---|---|---|---|
| Velvet_Salon_Hour → **SALÓN** | 2:59 | 124.950 | Re menor | ✅ limpia |
| Lights_at_Five_AM → CONFETI | 2:55 | 125.930 | Re mayor (r .51 débil) | ❌ **descartada** |

**CONFETI: se investigó antes de descartarla.** El prompt pedía que el último
tercio se quedara sin bombo, así que la hipótesis era que la cola arrastraba el
promedio y el cuerpo estaba bien. `diagnostica_confeti.py` la partió en 8 tramos
y **refutó la hipótesis**: está apagada de punta a punta (tramos de 427–1215 Hz,
la mayoría bajo 620) y sus primeros 2/3 miden 706 Hz, *peor* que la rola completa.
Comparada con SALÓN, que llega a picos de 1800–1968 Hz, no hay color. Barrido de
repisa: ninguna de 24 combinaciones la alcanza. Se descarta.

### TASA DE FALLO MEDIDA: 2 de 8

`Before_the_Light_Returns` y `Lights_at_Five_AM` salieron demasiado oscuras y sin
rescate posible. Un cuarto de lo generado. Vale la pena **medir el centroide
apenas baja el archivo**, antes de invertir tiempo en la rola.

## EL DISCO FINAL — 6 rolas aprobadas

| # | nombre | archivo | BPM | tono | brillo |
|---|--------|---------|-----|------|--------|
| 01 | VESTIDOR | Porcelain_and_Light | 125.165 | Mi menor | 1484 |
| 02 | REFLECTOR | Keys_Left_on_the_Table | **120.530** | Fa# menor | 1953 ✎ |
| 03 | LENTEJUELA | Light_Through_Glass | 124.945 | **La# MAYOR** | 1938 |
| 04 | SALÓN | Velvet_Salon_Hour | 124.950 | Re menor | 1850 |
| 05 | **PURPURINA** (pico) | Before_The_Curtains_Close | 124.945 | **Fa# MAYOR** (r .83) | 1854 |
| 06 | ÚLTIMA | Sunlight_On_A_Closed_Door | 124.970 | Sol#m / Mi mayor | 2112 |

✎ = corregida con repisa (+6.5 dB @ 2000 Hz)

`Sunlight_On_A_Closed_Door` cierra el disco: es la más brillante de las seis
(2112) y el nombre ya es una imagen de cierre. Sólo Keys (120.5) necesita
estirarse a 125; las otras cinco ya están en 124.9–125.2.

## REGLAS DE TODOS LOS PROMPTS

- **ORIGINAL** en la primera línea; **jamás** se nombra el grupo ni sus rolas
- FULL-LENGTH ≥4 min repetido dos veces (Gemini corta en ~2:50 si lo dejas)
- **NO VOCALS** — el sinte es la voz
- 126 BPM
- bajo **redondo y cálido**, nunca duro (2 strikes históricos de bajo saturado)
- NEVER: EDM, supersaw, builds de festival, drops, nada anthemic-de-estadio
  → OJO: "himno" aquí significa melodía que se canta sola, NO drop de festival.
    Ese matiz hay que dejarlo explícito o sale un Avicii (ya pasó con AURORA).
- los tonos se piden pero Gemini los ignora — se miden con analiza.py/rejilla.py
