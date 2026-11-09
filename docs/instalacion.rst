Instalación
===========

Requisito: **Python 3.10 o superior**, en Windows, Linux o macOS.

Desde PyPI
----------

Cuando el paquete esté publicado::

   pip install armadura-2d-andresdperezc

Eso instala la **lógica (NumPy) y los gráficos matplotlib**. No instala
Streamlit.

Desarrollo (modo editable)
--------------------------

Desde la carpeta del proyecto::

   python -m venv .venv

En Windows (PowerShell)::

   .\.venv\Scripts\Activate.ps1
   python -m pip install -e ".[dev,docs]"

En Linux o macOS::

   source .venv/bin/activate
   python -m pip install -e ".[dev,docs]"

Si el comando ``python`` no está en el PATH (Windows), use el launcher ``py``: ``py -3.12 -m venv .venv``.

Extras opcionales:

- ``[gui]`` — Streamlit, para ``streamlit run streamlit_app.py``
- ``[dev]`` — pytest, build, twine, Jupyter
- ``[docs]`` — Sphinx, Furo, rinohtype

Nombre PyPI vs import
---------------------

Se instala con **guion** y se importa con **guion bajo**::

   pip install armadura-2d-andresdperezc
   from armadura_2d_andresdperezc import Armadura2D
