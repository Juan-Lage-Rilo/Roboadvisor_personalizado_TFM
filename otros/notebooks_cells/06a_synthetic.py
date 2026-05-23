# §6.1 — 20 casos hand-crafted (q_norm, sentiment[0,1], confianza, perfil_esperado)
synthetic_cases = [
    # 5 alta divergencia: cuestionario agresivo + texto temeroso -> bajar
    dict(id="HD1", q_norm=+0.80, sentiment=0.05, conf="alta",  expected="conservador",
         scenario="agresivo + miedo extremo (alta) -> 2 escalones"),
    dict(id="HD2", q_norm=+0.70, sentiment=0.10, conf="alta",  expected="conservador",
         scenario="agresivo + miedo (alta) -> 2 escalones"),
    dict(id="HD3", q_norm=+0.50, sentiment=0.55, conf="alta",  expected="moderado",
         scenario="agresivo + precaución (alta) -> 1 escalón"),
    dict(id="HD4", q_norm=+0.70, sentiment=0.55, conf="media", expected="moderado",
         scenario="agresivo + neutral (media) -> 1 escalón"),
    dict(id="HD5", q_norm=+0.50, sentiment=0.05, conf="alta",  expected="conservador",
         scenario="agresivo + pánico (alta) -> 2 escalones"),
    # 5 baja divergencia: alineado
    dict(id="LD1", q_norm=-0.80, sentiment=0.15, conf="alta",  expected="conservador",
         scenario="conservador alineado (NLP también negativo)"),
    dict(id="LD2", q_norm=+0.00, sentiment=0.50, conf="alta",  expected="moderado",
         scenario="moderado alineado"),
    dict(id="LD3", q_norm=+0.80, sentiment=0.85, conf="alta",  expected="agresivo",
         scenario="agresivo alineado"),
    dict(id="LD4", q_norm=-0.50, sentiment=0.30, conf="alta",  expected="conservador",
         scenario="conservador alineado (sentiment levemente negativo)"),
    dict(id="LD5", q_norm=+0.20, sentiment=0.55, conf="alta",  expected="moderado",
         scenario="moderado alineado borderline"),
    # 5 confianza BAJA
    dict(id="LC1", q_norm=+0.50, sentiment=0.35, conf="baja",  expected="moderado",
         scenario="agresivo + sentiment negativo, conf baja -> 1 escalón"),
    dict(id="LC2", q_norm=+0.45, sentiment=0.30, conf="baja",  expected="moderado",
         scenario="div en banda moderado/grave (baja) -> 1 escalón"),
    dict(id="LC3", q_norm=+0.40, sentiment=0.40, conf="baja",  expected="agresivo",
         scenario="div leve + conf baja -> mantener con flag"),
    dict(id="LC4", q_norm=-0.20, sentiment=0.50, conf="baja",  expected="moderado",
         scenario="div pequeña + conf baja -> mantener moderado"),
    dict(id="LC5", q_norm=+0.40, sentiment=0.30, conf="baja",  expected="moderado",
         scenario="div alta + conf baja -> 1 escalón (no 2)"),
    # 5 edge cases
    dict(id="EC1", q_norm=+0.00, sentiment=0.50, conf="alta",  expected="moderado",
         scenario="neutral puro"),
    dict(id="EC2", q_norm=-0.99, sentiment=0.99, conf="baja",  expected="conservador",
         scenario="prudencia asimétrica: div negativa nunca sube"),
    dict(id="EC3", q_norm=+0.99, sentiment=0.85, conf="media", expected="agresivo",
         scenario="agresivo + sentiment alto, div leve (media) -> flag, mantener"),
    dict(id="EC4", q_norm=-0.40, sentiment=0.95, conf="alta",  expected="conservador",
         scenario="NLP ultra-optimista pero q conservador -> NO sube"),
    dict(id="EC5", q_norm=+0.34, sentiment=0.65, conf="alta",  expected="agresivo",
         scenario="borderline agresivo alineado"),
]

rows = []
for c in synthetic_cases:
    out = classify_profile(c["q_norm"], c["sentiment"], c["conf"])
    rows.append({
        "id": c["id"],
        "scenario": c["scenario"],
        "q_norm": c["q_norm"],
        "sentiment": c["sentiment"],
        "conf": c["conf"],
        "expected": c["expected"],
        **out,
        "pass": out["perfil_final"] == c["expected"],
    })

df_synth = pd.DataFrame(rows)
n_pass = int(df_synth["pass"].sum())
print(f"Casos pasados: {n_pass}/{len(df_synth)}")
df_synth
