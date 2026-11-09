"""Analizador de armaduras 2D isostáticas (mecánica vectorial).

Uso rápido::

    from armadura_2d_andresdperezc import Armadura2D

    a = Armadura2D.preset_triangulo()  # también preset_warren, preset_pratt, preset_howe
    r = a.resolver()
    print(r.equilibrio.ok)
    for barra in r.fuerzas:
        print(barra.id, barra.tipo, barra.fuerza)
    a.graficar(r)  # Figure de matplotlib; no abre ventana
"""

from .core import (
    Armadura2D,
    ChequeoEquilibrio,
    FuerzaBarra,
    Reaccion,
    ResultadoArmadura,
)

__version__ = "0.1.0"

__all__ = [
    "Armadura2D",
    "ChequeoEquilibrio",
    "FuerzaBarra",
    "Reaccion",
    "ResultadoArmadura",
    "__version__",
]
