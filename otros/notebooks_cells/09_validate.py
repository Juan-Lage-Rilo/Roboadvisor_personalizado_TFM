# §9.1 — Validación de integridad del propio notebook
import nbformat

nb_path = Path.cwd() / "M1_nlp_profiling.ipynb"
if not nb_path.exists():
    nb_path = PROJECT_ROOT / "notebooks" / "M1_nlp_profiling.ipynb"

if nb_path.exists():
    nb_obj = nbformat.read(nb_path, as_version=4)
    nbformat.validate(nb_obj)
    print(f"✅ Notebook válido: {nb_path.name} ({len(nb_obj.cells)} celdas)")
else:
    print("ℹ️ Ejecutar tras guardar el .ipynb para validar integridad.")
