# Dataset de 30 Personas Sintéticas — Plantilla C

**Propósito:** Validación empírica del modelo de fusión de M1 (Plantilla C) y testeo de las reglas implementadas (floor rule, ponderación adaptativa, agregación de B5 NLP).

**Archivos asociados:**
- `personas_sinteticas_M1_plantilla_c.xlsx` — Dataset principal con 4 hojas
- `personas_sinteticas_M1_plantilla_c.json` — Misma información en formato programático
- `personas_generator.py` — Definición de personas y modelo de scoring (reproducible)

---

## 1. Estructura del dataset

El conjunto contiene 30 personas distribuidas equitativamente en los tres perfiles MiFID II:

| Perfil resultante esperado | Personas | IDs |
|---|---|---|
| Conservador | 10 | CO01–CO10 |
| Moderado | 10 | MO01–MO10 |
| Agresivo | 10 | AG01–AG10 |

De las 30 personas, **10 son perfectamente coherentes** (las respuestas y textos forman un retrato consistente del perfil) y **20 incorporan incoherencias intencionadas** que reproducen patrones reales observados en cuestionarios MiFID II:

- 4 conservadores coherentes + 6 con incoherencias
- 3 moderados coherentes + 7 con incoherencias
- 3 agresivos coherentes + 7 con incoherencias

## 2. Catálogo de tipos de incoherencia

Las incoherencias diseñadas cubren ocho patrones distintos que un sistema de scoring robusto debe gestionar correctamente:

### 2.1 Activación de la floor rule

Cuando P5 ≤ 1 (impacto grave/catastrófico de pérdida) o P6 = 0 (deudas superiores al 50% de ingresos), el modelo asigna automáticamente perfil conservador independientemente del score numérico calculado. Este es el mecanismo de protección normativa más importante.

**Casos:** CO05 (Iván emprendedor, capital semilla), CO06 (Brian Dunning-Kruger), CO08 (Roberto prejubilado entusiasta), CO10 (Diego con deudas), CO07 (Marta inconsistencia P10-P11), CO09 (Paula vivienda).

### 2.2 Self-overestimation (Dunning-Kruger)

Inversor sin formación ni experiencia que marca opciones agresivas en todas las dimensiones. Su retórica eufórica en los textos libres no compensa la activación de la floor rule por su precariedad económica real.

**Caso:** CO06 (Brian, repartidor de 28 años con deudas que dice querer "hacerse rico con criptos").

### 2.3 Inconsistencia P10–P11

El inversor declara que mantendría la inversión ante una caída del 20% (P10=2 o 3) pero al mismo tiempo establece un tope de pérdida anual muy bajo (P11=1). Aparente racionalidad declarada con baja tolerancia real.

**Caso:** CO07 (Marta, profesora racional pero financieramente vulnerable).

### 2.4 Texto NLP contradictorio con respuestas cerradas

Las respuestas cerradas son cautas pero los textos libres rebosan emoción, ambición o euforia (o viceversa). Pone a prueba la integración entre B5 NLP y los demás bloques.

**Casos:** CO08 (Roberto, cerradas conservadoras pero textos eufóricos), MO07 (Ana, marca cauto pero textos ambiciosos).

### 2.5 Horizon-objective mismatch

El horizonte temporal declarado (P8) no es coherente con el objetivo de inversión (P9). Por ejemplo, horizonte inferior a 1 año + maximizar rentabilidad, o horizonte superior a 7 años + rentas estables.

**Caso:** CO09 (Paula, necesita el dinero en menos de 1 año para vivienda pero quiere maximizar rentabilidad).

### 2.6 Knowledge-experience mismatch

Alta formación financiera teórica (P1=3, posgrado/CFA) pero experiencia operativa nula (P2=0, P3=0). Patrón típico de profesionales recién certificados.

**Caso:** MO04 (Sara, CFA recién certificada que aún no ha invertido).

### 2.7 Alta varianza intra-NLP

Los tres textos libres dan scores FinBERT muy dispersos entre sí (positivo, negativo y neutral mezclados). La media B5 puede ser engañosa: oculta una incoherencia interna que el modelo puede detectar como métrica de auditoría conductual.

**Casos:** MO05 (Pablo comercial, optimista en abstracto pero ansioso ante pérdidas concretas), MO06 (Elena freelance, racional pero matizada por su realidad económica), AG06 (Manuel ejecutivo, admite estrés interno pese a perfil agresivo declarado).

### 2.8 Capacidad financiera insuficiente vs voluntad declarada

El inversor tiene voluntad y conocimientos para asumir riesgo, pero su realidad económica (ingresos, ahorro, fondo de emergencia) no lo permite. El bloque B2 actúa como ancla.

**Casos:** MO06 (Elena freelance ingresos volátiles), CO10 (Diego con deudas).

### 2.9 Sustainability override

Combinación de ESG estricto como requisito (P12=3) con objetivos de rentabilidad altos. Genera tensión que se manifestará en M2 al filtrar el universo de activos.

**Casos:** MO09 (Patricia profesora ESG), AG08 (Javier sostenibilidad).

### 2.10 Tolerancia atípica unidimensional

Inversor coherentemente agresivo o moderado en casi todas las dimensiones excepto una, donde marca una opción más conservadora que rompe el patrón sin invalidarlo.

**Casos:** AG04 (David, NLP con cautela ligera), AG05 (Beatriz, tope 15% pérdida), AG09 (Laura, poca experiencia operativa pero el resto agresivo).

## 3. Validación numérica

Tras aplicar el modelo de Plantilla C a las 30 personas, se observa una coincidencia del **100%** entre el perfil objetivo (definido por construcción) y el perfil resultante (calculado por el modelo). Esto valida que:

- La regla de suelo se activa correctamente en los 6 casos diseñados para ello.
- La fórmula de ponderación adaptativa por horizonte produce los rangos esperados.
- La agregación por media de los 3 scores NLP modula apropiadamente sin distorsionar.

Los scores finales se distribuyen así:

| Banda | Conservadores | Moderados | Agresivos |
|---|---|---|---|
| Mínimo | 0.260 | 0.570 | 0.844 |
| Mediana | ~0.45 | ~0.62 | ~0.90 |
| Máximo | 0.926 (con floor) | 0.649 | 0.985 |

Un detalle relevante: el conservador CO05 (Iván) tiene score numérico 0.926 —que sin floor rule lo clasificaría como agresivo— pero la regla de suelo lo protege correctamente.

## 4. Casos especiales para validación de tests

Los siguientes casos son particularmente útiles como tests unitarios del modelo:

**Test de la floor rule cerca del corte.** MO10 (Hugo, P5=2) es el caso límite que NO activa floor rule. Si un futuro cambio en el código accidentalmente lo trata como ≤1, este caso lo detectaría.

**Test del corte 0.65–0.66 (moderado/agresivo).** MO10 termina en 0.649 y CO06 (sin floor) acabaría en 0.665. Cualquier modificación de la fórmula que altere el corte se detectaría aquí.

**Test del corte 0.35–0.36 (conservador/moderado).** CO03 (José estudiante) termina en 0.303 sin floor rule, dejando margen pero confirmando que el cálculo de bloques bajos es correcto.

**Test de la agregación NLP.** MO05 (Pablo) tiene scores individuales 1.0, 0.0, 0.5 → media 0.5. Si la implementación cambiara accidentalmente a mediana o min/max, este caso lo detectaría.

**Test de los pesos por horizonte.** CO09 (P8=0) y AG09 (P8=3) son los extremos del eje. Cualquier error en el lookup de pesos en `WEIGHTS_BY_HORIZON` sería evidente.

## 5. Cómo cargar el dataset programáticamente

```python
import json

with open("personas_sinteticas_M1_plantilla_c.json", encoding="utf-8") as f:
    personas = json.load(f)

# Acceso al primer caso conservador
co01 = personas[0]
print(co01["nombre"])  # "María González"
print(co01["scores_calculados"]["score_final"])  # 0.260

# Filtrar incoherentes
incoherentes = [p for p in personas if not p["coherente"]]
assert len(incoherentes) == 20

# Filtrar por floor rule activa
floor_activos = [p for p in personas if p["scores_calculados"]["floor_rule_activa"]]
print(f"Casos con floor rule: {len(floor_activos)}")  # 8
```

## 6. Limitaciones conocidas del dataset

Algunas características del dataset deben tenerse presentes al usarlo:

**Scores FinBERT como proxy.** Los valores P13_finbert, P14_finbert, P15_finbert son aproximaciones manuales basadas en el contenido de los textos. En el pipeline real de M1, estos valores serán reemplazados por la salida directa del modelo FinBERT zero-shot tras la traducción. Esperan ligera variabilidad respecto al proxy.

**No hay ruido natural en respuestas.** Las respuestas cerradas son enteros perfectos sin error de medida. Los inversores reales pueden tener pequeñas inconsistencias por respuesta apresurada o ambivalencia. Una extensión natural sería añadir ruido gaussiano controlado para tests de robustez.

**Dataset balanceado por construcción.** La distribución 10/10/10 no refleja necesariamente la población real de inversores retail, donde los moderados suelen ser mayoría. Para evaluación de modelos predictivos posteriores, sería deseable un dataset adicional con distribución poblacional realista.

**Cobertura limitada de combinatoria.** No se exploran sistemáticamente todas las combinaciones posibles de los 12 ítems cerrados (3⁹ × 4 × 3 ≈ 250 mil combinaciones). El dataset cubre patrones representativos, no exhaustivos.

---

*Generado para TFM: Roboadvisor personalizado para el inversor retail. Mayo 2026.*
