# §7.1 — profile_investor
def profile_investor(
    texto_libre_es: str,
    q_score_raw: float,
    models: dict,
) -> dict:
    """Pipeline completo: traducir -> NLP dual -> fusion -> perfil.

    Args:
        texto_libre_es: respuesta abierta en castellano.
        q_score_raw   : puntuación del cuestionario en [0, 100].
        models        : dict de pipelines (output de load_models()).
    """
    try:
        if not 0.0 <= q_score_raw <= 100.0:
            raise ValueError(f"q_score_raw fuera de [0,100]: {q_score_raw}")
        q_norm = (q_score_raw - 50.0) / 50.0
        nlp = dual_nlp_score(texto_libre_es, models)
        decision = classify_profile(q_norm, nlp["sentiment_score"], nlp["confidence"])
        return {**decision, "q_score_raw": q_score_raw, "q_norm": q_norm, "nlp": nlp}
    except Exception as exc:
        logger.error("profile_investor error: %s", exc)
        raise


personas = [
    {
        "nombre": "Ana (conservadora)",
        "q_score": 25.0,
        "texto": ("No me gusta perder dinero. Prefiero rentabilidades modestas pero "
                  "seguras. La idea de que mi inversión caiga un 20% me genera "
                  "mucha ansiedad y miedo, y me haría retirar todo."),
    },
    {
        "nombre": "Luis (moderado)",
        "q_score": 55.0,
        "texto": ("Acepto ciertas pérdidas a corto plazo si a largo plazo el "
                  "rendimiento es razonable. Diversifico entre renta fija y variable."),
    },
    {
        "nombre": "Sofía (agresiva)",
        "q_score": 85.0,
        "texto": ("Busco maximizar el crecimiento del capital y el rendimiento. "
                  "Una caída del 30% es una oportunidad de compra, no un motivo de "
                  "preocupación. Prefiero renta variable y mercados emergentes."),
    },
]

for p in personas:
    res = profile_investor(p["texto"], p["q_score"], models)
    print(f"\n=== {p['nombre']} ===")
    print(f"  q_score_raw      : {res['q_score_raw']:.1f} -> q_norm={res['q_norm']:+.2f}")
    print(f"  sentiment_score  : {res['nlp']['sentiment_score']:.3f} "
          f"(A={res['nlp']['score_a']:+.2f}, B={res['nlp']['score_b']:+.2f}, "
          f"agreement={res['nlp']['agreement']:.2f}, conf={res['nlp']['confidence']})")
    print(f"  divergencia      : {res['divergencia']:+.3f}")
    print(f"  perfil_base      : {res['perfil_base']}")
    print(f"  perfil_final     : {res['perfil_final']}  (vol_cap={res['volatility_cap']:.2f})")
    print(f"  flag_revisar     : {res['flag_revisar']}  · escalones_bajados={res['escalones_bajados']}")
