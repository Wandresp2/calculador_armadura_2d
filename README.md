# armadura-2d-andresdperezc

Librería didáctica en Python para **armaduras 2D isostáticas** (mecánica vectorial): fuerzas internas, reacciones y clasificación tensión/compresión.

Se instala con **guion** y se importa con **guion bajo**:

```text
pip install armadura-2d-andresdperezc
from armadura_2d_andresdperezc import Armadura2D
```

Versión **0.1.0**. Python **≥ 3.10**. Licencia **MIT**.

La GUI de Streamlit **no** forma parte del paquete (llegará en una fase posterior, fuera de `src/`). En esta versión el preset **Triángulo** ya se resuelve; Warren, Pratt, Howe y los gráficos siguen pendientes.

## Instalación de desarrollo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

```python
from armadura_2d_andresdperezc import Armadura2D

a = Armadura2D.preset_triangulo()
r = a.resolver()
print(r.equilibrio.ok)
for barra in r.fuerzas:
    print(barra.id, barra.tipo, barra.fuerza)
```

```powershell
pytest -v
```

Decisiones de dominio y el plan por fases están en `CONTEXTO_DESARROLLO.md`. La receta de empaquetado está en `ARQUITECTURA_REPLICABLE.md`.

Autor: Andrés David Pérez Criollo — adperezc@udistrital.edu.co
