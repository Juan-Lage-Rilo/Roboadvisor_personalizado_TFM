# Guía Metodológica del Cuestionario MiFID II — Plantilla C

**Roboadvisor personalizado para el inversor retail**
*Trabajo Fin de Máster · Módulo M1 — Perfilado del Inversor*

---

## 1. Propósito y filosofía de diseño

La Plantilla C es uno de los tres modelos de cuestionario diseñados para el módulo M1 del roboadvisor. Su característica distintiva, frente a las plantillas A (scoring lineal) y B (mínimo denominador), es que **los pesos asignados a cada dimensión del perfil no son fijos, sino que se ajustan dinámicamente en función del horizonte temporal declarado por el inversor**.

La hipótesis subyacente es que la importancia relativa de las distintas dimensiones del perfil cambia según el plazo de la inversión. Para un inversor con horizonte inferior a un año, la situación financiera presente —su capacidad de soportar pérdidas en el corto plazo— es más crítica que sus objetivos a largo plazo. En cambio, para un inversor con horizonte superior a siete años, los objetivos de inversión y la actitud psicológica frente al riesgo (capturada vía análisis de sentimiento) ganan peso, mientras que la fotografía financiera presente importa relativamente menos.

Esta concepción adaptativa convierte el horizonte temporal —pregunta P8— en un metaparámetro del modelo, no en un score más entre otros. Es la decisión de diseño más diferenciadora de Plantilla C respecto a la práctica habitual de banca retail.

## 2. Marco regulatorio

El cuestionario se construye sobre la base normativa europea aplicable al asesoramiento financiero automatizado:

| Norma | Aspecto regulado |
|---|---|
| Directiva 2014/65/UE (MiFID II), Art. 25.2 | Obligación de evaluación de idoneidad |
| Reglamento Delegado (UE) 2017/565, Art. 54 | Información sobre objetivos y situación financiera |
| Reglamento Delegado (UE) 2017/565, Art. 55 | Información sobre conocimientos y experiencia |
| Reglamento Delegado (UE) 2021/1253 | Integración de preferencias de sostenibilidad (Green MiFID) |
| Directrices ESMA35-43-3172 (2023) | Aplicación práctica de los requisitos de idoneidad |

La normativa prescribe **categorías de información** a recabar, no preguntas concretas. Esto significa que el diseño específico del cuestionario es una decisión metodológica de la entidad —en este caso, del autor del TFM— siempre que cubra los bloques mandatorios. La Plantilla C cumple esta exigencia y va más allá al introducir el bloque de análisis de sentimiento.

## 3. Estructura del cuestionario: cinco dimensiones

El cuestionario se organiza en cinco bloques que totalizan 15 preguntas: 12 cerradas con respuesta puntuada y 3 abiertas que alimentan al modelo NLP.

### 3.1 Bloque 1 — Conocimientos y experiencia (3 preguntas)

Este bloque, mandatorio por el Art. 55.1 del Reglamento Delegado, recoge información sobre la familiaridad del inversor con instrumentos financieros, su historial operativo y su formación. Se cubre mediante tres preguntas: nivel de estudios financieros (P1), tipo de productos con los que ha operado en los últimos tres años (P2) y frecuencia operativa (P3).

La normalización del score se realiza dividiendo la suma de puntos obtenidos entre 10, que es el máximo teórico (3 + 4 + 3). El resultado cae en el intervalo [0, 1], donde 0 representa un inversor sin conocimientos ni experiencia y 1 un perfil profesional.

### 3.2 Bloque 2 — Situación financiera (4 preguntas)

Mandatorio por el Art. 54.3, este bloque mide la capacidad económica real del inversor para asumir riesgo. Las cuatro preguntas son: capacidad de ahorro mensual (P4), impacto subjetivo de una pérdida total (P5), nivel de endeudamiento (P6) y existencia de fondo de emergencia (P7).

La P5 y la P6 son particularmente sensibles porque activan la regla de suelo (ver sección 6). El máximo teórico de puntos es 11 (3 + 3 + 3 + 2), valor que se utiliza como denominador para normalizar el score del bloque al rango [0, 1].

### 3.3 Bloque 3 — Objetivos de inversión (4 preguntas)

Cubierto por el Art. 54.2, este bloque captura el horizonte (P8), la finalidad de la inversión (P9), la reacción simulada ante una caída del 20% (P10) y la pérdida máxima anual aceptable (P11). El máximo teórico de puntos es 12 y se normaliza al intervalo [0, 1].

La P8 cumple un doble rol: contribuye al score del bloque y, simultáneamente, determina los pesos que se aplicarán a todos los bloques en la fórmula final. Esta dualidad es la que define a Plantilla C como modelo adaptativo.

### 3.4 Bloque 4 — Preferencias de sostenibilidad (1 pregunta)

Obligatorio desde agosto de 2022 por el Reglamento Delegado 2021/1253, este bloque integra las preferencias ESG del inversor mediante una pregunta de ordinalidad creciente (P12) que va desde "no tengo preferencias" hasta "es un requisito obligatorio". Su score se normaliza dividiendo entre 3.

En el modelo de scoring, este bloque tiene un peso fijo del 5% en cualquier escenario de horizonte. La razón es que ESG funciona más como filtro del universo de activos en el módulo M2 que como modulador del nivel de riesgo. Su contribución al score final es por tanto modesta pero no nula.

### 3.5 Bloque 5 — Análisis de sentimiento NLP (3 preguntas abiertas)

Este es el bloque que constituye la **innovación diferencial del TFM** respecto a los cuestionarios convencionales. Se compone de tres preguntas de respuesta libre, cada una orientada a capturar una dimensión conductual distinta.

La pregunta P13 indaga la orientación general del inversor hacia el riesgo —su actitud declarada en abstracto. La pregunta P14 plantea un escenario hipotético concreto (caída del 30% a los seis meses) y solicita la reacción esperada, midiendo la respuesta conductual ante pérdidas reales. La pregunta P15 indaga la tolerancia psicológica continua a la volatilidad de mercado, incluyendo elementos como el sueño y la atención cotidiana a la cartera.

Cada respuesta se procesa de forma independiente con FinBERT (ProsusAI), modelo basado en BERT específicamente fine-tuneado sobre corpus financiero. El output del modelo (positivo, neutral, negativo) se mapea a valores numéricos: 1.0 para sentimiento positivo, 0.5 para neutral y 0.0 para negativo. Posteriormente, los tres scores individuales se agregan mediante media aritmética para obtener el score final del bloque B5.

La justificación de usar múltiples textos cortos en lugar de uno largo es doble. Por un lado, mejora la robustez estadística: con n=3 muestras, el error de medición esperado disminuye aproximadamente en un factor de √3 frente a una única respuesta. Por otro, permite triangular dimensiones conductuales independientes, lo que reduce el riesgo de capturar únicamente la formulación retórica habitual del inversor en lugar de su disposición real.

## 4. Pesos adaptativos por horizonte temporal

La matriz de pesos de Plantilla C es la siguiente:

| Horizonte (P8) | B1 | B2 | B3 | B4 | B5 |
|---|---|---|---|---|---|
| Menos de 1 año | 0.15 | **0.45** | 0.25 | 0.05 | 0.10 |
| 1 a 3 años | 0.20 | 0.30 | **0.35** | 0.05 | 0.10 |
| 3 a 7 años | 0.20 | 0.20 | **0.40** | 0.05 | 0.15 |
| Más de 7 años | 0.15 | 0.15 | **0.45** | 0.05 | 0.20 |

Cada fila suma exactamente 1.00, garantizando que el score final permanezca en el intervalo [0, 1] independientemente del horizonte seleccionado. Las celdas en negrita identifican el bloque dominante en cada escenario.

La lógica detrás de esta distribución responde a tres principios. Primero, la situación financiera presente (B2) decrece monotónicamente en peso conforme aumenta el horizonte, pasando del 45% en escenarios cortoplacistas al 15% en horizontes superiores a siete años. Segundo, los objetivos de inversión (B3) crecen de forma simétrica, del 25% al 45%. Tercero, el componente NLP (B5) se duplica entre los extremos del horizonte, del 10% al 20%, reflejando que el sesgo conductual psicológico cobra mayor relevancia cuando el inversor debe sostener una estrategia durante años con sus inevitables periodos de drawdown.

Los conocimientos (B1) y la sostenibilidad (B4) se mantienen aproximadamente constantes a lo largo del eje temporal porque son atributos relativamente independientes del plazo de inversión.

## 5. Fórmula de scoring final

El score final del inversor se calcula mediante la siguiente expresión:

```
Score_final = w₁(h)·S₁ + w₂(h)·S₂ + w₃(h)·S₃ + w₄·S₄ + w₅(h)·S₅
```

donde *h* es el índice del horizonte (0 a 3), *Sᵢ* son los scores normalizados de cada bloque y *wᵢ(h)* son los pesos correspondientes a cada bloque condicionados al horizonte.

El score final cae siempre en el intervalo [0, 1] por construcción, dado que cada *Sᵢ* está en [0, 1] y los pesos suman uno. Esta propiedad es crítica para que el output sea interpretable y comparable entre inversores con horizontes distintos.

## 6. La regla de suelo (floor rule)

Antes de aplicar la fórmula anterior, el modelo evalúa una condición de seguridad regulatoria que opera como salvaguarda independiente del score numérico calculado. Esta condición es:

```
si  P5 ≤ 1   o   P6 = 0   →   perfil = Conservador
```

Es decir, si el inversor declara que una pérdida total tendría impacto catastrófico o grave sobre su nivel de vida (P5), o que sus deudas representan más del 50% de sus ingresos regulares (P6), el sistema asigna automáticamente un perfil conservador con independencia del score final calculado.

Esta regla refleja el principio normativo del **mínimo denominador** establecido implícitamente por las Directrices ESMA: la capacidad de soportar pérdidas no puede ser compensada por otros indicadores de tolerancia al riesgo. Dicho de otro modo, un inversor con alta cultura financiera y voluntad de asumir riesgo, pero sin colchón económico real, debe ser tratado como conservador. La normativa europea es clara al respecto: la idoneidad no se decide por mayoría ni promedio entre dimensiones, sino por la dimensión más restrictiva cuando esta concierne a la capacidad económica.

## 7. Mapeo del score al perfil y a la restricción de volatilidad

El score final, una vez verificada la regla de suelo, se traduce en uno de los tres perfiles MiFID II canónicos según el siguiente mapeo:

| Score final | Perfil asignado | σ máxima anual (M3) |
|---|---|---|
| 0.00 — 0.35 | Conservador | 8% |
| 0.36 — 0.65 | Moderado | 15% |
| 0.66 — 1.00 | Agresivo | 25% |

La columna de volatilidad máxima es la conexión directa entre el módulo M1 (perfilado) y el módulo M3 (optimización de cartera). Concretamente, esta restricción se inyecta como cota superior en el problema de optimización de Markowitz o en el algoritmo HRP, garantizando que la cartera resultante no exceda el riesgo tolerable por el perfil del inversor.

Los umbrales de volatilidad (8%, 15%, 25%) se han calibrado tomando como referencia los rangos típicos de carteras retail observados en proveedores como Indexa Capital, MyInvestor Roboadvisor y Vanguard LifeStrategy. Estos valores son revisables y justificables empíricamente mediante backtesting en M4.

## 8. Ejemplo numérico completo

Para ilustrar el funcionamiento integral del modelo, consideremos un inversor con horizonte de 3 a 7 años (h=2) y los siguientes scores por bloque tras responder el cuestionario:

```
S₁ = 0.60     (formación universitaria, ETFs, frecuencia ocasional)
S₂ = 0.55     (15-30% ahorro, impacto moderado, hipoteca media, fondo parcial)
S₃ = 0.67     (horizonte 3-7y, crecimiento moderado, mantendría, 5-15%)
S₄ = 0.67     (preferencia ESG no requisito)
S₅ = 0.55     (media de tres respuestas NLP de tono neutral-positivo)
```

Con los pesos correspondientes a h=2 (0.20, 0.20, 0.40, 0.05, 0.15), la fórmula produce:

```
Score_final = 0.20·0.60 + 0.20·0.55 + 0.40·0.67 + 0.05·0.67 + 0.15·0.55
            = 0.120 + 0.110 + 0.268 + 0.033 + 0.083
            = 0.614
```

Como 0.614 cae en la banda [0.36, 0.65] y ni P5 ni P6 activan la regla de suelo, el inversor es clasificado como **Moderado** y se asigna una restricción de volatilidad máxima del 15% anual a su cartera optimizada en M3.

## 9. Justificación metodológica para la memoria del TFM

Plantilla C aporta tres contribuciones académicas defendibles en el documento del TFM.

La primera es la **adaptatividad de los pesos**, que se distancia de los modelos lineales fijos predominantes en banca retail. Esta decisión se puede justificar apelando a la literatura sobre lifecycle investing —Bodie, Merton y Samuelson (1992) entre otros— que argumenta que la composición óptima de cartera no es invariante en el tiempo y debe responder a la duración de la inversión. La transposición de esa idea al perfilado, no solo a la cartera, es la innovación.

La segunda contribución es la **integración del análisis de sentimiento** vía FinBERT como dimensión cuantitativa en un cuestionario MiFID II. Hasta donde alcanza la revisión de literatura realizada para el TFM, ninguno de los roboadvisors comerciales en España (Indexa, MyInvestor, Finizens, InbestMe) incorpora análisis NLP en su perfilado. La aportación se enmarca en la línea de investigación de Xiao et al. (2025) sobre uso de LLMs en finanzas, pero con un enfoque más conservador y reproducible: zero-shot validation sobre Financial PhraseBank, sin fine-tuning ni dependencia de modelos cerrados.

La tercera contribución es la **regla de suelo explícita** como mecanismo de cumplimiento normativo dentro del algoritmo. Aunque conceptualmente la regla está implícita en las Directrices ESMA, su implementación algorítmica explícita en un sistema automatizado de asesoramiento es una decisión de diseño que merece desarrollo en la memoria, especialmente en el capítulo de cumplimiento regulatorio.

## 10. Limitaciones y trabajo futuro

El modelo presenta tres limitaciones reconocidas que deben documentarse en la memoria.

Primero, los pesos adaptativos de la matriz son **calibrados a priori** por el autor con base en literatura financiera estándar, no aprendidos a partir de datos. Una extensión natural sería estimar los pesos óptimos mediante regresión sobre un dataset etiquetado de perfiles MiFID II reales, aunque la disponibilidad de tales datos está limitada por confidencialidad bancaria.

Segundo, FinBERT está entrenado sobre corpus en inglés y, dado que el cuestionario es en español, requiere una etapa de traducción mediante Helsinki-NLP/opus-mt-es-en. Esta traducción introduce un riesgo de pérdida semántica que debe evaluarse empíricamente, idealmente comparando con modelos nativos en español como pysentimiento/robertuito-sentiment-analysis.

Tercero, el modelo no captura **dinámicas temporales**: si el inversor responde el cuestionario en un momento de optimismo o pesimismo de mercado, el score NLP puede sesgarse. Una mitigación posible es repetir el perfilado periódicamente —cada 12 meses, lo que también es exigible normativamente— y promediar scores históricos para suavizar fluctuaciones psicológicas puntuales.

---

*Documento generado como parte del módulo M1 — Perfilado del Inversor.
Última actualización: mayo 2026.*
