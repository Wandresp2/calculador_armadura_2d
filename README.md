# armadura-2d-andresdperezc

Librería didáctica en Python para **armaduras 2D isostáticas** (mecánica vectorial). Resuelve el equilibrio nodal `A x = b`, clasifica cada barra en **tensión** / **compresión** / nula y dibuja la figura.

Se instala con **guion** y se importa con **guion bajo**:

```text
pip install armadura-2d-andresdperezc
from armadura_2d_andresdperezc import Armadura2D
```

La GUI de Streamlit **no** forma parte del paquete: vive en este repositorio (`streamlit_app.py`) y en la imagen Docker. El paquete no depende de Streamlit ni de Tkinter.

Versión **0.1.0**. Python **≥ 3.10**. Licencia **MIT**.

## Requisitos y sistemas

Corre en **Windows, Linux y macOS** (Python 3.10 o superior).

| Uso | Windows | Linux | macOS |
|---|---|---|---|
| `pip install` + NumPy + matplotlib | Sí | Sí | Sí |
| pytest y notebook | Sí | Sí | Sí |
| Streamlit en el navegador | Sí | Sí | Sí |
| Docker + Streamlit | Sí (Docker Desktop) | Sí | Sí |

Tkinter **no** es requisito. En Linux no hace falta `python3-tk`.

## Instalación

Cuando el paquete esté en [PyPI](https://pypi.org/project/armadura-2d-andresdperezc/):

```bash
pip install armadura-2d-andresdperezc
```

Eso instala la **lógica (NumPy) y los gráficos matplotlib**. No instala Streamlit ni copia `streamlit_app.py`.

### Desarrollo (modo editable)

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,docs]"
```

En Linux o macOS: `source .venv/bin/activate` y el mismo `pip install`.

Si el comando `python` no está en el PATH (Windows), use el launcher `py`.

Extras opcionales:

| Extra | Qué añade |
|---|---|
| `[gui]` | Streamlit, para `streamlit run streamlit_app.py` (hace falta el archivo del repo) |
| `[dev]` | pytest, build, twine, Jupyter |
| `[docs]` | Sphinx, Furo, rinohtype |

Todo junto: `python -m pip install -e ".[gui,dev,docs]"`.

Si PowerShell bloquea `Activate.ps1`: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (una sola vez).

## Uso básico

```python
from armadura_2d_andresdperezc import Armadura2D

a = Armadura2D.preset_triangulo()  # también preset_warren, preset_pratt, preset_howe
r = a.resolver()
print(r.equilibrio.ok)
for barra in r.fuerzas:
    print(barra.id, barra.tipo, barra.fuerza)

fig = a.graficar(r)
fig.savefig("triangulo.png")
```

Unidades fijas: **kN** y **m**. El eje `y` es positivo hacia arriba. Tensión `N > 0`; compresión `N < 0`.

El triángulo de libro (base 4 m, altura 3 m, 50 kN hacia abajo en la cúspide) da `Ry = 25 kN` en cada apoyo, B1 `=+50/3 kN` (tensión) y B2 = B3 `= −(25/3)√13 kN` (compresión).

### Métodos de `Armadura2D`

| Método | Resultado |
|---|---|
| `preset_triangulo()` / `preset_warren()` / `preset_pratt()` / `preset_howe()` | Armadura lista para `resolver()` |
| `agregar_nodo` / `agregar_barra` / `agregar_apoyo` / `agregar_carga` | Construcción libre. La GUI también la expone en el modo Propia |
| `definir_apoyos(fijo, movil, tipo_movil="movil")` | Un pin y un rodillo: `movil` (piso, Ry) o `movil_pared` (pared, Rx) |
| `ecuaciones()` | Sistema ΣFx = 0 y ΣFy = 0 de cada nudo, sin sustituir la solución |
| `graficar_nudo(nudo, resultado)` | Cuerpo libre de un nudo |
| `definir_cargas([(nudo, fx, fy), ...])` | Sustituye el conjunto de cargas |
| `reemplazar_coordenadas({id: (x, y), ...})` | Mueve todos los nudos a la vez |
| `longitud(barra)` / `angulo(barra)` | `L` en m y ángulo en radianes |
| `resolver()` | `ResultadoArmadura` (fuerzas, reacciones, equilibrio) |
| `verificar_equilibrio(resultado=None)` | Residuos `Σ Fx`, `Σ Fy`, `Σ M` |
| `graficar(resultado=None)` | `matplotlib.figure.Figure` con fuerzas, cargas y reacciones |
| `graficar_plano()` | La misma geometría sin resolver: nudos, barras, longitudes, apoyos y cargas |
| `snapshot_nodos()` / `snapshot_barras()` / `snapshot_apoyos()` / `snapshot_cargas()` | Lectura para GUI y scripts (sin tocar `_nodos`) |

Los gráficos **devuelven** la figura. En un script se guarda el PNG; en un notebook se muestra sola. En tests y Docker use el backend `Agg`.

Si la armadura no es isostática (`m + r = 2j`) o `A` es singular, se lanza `ValueError` con un mensaje en español.

### Unidades

| Magnitud | Unidad |
|---|---|
| Fuerza interna, reacción, carga | kN |
| Coordenadas y longitudes | m |
| Ángulo | rad |
| Momento (residuo de equilibrio) | kN·m |

### Presets

| Nombre | Geometría por defecto | Carga | Signo típico de las diagonales |
|---|---|---|---|
| Triángulo | 4 m × 3 m, 3 nudos | 50 kN en la cúspide | — |
| Warren | puente 4 m × 2 m, 2 paneles | 50 kN en el tablero central | — |
| Pratt | 6 nudos; diagonales hacia el centro | igual | **tensión** (`3-1`, `5-1`) |
| Howe | mismas cuerdas; diagonales hacia los apoyos | igual | **compresión** (`4-0`, `4-2`) |

La GUI ofrece estos cuatro y, además, una armadura propia. Se arma con las tablas o con clics en el plano: nudos en la cuadrícula de 0,5 m, barras entre dos nudos, y apoyos o cargas sobre un nudo. Borrar y afinar coordenadas sigue en la tabla.

## Ejemplos (sin Streamlit)

Demuestran que el paquete funciona **solo con pip**:

- `python examples/ejemplo_consola.py` — triángulo de libro, Pratt y Howe; PNG en `examples/`.
- `examples/notebook_didactico.ipynb` — teoría breve y llamadas a la librería (Jupyter; kernel del `.venv`).

## Pruebas

```powershell
python -m pip install -e ".[dev]"
pytest -v
```

Los tests contrastan el triángulo de libro, isostática y residuos ≈ 0 en los cuatro presets, signos Pratt vs Howe, `graficar()` → `Figure` y los `ValueError` de geometría ilegal. CI: `.github/workflows/tests.yml`.

## GUI (Streamlit, opcional)

La interfaz **no se publica en PyPI**. Hay que clonar este repositorio:

```powershell
python -m pip install -e ".[gui]"
streamlit run streamlit_app.py
```

Abra http://localhost:8501. Arriba están las páginas Calculadora y Ecuaciones. En la calculadora, los datos quedan a la izquierda y el plano a la derecha, tanto en una armadura precargada como en una propia. La figura con fuerzas y reacciones va centrada, antes del botón Calcular. Ese botón abre el equilibrio y las tablas. Las ecuaciones y el cuerpo libre de cada nudo están en la otra página. La GUI convierte “vertical hacia abajo (+)” a `Fy` negativa; las ecuaciones salen de `ecuaciones()`, no se reescriben en la interfaz.

## Docker

Cualquier sistema con Docker abre la misma GUI en el navegador (no usa Tkinter). Streamlit escucha en `0.0.0.0:8501`.

```bash
docker build -t andresperez3/armadura-2d-andresdperezc:0.1.0 .
docker run --rm -p 8501:8501 andresperez3/armadura-2d-andresdperezc:0.1.0
```

http://localhost:8501

El `docker push` a Docker Hub (usuario `andresperez3`) y GitHub Pages: [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md).

## Documentación (Sphinx)

```powershell
python -m pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
sphinx-build -b rinoh docs docs/_build/rinoh
```

HTML: `docs/_build/html/index.html`. PDF: `docs/_build/rinoh/armadura-2d-andresdperezc.pdf`.

GitHub Pages: *Settings → Pages → GitHub Actions* (flujo en `.github/workflows/pages.yml`).

## Publicar en PyPI (lo hace el autor)

Paso a paso, primero TestPyPI y luego PyPI: [`docs/PUBLICAR_PYPI.md`](docs/PUBLICAR_PYPI.md).

Solo se instala `src/armadura_2d_andresdperezc/`. `streamlit_app.py`, `plano_ui.py`, tests, docs, Docker y el notebook quedan fuera del wheel. La imagen de Docker sí copia esos dos archivos de la interfaz, porque ahí se abre la misma página.

## Limitaciones (0.1.0)

- Solo **2D** e **isostáticas**. Hiperestática, mecanismo o `A` singular → `ValueError`.
- Cargas solo en nudos. Sin peso propio ni carga distribuida en la barra.
- Apoyos: un fijo (Rx, Ry) y un móvil. El móvil puede estar en un piso (solo Ry) o en una pared vertical (solo Rx). Sin empotramiento ni rodillo inclinado.
- Sin pórticos, momento flector, 3D, diámetro, esfuerzo `σ = N/A`, pandeo ni códigos NSR/AISC.
- La armadura propia se arma con tablas o con clics en el plano (cuadrícula de 0,5 m, que crece alrededor de los nudos). No es un dibujo a mano alzada.
- Unidades fijas kN y m.

Si el desarrollo se **expande**, hay que **volver a validarlo**.

**Futuro** (no está en esta versión): diámetro o sección por barra y `σ = N/A` como postproceso, sin cambiar `A x = b`. Dibujar la armadura a mano alzada, sin la cuadrícula de 0,5 m, tampoco está. Tampoco hay pesos `W` ni cuerdas (elementos que solo trabajan a tensión): está anotado para una versión posterior, en la librería y en la imagen Docker, sin cambiar el equilibrio `A x = b`.

## Autor

Andrés David Pérez Criollo — adperezc@udistrital.edu.co

Universidad Distrital Francisco José de Caldas.

Licencia MIT. Ver [`LICENSE`](LICENSE).
