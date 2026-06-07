"""Diagnóstico del pipeline NLP de la demo (Rama A: Opus-MT ES→EN → FinBERT).

Responde a UNA pregunta: ¿por qué el sentimiento sale siempre 0.5 (neutral)?

Distingue las hipótesis:
  A) La traducción ES→EN falla en silencio (FinBERT recibe español → neutral).
  B) FinBERT recibe inglés correcto pero devuelve neutral porque mide polaridad
     de NOTICIAS financieras, no apetito de riesgo (limitación semántica).
  C) La API falla (provider/token) y el except lo traga.

Uso:
    set HF_TOKEN=hf_xxx          (Windows)  /  export HF_TOKEN=hf_xxx  (bash)
    python scripts/diag_nlp.py

Imprime, por cada texto: la traducción EN y la distribución COMPLETA de FinBERT
(las 3 probabilidades), sin tragar excepciones.
"""
from __future__ import annotations

import os
import sys

from huggingface_hub import InferenceClient

FINBERT = "ProsusAI/finbert"
OPUS = "Helsinki-NLP/opus-mt-es-en"

# Textos reales del caso_2 (apetito de riesgo).
TEXTOS_CASO = [
    "Estoy dispuesto a soportar volatilidad porque mi inversión es a largo plazo",
    "Compraría más si es una buena oportunidad",
    "No me preocupa la volatilidad, sé que es algo normal en los mercados",
]

# Controles: noticias financieras claramente +/− (dominio nativo de FinBERT).
CONTROLES = [
    ("control +", "La empresa registró beneficios récord y un crecimiento sólido"),
    ("control −", "La compañía quebró tras enormes pérdidas y despidos masivos"),
]


def main() -> int:
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("ERROR: define HF_TOKEN en el entorno antes de ejecutar.")
        return 1

    client = InferenceClient(token=token, timeout=30.0)
    print(f"huggingface_hub provider por defecto: {getattr(client, 'provider', 'n/a')}\n")

    def diagnostica(etiqueta: str, texto_es: str) -> None:
        print(f"[{etiqueta}] ES: {texto_es!r}")
        # 1) Traducción (sin tragar excepción)
        try:
            out = client.translation(texto_es, model=OPUS)
            text_en = getattr(out, "translation_text", None)
            print(f"    EN: {text_en!r}   (tipo respuesta: {type(out).__name__})")
            if text_en is None:
                print("    !! translation_text es None → el getattr caería al español")
                text_en = texto_es
        except Exception as exc:  # noqa: BLE001
            print(f"    !! TRADUCCIÓN FALLA: {type(exc).__name__}: {exc}")
            text_en = texto_es
        # 2) FinBERT distribución completa
        try:
            res = client.text_classification(text_en, model=FINBERT, top_k=None)
            dist = {r["label"].lower(): round(float(r["score"]), 4) for r in res}
            top = max(dist, key=dist.get)
            signed = ({"positive": +1, "negative": -1, "neutral": 0}[top]) * dist[top]
            sentiment = (signed + 1.0) / 2.0
            print(f"    FinBERT: {dist}  → top={top}  sentiment={sentiment:.3f}")
        except Exception as exc:  # noqa: BLE001
            print(f"    !! FINBERT FALLA: {type(exc).__name__}: {exc}")
        print()

    print("===== CONTROLES (noticias financieras, dominio de FinBERT) =====")
    for et, t in CONTROLES:
        diagnostica(et, t)

    print("===== TEXTOS DEL CASO (apetito de riesgo) =====")
    for i, t in enumerate(TEXTOS_CASO, 1):
        diagnostica(f"caso P1{i+2}", t)

    print("Interpretación:")
    print("  - Si los CONTROLES dan positive/negative pero los TEXTOS DEL CASO dan")
    print("    neutral → hipótesis B (limitación semántica de FinBERT). El NLP no")
    print("    puede medir apetito de riesgo; hay que repensar su rol.")
    print("  - Si la traducción devuelve español → hipótesis A (parsing/except).")
    print("  - Si algo lanza excepción → hipótesis C (API/token/provider).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
