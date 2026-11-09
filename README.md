# armadura-2d-andresdperezc

Librería didáctica en Python para **armaduras 2D isostáticas** (mecánica vectorial): fuerzas internas, reacciones y clasificación tensión/compresión.

Se instala con **guion** y se importa con **guion bajo**:

```text
pip install armadura-2d-andresdperezc
from armadura_2d_andresdperezc import Armadura2D
```

Versión **0.1.0**. Python **≥ 3.10**. Licencia **MIT**.

La GUI de Streamlit **no** forma parte del paquete (llegará en una fase posterior, fuera de `src/`). El solver, los presets y los gráficos aún no están implementados; este README es el esqueleto de la fase 1.

## Instalación de desarrollo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

```python
from armadura_2d_andresdperezc import Armadura2D, __version__

print(__version__)
print(Armadura2D())
```

Decisiones de dominio y el plan por fases están en `CONTEXTO_DESARROLLO.md`. La receta de empaquetado está en `ARQUITECTURA_REPLICABLE.md`.

Autor: Andrés David Pérez Criollo — adperezc@udistrital.edu.co
