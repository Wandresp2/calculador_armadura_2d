# Despliegue: Docker Hub y GitHub Pages

Las subidas las hace el autor. Esta guía asume la imagen
`andresperez3/armadura-2d-andresdperezc:0.1.0` y Streamlit en el puerto **8501**.

La GUI **no** va en el wheel de PyPI. Quien no quiera instalar Python usa
Docker. Quien quiera la documentación HTML usa GitHub Pages (estático; no
hospeda Streamlit).

## 1. Docker Hub

Usuario: `andresperez3`.

```bash
docker login
docker build -t andresperez3/armadura-2d-andresdperezc:0.1.0 .
docker push andresperez3/armadura-2d-andresdperezc:0.1.0
```

En cualquier PC (Windows, Linux o macOS) con Docker Desktop o motor Docker:

```bash
docker pull andresperez3/armadura-2d-andresdperezc:0.1.0
docker run --rm -p 8501:8501 andresperez3/armadura-2d-andresdperezc:0.1.0
```

Abra http://localhost:8501. No hace falta Tkinter.

Comprobar salud del contenedor:

```text
http://127.0.0.1:8501/_stcore/health
```

debe responder `ok`. El `Dockerfile` ya pone Streamlit en `0.0.0.0:8501`,
backend matplotlib `Agg` y un `HEALTHCHECK` a esa ruta.

Si cambia el código, reconstruya la imagen. Si ya empujó el tag `0.1.0`,
use un tag nuevo (`0.1.1`) igual que la versión del paquete.

La imagen base es `python:3.12-slim` (`linux/amd64`). En Mac Apple Silicon,
si Docker no emula solo:

```bash
docker run --rm --platform linux/amd64 -p 8501:8501 andresperez3/armadura-2d-andresdperezc:0.1.0
```

### Problemas habituales

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El navegador no carga | El mapeo `-p 8501:8501` falta o el puerto está ocupado | Cierre otro Streamlit local; vuelva a `docker run` |
| Tiempo de espera | Docker Desktop apagado o la imagen no arrancó | `docker logs` del contenedor |
| Carga en el contenedor pero no en el PC | Streamlit escucharía en `localhost` | No cambie el `CMD`; debe ser `0.0.0.0` |

Correr sin Docker (desarrollo):

```powershell
python -m pip install -e ".[gui]"
streamlit run streamlit_app.py
```

## 2. GitHub Pages (documentación Sphinx)

El flujo de trabajo ya está en `.github/workflows/pages.yml`. Lo activa el autor:

1. Cree el repositorio en GitHub y suba el proyecto (`main`).
2. *Settings → Pages → Source: **GitHub Actions***.
3. Cada push a `main` instala `.[docs]`, construye Sphinx y publica el HTML.

URL típica: `https://<usuario>.github.io/<repositorio>/`.

**A mano** (si no usa Actions): genere HTML localmente y súbalo a la rama
`gh-pages`. Incluya un archivo vacío `.nojekyll` para que GitHub no ignore
`_static`:

```powershell
python -m pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
```

PDF local (sin LaTeX):

```powershell
sphinx-build -b rinoh docs docs/_build/rinoh
```

El PDF queda en `docs/_build/rinoh/armadura-2d-andresdperezc.pdf`.

Los tests automáticos están en `.github/workflows/tests.yml` (`pytest` en
Python 3.10 y 3.12). No publican nada.

## 3. Orden recomendado el día de la entrega

1. `pytest -v`
2. TestPyPI → PyPI (`PUBLICAR_PYPI.md`)
3. `docker push` a `andresperez3`
4. GitHub + Pages (*Settings → Pages → GitHub Actions*)
