# Contexto y plan de desarrollo — Analizador de Armaduras 2D

**Cómo usar este archivo:** léelo completo al inicio de cada sesión de Cursor **antes** de editar código. Aquí está el alcance, las decisiones cerradas, la mecánica, los presets, la API, las limitaciones, el futuro y las fases.

Léelo junto con `ARQUITECTURA_REPLICABLE.md` (receta de empaquetado copiada de Bohr: `src/`, PyPI, Sphinx, Streamlit, Docker **sin EC2**). No copies física de Bohr ni secciones de EC2.

**Estado:** diseño cerrado. Fases 0 a 10 hechas. Queda publicar (usuario).

**Autor del paquete:** Andrés David Pérez Criollo  
**Correo:** adperezc@udistrital.edu.co  
**Trabajo:** individual, rama `main`.

---

## 0. Instrucciones para el asistente (sesiones futuras)

1. Leer **este archivo entero** y `ARQUITECTURA_REPLICABLE.md`.
2. No reabrir decisiones de la sección 3 salvo que el usuario lo pida.
3. Implementar **solo la fase que el usuario pida** en esa sesión. No adelantar fases “por si acaso”.
4. Al terminar una fase: actualizar la tabla de la sección 14 (estado: pendiente / en curso / hecha) y un breve “cómo verificar”.
5. No publicar en PyPI, Docker Hub, GitHub ni GitHub Pages: eso lo hace el usuario. Preparar archivos y comandos.
6. Idioma del repo, código, comentarios, docstrings, README, Sphinx, Streamlit y notebook: **español**.
7. No meter Streamlit (ni Tkinter) dentro de `src/`. El paquete no depende de la GUI.
8. No implementar REST/FastAPI/Flask. “API pública” = clases y métodos que se importan tras `pip install`.
9. No inventar patrones GoF (Strategy, Factory, Command, Observer). `Armadura2D` es **plana**.
10. **No EC2.** Ni en `DESPLIEGUE.md`, ni en README, ni en Sphinx.
11. En 0.1.0 **no** hay diámetro, esfuerzo, pandeo ni diseñador/CAD. Eso es futuro (sección 13).
12. Cálculos con **NumPy** (`numpy.linalg.solve`). Gráficos con **matplotlib** (devuelven `Figure`; backend `Agg` en Docker/tests).
13. La GUI **no duplica** fórmulas: si falta un cálculo, se añade a `core.py` y luego se consume.
14. No copiar textos, tests ni fórmulas de Bohr. Sí copiar capas, extras `[gui]`, `[dev]`, `[docs]` y el orden de fases.

---

## 1. Qué significa “API” en este proyecto

**No hay API HTTP.** No hay endpoints, FastAPI, Flask ni “el backend”.

API pública = lo que otra persona usa tras instalar el paquete:

```python
from armadura_2d_andresdperezc import Armadura2D

a = Armadura2D.preset_triangulo()
r = a.resolver()
a.graficar(r)
```

Streamlit solo **llama** esos métodos. Docker **muestra** esa GUI. GitHub Pages hospeda Sphinx (estático), no Streamlit.

---

## 2. Orígenes del requerimiento

### 2.1 De dónde sale el tema

Segundo desarrollo del curso, **otra temática** con la **misma arquitectura** que `entrega_libreria` (`bohr-h-andresdperezc`).

La diapositiva 15 del PPT de Bohr (“Desarrollo futuro: Analizador de Armaduras 2D”) es el contrato de dominio:

- Una armadura (puentes, techos) son barras unidas en nudos.
- A mano, el método de nudos ~30 min y un error de signo lo arruina.
- En Python se reduce a álgebra lineal: \(A \cdot x = b\).
- Por nudo: \(\sum F_x = 0\), \(\sum F_y = 0\).
- Geometría: \(L = \sqrt{\Delta x^2 + \Delta y^2}\), \(\cos\theta = \Delta x / L\), \(\sin\theta = \Delta y / L\).
- \(A\) = geometría (senos y cosenos); \(x\) = fuerzas internas + reacciones; \(b\) = cargas externas.
- Ejemplo dibujado: triángulo, 3 nudos, 3 barras, apoyo fijo, apoyo móvil, 50 kN en la cúspide.
- Signo: **+ tensión** (la barra se estira), **− compresión** (se acorta).
- GUI Streamlit: en aquella diapositiva era “opcional más adelante”. **En este parcial sí va.**

No hay Word de taller de armaduras en este repo. El alcance lo cerró el usuario en conversación (noviembre 2026), no un enunciado de Bohr.

### 2.2 Qué pidió el usuario (además de la diapositiva)

- Aplicación de **mecánica vectorial**: diseñar/analizar armaduras 2D.
- Varias armaduras **precargadas**; el usuario elige una y **edita** fuerzas, apoyos, longitudes (vía coordenadas).
- Librería Python publicable + GUI Streamlit + imagen Docker, con los mismos cálculos.
- NumPy y matplotlib para calcular y graficar.
- Desarrollar **por fases**, documentar al cerrar cada una, para no perder contexto.
- Documentar como **futuro** (no implementar ahora):
  1. Dibujar o diseñar cualquier tipo de armadura en la aplicación y calcular.
  2. Esfuerzo y más variables (diámetro de barras, etc.).

### 2.3 Arquitectura a copiar (no la física)

Fuente: `ARQUITECTURA_REPLICABLE.md` y ejemplos de clase <https://github.com/cagomezv/DS2026/tree/main/7Pypi>.

Regla de oro:

> El paquete **no depende** de la interfaz gráfica. `core.py` no importa Streamlit ni Tkinter. La GUI solo consume la API pública. Tests, notebook, docs y `Dockerfile` **no** entran al wheel: `pyproject.toml` solo empaqueta `src/`.

Tres públicos:

| Público | Qué recibe | Cómo |
|---|---|---|
| Quien instala la librería | Análisis + gráficos matplotlib | `pip install armadura-2d-andresdperezc` |
| Quien clona el repo | Lo mismo + GUI + tests + notebook + docs | `pip install -e ".[gui,dev,docs]"` |
| Quien no quiere Python | GUI en el navegador | Docker Hub, puerto 8501 |

Mejoras respecto a Bohr (la guía lo pide): Jupyter/ipykernel dentro de `[dev]`; workflow de CI con `pytest` (Bohr solo tenía Actions para Pages).

---

## 3. Decisiones cerradas

No reabrir salvo pedido explícito del usuario.

| # | Tema | Decisión |
|---|---|---|
| 1 | Producto 0.1.0 | Analizador de **armaduras 2D isostáticas** (mecánica vectorial). No es un CAD ni un dimensionador. |
| 2 | GUI | **Streamlit** única GUI. **No Tkinter.** Archivo `streamlit_app.py` en la raíz. |
| 3 | Nombre PyPI | `armadura-2d-andresdperezc` (revalidar el día de publicar: https://pypi.org/project/armadura-2d-andresdperezc/) |
| 4 | Nombre de import | `armadura_2d_andresdperezc` |
| 5 | Clase principal | `Armadura2D` |
| 6 | Idioma | Español en todo |
| 7 | Alcance mecánico | 2D, barras de dos fuerzas, cargas **solo en nudos**, un apoyo **fijo** (\(R_x, R_y\)) y un **móvil**: piso (solo \(R_y\), tipo ``movil``) o pared vertical (solo \(R_x\), tipo ``movil_pared``). Solo **isostáticas** (\(m + r = 2j\) y \(A\) invertible). |
| 8 | Unidades 0.1.0 | Fuerzas en **kN**, coordenadas y longitudes en **m**. Eje: origen abajo-izquierda, **y positivo hacia arriba**. |
| 9 | Diámetro / esfuerzo | **Fuera de 0.1.0.** Documentado como futuro. No bloquear `resolver()` por falta de diámetro. |
| 10 | Signo de fuerzas internas | **Positivo = tensión**, negativo = compresión. Barra de fuerza ≈ 0 → tipo `nula`. |
| 11 | \(\sum M = 0\) | No es una fila extra por nudo (fuerzas concurrentes). Es **verificación global** (y por nudo, residuo numérico) vía `verificar_equilibrio()`. El solver es \(A x = b\) por nudos. |
| 12 | Catálogo GUI | Cuatro presets: **Triángulo · Warren · Pratt · Howe**, más modo **Propia** por tablas (nudos, barras, cargas, apoyos). No hay lienzo para dibujar. |
| 13 | Edición | En precargada, misma topología (coordenadas, base/altura, cargas, apoyos). En propia se añaden y quitan nudos y barras. Sigue habiendo exactamente un fijo y un móvil. |
| 14 | Longitud | **Calculada** a partir de coordenadas. El usuario no escribe \(L\). Sliders globales (base, altura) + tabla \((x, y)\). |
| 15 | Carga en Streamlit | Campos “horizontal (→ +)” y “vertical **hacia abajo** (+)”. 50 kN abajo → el paquete recibe \(F_y = -50\). La API de la librería usa ejes matemáticos (\(F_y > 0\) hacia arriba). |
| 16 | Pedagogía GUI | Figura con color y valores, tablas, residuos y el **sistema completo** ΣFx = 0 y ΣFy = 0 (`ecuaciones()`), con el cuerpo libre de cada nudo (`graficar_nudo`). La GUI no reescribe las fórmulas. |
| 17 | Gráficos | `Armadura2D.graficar()` en la librería; **matplotlib es dependencia de runtime** del paquete. |
| 18 | Solver | `numpy.linalg.solve`. |
| 19 | Python | ≥ 3.10. Imagen Docker: `python:3.12-slim`. |
| 20 | Notebook | Didáctico: teoría breve + presets + `resolver` + figura. Extra `[dev]` incluye `jupyter` e `ipykernel`. |
| 21 | Licencia | MIT |
| 22 | Autor | Andrés David Pérez Criollo — adperezc@udistrital.edu.co |
| 23 | Git | Individual, rama `main` |
| 24 | GitHub / Pages | El usuario crea el repo y publica Pages. Pegar URL cuando exista. |
| 25 | Docker Hub | Usuario `andresperez3`. Imagen: `andresperez3/armadura-2d-andresdperezc:0.1.0`. El usuario hace `docker push`. |
| 26 | EC2 | **No.** |
| 27 | matplotlib | Dentro del paquete. Backend `Agg` en tests, scripts y Docker. |
| 28 | Streamlit | Fuera del paquete: extra `[gui]` + imagen Docker. Escucha `0.0.0.0:8501`. |
| 29 | Patrones de diseño | **No.** Clase plana + dataclasses de resultado. |
| 30 | API HTTP | **No.** |
| 31 | PPT | No forma parte de estas fases. |
| 32 | Publicación | TestPyPI, PyPI, Docker Hub, GitHub y Pages las sube el **usuario**. |
| 33 | Versión | `0.1.0` igual en `pyproject.toml` y `__init__.py`. |
| 34 | Rangos GUI (fase 6; ajustables) | Base ≈ 1–20 m; altura ≈ 0,5–10 m; carga ≈ 0–200 kN. Defaults según el preset (sección 5). |
| 35 | Colores T/C | Distintos y legibles (p. ej. tensión vs compresión). Detalle en la fase 4. |

---

## 4. Mecánica a implementar

### 4.1 Modelo ideal (didáctico)

Armadura 2D de **mecánica vectorial** (Hibbler / Beer & Johnston, método de nudos en forma matricial):

- Barras rectas unidas por **pasadores**; cada barra es un **elemento de dos fuerzas** (solo axial).
- Cargas **concentradas en nudos**. No hay peso propio ni carga a mitad de barra en 0.1.0.
- Apoyo **fijo (pin):** dos reacciones \(R_x, R_y\). Apoyo **móvil (rodillo)** sobre superficie horizontal: una reacción \(R_y\). **No hay momento de empotramiento.**
- En cada nudo las fuerzas son concurrentes → \(\sum M\) del nudo es idénticamente 0 (salvo ruido numérico). El \(\sum M = 0\) útil es el del **sólido completo**.

Isostática:

\[
m + r = 2j
\]

\(m\) = barras, \(r\) = componentes de reacción (3 si hay un fijo y un móvil), \(j\) = nudos.

- \(m + r > 2j\): **hiperestática** → `ValueError` (hace falta deformación / \(E,A\); no es este paquete).
- \(m + r < 2j\): **hipostática** / mecanismo → `ValueError`.
- \(m + r = 2j\) pero \(A\) singular: geometría degenerada o reacciones mal colocadas → `ValueError`.

### 4.2 Geometría de una barra \(i \rightarrow j\)

\[
L = \sqrt{(x_j - x_i)^2 + (y_j - y_i)^2}
\]

\[
\cos\theta = \frac{x_j - x_i}{L}, \qquad \sin\theta = \frac{y_j - y_i}{L}
\]

Longitud 0 (nudos coincidentes) → `ValueError`.

### 4.3 Equilibrio por nudo y sistema \(A x = b\)

Convenio: \(N > 0\) es **tensión**. La barra tira de cada nudo hacia el otro extremo. Fuerza de la barra \(k\) (une \(i\) y \(j\)) **sobre el nudo \(i\)**:

\[
\vec{F}_{k \to i} = N_k \, \hat{u}_{ij}, \qquad \hat{u}_{ij} = \frac{(x_j - x_i,\, y_j - y_i)}{L}
\]

Sobre el nudo \(j\): \(N_k \, \hat{u}_{ji} = - N_k \, \hat{u}_{ij}\).

En cada nudo \(i\):

\[
\sum_k N_k \hat{u}_{i,\text{otro}} + \vec{R}_i + \vec{F}_i^{\mathrm{ext}} = \vec{0}
\]

Dos ecuaciones por nudo (\(\sum F_x\), \(\sum F_y\)). Incógnitas \(x\): todas las \(N_k\) y las componentes de reacción existentes.

Orden sugerido de \(x\): barras en el orden en que se agregaron, luego reacciones por nudo id creciente (fijo: \(R_x, R_y\); móvil: \(R_y\)).

Pasar las cargas al lado derecho:

\[
A x = - F^{\mathrm{ext}}
\]

(en los GDL de reacción, las columnas de \(A\) son 1.0 en \(R_x\) o \(R_y\) de ese nudo). Resolver con `numpy.linalg.solve`. No usar `lstsq` como camino feliz: si es singular, debe fallar con mensaje claro.

### 4.4 Verificación de equilibrio

Tras resolver, `verificar_equilibrio()` comprueba residuos ≈ 0 (tolerancia relativa al tamaño de las cargas, p. ej. `1e-8` absoluto o relativo documentado en tests):

1. **Global:** \(\sum F_x\), \(\sum F_y\) y \(\sum M_z\) de **cargas externas + reacciones** (sin internas; las internas se anulan). Momento respecto del origen:

   \[
   M_z = \sum_i (x_i F_{iy} - y_i F_{ix})
   \]

   incluyendo reacciones en sus nudos. Debe ser ≈ 0.

2. **Por nudo:** residual de \(\sum F_x\) y \(\sum F_y\) incluyendo internas + reacción + carga.

La GUI muestra estos residuos. No hace falta imprimir \(A\).

### 4.5 Lectura del signo

| \(N\) | `tipo` | Significado |
|---|---|---|
| \(N > \varepsilon\) | `tension` | La barra se estira |
| \(N < -\varepsilon\) | `compresion` | La barra se acorta |
| \(\lvert N \rvert \le \varepsilon\) | `nula` | Fuerza nula (didáctico) |

En Pratt, con gravedad en el centro del tablero, las **diagonales tienden a tracción**. En Howe, las **diagonales tienden a compresión**. Usar eso en tests de signo (no hace falta memorizar todos los kN).

### 4.6 Lo que no es este modelo

No es un pórtico: las barras **no** transmiten momento. No es análisis matricial de rigideces (no hay \(E\), \(A\), desplazamientos). El diámetro **no** entra en \(A x = b\).

---

## 5. Presets (fábricas de la librería y selector de la GUI)

Nombres en el selector: **Triángulo · Warren · Pratt · Howe**.

Todos isostáticos, con un fijo y un móvil. Carga por defecto **50 kN hacia abajo** (en la librería \(F_y = -50\)).

Sliders de base/altura **escalan** respecto de la geometría por defecto (factor \(x\) = base/base₀, factor \(y\) = altura/altura₀), anclados en el origen. Después se pueden editar coordenadas nudo a nudo.

### 5.1 Triángulo (caso de libro — tests numéricos)

3 nudos, 3 barras. \(m + r = 3 + 3 = 6 = 2\cdot 3\).

Base₀ = **4 m**, altura₀ = **3 m**. Carga en la **cúspide**, no en la base.

| Nudo | \(x\) (m) | \(y\) (m) | Apoyo / carga por defecto |
|---|---|---|---|
| 0 | 0 | 0 | **fijo** |
| 1 | 4 | 0 | **móvil** (\(R_y\)) |
| 2 | 2 | 3 | \(F_y = -50\,\mathrm{kN}\) |

Barras: B1 `0-1`, B2 `0-2`, B3 `1-2`.

Valores de libro (pytest.approx):

| Magnitud | Valor |
|---|---|
| \(R_{0x}\) | \(0\) |
| \(R_{0y}\) | \(25\,\mathrm{kN}\) |
| \(R_{1y}\) | \(25\,\mathrm{kN}\) |
| B1 (base) | \(+50/3 \approx +16.667\,\mathrm{kN}\) **tensión** |
| B2 y B3 | \(-(25/3)\sqrt{13} \approx -30.046\,\mathrm{kN}\) **compresión** |
| \(L_{\mathrm{B1}}\) | \(4\,\mathrm{m}\) |
| \(L_{\mathrm{B2}} = L_{\mathrm{B3}}\) | \(\sqrt{13}\,\mathrm{m}\) |

Este es el “−13.6 eV” del proyecto.

### 5.2 Warren (2 paneles, sin verticales)

5 nudos, 7 barras. \(7 + 3 = 10 = 2\cdot 5\).

Base₀ = **4 m**, altura₀ = **2 m**. Carga en el **nudo central inferior**.

| Nudo | \(x\) | \(y\) | Rol |
|---|---|---|---|
| 0 | 0 | 0 | fijo |
| 1 | 2 | 0 | \(F_y = -50\,\mathrm{kN}\) |
| 2 | 4 | 0 | móvil |
| 3 | 1 | 2 | — |
| 4 | 3 | 2 | — |

Barras (ids sugeridos B1…B7): `0-1`, `1-2`, `3-4`, `0-3`, `2-4`, `3-1`, `1-4`.

```text
      3---------4
     / \       / \
    /   \     /   \
   0-----1-----2
```

### 5.3 Pratt (2 paneles)

6 nudos, 9 barras. \(9 + 3 = 12 = 2\cdot 6\).

Misma luz 4 m × altura 2 m. Carga 50 kN abajo en el nudo 1. **Diagonales hacia el centro** (en gravedad suelen ir a **tracción**).

| Nudo | \(x\) | \(y\) | Rol |
|---|---|---|---|
| 0 | 0 | 0 | fijo |
| 1 | 2 | 0 | \(F_y = -50\,\mathrm{kN}\) |
| 2 | 4 | 0 | móvil |
| 3 | 0 | 2 | — |
| 4 | 2 | 2 | — |
| 5 | 4 | 2 | — |

Cuerdas: `0-1`, `1-2`, `3-4`, `4-5`.  
Verticales: `0-3`, `1-4`, `2-5`.  
Diagonales: `3-1`, `5-1`.

```text
  3---------4---------5
  | \       |       / |
  |  \      |      /  |
  0---------1---------2
```

### 5.4 Howe (2 paneles)

Mismos 6 nudos, mismas cuerdas y verticales que Pratt. **Diagonales hacia los apoyos** (en gravedad suelen ir a **compresión**): `4-0`, `4-2`.

```text
  3---------4---------5
  |       / | \       |
  |      /  |  \      |
  0---------1---------2
```

### 5.5 Edición de apoyos y cargas (sin cambiar topología)

- Siempre debe quedar **exactamente un fijo y un móvil** entre nudos existentes ( \(r = 3\) ). Dos fijos → hiperestática. Cero móviles y un solo apoyo incompleto → hipostática. Mensajes en español.
- Cualquier nudo puede tener \(F_x, F_y\) (0 por defecto salvo el nudo cargado del preset).
- Mover nudos no cambia las barras que los unen. Si \(L \to 0\) o \(A\) sale singular → `ValueError`.

---

## 6. Diseño POO (plano)

Archivo principal: `src/armadura_2d_andresdperezc/core.py`.

Si el archivo crece, se puede partir en `modelo.py` / `equilibrio.py` / `graficos.py` **sin** cambiar lo que exporta `__init__.py`.

### 6.1 Piezas

| Pieza | Rol |
|---|---|
| `Armadura2D` | Estado encapsulado + operaciones |
| Dataclasses congelados | Resultados: `FuerzaBarra`, `Reaccion`, `ChequeoEquilibrio`, `ResultadoArmadura` |
| Validación | `ValueError` en el borde, mensajes en español |
| Fachada | `__init__.py` reexporta clases + `__version__` |
| Presets | `classmethod` en `Armadura2D` (no un patrón Factory de libro) |
| Adaptador GUI | `streamlit_app.py` solo llama la API |

### 6.2 API pública (borrador; nombres estables)

```python
from armadura_2d_andresdperezc import Armadura2D

a = Armadura2D.preset_triangulo()   # también preset_warren, preset_pratt, preset_howe
a.agregar_nodo(0, 0.0, 0.0)        # construcción libre en la librería (tests / pip)
a.agregar_barra("B1", 0, 1)
a.agregar_apoyo(0, "fijo")         # "fijo" | "movil"
a.agregar_carga(2, fx=0.0, fy=-50.0)

L = a.longitud("B1")
theta = a.angulo("B1")             # radianes; documentar. Grados solo si se etiqueta en GUI.

r = a.resolver()                   # ResultadoArmadura
eq = a.verificar_equilibrio(r)
fig = a.graficar(r)                # matplotlib.figure.Figure

# Lectura para la GUI (sin tocar _nodos / _barras):
a.snapshot_nodos()                 # [(id, x, y), ...]
a.snapshot_barras()                # [(id, i, j), ...]
a.snapshot_apoyos()                # [(nudo, "fijo"|"movil"), ...]
a.snapshot_cargas()                # [(nudo, fx, fy), ...]  fy ya en ejes (abajo = negativo)
a.definir_apoyos(fijo, movil)
a.definir_cargas([(nudo, fx, fy), ...])
a.reemplazar_coordenadas({id: (x, y), ...})  # todas a la vez (evita L=0 intermedio)
```

Construcción libre (`agregar_*`) **sí va en la librería** (quien instala por pip puede armar cualquier isostática). La **GUI 0.1.0 no expone** un diseñador vacío: solo presets editables. El futuro “dibujar cualquiera” reutilizará `agregar_*`.

`__init__.py` exporta al menos:

```text
Armadura2D, FuerzaBarra, Reaccion, ChequeoEquilibrio, ResultadoArmadura, __version__
```

Campos mínimos sugeridos:

- `FuerzaBarra`: id, nudo_i, nudo_j, fuerza (kN), tipo (`tension`/`compresion`/`nula`), longitud (m), angulo (rad), coseno, seno.
- `Reaccion`: nudo, rx (kN; 0 si el GDL no existe), ry (kN).
- `ChequeoEquilibrio`: sum_fx, sum_fy, sum_mz, ok (bool), residuos por nudo si es práctico.
- `ResultadoArmadura`: fuerzas (lista), reacciones (lista), equilibrio, y opcionalmente el vector \(x\) **no** se pinta en Streamlit.

Estado interno: nudos, barras, apoyos y cargas como estructuras privadas (`self._nodos`, etc.). Coordenadas y cargas se editan con `reemplazar_coordenadas`, `definir_cargas` y `definir_apoyos`. Streamlit no lee ni escribe atributos privados.

### 6.3 `graficar(resultado)`

Devuelve `matplotlib.figure.Figure`, **no** abre ventanas (`plt.show()` prohibido en la librería).

Debe mostrar: nudos etiquetados, barras coloreadas por T/C, apoyos distinguibles (fijo vs móvil), flechas de cargas y de reacciones, leyenda de signo. Grosor de barra puede ser fijo (no hay diámetro). Funciona en script, notebook y `st.pyplot(fig)`.

Tests: `isinstance(fig, matplotlib.figure.Figure)` con backend `Agg`; `plt.close("all")` en fixture.

---

## 7. Tests (`tests/test_core.py`)

Solo importan la librería. No testean Streamlit.

Cubrir:

1. Caso de libro del **triángulo** (tabla 5.1).
2. Longitudes del triángulo.
3. `verificar_equilibrio` con residuos ≈ 0 en los cuatro presets por defecto.
4. Pratt: diagonales `3-1` y `5-1` a **tracción** con la carga por defecto.
5. Howe: diagonales `4-0` y `4-2` a **compresión** con la carga por defecto.
6. Determinación: \(m + r = 2j\) en cada preset.
7. `ValueError`: nudo repetido, barra a nudo inexistente, \(L=0\), barra duplicada, hiperestática (p. ej. segundo fijo o barra extra), hipostática (quitar un apoyo), tipo de apoyo ilegal, carga en nudo inexistente.
8. `graficar` devuelve `Figure`.
9. Presets existen y se pueden `resolver()` sin GUI.
10. `snapshot_*`, `reemplazar_coordenadas` (todas las coords o `ValueError`) y `definir_cargas`.

No hace falta Selenium/Playwright. 37 tests en verde al cerrar la fase 6.

---

## 8. GUI Streamlit (`streamlit_app.py`)

Fuera de `src/`. Única importación de dominio: el paquete. Extra `[gui]`. **Hecha** (fase 6).

Flujo (como quedó tras el ajuste de páginas):

1. Barra superior: **Calculadora** y **Ecuaciones** (`st.navigation`, `position="top"`).
2. En Calculadora, `st.radio`: Precargada / Propia. En precargada, otro radio: Triángulo / Warren / Pratt / Howe. Al cambiar de preset se recargan geometría, apoyos y cargas por defecto.
3. Los dos modos usan la misma disposición: datos a la izquierda y plano a la derecha (`plano_ui.figura_plano`). En propia el plano crea nudos, barras, apoyos y cargas. En precargada el plano solo se mira: la topología del preset no cambia.
4. Sliders **base** (1–20 m) y **altura** (0,5–10 m), tabla de nudos, apoyos y cargas siguen en la columna izquierda. `data_editor` puede devolver DataFrame; se normaliza a filas. La GUI convierte “abajo +” a \(F_y\) negativa **antes** de `definir_cargas`.
5. Figura `graficar(resultado)` centrada y más angosta, **antes** del botón. Si la armadura todavía no cierra, ahí va el error.
6. Botón **Calcular**. Recién entonces: residuos \(\sum F_x\), \(\sum F_y\), \(\sum M\), tablas de \(N\) / T/C / reacciones y longitudes. Si los datos cambian, esos resultados se ocultan hasta pulsar de nuevo.
7. La página Ecuaciones muestra `ecuaciones()` y `graficar_nudo()` del último cálculo guardado en `st.session_state`.
8. `ImportError` amigable: `pip install -e ".[gui]"`.
9. `os.environ.setdefault("MPLBACKEND", "Agg")`.

No recalcular senos ni armar \(A\) en este archivo. Acceso al modelo solo por `snapshot_*`, `reemplazar_coordenadas`, `definir_apoyos`, `definir_cargas`.

---

## 9. Empaquetado y carpetas

Seguir `ARQUITECTURA_REPLICABLE.md`. Estructura objetivo:

```text
segundo_parcial/
├── CONTEXTO_DESARROLLO.md          ← local; NO va a GitHub
├── ARQUITECTURA_REPLICABLE.md      ← local; NO va a GitHub
├── pyproject.toml
├── README.md
├── LICENSE                         ← MIT
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example                    ← sin secretos; .env no se versiona
├── streamlit_app.py                ← GUI en la raíz (Docker / Streamlit)
├── plano_ui.py
├── examples/
│   ├── ejemplo_consola.py
│   └── notebook_didactico.ipynb
├── src/
│   └── armadura_2d_andresdperezc/
│       ├── __init__.py
│       └── core.py
├── tests/
│   ├── test_core.py
│   └── test_plano_ui.py
├── docs/                           ← Sphinx + guías PUBLICAR_PYPI / DESPLIEGUE
└── .github/workflows/
    ├── pages.yml
    └── tests.yml
```

`[tool.setuptools.packages.find] where = ["src"]`.

`pyproject.toml` (resumen):

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "armadura-2d-andresdperezc"
version = "0.1.0"
description = "Analizador de armaduras 2D isostáticas: fuerzas internas, reacciones, tensión/compresión y gráficos."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
license-files = ["LICENSE"]
authors = [
    { name = "Andrés David Pérez Criollo", email = "adperezc@udistrital.edu.co" },
]
keywords = ["armadura", "estática", "mecánica vectorial", "educación"]
dependencies = [
    "numpy>=1.22",
    "matplotlib>=3.5",
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

Instalación de desarrollo (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[gui,dev,docs]"
```

`.env` / `.env.example` de este repo están vacíos y **no** forman parte de la arquitectura (tokens PyPI van en `~/.pypirc`, nunca al git). En fase 1: `.gitignore` según la guía; no versionar secretos.

---

## 10. Docker (sin EC2)

Igual que la plantilla de `ARQUITECTURA_REPLICABLE.md`:

- Base `python:3.12-slim`
- `MPLBACKEND=Agg`, Streamlit headless, `0.0.0.0:8501`
- Instala `".[gui]"` (Streamlit y Plotly)
- Copia `streamlit_app.py` y `plano_ui.py` (la página). No copiar tests, docs, notebook ni `.venv`
- Fuentes `fonts-dejavu-core`
- `HEALTHCHECK` a `/_stcore/health`

```bash
docker build -t andresperez3/armadura-2d-andresdperezc:0.1.0 .
docker run --rm -p 8501:8501 andresperez3/armadura-2d-andresdperezc:0.1.0
```

http://localhost:8501

---

## 11. Sphinx, README, ejemplos

Sphinx: autodoc + napoleon + Furo + rinohtype (PDF en Windows **sin LaTeX**). Páginas: `index`, `instalacion`, `uso`, `api`, `gui`, `limitaciones`, `publicar`. Docstrings NumPy/Google en la API pública. **Sin** menciones a EC2.

README (fase 10): propósito, pip vs import, GUI no va en el paquete, versión, Python ≥ 3.10, MIT, tabla Windows/Linux/macOS **sin fila EC2**, extras, uso básico, tabla de métodos, unidades, presets, tests, Streamlit, Docker, Sphinx, enlace a `PUBLICAR_PYPI.md`, limitaciones, futuro breve, autor.

`ejemplo_consola.py`: al menos el triángulo (números de libro) y un preset puente; imprime T/C y reacciones; opcionalmente guarda un PNG.

Notebook: no usa Streamlit; instala el paquete; teoría mínima de armaduras; celdas con presets y figuras.

---

## 12. Limitaciones 0.1.0 (documentar en README + Sphinx)

- Solo 2D.
- Solo isostáticas. Hiperestática / mecanismo / \(A\) singular → `ValueError`.
- Cargas solo en nudos. Sin peso propio ni carga distribuida en la barra.
- Apoyos: un fijo + un móvil vertical. Sin empotramiento, sin rodillo inclinado en 0.1.0.
- Sin pórticos, ni momento flector en barras, ni 3D.
- Sin diámetro, esfuerzo \(\sigma = N/A\), pandeo de Euler, ni códigos NSR/AISC.
- La GUI no dibuja armaduras arbitrarias: solo los cuatro presets, editando números y la misma topología.
- Unidades fijas kN y m.
- Si se expande, **hay que validar de nuevo** (tests + nota en docs).

---

## 13. Futuro (no implementar en las fases 1–10)

Dejarlo escrito en README y `docs/limitaciones.rst` para no perderlo:

1. **Diseñar / dibujar cualquier armadura** en la aplicación (lienzo o tablas de topología: añadir/quitar nudos y barras) y correr el mismo `resolver()`. La librería ya tendrá `agregar_*`; faltará la UI.
2. **Esfuerzo y más variables:** diámetro (o sección) por barra, \(\sigma = N/A\), quizá material, pandeo u otras magnitudes de resistencia de materiales. Eso **no** cambia \(A x = b\) de la estática; es postproceso o un modelo más rico.
3. **Pesos \(W\) y cuerdas** (pedido el 18 nov 2026). Documentado para hacerlo después. **No implementado:** ni en `core.py`, ni en la GUI, ni en Docker.

   El usuario quiere, al crear la armadura, inputs nuevos además de las cargas: pesos \(W\) (no son la carga nodal de hoy) y cuerdas, que solo trabajan a tensión. El equilibrio debe seguir siendo \(A x = b\). Los resultados muestran lo configurado. Entra en la librería y, al hacerlo, se reconstruye la imagen Docker (`docker build`): la imagen copia `src/` y `streamlit_app.py`; no hay un cálculo aparte en el `Dockerfile`.

   Camino que cabe en el solver actual:

   - **Peso en un nudo:** \(W\) hacia abajo se suma al lado de las cargas al armar \(b\), y en resultados se lista aparte de las cargas.
   - **Peso de una barra:** se reparte en partes iguales entre sus dos nudos. Así la barra sigue siendo de dos fuerzas. Un peso a mitad de la barra, o repartido a lo largo, queda fuera: esa barra deja de ser de dos fuerzas.
   - **Cuerda:** sustituye a una barra o la armadura propia sigue cumpliendo \(m + r = 2j\). Agregarla encima de un preset que ya es isostático lo vuelve hiperestático y `resolver()` debe seguir rechazándolo.

   Queda por cerrar con el usuario, antes de codificar: si una cuerda sale a compresión, el programa avisa y se detiene, o la quita y vuelve a resolver. Lo segundo ya no es una sola llamada a `numpy.linalg.solve`. Con \(W = 0\) y sin cuerdas, el triángulo de libro y los signos de Pratt y Howe no pueden cambiar.

No son deuda de la 0.1.0. No abrir issues de código ahora. El punto 3 tampoco se codifica hasta que el usuario lo pida en una sesión.

---

## 14. Fases de desarrollo (una por sesión)

Trabajar **una fase por vez**. Al cerrar: actualizar esta tabla.

| Fase | Objetivo | Estado | Qué entra | Criterio de listo |
|---|---|---|---|---|
| 0 | Contexto | **Hecha** | Este archivo | Decisiones, mecánica, presets, API, limitaciones, futuro y fases escritos |
| 1 | Esqueleto instalable | **Hecha** | `pyproject.toml`, `LICENSE`, `.gitignore`, `src/.../__init__.py`, `core.py` mínimo, README corto | `pip install -e .` e `import armadura_2d_andresdperezc` |
| 2 | Dominio + tests triángulo | **Hecha** | Construcción, \(A x = b\), T/C, reacciones, `verificar_equilibrio`, validaciones, tests de libro | `pytest -v` verde con la tabla 5.1 |
| 3 | Presets Warren / Pratt / Howe | **Hecha** | `preset_*`, tests de isostática, residuos ≈ 0, signos Pratt vs Howe | Los cuatro presets `resolver()` sin GUI |
| 4 | Gráficos | **Hecha** | `graficar()` + test de `Figure` | Figura sin Streamlit |
| 5 | Ejemplos | **Hecha** | `ejemplo_consola.py` + `examples/notebook_didactico.ipynb` | Uso sin GUI |
| 6 | Streamlit | **Hecha** | `streamlit_app.py` + snapshots en `core.py` | `streamlit run streamlit_app.py`; triángulo de libro y Pratt/Howe con T/C correctos |
| 7 | Sphinx + PDF | **Hecha** | `docs/`, autodoc, `.github/workflows/pages.yml` | HTML Furo + PDF rinohtype; limitaciones y futuro |
| 8 | Docker | **Hecha** | `Dockerfile`, `.dockerignore` | `docker build` + `run -p 8501:8501`; HEALTHCHECK ok; triángulo de libro |
| 9 | Guías | **Hecha** | `PUBLICAR_PYPI.md`, `DESPLIEGUE.md`, `.github/workflows/tests.yml` | `twine check` PASSED; el usuario puede subir sin adivinar |
| 10 | README completo | **Hecha** | Cara pública del repo y de PyPI | Alguien ajeno instala y usa; `twine check` PASSED |
| 11 | Lectura, armadura propia y rodillo en pared | **Hecha** | GUI en una sola página; modo Propia; `movil_pared`; `ecuaciones()` y `graficar_nudo()`; test del problema 6.1 | `pytest -v` verde y la página muestra figura, resultados y el sistema |
| 12 | Calculadora en dos páginas | **Hecha** | Datos a la izquierda y plano a la derecha también en precargada; figura centrada antes de **Calcular**; ecuaciones en otra página | `pytest -v` verde; en :8501 el triángulo de libro sale tras Calcular y las ecuaciones no comparten esa página |

**Fuera de fases (usuario):** crear GitHub, Pages, `docker push`, TestPyPI, PyPI. Pegar URLs cuando existan.

**Dependencias:** 1 → 2 → 3 → 4. 5 y 6 en paralelo tras 4 (6 podría arrancar tras 3 con figura placeholder, pero el criterio pide `graficar`). 7 tras docstrings (2–4). 8 necesita 6. 9 tras 8. 10 al final.

### Cómo verificar la fase 1

En este equipo el launcher es `py` (no `python` de la Store):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -c "from armadura_2d_andresdperezc import Armadura2D, __version__; print(__version__, Armadura2D())"
```

Debe imprimir `0.1.0 Armadura2D(nombre='armadura')`. En fase 1, `agregar_*` / `resolver` aún no existían.

### Cómo verificar la fase 2

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -v
```

21 tests en verde (fase 2): reacciones 25 kN, B1 \(=+50/3\) kN (tensión), B2 y B3 \(=-(25/3)\sqrt{13}\) kN (compresión), residuos ≈ 0, `ValueError` en casos ilegales.

### Cómo verificar la fase 3

```powershell
.\.venv\Scripts\Activate.ps1
pytest -v
```

28 tests de solver/presets en verde (fase 3). Pratt: diagonales a tracción; Howe: a compresión.

### Cómo verificar la fase 4

```powershell
.\.venv\Scripts\Activate.ps1
pytest -v
```

35 tests en verde. `graficar()` devuelve `matplotlib.figure.Figure` (backend Agg) en los cuatro presets.

### Cómo verificar la fase 5

```powershell
.\.venv\Scripts\Activate.ps1
python examples/ejemplo_consola.py
```

Imprime el triángulo de libro, Pratt y Howe (T/C y reacciones) y guarda PNG en `examples/` (gitignorados). El notebook `examples/notebook_didactico.ipynb` no usa Streamlit; kernel = `.venv`.

### Cómo verificar la fase 6

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[gui]"
pytest -v
streamlit run streamlit_app.py
```

37 tests en verde. En el navegador (http://127.0.0.1:8501):

- Triángulo 4×3 m, 50 kN en cúspide: B1 \(=+50/3\) kN (tensión), B2 y B3 \(=-(25/3)\sqrt{13}\) kN (compresión), Ry = 25 kN, equilibrio sí.
- Pratt: diagonales 3–1 y 5–1 a **tensión**.
- Howe: diagonales 4–0 y 4–2 a **compresión**.
- Cambiar radio recarga geometría; sliders cambian base/altura del preset.

### Cómo verificar la fase 7

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
sphinx-build -b rinoh docs docs/_build/rinoh
```

Abra `docs/_build/html/index.html`. El PDF queda en `docs/_build/rinoh/armadura-2d-andresdperezc.pdf`. Páginas: instalación, uso, API, GUI, limitaciones (futuro CAD/esfuerzo), publicar. Workflow: `.github/workflows/pages.yml` (el usuario activa Pages en GitHub). 37 tests siguen en verde.

### Cómo verificar la fase 8

```powershell
docker build -t andresperez3/armadura-2d-andresdperezc:0.1.0 .
docker run --rm -p 8501:8501 andresperez3/armadura-2d-andresdperezc:0.1.0
```

Abra http://localhost:8501. HEALTHCHECK: `http://127.0.0.1:8501/_stcore/health` responde `ok`. El triángulo de libro debe coincidir con la GUI local (B1 16.6667 kN tensión, B2/B3 −30.0463 kN). `docker push` lo hace el usuario.

### Cómo verificar la fase 9

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install build twine
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
python -m build
python -m twine check dist/*
```

`twine check` debe decir **PASSED** en el `.whl` y el `.tar.gz`. El wheel solo contiene `src/armadura_2d_andresdperezc/` (no `streamlit_app.py`). Guías: `PUBLICAR_PYPI.md` y `DESPLIEGUE.md` (Docker Hub + Pages). CI: `.github/workflows/tests.yml` (pytest en 3.10 y 3.12). Las subidas las hace el usuario; no hay tokens en el repo.

### Cómo verificar la fase 10

El `README.md` cubre propósito, pip vs import, GUI fuera del paquete, extras, uso, métodos, unidades, presets, tests, Streamlit, Docker, Sphinx, `PUBLICAR_PYPI.md`, limitaciones, futuro y autor. Tabla Windows/Linux/macOS **sin** fila de máquina en la nube. Tras editarlo:

```powershell
python -m build
python -m twine check dist/*
```

sigue en **PASSED**.

### Cómo verificar la fase 11

```powershell
.\.venv\Scripts\Activate.ps1
pytest -v
streamlit run streamlit_app.py
```

43 tests en verde, incluido el problema 6.1 de Beer (1500 lb, 2500 lb, …) y el rodillo en pared. En http://127.0.0.1:8501 la página va de la explicación a los datos, la figura, los resultados y el sistema de ecuaciones. Hay que **reiniciar** Streamlit si ya estaba abierto: el proceso no recarga solo `core.py`.

### Cómo verificar la fase 12

```powershell
.\.venv\Scripts\Activate.ps1
pytest -v
streamlit run streamlit_app.py
```

En http://127.0.0.1:8501 la barra superior tiene Calculadora y Ecuaciones. En Calculadora, precargada y propia muestran datos a la izquierda y plano a la derecha. La figura de la armadura queda centrada, antes del botón. Tras **Calcular**, el triángulo de libro sigue dando B1 \(=+50/3\) kN y Ry = 25 kN. Las ecuaciones no aparecen en esa página: están en Ecuaciones, y se vacían si los datos cambian.

---

## 15. Compatibilidad de sistemas

| Uso | Windows | Linux | macOS |
|---|---|---|---|
| `pip install` + NumPy + matplotlib | Sí | Sí | Sí |
| pytest y notebook | Sí | Sí | Sí |
| Streamlit en el navegador | Sí | Sí | Sí |
| Docker + Streamlit | Sí (Docker Desktop) | Sí | Sí |

**Sin fila EC2.** Tkinter no es requisito.

---

## 16. Checklist de replicación (ir marcando)

### Librería / PyPI

- [x] `src/armadura_2d_andresdperezc/` con `__init__.py` y `core.py`
- [x] `pyproject.toml` con `where = ["src"]`
- [x] Versión igual en toml y `__init__.py`
- [ ] Nombre PyPI libre el día de publicar
- [x] LICENSE MIT y README completo (cara de PyPI)
- [x] `python -m build` + `twine check` PASSED
- [x] Guía TestPyPI → PyPI

### POO / calidad

- [x] `Armadura2D` + dataclasses de resultado (API definida; solver en fase 2)
- [x] Validaciones `ValueError` (nudo, barra, apoyos, isostática, sistema singular)
- [x] Docstrings NumPy/Google en la API de fase 2
- [x] `pytest -v` en verde (triángulo de libro + Warren/Pratt/Howe + errores)
- [x] GUI no duplica lógica

### GUI / Docker

- [x] `streamlit_app.py` fuera de `src/`
- [x] Extra `[gui]`
- [x] Cuatro presets editables (misma topología)
- [x] Dockerfile `0.0.0.0:8501`, Agg, HEALTHCHECK
- [x] `.dockerignore`
- [x] **Ninguna** sección EC2 (`DESPLIEGUE.md` = Docker Hub + Pages)

### Docs / ejemplos

- [x] Sphinx + Furo + autodoc + rinoh
- [x] Pages workflow + CI pytest (`.github/workflows/pages.yml` y `tests.yml`)
- [x] Notebook y `ejemplo_consola.py`
- [x] Limitaciones, futuro (dibujar / esfuerzo) y compatibilidad SO (`docs/limitaciones.rst`)

---

## 17. Conversación resumida (para no perder el hilo)

1. Repo `segundo_parcial` vacío; receta en `ARQUITECTURA_REPLICABLE.md`; origen `entrega_libreria` (Bohr).
2. Tema: analizador de armaduras 2D según la diapositiva 15 del PPT y pedidos del usuario (presets editables, NumPy/matplotlib, fases, documentar futuro).
3. Cerrado: isostáticas 2D, \(A x = b\), T/C, Streamlit, Docker sin EC2, matplotlib en el paquete, diámetro **no** en 0.1.0.
4. GUI: solo catálogo de presets, misma topología, sliders base/altura + coordenadas; \(L\) calculada; carga “abajo +” en la GUI.
5. Catálogo: Triángulo (4×3 m, 50 kN en cúspide) + Warren + Pratt + Howe (puentes 4×2 m, 2 paneles, 50 kN en centro inferior).
6. Autor, correo y Docker Hub iguales a Bohr. pip `armadura-2d-andresdperezc`.
7. Futuro escrito: dibujar cualquier armadura; esfuerzo/diámetro. El 18 nov 2026 se añadió, solo en la documentación, pesos \(W\) y cuerdas (mismo \(A x = b\); no codificado).
8. Fase 0 = este archivo.
9. Fase 1 = esqueleto instalable (`pip install -e .`, import `Armadura2D`).
10. Fase 2 = `A x = b`, T/C, `preset_triangulo`, tests de libro.
11. Fase 3 = `preset_warren`, `preset_pratt`, `preset_howe`.
12. Fase 4 = `graficar()` → `Figure`.
13. Fase 5 = `ejemplo_consola.py` + notebook (sin Streamlit).
14. Fase 6 = `streamlit_app.py` (radio de presets, sliders, tablas, `st.pyplot`). La GUI solo usa API pública (`snapshot_*`, `reemplazar_coordenadas`, `definir_cargas`).
15. Fase 7 = Sphinx (Furo, autodoc, napoleon) + PDF rinohtype + `pages.yml`.
16. Fase 8 = `Dockerfile` + `.dockerignore` (imagen `andresperez3/armadura-2d-andresdperezc:0.1.0`, puerto 8501).
17. Fase 9 = `PUBLICAR_PYPI.md`, `DESPLIEGUE.md` (Docker Hub + Pages) y CI `tests.yml`. `twine check` PASSED.
18. Fase 10 = README completo (cara de PyPI). No hay más fases de código.

---

## 18. Pendiente del usuario (publicación)

- Crear el repositorio GitHub y pasar la URL.
- Activar Pages: *Settings → Pages → Source: GitHub Actions*.
- El día de publicar, confirmar que `armadura-2d-andresdperezc` sigue libre en PyPI.
- Subidas: TestPyPI, PyPI, Docker Hub (`docker push`), Pages.

Fase 11 (lectura de la GUI, armadura propia, rodillo en pared, sistema de ecuaciones) quedó hecha después del cierre 0–10. Las subidas las hace el usuario (`PUBLICAR_PYPI.md`, `DESPLIEGUE.md`).
