Limitaciones y futuro
=====================

Alcance de la 0.1.0
-------------------

- Solo **2D**.
- Solo **isostáticas**. Hiperestática, mecanismo o :math:`A` singular
  → ``ValueError``.
- Cargas **solo en nudos**. Sin peso propio ni carga distribuida en la
  barra.
- Apoyos: un **fijo** (Rx, Ry) y un **móvil**. El móvil está en un
  piso (solo Ry) o en una pared vertical (solo Rx). Sin empotramiento
  ni rodillo inclinado.
- Sin pórticos, ni momento flector en barras, ni 3D.
- Sin diámetro, esfuerzo :math:`\sigma = N/A`, pandeo de Euler ni
  códigos NSR/AISC.
- La armadura propia se arma con tablas. No hay lienzo para dibujarla.
- Unidades fijas **kN** y **m**.

Si el desarrollo se **expande**, hay que **volver a validarlo** (tests +
esta página).

Futuro (no es deuda de la 0.1.0)
--------------------------------

1. **Dibujar la armadura en un lienzo** (la propia ya se arma con
   tablas y usa el mismo ``resolver()``).
2. **Esfuerzo y más variables:** diámetro (o sección) por barra,
   :math:`\sigma = N/A`, quizá material o pandeo. Eso **no** cambia
   :math:`A x = b` de la estática; es postproceso o un modelo más rico.

Unidades
--------

================== ========
Magnitud           Unidad
================== ========
Fuerza interna     kN
Reacción           kN
Carga nodal        kN
Longitud           m
Ángulo             rad
Momento (residuo)  kN·m
================== ========

Sistemas operativos
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Uso
     - Windows / Linux / macOS
   * - ``pip install``
     - Sí (Python ≥ 3.10)
   * - pytest, notebook, matplotlib
     - Sí
   * - Streamlit local
     - Sí (navegador)
   * - Docker + Streamlit
     - Sí (Docker Desktop o motor Docker)

Tkinter **no** es requisito. En Linux no hace falta ``python3-tk`` para
esta librería.
