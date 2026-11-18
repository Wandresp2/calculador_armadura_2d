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

Abra http://localhost:8501. La página se lee de arriba hacia abajo:

1. Qué hace el programa.
2. Datos: armadura **precargada** (Triángulo, Warren, Pratt, Howe, con
   base, altura, nudos, apoyos y cargas) o **propia** (tablas para
   agregar y quitar nudos y barras). En la propia, el plano de al lado
   también crea elementos: nudo en la cuadrícula de 0,5 m (crece 4 m
   alrededor de los nudos), barra entre dos nudos, apoyo o carga sobre
   un nudo. Ese plano está en ``plano_ui.py`` y no entra al paquete de
   PyPI.
3. Figura con color, fuerza en cada barra, cargas y reacciones.
4. Tablas de resultados.
5. Sistema completo de ecuaciones y cuerpo libre de cada nudo
   (``ecuaciones()`` y ``graficar_nudo()``).

El apoyo móvil puede ser de **piso** (solo Ry) o de **pared vertical**
(solo Rx). La GUI convierte “vertical hacia abajo (+)” a
:math:`F_y` negativa antes de llamar a la librería. No arma la matriz
:math:`A` ni duplica fórmulas.

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

El ``Dockerfile`` hace escuchar a Streamlit en ``0.0.0.0:8501``.
GitHub Pages hospeda **solo** este HTML estático, no la GUI.
