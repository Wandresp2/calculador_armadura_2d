"""Analizador de armaduras 2D isostáticas (mecánica vectorial).

Uso rápido (el solver se completa en la fase 2)::

    from armadura_2d_andresdperezc import Armadura2D

    a = Armadura2D()
    print(a)
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
