armadura-2d-andresdperezc
=========================

Librería didáctica en Python para **armaduras 2D isostáticas** (mecánica
vectorial): fuerzas internas, reacciones y clasificación tensión /
compresión.

Instalación::

   pip install armadura-2d-andresdperezc

Uso mínimo::

   from armadura_2d_andresdperezc import Armadura2D

   a = Armadura2D.preset_triangulo()
   r = a.resolver()
   print(r.equilibrio.ok)
   for barra in r.fuerzas:
       print(barra.id, barra.tipo, barra.fuerza)
   a.graficar(r)  # Figure de matplotlib; no abre ventana

La clase :class:`~armadura_2d_andresdperezc.Armadura2D` encapsula el
modelo :math:`A x = b` y los gráficos. La GUI de Streamlit **no** forma
parte del paquete: vive en ``streamlit_app.py`` y solo llama a esta API.

.. toctree::
   :maxdepth: 2
   :caption: Contenido

   instalacion
   uso
   api
   gui
   limitaciones
   publicar

Autor
-----

Andrés David Pérez Criollo — adperezc@udistrital.edu.co

Licencia MIT. Versión |release|.
