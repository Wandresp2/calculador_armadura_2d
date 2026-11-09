GUI (Streamlit)
===============

La interfaz gráfica **no se publica en PyPI**. El paquete no importa
Streamlit ni Tkinter. ``streamlit_app.py`` solo consume
:class:`~armadura_2d_andresdperezc.Armadura2D`.

Streamlit (local)
-----------------

::

   python -m pip install -e ".[gui]"
   streamlit run streamlit_app.py

Abra http://localhost:8501. Controles:

- radio **Triángulo / Warren / Pratt / Howe** (misma topología; no se
  pueden añadir ni quitar barras)
- sliders de **base** (1–20 m) y **altura** (0,5–10 m)
- tablas de nudos, apoyos y cargas
- longitudes :math:`L` calculadas (solo lectura)
- figura tensión / compresión, residuos :math:`\sum F_x`,
  :math:`\sum F_y`, :math:`\sum M` y tablas de :math:`N` y reacciones

La GUI convierte “vertical hacia abajo (+)” a :math:`F_y` negativa
antes de llamar a la librería. No arma la matriz :math:`A` ni duplica
fórmulas.

Docker
------

La imagen (cuando esté en Docker Hub, usuario ``andresperez3``) expone
el mismo Streamlit en el puerto **8501**. Cualquier sistema operativo
abre el navegador; no hace falta Tkinter.

Construir y publicar (lo hace el autor del paquete)::

   docker build -t andresperez3/armadura-2d-andresdperezc:0.1.0 .
   docker push andresperez3/armadura-2d-andresdperezc:0.1.0

Usar en cualquier PC::

   docker run --rm -p 8501:8501 andresperez3/armadura-2d-andresdperezc:0.1.0

Luego http://localhost:8501.

El ``Dockerfile`` (fase 8) hará escuchar a Streamlit en ``0.0.0.0:8501``.
GitHub Pages hospeda **solo** este HTML estático, no la GUI.
