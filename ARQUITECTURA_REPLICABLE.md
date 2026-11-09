# Arquitectura replicable — librería Python + Sphinx + Streamlit + Docker + PyPI

**Instancia en este repo.** El tema ya no es Bohr: es el analizador de armaduras 2D. Nombres: `armadura-2d-andresdperezc` / `armadura_2d_andresdperezc`, clase `Armadura2D`. Decisiones de dominio y fases: `CONTEXTO_DESARROLLO.md`. Este archivo sigue siendo la receta de capas (PyPI, Sphinx, Streamlit, Docker **sin EC2**).

Guía original para **copiar la arquitectura** del repositorio `entrega_libreria` / `bohr-h-andresdperezc` en **otro proyecto de otra temática**. No copies la física de Bohr: copia las capas, las reglas de empaquetado y el orden de trabajo.

Este archivo resume cómo está armada esa receta, qué decisiones hay que repetir, qué **no** llevar (EC2) y qué piezas extras conviene incluir aunque no las hayas listado al inicio.

---

## 0. Qué problema resuelve esta arquitectura

Una sola receta cubre tres públicos distintos **sin mezclarlos**:

| Público | Qué recibe | Cómo |
|---|---|---|
| Quien instala la librería | Cálculos + API de clases (y gráficos si son parte del dominio) | `pip install <pypi-name>` desde PyPI |
| Quien clona el repo | Lo mismo + GUI + tests + notebook + docs | `pip install -e ".[gui,dev,docs]"` |
| Quien no quiere instalar Python | La GUI en el navegador | Imagen Docker en Docker Hub, puerto 8501 |

La **regla de oro** (igual que en los ejemplos de clase DS2026 y en este repo):

> El paquete **no depende** de la interfaz gráfica. `core.py` no importa Streamlit ni Tkinter. La GUI **solo consume** la API pública. Tests, notebook, `streamlit_app.py`, `docs/` y `Dockerfile` **no** entran al wheel de PyPI porque `pyproject.toml` solo empaqueta lo que está en `src/`.

---

## 1. Alcance para el nuevo desarrollo

### Incluir (igual que aquí)

- Librería instalable, publicable en **TestPyPI** y luego **PyPI**.
- Código con **docstrings** para **Sphinx** (HTML estilo pandas/matplotlib + PDF).
- **GUI Streamlit independiente** de la lógica.
- **Imagen Docker** subida a **Docker Hub**: cualquiera, en cualquier SO, hace `docker pull` + `docker run -p 8501:8501` y abre la app.
- **Notebook Jupyter** que instala/usa la librería y juega con métodos y atributos.
- Repo limpio, documentado, con dependencias declaradas para que alguien clone y corra (con o sin GUI).
- **Tests pytest** de la librería.
- Diseño **POO** claro, ordenado y fácil de leer.
- Documentación Sphinx publicable en **GitHub Pages** (este repo ya lo tiene; conviene repetirlo).

### Excluir a propósito

- **AWS EC2** (y cualquier VM en la nube). En el repo actual está en `DESPLIEGUE.md`; **no lo copies**. Docker local / Docker Hub basta para “cualquier persona, cualquier SO”.
- Tkinter, Qt, FastAPI, Flask, REST. “API pública” = **clases y métodos** que se importan tras `pip install`, no endpoints HTTP.
- Patrones GoF forzados (Strategy, Command, Observer) si el dominio no los necesita. Este repo usó una clase de dominio **plana** más un DTO. Eso es válido y se entiende. En el nuevo proyecto usa POO **clara**, no patrones de adorno.

### Extra de este repo que sí conviene llevar (aunque no lo hayas pedido)

Están implementados aquí y suelen olvidarse al replicar:

1. **Layout `src/`** — sin él, Streamlit y tests se cuelan en el wheel.
2. **Nombre PyPI ≠ nombre de import** — guion vs guion bajo.
3. **Versión duplicada** en `pyproject.toml` y `__init__.py`. PyPI no deja repetir versión.
4. **Extras opcionales** `[gui]`, `[dev]`, `[docs]` en vez de un `requirements.txt` único.
5. **`ejemplo_consola.py`** — demuestra que el paquete funciona **sin** Streamlit.
6. **LICENSE** (aquí MIT) + `readme = "README.md"` en el paquete.
7. **Backend matplotlib `Agg`** — gráficos sin ventana (Docker, tests, scripts).
8. Streamlit escuchando en **`0.0.0.0:8501`** — si dejas `localhost`, Docker no sirve.
9. **HEALTHCHECK** y fuentes (`fonts-dejavu-core`) en el `Dockerfile`.
10. **`.dockerignore` / `.gitignore`** — imagen y repo limpios.
11. **Sphinx autodoc + napoleon + Furo + rinohtype** (PDF en Windows **sin LaTeX**).
12. **GitHub Actions** `.github/workflows/pages.yml` + archivo `.nojekyll`.
13. Tests de **validación** (`ValueError`) además de casos felices.
14. Documento de **limitaciones** y nota “si se expande, hay que validar”.
15. **`CONTEXTO_DESARROLLO.md`** — plan de fases para no mezclar trabajo (útil al empezar el otro tema).

Mejora recomendada que **este repo no tiene** y el nuevo sí puede tener:

- Extra `[notebook]` o Jupyter dentro de `[dev]` (`jupyter`, `ipykernel`) para que el notebook arranque sin instalar a mano.
- Workflow de CI con `pytest` (aquí solo hay Actions para Pages).

---

## 2. Arquitectura en capas (la que hay que copiar)

```text
┌─────────────────────────────────────────────────────────────┐
│  Entrega / operación                                        │
│  Docker Hub  ·  GitHub Pages (Sphinx HTML)  ·  PyPI         │
│  (NO EC2)                                                   │
├─────────────────────────────────────────────────────────────┤
│  Adaptadores (NO van en el wheel)                           │
│  streamlit_app.py  ·  ejemplo_consola.py  ·  notebook       │
├─────────────────────────────────────────────────────────────┤
│  Documentación y calidad (NO van en el wheel)               │
│  docs/ (Sphinx)  ·  tests/  ·  README  ·  guías .md         │
├─────────────────────────────────────────────────────────────┤
│  Núcleo / librería  ←  ÚNICO contenido de PyPI              │
│  src/<import_name>/                                         │
│    __init__.py   API pública + __version__                  │
│    core.py       clases de dominio, cálculos, gráficos      │
└─────────────────────────────────────────────────────────────┘
```

Flujo de datos:

```text
Usuario GUI  →  streamlit_app.py  →  import <import_name>  →  ClasePrincipal
Usuario pip  →  from <import_name> import ClasePrincipal
Notebook     →  mismas llamadas que pip
Tests        →  mismas llamadas; no abren Streamlit
Docker       →  instala el paquete + extra [gui] y arranca Streamlit
```

Ningún adaptador escribe lógica de negocio. Si mañana cambias Streamlit por un script, **no tocas** `src/`.

---

## 3. Estructura de carpetas (plantilla)

Sustituye los placeholders. Lo que está entre `< >` cambia con el tema; lo demás se replica.

```text
<repo>/
├── pyproject.toml                 # metadatos, deps, extras, src layout
├── README.md                      # propósito, install, uso, limitaciones, autor
├── LICENSE                        # p. ej. MIT
├── PUBLICAR_PYPI.md               # TestPyPI → PyPI (el autor sube)
├── DESPLIEGUE.md                  # Docker Hub + GitHub Pages  (SIN EC2)
├── Dockerfile
├── .dockerignore
├── .gitignore
├── streamlit_app.py               # GUI; NO se publica en PyPI
├── ejemplo_consola.py             # prueba sin GUI
├── examples/
│   └── notebook_didactico.ipynb
├── src/
│   └── <import_name>/
│       ├── __init__.py            # exporta clases públicas y __version__
│       └── core.py                # dominio + gráficos; SIN streamlit
├── tests/
│   └── test_core.py
├── docs/                          # Sphinx
│   ├── conf.py
│   ├── index.rst
│   ├── instalacion.rst
│   ├── uso.rst
│   ├── api.rst                    # autodoc
│   ├── gui.rst
│   ├── limitaciones.rst
│   ├── publicar.rst
│   ├── Makefile
│   └── make.bat
└── .github/
    └── workflows/
        └── pages.yml              # Sphinx → GitHub Pages
```

Opcional, como en este repo:

- `CONTEXTO_DESARROLLO.md` — decisiones y fases (no forma parte del paquete).
- `instrucciones/` — enunciados de clase; **no** van en Docker ni en PyPI.

`[tool.setuptools.packages.find] where = ["src"]` es lo que impide que Streamlit, tests y docs se suban a PyPI.

El sdist (`.tar.gz`) sí puede incluir `tests/` (habitual). El **wheel** (`.whl`) solo lleva `src/<import_name>/`.

---

## 4. Diseño POO (claro, sin adornos)

### 4.1 Qué hizo este repo (referencia)

No usó Strategy/Factory/Command. Usó tres piezas fáciles de explicar en una rúbrica o en un PPT:

| Pieza | Rol | Ejemplo aquí |
|---|---|---|
| Clase de dominio | Encapsula estado + constantes + operaciones | `BohrAtom` |
| Objeto de resultado (DTO / value object) | Datos inmutables de una operación | `Transicion` (`@dataclass(frozen=True)`) |
| Función de validación | Rechaza entradas ilegales con `ValueError` | `_entero_positivo` |
| Fachada pública | `__init__.py` reexporta lo que el usuario importa | `BohrAtom`, `Transicion`, `__version__` |
| Adaptador GUI | Solo llama métodos públicos | `streamlit_app.py` |

Eso **es** un diseño POO: encapsulación (`self._z`, `@property`), cohesión (la física vive en una clase), separación GUI/dominio.

### 4.2 Qué repetir en el otro tema

1. **Una clase principal** con nombre del dominio (`<ClasePrincipal>`), no un montón de funciones sueltas en la raíz.
2. **Estado encapsulado**: atributos privados + properties de solo lectura si no deben mutar a lo loco.
3. **Constantes de dominio** como atributos de clase (con docstring), no números mágicos en medio de los métodos.
4. **Resultados ricos**: si un método devuelve varios datos, usa un `@dataclass` (como `Transicion`), no una tupla anónima.
5. **Validación en el borde**: constructor y métodos públicos lanzan `ValueError` (o el error que elijas) con mensaje claro; los métodos internos asumen datos ya validados.
6. **Gráficos en el dominio solo si el enunciado lo pide** (aquí el taller exigía `graficar_*` en la clase, por eso matplotlib **sí** es dependencia del paquete). Si en el nuevo tema los gráficos son solo de la GUI, matplotlib puede ir en `[gui]` y no en el wheel.
7. **Sin API HTTP.** Streamlit llama a la clase; no hay backend REST.
8. Si el dominio crece, parte `core.py` en módulos (`modelo.py`, `calculos.py`, `graficos.py`) pero **sigue exportando una API pequeña** desde `__init__.py`. No inventes un framework.

Esqueleto mínimo del núcleo (cambia nombres y fórmulas):

```python
"""Núcleo del dominio. No importa Streamlit ni Tkinter."""

from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class ResultadoOperacion:
    """Resultado inmutable de una operación de dominio."""

    valor: float
    unidad: str
    etiqueta: str


class ClasePrincipal:
    """Encapsula parámetros, constantes y operaciones del tema.

    Parameters
    ----------
    parametro : tipo
        Descripción. Sphinx (napoleon) lee este bloque.
    """

    CONSTANTE_DE_LIBRO = 1.0
    """Constante didáctica. Documentar unidades."""

    def __init__(self, parametro=1):
        self._parametro = _validar(parametro, "parametro")

    @property
    def parametro(self):
        """Parámetro de construcción (solo lectura)."""
        return self._parametro

    def calcular(self, n):
        """Operación principal.

        Returns
        -------
        float

        Raises
        ------
        ValueError
            Si ``n`` no es válido.
        """
        n = _validar(n, "n")
        return self.CONSTANTE_DE_LIBRO * n

    def graficar(self, n_max):
        """Opcional: devolver matplotlib.figure.Figure, no abrir ventanas."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        # ... dibujar usando self.calcular ...
        return fig

    def __repr__(self):
        return f"ClasePrincipal(parametro={self._parametro})"
```

`__init__.py`:

```python
from .core import ClasePrincipal, ResultadoOperacion

__version__ = "0.1.0"

__all__ = ["ClasePrincipal", "ResultadoOperacion", "__version__"]
```

La versión **0.1.0** debe coincidir con `pyproject.toml`.

---

## 5. Empaquetado: `pyproject.toml`

Plantilla (la de este repo, generalizada):

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "<pypi-name>"                 # con GUIÓN: pip install <pypi-name>
version = "0.1.0"
description = "<una línea del tema>"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
license-files = ["LICENSE"]
authors = [
    { name = "<Nombre>", email = "<correo>" },
]
keywords = ["<tema>", "educación"]
classifiers = [
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent",
    "Intended Audience :: Education",
]
dependencies = [
    "numpy>=1.22",
    # matplotlib>=3.5  ← solo si los gráficos son parte de la librería
]

[project.optional-dependencies]
gui = ["streamlit>=1.28"]
dev = ["pytest>=7", "build", "twine", "jupyter", "ipykernel"]
docs = ["sphinx", "furo", "myst-parser", "rinohtype", "ziamath"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Nombre PyPI vs import

| Uso | Convención | Ejemplo de este repo |
|---|---|---|
| `pip install` / PyPI | guiones | `bohr-h-andresdperezc` |
| `import` / carpeta en `src/` | guiones bajos | `bohr_h_andresdperezc` |
| Imagen Docker | minúsculas, mismo espíritu | `andresperez3/bohr-h-andresdperezc:0.1.0` |

Antes de publicar, busca el nombre en https://pypi.org/project/<pypi-name>/ — si existe, cámbialo.

### Qué va en `dependencies` vs extras

| Extra / grupo | Librerías | Quién las necesita |
|---|---|---|
| runtime (`dependencies`) | numpy, y matplotlib **si** `graficar_*` está en la clase | `pip install` puro |
| `[gui]` | streamlit | clonar repo y correr la GUI, o Docker |
| `[dev]` | pytest, build, twine, jupyter | desarrollar, testear, publicar, notebook |
| `[docs]` | sphinx, furo, myst-parser, rinohtype | HTML/PDF y Pages |

Instalación de desarrollo (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[gui,dev,docs]"
```

Linux/macOS: `source .venv/bin/activate` y el mismo `pip install`.

Si PowerShell bloquea `Activate.ps1`: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (una vez).

---

## 6. Publicar en TestPyPI y PyPI

Copia la guía `PUBLICAR_PYPI.md` cambiando nombres. Resumen operativo:

### 6.1 Qué se publica

Solo `src/<import_name>/`. No van: `streamlit_app.py`, `ejemplo_consola.py`, `docs/`, `Dockerfile`, notebook, `tests/` en el wheel.

### 6.2 Pasos

```powershell
pytest -v
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
python -m build
python -m twine check dist/*
```

Deben aparecer:

- `dist/<import_name>-0.1.0.tar.gz`
- `dist/<import_name>-0.1.0-py3-none-any.whl`

`twine check` debe decir **PASSED**.

Cuentas **independientes** (ambas con 2FA):

1. https://test.pypi.org/account/register/
2. https://pypi.org/account/register/

Token: *Account settings → API tokens*. Empieza por `pypi-` y se muestra una vez.

Opcional `~/.pypirc` (**nunca** al git):

```ini
[pypi]
  username = __token__
  password = pypi-...

[testpypi]
  username = __token__
  password = pypi-...
```

Ensayo:

```powershell
python -m twine upload --repository testpypi dist/*
```

Probar en un venv **limpio**. numpy/matplotlib salen de PyPI real:

```powershell
python -m pip install `
    --index-url https://test.pypi.org/simple/ `
    --extra-index-url https://pypi.org/simple/ `
    <pypi-name>
python -c "from <import_name> import ClasePrincipal; print(ClasePrincipal())"
```

Publicación real:

```powershell
python -m twine upload dist/*
```

Después: `pip install <pypi-name>`.

### 6.3 Versión nueva

PyPI **no permite** subir dos veces `0.1.0`.

1. Cambios + `pytest -v`.
2. Subir versión en `pyproject.toml` **y** `__init__.py`.
3. Borrar `dist/`, reconstruir, `twine check`, `twine upload`.

Errores frecuentes: `403` nombre ocupado; `400 File already exists` versión repetida; `ModuleNotFoundError` falta `__init__.py` o el paquete no está en `src/`.

Las subidas las hace el **autor**. El asistente deja artefactos y la guía; no pide tokens en el chat.

---

## 7. Sphinx (docstrings → HTML + PDF, estilo librería real)

### 7.1 Cómo escribir el código para que Sphinx funcione solo

Sphinx **no magia el código**: lee módulos y docstrings.

En este repo se usa:

- Extensiones: `autodoc`, `napoleon`, `viewcode`, `mathjax`, `myst_parser`.
- Estilo **NumPy o Google** en los docstrings (`Parameters`, `Returns`, `Raises`).
- Tema HTML **Furo**.
- PDF con **rinohtype** (`sphinx-build -b rinoh`) — no requiere LaTeX en Windows.
- `docs/api.rst` con `automodule` / `autoclass` / `:members:`.

Reglas prácticas (cópialas al nuevo `core.py`):

1. Docstring de módulo al inicio (qué hace, que **no** depende de Streamlit).
2. Docstring de clase con `Parameters`.
3. Docstring de cada método público con `Returns` y `Raises`.
4. Docstring de cada campo del dataclass (Sphinx los documenta).
5. Constantes de clase con docstring debajo.
6. Métodos `_privados` pueden ir sin autodoc; la API pública debe estar completa.
7. Fórmulas en reST/Markdown de `docs/` con `:math:` o `.. math::`. En docstrings, `:math:` también funciona si napoleon/mathjax están activos.

`docs/conf.py` esencial:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

project = "<pypi-name>"
author = "<Nombre>"
release = "0.1.0"
language = "es"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "myst_parser",
]

html_theme = "furo"
napoleon_google_docstring = True
napoleon_numpy_docstring = True
autodoc_member_order = "bysource"
```

`docs/api.rst` típico:

```rst
API pública
===========

Tras ``pip install``, esto es lo que se importa. No hay API HTTP.

.. automodule:: <import_name>

.. autoclass:: <import_name>.ClasePrincipal
   :members:
   :undoc-members:
   :show-inheritance:
```

Páginas Sphinx que este repo ya tiene y conviene repetir: `index`, `instalacion`, `uso`, `api`, `gui`, `limitaciones`, `publicar`.

Construir:

```powershell
python -m pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
sphinx-build -b rinoh docs docs/_build/rinoh
```

HTML: `docs/_build/html/index.html`.  
PDF: `docs/_build/rinoh/<pypi-name>.pdf`.

### 7.2 GitHub Pages

Este repo publica Sphinx con `.github/workflows/pages.yml`:

1. Crear el repo, rama `main`.
2. *Settings → Pages → Source: GitHub Actions*.
3. Cada push a `main` instala `.[docs]`, construye HTML y publica.
4. Incluir `.nojekyll` en el artefacto (el workflow ya hace `touch docs/_build/html/.nojekyll`) para que GitHub no ignore `_static`.

URL típica: `https://<usuario>.github.io/<repositorio>/`.

Pages **no** hospeda Streamlit (solo estático). Docs = Pages. GUI = Docker / `streamlit run` local.

---

## 8. GUI Streamlit (independiente de la lógica)

### 8.1 Reglas

- Archivo en la **raíz**: `streamlit_app.py` (no dentro de `src/`).
- Única importación de dominio: `from <import_name> import ClasePrincipal`.
- Cero fórmulas duplicadas: si el cálculo no existe en la librería, **añádelo a `core.py`** y luego úsalo en la GUI.
- No testear Streamlit en pytest (la GUI no es el paquete).
- Mensaje de `ImportError` diciendo que hay que `pip install -e ".[gui]"`.
- `os.environ.setdefault("MPLBACKEND", "Agg")` si hay figuras.

### 8.2 Arranque local

```powershell
python -m pip install -e ".[gui]"
streamlit run streamlit_app.py
```

http://localhost:8501

### 8.3 Arranque en Docker (imprescindible)

```text
streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true
```

Si Streamlit escucha solo en `127.0.0.1`, el puerto publicado por Docker no muestra nada.

Por qué Streamlit y no Tkinter: Tkinter abre una **ventana del SO**. Docker no tiene esa ventana de forma portable. Streamlit abre un **servidor HTTP**; el navegador es la GUI en Windows, Linux y macOS.

---

## 9. Docker y Docker Hub (sin EC2)

### 9.1 `Dockerfile` (el de este repo, generalizado)

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY streamlit_app.py ./

RUN pip install --upgrade pip \
    && pip install ".[gui]"

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=8s --start-period=25s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
```

La imagen instala **el paquete + `[gui]`**. No copia tests, docs, notebook ni `.venv`.

### 9.2 `.dockerignore` (mínimo)

```text
.venv/
.git/
.github/
.pytest_cache/
__pycache__/
*.egg-info/
dist/
build/
docs/_build/
tests/
examples/
instrucciones/
*.png
```

### 9.3 Construir, subir, usar

El **autor** hace login y push:

```bash
docker login
docker build -t <usuario-dockerhub>/<pypi-name>:0.1.0 .
docker push <usuario-dockerhub>/<pypi-name>:0.1.0
```

Cualquier persona, cualquier SO (Docker Desktop o motor Docker):

```bash
docker pull <usuario-dockerhub>/<pypi-name>:0.1.0
docker run --rm -p 8501:8501 <usuario-dockerhub>/<pypi-name>:0.1.0
```

Abrir http://localhost:8501.

Notas:

- Tag igual que la versión del paquete (`0.1.0`). Si cambias código ya publicado, usa `0.1.1`; no reutilices el tag a la ligera.
- La imagen base es `linux/amd64`. En Mac Apple Silicon, si no emula solo: `docker run --platform linux/amd64 ...`.
- **No documentes EC2** en el nuevo `DESPLIEGUE.md`. Quédate en: construir, push a Hub, pull + run local.

---

## 10. Notebook Jupyter

Archivo: `examples/notebook_didactico.ipynb`.

Debe:

1. Decir que **no usa Streamlit**.
2. Indicar instalación (`pip install -e .` o, cuando exista PyPI, `pip install <pypi-name>`).
3. Pedir el kernel del venv del proyecto.
4. Teoría breve del **nuevo** tema (no Bohr).
5. Celdas que instancian `<ClasePrincipal>`, leen atributos/constantes, llaman métodos, muestran gráficos si aplica.
6. Dejar `execution_count` / `outputs` vacíos o regenerarlos; no subir basura enorme.

Estructura de celdas que funcionó aquí (adapta el contenido):

1. Markdown: título + cómo instalar + “no usa Streamlit”.
2. Markdown: teoría mínima.
3. Código: `from ... import ClasePrincipal` + atributos.
4. Código: operaciones principales.
5. Código: caso de libro / validación visual.
6. Código: gráficos (`fig` se muestra sola en Jupyter porque `graficar_*` **devuelve** la figura, no abre Tkinter).

Para que “alguien baje el repo y juegue”, añade Jupyter al extra `[dev]` (mejora respecto a este repo).

---

## 11. Tests (`pytest`)

Archivo: `tests/test_core.py`. Solo importan la librería.

```powershell
python -m pip install -e ".[dev]"
pytest -v
```

Qué cubrir (traduce “valores de libro” a tu tema):

| Tipo | Qué |
|---|---|
| Caso canónico | Resultado conocido del dominio (aquí: \(E_1 = -13.6\,\mathrm{eV}\)) |
| Proporcionalidades / invariantes | Relaciones que no pueden romperse |
| Objeto resultado | Tipo, campos, signo, unidades |
| Colecciones | `energias(n_max)` / equivalentes |
| Validación | parametrize con 0, negativos, floats, bool, strings → `ValueError` |
| Gráficos | `isinstance(fig, matplotlib.figure.Figure)` (backend `Agg`) |

Al inicio del archivo de tests:

```python
import matplotlib
matplotlib.use("Agg")
```

Fixture `plt.close("all")` para no dejar figuras abiertas.

No hace falta Selenium/Playwright sobre Streamlit para validar la librería.

---

## 12. README del repo (cara pública)

El `README.md` de este proyecto es el modelo. Secciones mínimas:

1. Qué es y para qué.
2. Nombre pip vs import.
3. Que la GUI **no** va en el paquete.
4. Versión, Python ≥ 3.10, licencia.
5. Tabla Windows / Linux / macOS (pip, pytest, notebook, Streamlit, Docker). **Sin fila EC2.**
6. Instalación PyPI y modo editable + tabla de extras.
7. Uso básico (10–20 líneas).
8. Tabla de métodos de la clase principal.
9. Unidades / convenciones del dominio.
10. Ejemplos (`ejemplo_consola.py`, notebook).
11. Cómo correr tests.
12. Cómo correr Streamlit.
13. Cómo correr Docker.
14. Cómo construir Sphinx.
15. Enlace a `PUBLICAR_PYPI.md`.
16. Limitaciones y “si se expande, validar”.
17. Autor.

`readme = "README.md"` hace que esa misma cara salga en PyPI.

---

## 13. `.gitignore` mínimo

```text
.venv/
venv/
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.pytest_cache/
.ipynb_checkpoints/
.mypy_cache/
*.log
docs/_build/
examples/*.png
```

Nunca: `.pypirc`, tokens, `.pem`, secretos.

---

## 14. Orden de implementación (fases)

Trabaja **una fase por vez**. Es el método que cerró este repo.

| Fase | Objetivo | Criterio de listo |
|---|---|---|
| 0 | Contexto del **nuevo** tema | Decisiones escritas (nombre, clase, unidades, GUI Streamlit, sin EC2) |
| 1 | Esqueleto instalable | `pip install -e .` e `import <import_name>` |
| 2 | Dominio + tests | `pytest -v` verde con valores de referencia |
| 3 | Gráficos (si aplican) | `graficar_*` devuelve `Figure` |
| 4 | Ejemplos | `ejemplo_consola.py` + notebook |
| 5 | Streamlit | `streamlit run streamlit_app.py` usa solo la API |
| 6 | Sphinx + PDF | HTML local + rinoh; docstrings suficientes |
| 7 | Docker | `docker build` + `run -p 8501:8501` abre la GUI |
| 8 | Guías | `PUBLICAR_PYPI.md` + `DESPLIEGUE.md` **sin EC2** |
| 9 | README completo | Alguien ajeno puede instalar y usar |

Fuera de fases (las hace el autor, no el asistente): GitHub, Pages, `docker push`, TestPyPI, PyPI.

Dependencias: 1 → 2 → 3 → 4 y 5 en paralelo. 6 tras docstrings (2–3). 7 necesita 5.

---

## 15. Checklist de replicación

### Librería / PyPI

- [ ] `src/<import_name>/` con `__init__.py` y `core.py`
- [ ] `pyproject.toml` con `where = ["src"]`
- [ ] Versión igual en toml y `__init__.py`
- [ ] Nombre PyPI libre (guion) ≠ import (guion bajo)
- [ ] LICENSE y README
- [ ] `python -m build` + `twine check` PASSED
- [ ] Guía TestPyPI → PyPI

### POO / calidad

- [ ] Clase principal + dataclass de resultados si hace falta
- [ ] Validaciones con `ValueError`
- [ ] Docstrings NumPy/Google en API pública
- [ ] `pytest -v` en verde
- [ ] La GUI no duplica lógica

### GUI / Docker

- [ ] `streamlit_app.py` fuera de `src/`
- [ ] Extra `[gui]`
- [ ] `Dockerfile` con `0.0.0.0:8501`, Agg, HEALTHCHECK
- [ ] `.dockerignore`
- [ ] Guía `docker build` / `push` / `pull` / `run`
- [ ] **Ninguna** sección EC2

### Docs / ejemplos

- [ ] `docs/` Sphinx + Furo + autodoc
- [ ] Receta PDF rinohtype
- [ ] Pages workflow (opcional pero recomendado)
- [ ] Notebook didáctico
- [ ] `ejemplo_consola.py`
- [ ] Limitaciones y compatibilidad SO

---

## 16. Tabla de traducción Bohr → nuevo proyecto

Usa esta tabla al copiar archivos para no dejar nombres viejos.

| Aquí (Bohr) | En el nuevo repo |
|---|---|
| `bohr-h-andresdperezc` | `<pypi-name>` |
| `bohr_h_andresdperezc` | `<import_name>` |
| `BohrAtom` | `<ClasePrincipal>` |
| `Transicion` | `<Resultado…>` |
| `energia` / `radio` / `transicion` | métodos del nuevo dominio |
| `Z`, `n` | parámetros del nuevo dominio |
| `andresperez3/bohr-h-andresdperezc:0.1.0` | `<usuario-dockerhub>/<pypi-name>:0.1.0` |
| Puerto 8501 | 8501 (o el que documentes; sé consistente) |
| `CONTEXTO_DESARROLLO.md` (física Bohr) | reescribir; no reutilizar el texto de Bohr |
| `DESPLIEGUE.md` sección EC2 | **borrar** |
| `docs/gui.rst` menciones EC2 | **borrar** |
| PPT / `presentacion/` | solo si el nuevo enunciado lo pide |

---

## 17. Qué no copiar de este repo

- Física, fórmulas, tests de Balmer, textos de hidrogenoides.
- Usuario Docker Hub y correo del autor, salvo que sea el mismo.
- Sección EC2 de `DESPLIEGUE.md`, `docs/gui.rst`, `docs/limitaciones.rst` y el README.
- `instrucciones/TALLER_Modelo_Atomico.docx` y el PPT de Bohr.
- `CONTEXTO_DESARROLLO.md` tal cual (sí copia la **idea** de fases y decisiones cerradas).

---

## 18. Referencia rápida de comandos (nuevo repo)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[gui,dev,docs]"

pytest -v
python ejemplo_consola.py
streamlit run streamlit_app.py

sphinx-build -b html docs docs/_build/html
sphinx-build -b rinoh docs docs/_build/rinoh

docker build -t <usuario-dockerhub>/<pypi-name>:0.1.0 .
docker run --rm -p 8501:8501 <usuario-dockerhub>/<pypi-name>:0.1.0

python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
```

---

## 19. Mapa de este repositorio (origen de la receta)

| Archivo actual | Para qué sirve al replicar |
|---|---|
| `pyproject.toml` | Empaquetado, extras, pytest, src layout |
| `src/bohr_h_andresdperezc/core.py` | Modelo de clase + docstrings + validación + gráficos que devuelven Figure |
| `src/bohr_h_andresdperezc/__init__.py` | API pública y versión |
| `tests/test_core.py` | Estilo de tests (libro + errores + figuras) |
| `streamlit_app.py` | GUI que solo consume la API |
| `ejemplo_consola.py` | Demo sin GUI |
| `examples/notebook_didactico.ipynb` | Demo Jupyter |
| `Dockerfile` + `.dockerignore` | Imagen portable de la GUI |
| `docs/` + `.github/workflows/pages.yml` | Sphinx + Pages |
| `PUBLICAR_PYPI.md` | TestPyPI / PyPI |
| `DESPLIEGUE.md` | Docker Hub (+ EC2: **no replicar**) |
| `README.md` | Cara pública |
| `CONTEXTO_DESARROLLO.md` | Cómo se planificó por fases |

Si el nuevo desarrollo sigue esta guía, obtiene la misma arquitectura: librería publicable, documentación tipo librería científica, GUI desacoplada, imagen Docker usable en cualquier SO, notebook de prueba y tests, **sin** despliegue en EC2.
