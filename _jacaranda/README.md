# JACARANDA — material fuente

> **Historia del nombre.** Este material se generó como OFRENDA (ocho fuerzas
> naturales sin cara). Después André decidió borrar los dos discos JACARANDA
> viejos —los sintetizados con el motor anterior— y **mudar esta música al
> nombre JACARANDA**, con nombres de rola nuevos y místicos. El disco es el
> mismo audio; cambió la identidad. Los archivos de `_raw/` conservan los
> títulos que les puso Gemini.

`_raw/` son los archivos tal cual salieron de Gemini, sin tocar. Se guardan
porque son el original: si algún día hay que rehacer el master o resecuenciar,
se parte de aquí y no de un archivo ya procesado.

`_tmp/` NO está en el repo (3.6 GB de WAVs intermedios). Se regenera solo
corriendo `make_ofrenda.py`.

## Qué archivo es qué rola

Gemini bautiza con títulos poéticos que no dicen de cuál prompt salieron, así
que el mapeo se resolvió midiendo con `analiza.py` y `rejilla.py`:

| archivo | rola | tono medido | BPM |
|---|---|---|---|
| Before_The_Sun_Hits.mp3 | 01 VÍSPERA | Fa mayor | 119.935 |
| Cooling_The_Soil.mp3 | 02 AUGURIO | Fa mayor | 119.965 |
| Glow_in_the_Deep.mp3 | 03 FULGOR | Do mayor | 119.955 |
| Murmuration_at_Dusk.mp3 | 04 LETANÍA | Do mayor | 119.925 |
| Sky_Catches_Fire.mp3 | 05 EPIFANÍA | Re menor / Fa mayor | 119.950 |
| Midnight_at_Noon.mp3 | 06 PENUMBRA | La menor | 119.940 |
| Salt_Flat_Mirror.mp3 | 07 ÉTER | Mi menor | 119.780 |
| Between_The_Tides.mp4 | 08 VESTIGIO | Re menor | 119.950 |
| When_The_Horizon_Cools.mp3 | **fuera del set** | Sib menor | **125.065** |

`When_The_Horizon_Cools` fue el primer intento de la 01. Queda fuera por dos
razones medidas: va a 125 BPM contra los 120 de las otras ocho (confirmado en
los 4 tramos, no es error de medición), y su tonalidad es la peor definida de
todas (correlación 0.53 contra 0.64–0.82 del resto). No se borra: es alterna.

## Lo que Gemini NO respetó

- **La duración.** Se pidieron 6 y 7 minutos; todas salieron entre 2:41 y 2:57.
  Parece haber un tope cerca de 3 minutos. Por eso el set dura 20.8 min y no
  una hora: para un set largo hacen falta más rolas, no rolas más largas.
- **Las tonalidades.** Se pidieron Fa menor, Do menor, Sol menor, Re menor, Fa
  mayor, Re menor, La menor, Fa menor. Salió otra cosa. El arco armónico del
  set se rehízo sobre lo medido.
- **El tempo exacto.** Se pidieron 121 BPM y entregó 120.

## EPIFANÍA salió y volvió

`Sky_Catches_Fire.mp3` se quitó del set porque André dijo "parece Avicii"
señalando el minuto 11:30. Después aclaró que se había confundido y que esa sí
le gustaba, y volvió a su lugar. **Queda anotado para no sacarla otra vez por
error.**

El diagnóstico original sigue siendo válido como lección de prompt: le pedí a
Gemini *"bright, vast, transcendent"* y *"the peak of the record"* en tonalidad
MAYOR — esa es la receta del EDM de estadio, y la siguió. Si algún día una rola
sale demasiado eufórica, el culpable es el prompt, no el modelo.
