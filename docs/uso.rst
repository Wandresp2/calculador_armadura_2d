Uso
===

Presets
-------

::

   from armadura_2d_andresdperezc import Armadura2D

   triangulo = Armadura2D.preset_triangulo()
   warren = Armadura2D.preset_warren()
   pratt = Armadura2D.preset_pratt()
   howe = Armadura2D.preset_howe()

   r = triangulo.resolver()
   r.equilibrio.ok          # True si ΣFx, ΣFy y ΣM ≈ 0
   r.fuerzas                # tupla de FuerzaBarra
   r.reacciones             # tupla de Reaccion

Unidades fijas: **kN** y **m**. El eje :math:`y` es positivo hacia
arriba. Tensión :math:`N > 0`; compresión :math:`N < 0`.

Caso de libro (triángulo)
-------------------------

Base 4 m, altura 3 m, 50 kN hacia abajo en la cúspide
(:math:`F_y = -50` kN). Fijo en el nudo 0, móvil de piso en el nudo 1.

.. math::

   R_{0y} = R_{1y} = 25\,\mathrm{kN},
   \qquad
   N_{\mathrm{B1}} = +\frac{50}{3}\,\mathrm{kN},
   \qquad
   N_{\mathrm{B2}} = N_{\mathrm{B3}} = -\frac{25}{3}\sqrt{13}\,\mathrm{kN}.

B1 (base) sale a **tensión**; B2 y B3 a **compresión**.

Equilibrio nodal
----------------

El paquete arma :math:`A x = b` (una ecuación :math:`F_x` y una
:math:`F_y` por nudo) y lo resuelve con ``numpy.linalg.solve``. El
vector :math:`x` contiene las fuerzas de barra y las reacciones. Si la
armadura no es isostática (:math:`m + r = 2j`) o :math:`A` es singular,
se lanza ``ValueError``.

No es un pórtico: las barras **no** transmiten momento. No hay módulo de
elasticidad ni diámetro en :math:`A x = b`.

Construcción libre
------------------

Quien instala por pip puede armar cualquier isostática 2D::

   a = Armadura2D(nombre="mía")
   a.agregar_nudo(0, 0.0, 0.0)
   a.agregar_nudo(1, 4.0, 0.0)
   a.agregar_nudo(2, 2.0, 3.0)
   a.agregar_barra("B1", 0, 1)
   a.agregar_barra("B2", 0, 2)
   a.agregar_barra("B3", 1, 2)
   a.agregar_apoyo(0, "fijo")
   a.agregar_apoyo(1, "movil")
   a.agregar_carga(2, fx=0.0, fy=-50.0)

Edición de números (misma topología)::

   a.reemplazar_coordenadas({0: (0, 0), 1: (8, 0), 2: (4, 6)})
   a.definir_apoyos(0, 1)                 # piso: solo Ry
   a.definir_apoyos(0, 1, "movil_pared")  # pared vertical: solo Rx
   a.definir_cargas([(2, 0.0, -20.0)])
   print(a.longitud("B1"), a.angulo("B1"))
   print(a.ecuaciones().texto)

``movil_pared`` aporta Rx. Si ese rodillo queda a la misma altura que
el apoyo fijo, el sistema es singular.

La GUI ofrece los cuatro presets y una armadura propia (tablas de
nudos y barras). ``graficar_nudo`` dibuja el cuerpo libre de un nudo.

Gráficos
--------

``graficar`` devuelve una figura de matplotlib (no llama a
``plt.show()``). En un script puede guardar el archivo; en un notebook
se muestra sola::

   fig = triangulo.graficar(r)
   fig.savefig("triangulo.png")

Colores: teal = tensión, oro = compresión, gris = nula. En tests y
Docker use el backend ``Agg``.

Ejemplos del repositorio
------------------------

- ``python ejemplo_consola.py`` — imprime el triángulo de libro, Pratt y
  Howe, y guarda PNG en ``examples/``.
- ``examples/notebook_didactico.ipynb`` — teoría breve y llamadas a la
  API.

Ninguno de los dos usa Streamlit: demuestran que el paquete es
independiente de la GUI.

Pratt vs Howe
-------------

Con la carga por defecto (50 kN hacia abajo en el centro del tablero):

- **Pratt:** diagonales ``3-1`` y ``5-1`` a **tracción**.
- **Howe:** diagonales ``4-0`` y ``4-2`` a **compresión**.
