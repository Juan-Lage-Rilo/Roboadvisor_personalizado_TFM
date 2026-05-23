"""
Generador de 30 personas sintéticas para validación de Plantilla C (M1).
Cada persona incluye:
- Respuestas P1-P12 (cerradas)
- Textos P13, P14, P15 + scores FinBERT esperados (proxy)
- Marcador de coherencia/incoherencia con descripción
- Cálculo de scores por bloque y score final aplicando floor rule
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path

# ─────────────────────────────────────────────────────────
# Definiciones del modelo Plantilla C
# ─────────────────────────────────────────────────────────

WEIGHTS_BY_HORIZON = {
    0: (0.15, 0.45, 0.25, 0.05, 0.10),   # < 1 año
    1: (0.20, 0.30, 0.35, 0.05, 0.10),   # 1–3 años
    2: (0.20, 0.20, 0.40, 0.05, 0.15),   # 3–7 años
    3: (0.15, 0.15, 0.45, 0.05, 0.20),   # > 7 años
}

# Máximos teóricos por bloque (para normalización a [0,1])
MAX_B1 = 10   # P1(3) + P2(4) + P3(3)
MAX_B2 = 11   # P4(3) + P5(3) + P6(3) + P7(2)
MAX_B3 = 12   # P8(3) + P9(3) + P10(3) + P11(3)
MAX_B4 = 3    # P12(3)


@dataclass
class Persona:
    id: str
    nombre: str
    edad: int
    contexto: str
    perfil_objetivo: str         # 'conservador', 'moderado' o 'agresivo'
    coherente: bool
    tipo_incoherencia: Optional[str]
    descripcion_incoherencia: Optional[str]

    # Respuestas cerradas (puntos crudos)
    p1: int
    p2: int
    p3: int
    p4: int
    p5: int
    p6: int
    p7: int
    p8: int
    p9: int
    p10: int
    p11: int
    p12: int

    # Textos libres
    p13_texto: str
    p14_texto: str
    p15_texto: str

    # Scores FinBERT esperados (proxy: 0.0 negativo, 0.5 neutral, 1.0 positivo)
    p13_finbert: float
    p14_finbert: float
    p15_finbert: float


def calcular_scores(p: Persona) -> Dict[str, Any]:
    """Calcula scores por bloque, score final y perfil aplicando Plantilla C."""
    s1 = (p.p1 + p.p2 + p.p3) / MAX_B1
    s2 = (p.p4 + p.p5 + p.p6 + p.p7) / MAX_B2
    s3 = (p.p8 + p.p9 + p.p10 + p.p11) / MAX_B3
    s4 = p.p12 / MAX_B4
    s5 = (p.p13_finbert + p.p14_finbert + p.p15_finbert) / 3

    # Pesos según horizonte (P8)
    w = WEIGHTS_BY_HORIZON[p.p8]
    score_final = w[0]*s1 + w[1]*s2 + w[2]*s3 + w[3]*s4 + w[4]*s5

    # Floor rule
    floor_active = (p.p5 <= 1) or (p.p6 == 0)

    # Mapeo a perfil
    if floor_active:
        perfil_resultante = 'Conservador'
        sigma = 0.08
    elif score_final <= 0.35:
        perfil_resultante = 'Conservador'
        sigma = 0.08
    elif score_final <= 0.65:
        perfil_resultante = 'Moderado'
        sigma = 0.15
    else:
        perfil_resultante = 'Agresivo'
        sigma = 0.25

    return {
        'S1_conocimientos': round(s1, 3),
        'S2_situacion_fin': round(s2, 3),
        'S3_objetivos': round(s3, 3),
        'S4_esg': round(s4, 3),
        'S5_nlp': round(s5, 3),
        'pesos_horizonte': w,
        'score_final': round(score_final, 3),
        'floor_rule_activa': floor_active,
        'perfil_resultante': perfil_resultante,
        'sigma_max': sigma,
        'coincide_objetivo': perfil_resultante.lower() == p.perfil_objetivo.lower(),
    }


# ═════════════════════════════════════════════════════════
# DEFINICIÓN DE LAS 30 PERSONAS SINTÉTICAS
# ═════════════════════════════════════════════════════════

PERSONAS: List[Persona] = []

# ─────────────────────────────────────────────────────────
# CONSERVADORES (10) — perfil resultante esperado: Conservador
# ─────────────────────────────────────────────────────────

PERSONAS.append(Persona(
    id="CO01", nombre="María González", edad=67, contexto="Jubilada, pensión modesta, viuda",
    perfil_objetivo="conservador", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=0, p2=1, p3=0, p4=0, p5=1, p6=3, p7=2,
    p8=0, p9=0, p10=0, p11=0, p12=0,
    p13_texto="Quiero asegurar mis ahorros para mis nietos. No entiendo de inversiones y me preocupa mucho perder dinero. Solo quiero algo seguro.",
    p14_texto="Sería un golpe terrible. Probablemente vendería todo de inmediato. No puedo permitirme perder esto.",
    p15_texto="No miraría la cartera nunca, me quitaría el sueño. Cualquier movimiento me pondría nerviosa.",
    p13_finbert=0.0, p14_finbert=0.0, p15_finbert=0.0,
))

PERSONAS.append(Persona(
    id="CO02", nombre="Pilar Ruiz", edad=55, contexto="Oficinista cerca de la jubilación, dos hijos",
    perfil_objetivo="conservador", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=1, p2=1, p3=1, p4=1, p5=1, p6=1, p7=2,
    p8=1, p9=0, p10=1, p11=1, p12=1,
    p13_texto="Llevo años ahorrando para complementar la pensión. Me gustaría obtener algo de rentabilidad pero sin arriesgar lo que tanto me ha costado.",
    p14_texto="Me preocuparía mucho. Probablemente vendería una parte para evitar más pérdidas. Es dinero que necesito en pocos años.",
    p15_texto="Las subidas y bajadas me ponen nerviosa. Prefiero algo estable aunque rinda menos.",
    p13_finbert=0.5, p14_finbert=0.0, p15_finbert=0.0,
))

PERSONAS.append(Persona(
    id="CO03", nombre="José Martín", edad=22, contexto="Estudiante universitario, primera inversión pequeña",
    perfil_objetivo="conservador", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=0, p2=0, p3=0, p4=0, p5=2, p6=3, p7=0,
    p8=1, p9=1, p10=1, p11=1, p12=1,
    p13_texto="Quiero empezar a invertir poco a poco. No tengo experiencia y prefiero ir aprendiendo sin grandes riesgos.",
    p14_texto="Me asustaría bastante porque es la primera vez. Creo que vendería una parte para no perder más.",
    p15_texto="No miraría la cartera todos los días, no quiero obsesionarme. Pero ver caídas grandes me afectaría.",
    p13_finbert=0.5, p14_finbert=0.0, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="CO04", nombre="Carmen López", edad=45, contexto="Empleada divorciada, custodia de dos hijos",
    perfil_objetivo="conservador", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=1, p2=2, p3=2, p4=1, p5=1, p6=1, p7=1,
    p8=2, p9=1, p10=2, p11=1, p12=2,
    p13_texto="Busco rentabilidad para los estudios futuros de mis hijos. Tengo cierta experiencia con fondos pero soy cautelosa.",
    p14_texto="Aguantaría sin vender en pánico, pero estaría preocupada. Probablemente revisaría la estrategia.",
    p15_texto="Procuro no mirar la cartera muy a menudo. La volatilidad es parte del juego, lo asumo aunque no me guste.",
    p13_finbert=0.5, p14_finbert=0.5, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="CO05", nombre="Iván Castro", edad=30, contexto="Emprendedor, capital semilla para su startup",
    perfil_objetivo="conservador", coherente=False,
    tipo_incoherencia="Floor rule activa pese a score alto",
    descripcion_incoherencia=("Inversor con alta cultura financiera y voluntad de riesgo, pero el dinero invertido "
                              "es su capital semilla emprendedor. P5=1 activa floor rule: aunque su score "
                              "calculado lo clasificaría como agresivo, el modelo lo asigna a conservador."),
    p1=2, p2=3, p3=3, p4=3, p5=1, p6=3, p7=2,
    p8=3, p9=3, p10=3, p11=3, p12=2,
    p13_texto="Tengo una visión clara de largo plazo. Las oportunidades están ahí para quien sabe identificarlas.",
    p14_texto="Una caída del 30% sería una oportunidad de comprar más, no de vender. Mantengo la estrategia.",
    p15_texto="No me afecta la volatilidad diaria. Lo importante es la tesis a largo plazo.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="CO06", nombre="Brian Sosa", edad=28, contexto="Repartidor con sueños de hacerse rico rápido",
    perfil_objetivo="conservador", coherente=False,
    tipo_incoherencia="Self-overestimation (Dunning-Kruger) + floor rule",
    descripcion_incoherencia=("Sin formación ni experiencia, pero marca opciones agresivas en todas las preguntas. "
                              "P5=0 (impacto catastrófico) y P6=0 (deudas >50% ingresos) activan doble floor rule. "
                              "Pese a su retórica eufórica, el modelo correctamente lo clasifica como conservador."),
    p1=0, p2=0, p3=1, p4=0, p5=0, p6=0, p7=0,
    p8=3, p9=3, p10=3, p11=3, p12=0,
    p13_texto="Quiero hacerme rico. He visto videos en YouTube de gente que se forró con criptos y quiero hacer lo mismo.",
    p14_texto="No me importa, sigo invirtiendo más. Hay que tener huevos en este juego.",
    p15_texto="Cuanto más sube y baja, más oportunidades hay de ganar pasta. Lo veo todo el día en el móvil.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="CO07", nombre="Marta Vidal", edad=50, contexto="Profesora de instituto, sin pareja",
    perfil_objetivo="conservador", coherente=False,
    tipo_incoherencia="Inconsistencia P10–P11 + impacto grave (floor rule activa)",
    descripcion_incoherencia=("Marca P10=2 (mantendría ante caída del 20%) pero P11=1 (solo acepta 5% de pérdida "
                              "anual). Inconsistencia conductual clásica: cree ser racional pero su tope de "
                              "tolerancia es bajo. Además P5=1 (impacto grave) activa floor rule, garantizando "
                              "perfil conservador pese a un score numérico moderado-alto."),
    p1=2, p2=2, p3=2, p4=2, p5=1, p6=3, p7=2,
    p8=2, p9=2, p10=2, p11=1, p12=2,
    p13_texto="Tengo formación financiera y me considero una persona racional. Quiero invertir con cabeza.",
    p14_texto="Mantendría la inversión, no soy de vender por miedo. Es ruido a corto plazo.",
    p15_texto="Reviso la cartera mensualmente. Las caídas son normales, las acepto si son moderadas.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="CO08", nombre="Roberto Aznar", edad=60, contexto="Prejubilado con paro cobrado, próximo a pensión",
    perfil_objetivo="conservador", coherente=False,
    tipo_incoherencia="Texto libre positivo vs cerradas conservadoras + floor rule",
    descripcion_incoherencia=("Sus respuestas cerradas son conservadoras (impacto grave de pérdida activa floor rule) "
                              "pero los textos libres rebosan emoción y entusiasmo por empezar a invertir. "
                              "El score B5 sube pero la floor rule sigue dominando: conservador final."),
    p1=2, p2=2, p3=1, p4=1, p5=1, p6=2, p7=2,
    p8=1, p9=1, p10=1, p11=1, p12=1,
    p13_texto="Por fin voy a poder invertir, llevo años deseándolo. Estoy muy ilusionado con esta nueva etapa.",
    p14_texto="Bueno, hay que asumir que pueden venir mal dadas. Lo aceptaría como parte del proceso.",
    p15_texto="Me motivaría seguir aprendiendo durante los altibajos. Es algo nuevo y lo veo con ganas.",
    p13_finbert=1.0, p14_finbert=0.5, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="CO09", nombre="Paula Ortega", edad=40, contexto="Madre soltera planificando entrada de vivienda",
    perfil_objetivo="conservador", coherente=False,
    tipo_incoherencia="Horizon-objective mismatch + floor rule (impacto grave)",
    descripcion_incoherencia=("Necesita el dinero en menos de un año para la entrada de su vivienda (P8=0), "
                              "pero P9=3 (maximizar rentabilidad). Esta incoherencia clásica se combina con "
                              "P5=1 (impacto grave si pierde, porque es el dinero de la vivienda) que "
                              "activa la floor rule. El modelo la protege de su propia inconsistencia."),
    p1=1, p2=2, p3=1, p4=1, p5=1, p6=1, p7=1,
    p8=0, p9=3, p10=2, p11=2, p12=1,
    p13_texto="Necesito el dinero pronto pero quiero sacarle el máximo partido. He oído que algunos productos rinden bien.",
    p14_texto="Pues bastante mal porque lo necesito ya. Tendría que pedir un préstamo o algo.",
    p15_texto="No puedo permitirme volatilidad ahora mismo. Pero sí me gustaría ganar algo más que un depósito.",
    p13_finbert=0.5, p14_finbert=0.0, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="CO10", nombre="Diego Herrera", edad=35, contexto="Autónomo precario, deudas múltiples",
    perfil_objetivo="conservador", coherente=False,
    tipo_incoherencia="Liquidity tension (deudas altas + sin fondo emergencia + quiere agresivo)",
    descripcion_incoherencia=("Quiere invertir agresivo pero tiene deudas que superan el 50% de sus ingresos "
                              "(P6=0), lo que activa floor rule. Adicionalmente, no tiene fondo de emergencia. "
                              "El modelo lo protege correctamente clasificándolo como conservador."),
    p1=1, p2=2, p3=2, p4=1, p5=2, p6=0, p7=0,
    p8=2, p9=2, p10=2, p11=2, p12=1,
    p13_texto="Quiero generar ingresos extra para salir de mis deudas. Necesito que el dinero trabaje para mí.",
    p14_texto="Sería un drama porque ya estoy ajustado. Tendría que vender algo para no hundirme más.",
    p15_texto="Reviso las cuentas constantemente, vivo con mucha incertidumbre financiera ya de por sí.",
    p13_finbert=0.5, p14_finbert=0.0, p15_finbert=0.0,
))

# ─────────────────────────────────────────────────────────
# MODERADOS (10) — perfil resultante esperado: Moderado
# ─────────────────────────────────────────────────────────

PERSONAS.append(Persona(
    id="MO01", nombre="Carlos Ruiz", edad=38, contexto="Ingeniero senior, casado, hipoteca, planifica vivienda",
    perfil_objetivo="moderado", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=2, p2=2, p3=2, p4=2, p5=2, p6=1, p7=1,
    p8=2, p9=2, p10=2, p11=2, p12=2,
    p13_texto="Quiero que mi dinero crezca a medio plazo para comprar casa. Entiendo que puede haber bajadas, lo asumiría si son temporales.",
    p14_texto="Lo asumiría pero estaría incómodo. Probablemente mantendría la inversión y esperaría a que se recuperase.",
    p15_texto="Reviso la cartera cada par de meses. La volatilidad de corto plazo no me afecta especialmente.",
    p13_finbert=0.5, p14_finbert=0.5, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="MO02", nombre="Lucía Fernández", edad=42, contexto="Médico de cabecera, sin hijos, alquiler",
    perfil_objetivo="moderado", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=2, p2=2, p3=2, p4=3, p5=2, p6=3, p7=2,
    p8=2, p9=1, p10=2, p11=2, p12=2,
    p13_texto="Tengo ingresos estables y quiero que mis ahorros generen rentabilidad. Sin grandes sustos pero con crecimiento real.",
    p14_texto="Mantendría la inversión. Sé que las recuperaciones suelen llegar y vender en mínimo es el peor error.",
    p15_texto="No miro la cartera a diario. La volatilidad es el precio que se paga por la rentabilidad a largo plazo.",
    p13_finbert=0.5, p14_finbert=0.5, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="MO03", nombre="Andrés Pérez", edad=35, contexto="Programador en empresa tech, salario alto",
    perfil_objetivo="moderado", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=1, p2=2, p3=2, p4=2, p5=2, p6=2, p7=2,
    p8=2, p9=2, p10=2, p11=1, p12=1,
    p13_texto="Llevo varios años ahorrando con depósitos pero quiero dar el salto a algo más rentable. Estoy dispuesto a aprender.",
    p14_texto="Una caída así dolería pero la entendería como parte del proceso. Mantendría la estrategia.",
    p15_texto="Soy bastante racional con esto. La volatilidad no me obsesiona si la cartera está bien planteada.",
    p13_finbert=0.5, p14_finbert=0.5, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="MO04", nombre="Sara Iglesias", edad=27, contexto="Recién certificada CFA, sin experiencia operativa",
    perfil_objetivo="moderado", coherente=False,
    tipo_incoherencia="Knowledge-experience mismatch (alto conocimiento, cero experiencia)",
    descripcion_incoherencia=("Tiene formación financiera del más alto nivel (CFA recién certificada, P1=3) pero "
                              "nunca ha invertido (P2=0, P3=0). Discrepancia entre saber teórico y experiencia "
                              "práctica: el modelo lo refleja correctamente con score moderado. Su cautela "
                              "técnica se traduce en P11=2 (acepta hasta 15%, no más)."),
    p1=3, p2=0, p3=0, p4=2, p5=2, p6=3, p7=2,
    p8=2, p9=2, p10=2, p11=2, p12=2,
    p13_texto="Conozco bien la teoría de carteras y la diversificación. Quiero aplicar lo que he aprendido pero con cautela inicial.",
    p14_texto="Sé que las correcciones del 30% son históricamente normales. La paciencia suele ser recompensada.",
    p15_texto="Entiendo la volatilidad como una característica del activo, no como un riesgo a temer.",
    p13_finbert=0.5, p14_finbert=0.5, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="MO05", nombre="Pablo Núñez", edad=33, contexto="Comercial, ingresos variables por comisiones",
    perfil_objetivo="moderado", coherente=False,
    tipo_incoherencia="Alta varianza intra-NLP (P13 positivo, P14 muy negativo, P15 neutral)",
    descripcion_incoherencia=("Sus respuestas cerradas son moderadas pero los 3 textos libres dan scores muy "
                              "dispersos: optimista en abstracto, ansioso ante el escenario concreto de "
                              "pérdida, neutral sobre la volatilidad continua. La media B5=0.50 esconde "
                              "incoherencia interna detectable como métrica de auditoría."),
    p1=1, p2=2, p3=2, p4=2, p5=2, p6=2, p7=1,
    p8=2, p9=2, p10=2, p11=2, p12=1,
    p13_texto="Soy optimista por naturaleza. Creo en el largo plazo y en que el mercado tiende a subir.",
    p14_texto="Una caída del 30% me destrozaría. Probablemente vendería todo, no podría aguantar viendo cómo se evapora mi dinero.",
    p15_texto="Procuro no mirar la cartera todos los días. Trato de mantener la disciplina aunque cueste.",
    p13_finbert=1.0, p14_finbert=0.0, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="MO06", nombre="Elena Sanz", edad=41, contexto="Diseñadora freelance, ingresos irregulares",
    perfil_objetivo="moderado", coherente=False,
    tipo_incoherencia="Capacidad financiera tensa (alto conocimiento, ahorro limitado por ingresos volátiles)",
    descripcion_incoherencia=("Buen conocimiento financiero y voluntad de riesgo, pero P4=1 (baja capacidad "
                              "de ahorro) por la naturaleza freelance. El modelo termina clasificándola "
                              "como moderada porque B2 está penalizado a pesar de B1 y B3 altos. Texto "
                              "racional pero con cautela por su realidad económica."),
    p1=2, p2=2, p3=2, p4=1, p5=2, p6=2, p7=1,
    p8=2, p9=2, p10=2, p11=2, p12=3,
    p13_texto="Quiero compensar la inestabilidad de mis ingresos con una cartera bien diversificada y orientada al largo plazo.",
    p14_texto="Lo asumiría como parte de la naturaleza del mercado. Mi horizonte es largo, no quiero entrar en pánico.",
    p15_texto="Trato de desconectar emocionalmente de las fluctuaciones diarias. Lo que importa es la tesis de fondo.",
    p13_finbert=0.5, p14_finbert=0.5, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="MO07", nombre="Ana Mendoza", edad=48, contexto="Funcionaria, prepara jubilación, casada con arquitecto",
    perfil_objetivo="moderado", coherente=False,
    tipo_incoherencia="Cerradas conservadoras + textos NLP positivos",
    descripcion_incoherencia=("En las preguntas cerradas marca opciones cautas (objetivo rentas estables, "
                              "pérdida máx 5–15%) pero sus textos libres muestran ambición latente: "
                              "habla de 'explorar', 'no quedarse atrás'. El B5 alto compensa hacia "
                              "moderado-alto."),
    p1=1, p2=2, p3=1, p4=2, p5=2, p6=2, p7=2,
    p8=2, p9=1, p10=2, p11=2, p12=2,
    p13_texto="Quiero asegurar mi jubilación pero también explorar oportunidades que me hagan crecer. No quiero quedarme atrás.",
    p14_texto="Sería duro pero confío en la recuperación. Probablemente mantendría e incluso aprovecharía si tuviese liquidez.",
    p15_texto="Reviso la cartera con interés, no con miedo. Las oportunidades aparecen en los momentos difíciles.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="MO08", nombre="Jorge Pascual", edad=39, contexto="Abogado mercantil, dos hijos pequeños",
    perfil_objetivo="moderado", coherente=False,
    tipo_incoherencia="Aversión asimétrica suave (mantendría caída pero limita pérdida anual)",
    descripcion_incoherencia=("Coherente con un perfil moderado, pero su P10=2 (mantiene caída del 20%) "
                              "y P11=2 (acepta hasta 15% pérdida anual) revelan una asimetría: dice "
                              "que aguanta caídas pero pone tope. Persona estable financieramente, "
                              "racional, pero con dos hijos pequeños que matizan su disposición."),
    p1=2, p2=2, p3=1, p4=2, p5=2, p6=2, p7=2,
    p8=2, p9=2, p10=2, p11=2, p12=2,
    p13_texto="Ya he invertido en fondos antes. Busco crecimiento moderado para complementar mi plan de pensiones.",
    p14_texto="Una caída así me preocuparía pero no me haría vender en pánico. He visto correcciones similares.",
    p15_texto="No miro la cartera obsesivamente. Si la estrategia es buena, hay que dejarla trabajar.",
    p13_finbert=0.5, p14_finbert=0.5, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="MO09", nombre="Patricia Vega", edad=45, contexto="Activista ESG, profesora universitaria",
    perfil_objetivo="moderado", coherente=False,
    tipo_incoherencia="Sustainability override (ESG estricto + objetivos altos pero capacidad financiera media)",
    descripcion_incoherencia=("Quiere ESG como requisito obligatorio (P12=3) y crecimiento patrimonial sólido. "
                              "Esta combinación creará tensión en M2 al filtrar el universo de activos. "
                              "Score termina en moderado por su capacidad financiera media (sueldo de "
                              "profesora universitaria, sin gran patrimonio acumulado)."),
    p1=2, p2=2, p3=1, p4=2, p5=2, p6=2, p7=1,
    p8=2, p9=2, p10=2, p11=2, p12=3,
    p13_texto="Quiero invertir en empresas que generen impacto positivo y al mismo tiempo den buena rentabilidad. No es incompatible.",
    p14_texto="Lo asumiría como parte del horizonte largo. La sostenibilidad es una tesis estructural a 20 años.",
    p15_texto="No me afectan las fluctuaciones, miro las tendencias regulatorias y de cambio climático.",
    p13_finbert=0.5, p14_finbert=0.5, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="MO10", nombre="Hugo Cabrera", edad=55, contexto="Directivo en industria, próximo a la jubilación",
    perfil_objetivo="moderado", coherente=False,
    tipo_incoherencia="Floor rule cerca pero no activa (P5=2)",
    descripcion_incoherencia=("Su P5=2 (impacto moderado) está justo en el límite de no activar la floor "
                              "rule. Si hubiese marcado P5=1 sería conservador automático. Caso útil "
                              "para validar que el corte 1↔2 funciona correctamente."),
    p1=2, p2=2, p3=2, p4=2, p5=2, p6=2, p7=2,
    p8=2, p9=2, p10=2, p11=2, p12=1,
    p13_texto="Tengo experiencia en mercados y entiendo que el corto plazo es ruido. Quiero aprovechar mis últimos años activos.",
    p14_texto="Mantendría la posición. He pasado por varias correcciones a lo largo de mi carrera.",
    p15_texto="Reviso la cartera trimestralmente. Las decisiones precipitadas suelen ser las peores.",
    p13_finbert=0.5, p14_finbert=1.0, p15_finbert=0.5,
))

# ─────────────────────────────────────────────────────────
# AGRESIVOS (10) — perfil resultante esperado: Agresivo
# ─────────────────────────────────────────────────────────

PERSONAS.append(Persona(
    id="AG01", nombre="Alejandro López", edad=29, contexto="Developer en startup, sin cargas familiares",
    perfil_objetivo="agresivo", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=3, p2=3, p3=3, p4=3, p5=3, p6=3, p7=2,
    p8=3, p9=3, p10=3, p11=3, p12=2,
    p13_texto="Tengo todo el tiempo del mundo. Las caídas del mercado son oportunidades. Quiero construir riqueza real a largo plazo y no me asusta la volatilidad.",
    p14_texto="Una caída del 30% sería momento de comprar más. Tengo conviccción en el largo plazo y la volatilidad es el peaje.",
    p15_texto="No me afectaría psicológicamente. Tengo claro el plan y la disciplina para no actuar por emoción.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="AG02", nombre="Sandra Beltrán", edad=31, contexto="Abogada en M&A, alto patrimonio, soltera",
    perfil_objetivo="agresivo", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=3, p2=3, p3=2, p4=3, p5=3, p6=3, p7=2,
    p8=3, p9=3, p10=2, p11=3, p12=3,
    p13_texto="Trabajo en M&A, conozco bien los ciclos de mercado. Quiero una cartera diversificada con sesgo a renta variable de calidad.",
    p14_texto="Mantendría la cartera y rebalancearía. Las correcciones del 30% son matemáticamente esperables.",
    p15_texto="Mi trabajo es analizar valor; no me dejo arrastrar por el ruido de corto plazo.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="AG03", nombre="Ricardo Marín", edad=26, contexto="Trader amateur con 4 años operando, vive con padres",
    perfil_objetivo="agresivo", coherente=True, tipo_incoherencia=None, descripcion_incoherencia=None,
    p1=2, p2=4, p3=3, p4=3, p5=3, p6=3, p7=1,
    p8=3, p9=3, p10=3, p11=3, p12=0,
    p13_texto="Me dedico al trading desde hace años. Conozco derivados y opciones. Soy consciente del riesgo y lo gestiono.",
    p14_texto="Una caída del 30% es trading habitual. Tengo stop-loss y plan de gestión de riesgo definido.",
    p15_texto="La volatilidad es mi entorno natural. Cuanto mayor, más oportunidades en mi estrategia.",
    p13_finbert=1.0, p14_finbert=0.5, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="AG04", nombre="David Tomás", edad=32, contexto="Consultor estratégico, ascenso reciente",
    perfil_objetivo="agresivo", coherente=False,
    tipo_incoherencia="NLP atenuante: cerradas todo agresivo, P14 ligeramente cauto",
    descripcion_incoherencia=("Marca opciones agresivas en todas las preguntas cerradas, pero su texto P14 "
                              "(reacción ante caída del 30%) muestra una ligera cautela: 'me preocuparía "
                              "pero...'. El score B5 baja ligeramente pero el resultado sigue siendo "
                              "agresivo, en el borde alto del rango."),
    p1=2, p2=3, p3=2, p4=3, p5=3, p6=3, p7=2,
    p8=3, p9=3, p10=3, p11=3, p12=2,
    p13_texto="Quiero maximizar la rentabilidad de mi capital, soy joven y puedo asumir riesgo elevado.",
    p14_texto="Sinceramente me preocuparía bastante una caída así, pero mantendría la posición porque tengo horizonte largo.",
    p15_texto="No me afecta la volatilidad, lo veo como parte normal del juego.",
    p13_finbert=1.0, p14_finbert=0.5, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="AG05", nombre="Beatriz Cano", edad=28, contexto="Dentista joven con consulta propia exitosa",
    perfil_objetivo="agresivo", coherente=False,
    tipo_incoherencia="Conservadora en una dimensión (acepta solo 15% pérdida anual)",
    descripcion_incoherencia=("Todo agresivo excepto P11=2 (tope 15% pérdida anual en lugar del máximo). "
                              "Detalle realista: alta tolerancia general pero con un límite explícito. "
                              "Score sigue siendo agresivo pero al borde del rango."),
    p1=2, p2=3, p3=2, p4=3, p5=3, p6=2, p7=2,
    p8=3, p9=3, p10=3, p11=2, p12=2,
    p13_texto="Mi consulta va bien y puedo permitirme invertir agresivo. Quiero diversificar fuera de mi negocio.",
    p14_texto="Mantendría la inversión. Confío en que el mercado se recupera y mi situación financiera es sólida.",
    p15_texto="No reviso la cartera a diario, prefiero el largo plazo. Las caídas son ruido temporal.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="AG06", nombre="Manuel Alcaraz", edad=45, contexto="Ejecutivo financiero, hijos universitarios",
    perfil_objetivo="agresivo", coherente=False,
    tipo_incoherencia="Alta varianza intra-NLP (positivo-negativo-positivo)",
    descripcion_incoherencia=("Cerradas agresivas pero los textos libres muestran inconsistencia: P13 "
                              "ambicioso, P14 admite estrés ante caídas grandes, P15 vuelve a tono "
                              "positivo. Caso borderline: la media NLP=0.50 lo deja en agresivo bajo "
                              "o moderado alto según los pesos exactos."),
    p1=3, p2=3, p3=3, p4=3, p5=3, p6=3, p7=2,
    p8=3, p9=3, p10=2, p11=3, p12=2,
    p13_texto="Trabajo en finanzas y conozco bien las dinámicas. Quiero maximizar el retorno aprovechando mi cultura financiera.",
    p14_texto="Honestamente, una caída del 30% me generaría mucho estrés. Trabajo con números todo el día y vería el daño con claridad.",
    p15_texto="Tengo la disciplina necesaria para no tocar la cartera durante los altibajos. La experiencia ayuda.",
    p13_finbert=1.0, p14_finbert=0.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="AG07", nombre="Cristina Salas", edad=38, contexto="Empresaria autodidacta, e-commerce de éxito",
    perfil_objetivo="agresivo", coherente=False,
    tipo_incoherencia="Conocimientos financieros bajos pero todo lo demás agresivo",
    descripcion_incoherencia=("Sin formación financiera reglada (P1=1, formación básica) y poca experiencia "
                              "operativa con productos financieros (P2=2, P3=1) pero alta capacidad financiera, "
                              "horizonte largo y voluntad de riesgo. Pesos B1=15% no penalizan demasiado, "
                              "score termina agresivo."),
    p1=1, p2=2, p3=1, p4=3, p5=3, p6=3, p7=2,
    p8=3, p9=3, p10=3, p11=3, p12=2,
    p13_texto="No soy experta en mercados pero llevo años emprendiendo y sé asumir riesgo. Quiero diversificar fuera de mi empresa.",
    p14_texto="No me asusta perder en bolsa porque he perdido y ganado mucho más en mi negocio. Aguanto.",
    p15_texto="No miro la cartera a diario, no me da la vida. Confío en el largo plazo.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=0.5,
))

PERSONAS.append(Persona(
    id="AG08", nombre="Javier Solano", edad=34, contexto="Profesional independiente, comprometido con sostenibilidad",
    perfil_objetivo="agresivo", coherente=False,
    tipo_incoherencia="ESG estricto en perfil agresivo (tensión con M2)",
    descripcion_incoherencia=("Agresivo en todas las dimensiones + ESG como requisito obligatorio (P12=3). "
                              "Score totalmente agresivo. La tensión aparecerá en M2: el filtro ESG estricto "
                              "puede limitar el universo de activos disponibles para una cartera agresiva, "
                              "lo cual debe gestionarse en el módulo siguiente."),
    p1=3, p2=3, p3=3, p4=3, p5=3, p6=3, p7=2,
    p8=3, p9=3, p10=3, p11=3, p12=3,
    p13_texto="Solo invierto en empresas alineadas con mis valores climáticos. Energías limpias, transición ecológica.",
    p14_texto="La transición energética no se detiene por una caída coyuntural. Mantengo y refuerzo posiciones.",
    p15_texto="La volatilidad de corto plazo no me afecta. Lo importante es estar en el lado correcto del cambio.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="AG09", nombre="Laura Jiménez", edad=25, contexto="Recién licenciada en biotech, primer trabajo",
    perfil_objetivo="agresivo", coherente=False,
    tipo_incoherencia="Experiencia operativa baja (P3=1) en perfil agresivo",
    descripcion_incoherencia=("Inversora coherentemente agresiva por edad, horizonte y disposición psicológica, "
                              "pero su experiencia operativa real es escasa: solo ha operado puntualmente "
                              "(P3=1). Caso típico de inversora joven con conocimiento académico pero poco "
                              "track record. Score termina en agresivo bajo, justo dentro del rango."),
    p1=2, p2=2, p3=1, p4=2, p5=3, p6=3, p7=1,
    p8=3, p9=3, p10=3, p11=2, p12=2,
    p13_texto="Tengo 25 años y por delante 40 años de horizonte. Quiero aprovechar el interés compuesto desde ahora.",
    p14_texto="Una caída del 30% sería una bendición porque puedo comprar más a precios bajos. El tiempo está de mi lado.",
    p15_texto="No me afecta para nada la volatilidad. Estoy empezando, todavía no tengo casi nada que perder.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))

PERSONAS.append(Persona(
    id="AG10", nombre="Marcos Bravo", edad=30, contexto="Crypto-trader, alta tolerancia al riesgo, sin cargas",
    perfil_objetivo="agresivo", coherente=False,
    tipo_incoherencia="Texto excesivamente eufórico (posible overconfidence)",
    descripcion_incoherencia=("Sus respuestas cerradas son agresivas y consistentes; pero los textos libres "
                              "destilan una euforia que sugiere overconfidence. El score sale al máximo del "
                              "rango. La memoria del TFM puede usar este caso para discutir la diferencia "
                              "entre tolerancia al riesgo y temeridad."),
    p1=2, p2=4, p3=3, p4=3, p5=3, p6=3, p7=1,
    p8=3, p9=3, p10=3, p11=3, p12=0,
    p13_texto="El miedo es para los débiles. He triplicado mi capital tres veces con criptos, sé lo que hago.",
    p14_texto="Una caída del 30% es nada en cripto, lo veo cada semana. Compro más y a otra cosa.",
    p15_texto="La volatilidad es mi mejor amiga. Cuanto más se mueve, más oportunidades de ganar dinero.",
    p13_finbert=1.0, p14_finbert=1.0, p15_finbert=1.0,
))


if __name__ == "__main__":
    print(f"Total personas: {len(PERSONAS)}")
    coherentes = sum(1 for p in PERSONAS if p.coherente)
    print(f"Coherentes: {coherentes}, Incoherentes: {len(PERSONAS) - coherentes}")

    # Validación: cada persona pasa por el modelo
    for p in PERSONAS:
        r = calcular_scores(p)
        match = "✓" if r['coincide_objetivo'] else "✗"
        print(f"{p.id} {match} | objetivo={p.perfil_objetivo:12s} | resultante={r['perfil_resultante']:12s} | "
              f"score={r['score_final']:.3f} | floor={r['floor_rule_activa']}")
