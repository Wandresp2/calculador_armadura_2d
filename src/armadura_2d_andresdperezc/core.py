"""Núcleo del analizador de armaduras 2D isostáticas.

Este módulo no depende de Streamlit ni de Tkinter. El solver, la validación
completa, los presets y los gráficos se completan en fases posteriores
(ver ``CONTEXTO_DESARROLLO.md``).
"""

from dataclasses import dataclass, field

__all__ = [
    "Armadura2D",
    "FuerzaBarra",
    "Reaccion",
    "ChequeoEquilibrio",
    "ResultadoArmadura",
]


def _fase_pendiente(fase, metodo):
    raise NotImplementedError(
        f"{metodo} se implementa en la fase {fase} "
        "(ver CONTEXTO_DESARROLLO.md)."
    )


@dataclass(frozen=True)
class FuerzaBarra:
    """Fuerza axial de una barra tras resolver la armadura.

    El signo de ``fuerza`` es positivo en tensión y negativo en compresión.
    Unidades: kN y m. ``angulo`` en radianes.
    """

    id: str
    """Identificador de la barra."""

    nudo_i: int
    """Nudo de origen."""

    nudo_j: int
    """Nudo de destino."""

    fuerza: float
    """Fuerza axial en kN. Positiva = tensión."""

    tipo: str
    """``tension``, ``compresion`` o ``nula``."""

    longitud: float
    """Longitud de la barra en m."""

    angulo: float
    """Ángulo de i → j en radianes (eje x del modelo)."""

    coseno: float
    """cos θ = Δx / L."""

    seno: float
    """sin θ = Δy / L."""


@dataclass(frozen=True)
class Reaccion:
    """Reacción en un nudo de apoyo, en kN.

    Si el GDL no existe (rodillo vertical), ``rx`` vale 0.
    """

    nudo: int
    """Identificador del nudo."""

    rx: float
    """Componente horizontal, positiva hacia +x."""

    ry: float
    """Componente vertical, positiva hacia +y."""


@dataclass(frozen=True)
class ChequeoEquilibrio:
    """Residuos de equilibrio global tras resolver (kN y kN·m)."""

    sum_fx: float
    """Σ F_x de cargas externas y reacciones."""

    sum_fy: float
    """Σ F_y de cargas externas y reacciones."""

    sum_mz: float
    """Σ M_z respecto del origen (x F_y − y F_x)."""

    ok: bool
    """True si los residuos están bajo la tolerancia."""

    residuos_nodos: tuple = field(default_factory=tuple)
    """Residuos por nudo, si se calculan. Vacío hasta la fase 2."""


@dataclass(frozen=True)
class ResultadoArmadura:
    """Resultado de ``Armadura2D.resolver()``."""

    fuerzas: tuple
    """Tupla de ``FuerzaBarra``."""

    reacciones: tuple
    """Tupla de ``Reaccion``."""

    equilibrio: ChequeoEquilibrio
    """Chequeo ΣFx, ΣFy, ΣM."""


class Armadura2D:
    """Armadura plana isostática en el plano (mecánica vectorial).

    Unidades por defecto: fuerzas en kN, coordenadas y longitudes en m.
    El eje y es positivo hacia arriba. Streamlit no se importa aquí.

    Parameters
    ----------
    nombre : str, optional
        Etiqueta del modelo (por ejemplo el nombre del preset).
    """

    def __init__(self, nombre="armadura"):
        self._nombre = str(nombre)
        self._nodos = {}
        self._barras = {}
        self._apoyos = {}
        self._cargas = {}

    @property
    def nombre(self):
        """Etiqueta del modelo (solo lectura)."""
        return self._nombre

    def agregar_nodo(self, id, x, y):
        """Agrega un nudo con coordenadas en m.

        Raises
        ------
        NotImplementedError
            Hasta la fase 2.
        """
        _fase_pendiente(2, "agregar_nodo")

    def agregar_barra(self, id, nudo_i, nudo_j):
        """Agrega una barra entre dos nudos existentes.

        Raises
        ------
        NotImplementedError
            Hasta la fase 2.
        """
        _fase_pendiente(2, "agregar_barra")

    def agregar_apoyo(self, nudo, tipo):
        """Agrega un apoyo ``fijo`` o ``movil`` (rodillo vertical) en un nudo.

        Raises
        ------
        NotImplementedError
            Hasta la fase 2.
        """
        _fase_pendiente(2, "agregar_apoyo")

    def agregar_carga(self, nudo, fx=0.0, fy=0.0):
        """Agrega una carga nodal en kN (ejes matemáticos: fy > 0 hacia arriba).

        Raises
        ------
        NotImplementedError
            Hasta la fase 2.
        """
        _fase_pendiente(2, "agregar_carga")

    def longitud(self, barra_id):
        """Longitud de una barra en m.

        Raises
        ------
        NotImplementedError
            Hasta la fase 2.
        """
        _fase_pendiente(2, "longitud")

    def angulo(self, barra_id):
        """Ángulo de una barra en radianes (i → j).

        Raises
        ------
        NotImplementedError
            Hasta la fase 2.
        """
        _fase_pendiente(2, "angulo")

    def resolver(self):
        """Resuelve A x = b y clasifica tensión/compresión.

        Returns
        -------
        ResultadoArmadura

        Raises
        ------
        NotImplementedError
            Hasta la fase 2.
        """
        _fase_pendiente(2, "resolver")

    def verificar_equilibrio(self, resultado=None):
        """Comprueba residuos de ΣFx, ΣFy y ΣM.

        Raises
        ------
        NotImplementedError
            Hasta la fase 2.
        """
        _fase_pendiente(2, "verificar_equilibrio")

    def graficar(self, resultado=None):
        """Devuelve una ``matplotlib.figure.Figure`` de la armadura.

        Raises
        ------
        NotImplementedError
            Hasta la fase 4.
        """
        _fase_pendiente(4, "graficar")

    @classmethod
    def preset_triangulo(cls):
        """Preset del triángulo isósceles de libro (fase 2)."""
        _fase_pendiente(2, "preset_triangulo")

    @classmethod
    def preset_warren(cls):
        """Preset Warren de 2 paneles (fase 3)."""
        _fase_pendiente(3, "preset_warren")

    @classmethod
    def preset_pratt(cls):
        """Preset Pratt de 2 paneles (fase 3)."""
        _fase_pendiente(3, "preset_pratt")

    @classmethod
    def preset_howe(cls):
        """Preset Howe de 2 paneles (fase 3)."""
        _fase_pendiente(3, "preset_howe")

    def __repr__(self):
        return f"Armadura2D(nombre={self._nombre!r})"
