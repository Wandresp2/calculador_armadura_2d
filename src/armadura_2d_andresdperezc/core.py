"""Núcleo del analizador de armaduras 2D isostáticas.

Este módulo no depende de Streamlit ni de Tkinter. Resuelve el equilibrio
nodal A x = b con NumPy. ``graficar`` devuelve una Figure de matplotlib
(no abre ventanas).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "Armadura2D",
    "FuerzaBarra",
    "Reaccion",
    "ChequeoEquilibrio",
    "ResultadoArmadura",
]


def _entero(valor, nombre):
    """Exige un entero (admite 0). Rechaza bool y no enteros."""
    if isinstance(valor, bool) or not isinstance(valor, (int, np.integer)):
        raise ValueError(
            f"{nombre} debe ser un entero; se recibió {valor!r}."
        )
    return int(valor)


def _real(valor, nombre):
    """Exige un número real. Rechaza bool."""
    if isinstance(valor, bool) or not isinstance(
        valor, (int, float, np.integer, np.floating)
    ):
        raise ValueError(
            f"{nombre} debe ser un número real; se recibió {valor!r}."
        )
    if not math.isfinite(float(valor)):
        raise ValueError(f"{nombre} debe ser finito; se recibió {valor!r}.")
    return float(valor)


def _id_barra(valor):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(
            f"El id de barra debe ser un texto no vacío; se recibió {valor!r}."
        )
    return valor


def _tipo_apoyo(valor):
    if valor not in Armadura2D.TIPOS_APOYO:
        raise ValueError(
            "El tipo de apoyo debe ser 'fijo' o 'movil'; "
            f"se recibió {valor!r}."
        )
    return valor


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
    """Tupla de ``(nudo, res_fx, res_fy)`` ordenada por nudo."""


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

    TIPOS_APOYO = ("fijo", "movil")
    """Apoyos de la 0.1.0: pin (Rx, Ry) y rodillo vertical (Ry)."""

    TOLERANCIA_EQUILIBRIO = 1e-8
    """Tolerancia absoluta de residuos (kN y kN·m)."""

    EPS_FUERZA_NULA = 1e-8
    """Umbral del valor absoluto de N para clasificar una barra como ``nula``."""

    COLOR_TENSION = "#1A6B7A"
    """Teal: barra a tracción (como en el PPT del curso)."""

    COLOR_COMPRESION = "#C9A227"
    """Oro: barra a compresión."""

    COLOR_NULA = "#7F8C8D"
    """Gris: fuerza nula o barra aún sin resultado."""

    COLOR_CARGA = "#A83226"
    """Rojo: cargas externas."""

    COLOR_REACCION = "#1F6FA5"
    """Azul: reacciones en apoyos."""

    def __init__(self, nombre="armadura"):
        self._nombre = str(nombre)
        self._nodos = {}
        self._barras = {}
        self._apoyos = {}
        self._cargas = {}
        self._base_ref = None
        self._altura_ref = None

    @property
    def nombre(self):
        """Etiqueta del modelo (solo lectura)."""
        return self._nombre

    @property
    def base_ref(self):
        """Base del preset en m, o ``None`` si no es un preset."""
        return self._base_ref

    @property
    def altura_ref(self):
        """Altura del preset en m, o ``None`` si no es un preset."""
        return self._altura_ref

    def snapshot_nodos(self):
        """Copia de nudos para la GUI y scripts (no expone ``_nodos``).

        Returns
        -------
        tuple of tuple
            ``(id, x, y)`` ordenados por id.
        """
        return tuple(
            (nudo, xy[0], xy[1]) for nudo, xy in sorted(self._nodos.items())
        )

    def snapshot_barras(self):
        """Copia de barras en el orden en que se agregaron.

        Returns
        -------
        tuple of tuple
            ``(id, nudo_i, nudo_j)``.
        """
        return tuple(
            (barra, nudo_i, nudo_j)
            for barra, (nudo_i, nudo_j) in self._barras.items()
        )

    def snapshot_apoyos(self):
        """Copia de apoyos.

        Returns
        -------
        tuple of tuple
            ``(nudo, tipo)`` con ``tipo`` igual a ``"fijo"`` o ``"movil"``.
        """
        return tuple(
            (nudo, tipo) for nudo, tipo in sorted(self._apoyos.items())
        )

    def snapshot_cargas(self):
        """Copia de cargas nodales en ejes del modelo (fy > 0 hacia arriba).

        Returns
        -------
        tuple of tuple
            ``(nudo, fx, fy)`` en kN.
        """
        return tuple(
            (nudo, fx, fy)
            for nudo, (fx, fy) in sorted(self._cargas.items())
        )

    def agregar_nodo(self, nudo, x, y):
        """Agrega un nudo con coordenadas en m.

        Parameters
        ----------
        nudo : int
            Identificador entero (puede ser 0).
        x, y : float
            Coordenadas en m.

        Raises
        ------
        ValueError
            Si el id no es entero, las coordenadas no son reales o el nudo
            ya existe.
        """
        nudo = _entero(nudo, "nudo")
        x = _real(x, "x")
        y = _real(y, "y")
        if nudo in self._nodos:
            raise ValueError(f"El nudo {nudo} ya existe.")
        self._nodos[nudo] = (x, y)

    def agregar_barra(self, barra, nudo_i, nudo_j):
        """Agrega una barra entre dos nudos existentes.

        Parameters
        ----------
        barra : str
            Identificador de la barra (p. ej. ``"B1"``).
        nudo_i, nudo_j : int
            Nudos que une.

        Raises
        ------
        ValueError
            Barra repetida, nudos iguales o inexistentes, o longitud nula.
        """
        barra = _id_barra(barra)
        nudo_i = self._exigir_nudo(nudo_i, "nudo_i")
        nudo_j = self._exigir_nudo(nudo_j, "nudo_j")
        if nudo_i == nudo_j:
            raise ValueError(
                f"La barra {barra!r} no puede unir un nudo consigo mismo."
            )
        if barra in self._barras:
            raise ValueError(f"La barra {barra!r} ya existe.")
        par = frozenset((nudo_i, nudo_j))
        for existente, (i, j) in self._barras.items():
            if frozenset((i, j)) == par:
                raise ValueError(
                    f"Ya existe la barra {existente!r} entre los nudos "
                    f"{nudo_i} y {nudo_j}."
                )
        if self._longitud_entre(nudo_i, nudo_j) == 0.0:
            raise ValueError(
                f"La barra {barra!r} tiene longitud 0 "
                f"(nudos {nudo_i} y {nudo_j} coinciden)."
            )
        self._barras[barra] = (nudo_i, nudo_j)

    def agregar_apoyo(self, nudo, tipo):
        """Agrega un apoyo ``fijo`` o ``movil`` (rodillo vertical) en un nudo.

        Parameters
        ----------
        nudo : int
        tipo : {"fijo", "movil"}

        Raises
        ------
        ValueError
            Nudo inexistente, tipo ilegal o apoyo ya definido en ese nudo.
        """
        nudo = self._exigir_nudo(nudo, "nudo")
        tipo = _tipo_apoyo(tipo)
        if nudo in self._apoyos:
            raise ValueError(f"El nudo {nudo} ya tiene un apoyo.")
        self._apoyos[nudo] = tipo

    def agregar_carga(self, nudo, fx=0.0, fy=0.0):
        """Agrega una carga nodal en kN (ejes matemáticos: fy > 0 hacia arriba).

        Parameters
        ----------
        nudo : int
        fx, fy : float, optional
            Componentes en kN. En la GUI, “hacia abajo (+)” se convierte a fy negativa.

        Raises
        ------
        ValueError
            Nudo inexistente, componentes no reales, o el nudo ya tenía carga.
        """
        nudo = self._exigir_nudo(nudo, "nudo")
        fx = _real(fx, "fx")
        fy = _real(fy, "fy")
        if nudo in self._cargas:
            raise ValueError(
                f"El nudo {nudo} ya tiene una carga; use reemplazar_carga."
            )
        self._cargas[nudo] = (fx, fy)

    def reemplazar_carga(self, nudo, fx=0.0, fy=0.0):
        """Sustituye (o crea) la carga nodal en kN.

        Parameters
        ----------
        nudo : int
        fx, fy : float, optional
        """
        nudo = self._exigir_nudo(nudo, "nudo")
        self._cargas[nudo] = (_real(fx, "fx"), _real(fy, "fy"))

    def mover_nodo(self, nudo, x, y):
        """Cambia las coordenadas de un nudo (m).

        Raises
        ------
        ValueError
            Nudo inexistente o alguna barra quedaría con longitud 0.
        """
        nudo = self._exigir_nudo(nudo, "nudo")
        x = _real(x, "x")
        y = _real(y, "y")
        anterior = self._nodos[nudo]
        self._nodos[nudo] = (x, y)
        try:
            for barra, (i, j) in self._barras.items():
                if self._longitud_entre(i, j) == 0.0:
                    raise ValueError(
                        f"Mover el nudo {nudo} deja la barra {barra!r} "
                        "con longitud 0."
                    )
        except ValueError:
            self._nodos[nudo] = anterior
            raise

    def escalar(self, factor_x, factor_y):
        """Escala las coordenadas desde el origen.

        Parameters
        ----------
        factor_x, factor_y : float
            Multiplicadores de x e y. Deben ser finitos y no nulos.
        """
        factor_x = _real(factor_x, "factor_x")
        factor_y = _real(factor_y, "factor_y")
        if factor_x == 0.0 or factor_y == 0.0:
            raise ValueError("Los factores de escala no pueden ser 0.")
        anterior = dict(self._nodos)
        self._nodos = {
            nudo: (x * factor_x, y * factor_y)
            for nudo, (x, y) in self._nodos.items()
        }
        try:
            for barra, (i, j) in self._barras.items():
                if self._longitud_entre(i, j) == 0.0:
                    raise ValueError(
                        f"La escala deja la barra {barra!r} con longitud 0."
                    )
        except ValueError:
            self._nodos = anterior
            raise

    def definir_apoyos(self, nudo_fijo, nudo_movil):
        """Deja exactamente un apoyo fijo y un móvil en nudos existentes.

        Parameters
        ----------
        nudo_fijo, nudo_movil : int
            Deben ser nudos distintos. El fijo aporta Rx y Ry; el móvil, Ry.

        Raises
        ------
        ValueError
            Nudo inexistente o ambos ids iguales.
        """
        nudo_fijo = self._exigir_nudo(nudo_fijo, "nudo_fijo")
        nudo_movil = self._exigir_nudo(nudo_movil, "nudo_movil")
        if nudo_fijo == nudo_movil:
            raise ValueError(
                "El apoyo fijo y el móvil deben estar en nudos distintos."
            )
        self._apoyos = {nudo_fijo: "fijo", nudo_movil: "movil"}

    def definir_cargas(self, cargas):
        """Sustituye el conjunto de cargas nodales.

        Parameters
        ----------
        cargas : iterable
            Triplets ``(nudo, fx, fy)`` en kN (fy > 0 hacia arriba).
        """
        nuevo = {}
        for nudo, fx, fy in cargas:
            nudo = self._exigir_nudo(nudo, "nudo")
            nuevo[nudo] = (_real(fx, "fx"), _real(fy, "fy"))
        self._cargas = nuevo

    def reemplazar_coordenadas(self, coordenadas):
        """Sustituye las coordenadas de todos los nudos existentes a la vez.

        Parameters
        ----------
        coordenadas : mapping
            ``nudo -> (x, y)`` en m. Debe incluir exactamente los nudos actuales.

        Raises
        ------
        ValueError
            Nudos de más o de menos, o alguna barra con longitud 0.
        """
        if set(coordenadas) != set(self._nodos):
            raise ValueError(
                "Las coordenadas deben incluir exactamente los nudos actuales; "
                "no se pueden añadir ni quitar nudos."
            )
        nuevos = {}
        for nudo, xy in coordenadas.items():
            nudo = self._exigir_nudo(nudo, "nudo")
            try:
                x, y = xy
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"La coordenada del nudo {nudo} debe ser un par (x, y)."
                ) from exc
            nuevos[nudo] = (_real(x, "x"), _real(y, "y"))
        anterior = dict(self._nodos)
        self._nodos = nuevos
        try:
            for barra, (i, j) in self._barras.items():
                if self._longitud_entre(i, j) == 0.0:
                    raise ValueError(
                        f"Las coordenadas dejan la barra {barra!r} con longitud 0."
                    )
        except ValueError:
            self._nodos = anterior
            raise

    def longitud(self, barra):
        """Longitud de una barra en m.

        Parameters
        ----------
        barra : str

        Returns
        -------
        float
        """
        i, j = self._barra(barra)
        return self._longitud_entre(i, j)

    def angulo(self, barra):
        """Ángulo de una barra en radianes (i → j).

        Parameters
        ----------
        barra : str

        Returns
        -------
        float
        """
        i, j = self._barra(barra)
        dx, dy = self._delta(i, j)
        return math.atan2(dy, dx)

    def resolver(self):
        """Resuelve A x = b y clasifica tensión/compresión.

        Returns
        -------
        ResultadoArmadura

        Raises
        ------
        ValueError
            Si la armadura no es isostática o el sistema es singular.
        """
        j = len(self._nodos)
        m = len(self._barras)
        r = self._n_reacciones()
        if j == 0:
            raise ValueError("La armadura no tiene nudos.")
        if m + r > 2 * j:
            raise ValueError(
                "La armadura es hiperestática (m + r > 2j); "
                "este paquete solo resuelve isostáticas."
            )
        if m + r < 2 * j:
            raise ValueError(
                "La armadura es hipostática (m + r < 2j); "
                "faltan barras o reacciones."
            )

        nudos = sorted(self._nodos)
        fila = {nudo: 2 * k for k, nudo in enumerate(nudos)}
        barras = list(self._barras.items())
        n = 2 * j
        a_mat = np.zeros((n, n), dtype=float)
        b_vec = np.zeros(n, dtype=float)

        for nudo in nudos:
            fx, fy = self._carga(nudo)
            b_vec[fila[nudo]] = -fx
            b_vec[fila[nudo] + 1] = -fy

        for col, (_barra, (nudo_i, nudo_j)) in enumerate(barras):
            ux, uy = self._unitario(nudo_i, nudo_j)
            a_mat[fila[nudo_i], col] += ux
            a_mat[fila[nudo_i] + 1, col] += uy
            a_mat[fila[nudo_j], col] += -ux
            a_mat[fila[nudo_j] + 1, col] += -uy

        col = m
        gdl_reaccion = []
        for nudo in sorted(self._apoyos):
            tipo = self._apoyos[nudo]
            if tipo == "fijo":
                a_mat[fila[nudo], col] = 1.0
                gdl_reaccion.append((nudo, "rx", col))
                col += 1
                a_mat[fila[nudo] + 1, col] = 1.0
                gdl_reaccion.append((nudo, "ry", col))
                col += 1
            else:
                a_mat[fila[nudo] + 1, col] = 1.0
                gdl_reaccion.append((nudo, "ry", col))
                col += 1

        try:
            x = np.linalg.solve(a_mat, b_vec)
        except np.linalg.LinAlgError as exc:
            raise ValueError(
                "El sistema de equilibrio es singular "
                "(geometría degenerada o apoyos mal colocados)."
            ) from exc

        fuerzas = []
        for col, (barra, (nudo_i, nudo_j)) in enumerate(barras):
            fuerzas.append(self._fuerza_barra(barra, nudo_i, nudo_j, float(x[col])))

        rx_ry = {nudo: [0.0, 0.0] for nudo in self._apoyos}
        for nudo, gdl, col in gdl_reaccion:
            if gdl == "rx":
                rx_ry[nudo][0] = float(x[col])
            else:
                rx_ry[nudo][1] = float(x[col])
        reacciones = tuple(
            Reaccion(nudo=nudo, rx=rx_ry[nudo][0], ry=rx_ry[nudo][1])
            for nudo in sorted(self._apoyos)
        )
        fuerzas = tuple(fuerzas)
        equilibrio = self._chequear(fuerzas, reacciones)
        return ResultadoArmadura(
            fuerzas=fuerzas,
            reacciones=reacciones,
            equilibrio=equilibrio,
        )

    def verificar_equilibrio(self, resultado=None):
        """Comprueba residuos de ΣFx, ΣFy y ΣM.

        Parameters
        ----------
        resultado : ResultadoArmadura, optional
            Si se omite, se llama a ``resolver()``.

        Returns
        -------
        ChequeoEquilibrio
        """
        if resultado is None:
            return self.resolver().equilibrio
        if not isinstance(resultado, ResultadoArmadura):
            raise ValueError(
                "resultado debe ser un ResultadoArmadura; "
                f"se recibió {type(resultado)!r}."
            )
        return self._chequear(resultado.fuerzas, resultado.reacciones)

    def graficar(self, resultado=None):
        """Dibuja la armadura: barras T/C, nudos, apoyos, cargas y reacciones.

        No llama a ``plt.show()``. En tests, scripts y Docker usar backend Agg.

        Parameters
        ----------
        resultado : ResultadoArmadura, optional
            Si se omite, se llama a ``resolver()``.

        Returns
        -------
        matplotlib.figure.Figure

        Raises
        ------
        ValueError
            Si no hay nudos o ``resultado`` no es un ``ResultadoArmadura``.
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, Polygon

        if not self._nodos:
            raise ValueError("La armadura no tiene nudos.")
        if resultado is None:
            resultado = self.resolver()
        if not isinstance(resultado, ResultadoArmadura):
            raise ValueError(
                "resultado debe ser un ResultadoArmadura; "
                f"se recibió {type(resultado)!r}."
            )

        fuerzas = {barra.id: barra for barra in resultado.fuerzas}
        span = self._span_dibujo()
        fig, ax = plt.subplots(figsize=(8.0, 6.0), layout="constrained")

        vistos = set()
        for barra_id, (nudo_i, nudo_j) in self._barras.items():
            x_i, y_i = self._nodos[nudo_i]
            x_j, y_j = self._nodos[nudo_j]
            dato = fuerzas.get(barra_id)
            tipo = dato.tipo if dato is not None else "nula"
            color = self._color_tipo(tipo)
            etiqueta = None
            if tipo not in vistos:
                etiqueta = {
                    "tension": "tensión",
                    "compresion": "compresión",
                    "nula": "nula",
                }[tipo]
                vistos.add(tipo)
            ax.plot(
                [x_i, x_j],
                [y_i, y_j],
                color=color,
                linewidth=2.6,
                solid_capstyle="round",
                label=etiqueta,
                zorder=2,
            )
            mx, my = (x_i + x_j) / 2.0, (y_i + y_j) / 2.0
            dx, dy = x_j - x_i, y_j - y_i
            largo = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / largo, dx / largo
            off = 0.045 * span
            texto = barra_id
            if dato is not None:
                texto = f"{barra_id}\n{dato.fuerza:.1f} kN"
            ax.text(
                mx + off * nx,
                my + off * ny,
                texto,
                ha="center",
                va="center",
                fontsize=8,
                color="#1C2333",
                zorder=4,
            )

        radio_nudo = 0.035 * span
        for nudo, (x, y) in self._nodos.items():
            ax.add_patch(
                Circle(
                    (x, y),
                    radio_nudo,
                    facecolor="#F6F3EC",
                    edgecolor="#0B1F3A",
                    linewidth=1.4,
                    zorder=5,
                )
            )
            ax.text(
                x,
                y + 1.7 * radio_nudo,
                str(nudo),
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color="#0B1F3A",
                zorder=6,
            )
            tipo_apoyo = self._apoyos.get(nudo)
            if tipo_apoyo == "fijo":
                self._dibujar_apoyo_fijo(ax, x, y, span, Polygon)
            elif tipo_apoyo == "movil":
                self._dibujar_apoyo_movil(ax, x, y, span, Circle, Polygon)

        vectores = []
        for nudo, (fx, fy) in self._cargas.items():
            vectores.append((fx, fy))
        for rec in resultado.reacciones:
            vectores.append((rec.rx, rec.ry))
        f_max = max((math.hypot(fx, fy) for fx, fy in vectores), default=1.0)
        if f_max <= 0.0:
            f_max = 1.0

        hubo_carga = False
        for nudo, (fx, fy) in self._cargas.items():
            if math.hypot(fx, fy) <= self.EPS_FUERZA_NULA:
                continue
            x, y = self._nodos[nudo]
            self._flecha(
                ax, x, y, fx, fy, span, f_max, self.COLOR_CARGA, hacia_nudo=True
            )
            hubo_carga = True
        if hubo_carga:
            ax.plot([], [], color=self.COLOR_CARGA, lw=1.8, label="carga")

        hubo_reaccion = False
        for rec in resultado.reacciones:
            if math.hypot(rec.rx, rec.ry) <= self.EPS_FUERZA_NULA:
                continue
            x, y = self._nodos[rec.nudo]
            self._flecha(
                ax,
                x,
                y,
                rec.rx,
                rec.ry,
                span,
                f_max,
                self.COLOR_REACCION,
                hacia_nudo=False,
            )
            hubo_reaccion = True
        if hubo_reaccion:
            ax.plot([], [], color=self.COLOR_REACCION, lw=1.8, label="reacción")

        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_title(f"{self._nombre}  ·  + tensión  /  − compresión")
        ax.grid(True, alpha=0.25)
        xs = [xy[0] for xy in self._nodos.values()]
        ys = [xy[1] for xy in self._nodos.values()]
        margen = 0.28 * span
        ax.set_xlim(min(xs) - margen, max(xs) + margen)
        ax.set_ylim(min(ys) - margen, max(ys) + margen)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.92)
        return fig

    def _color_tipo(self, tipo):
        return {
            "tension": self.COLOR_TENSION,
            "compresion": self.COLOR_COMPRESION,
            "nula": self.COLOR_NULA,
        }.get(tipo, self.COLOR_NULA)

    def _span_dibujo(self):
        xs = [xy[0] for xy in self._nodos.values()]
        ys = [xy[1] for xy in self._nodos.values()]
        return max(max(xs) - min(xs), max(ys) - min(ys), 1.0)

    def _flecha(self, ax, x, y, fx, fy, span, f_max, color, hacia_nudo):
        mag = math.hypot(fx, fy)
        if mag <= 0.0:
            return
        largo = 0.32 * span * (mag / f_max)
        dx = largo * fx / mag
        dy = largo * fy / mag
        if hacia_nudo:
            cola = (x - dx, y - dy)
            cabeza = (x, y)
        else:
            cola = (x, y)
            cabeza = (x + dx, y + dy)
        ax.annotate(
            "",
            xy=cabeza,
            xytext=cola,
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=1.7,
                mutation_scale=11,
            ),
            zorder=7,
        )

    def _dibujar_apoyo_fijo(self, ax, x, y, span, polygon_cls):
        t = 0.08 * span
        triangulo = polygon_cls(
            [(x, y), (x - 0.7 * t, y - t), (x + 0.7 * t, y - t)],
            closed=True,
            facecolor="#C9A227",
            edgecolor="#0B1F3A",
            linewidth=1.0,
            zorder=3,
        )
        ax.add_patch(triangulo)
        ax.plot(
            [x - 1.1 * t, x + 1.1 * t],
            [y - t, y - t],
            color="#0B1F3A",
            lw=1.4,
            zorder=3,
        )

    def _dibujar_apoyo_movil(self, ax, x, y, span, circle_cls, polygon_cls):
        t = 0.08 * span
        triangulo = polygon_cls(
            [(x, y), (x - 0.7 * t, y - 0.75 * t), (x + 0.7 * t, y - 0.75 * t)],
            closed=True,
            facecolor="#C9A227",
            edgecolor="#0B1F3A",
            linewidth=1.0,
            zorder=3,
        )
        ax.add_patch(triangulo)
        radio = 0.16 * t
        for signo in (-1, 1):
            ax.add_patch(
                circle_cls(
                    (x + signo * 0.28 * t, y - 0.75 * t - radio),
                    radio,
                    facecolor="#F6F3EC",
                    edgecolor="#0B1F3A",
                    linewidth=1.0,
                    zorder=3,
                )
            )

    @classmethod
    def preset_triangulo(cls):
        """Triángulo isósceles de libro: 4 m × 3 m, 50 kN en la cúspide.

        Returns
        -------
        Armadura2D
            Fijo en 0, móvil en 1, :math:`F_y = -50` kN en el nudo 2.
        """
        armadura = cls(nombre="Triángulo")
        armadura.agregar_nodo(0, 0.0, 0.0)
        armadura.agregar_nodo(1, 4.0, 0.0)
        armadura.agregar_nodo(2, 2.0, 3.0)
        armadura.agregar_barra("B1", 0, 1)
        armadura.agregar_barra("B2", 0, 2)
        armadura.agregar_barra("B3", 1, 2)
        armadura.agregar_apoyo(0, "fijo")
        armadura.agregar_apoyo(1, "movil")
        armadura.agregar_carga(2, fx=0.0, fy=-50.0)
        armadura._base_ref = 4.0
        armadura._altura_ref = 3.0
        return armadura

    @classmethod
    def preset_warren(cls):
        """Puente Warren de 2 paneles: 4 m × 2 m, 50 kN en el tablero central.

        Returns
        -------
        Armadura2D
        """
        armadura = cls._puente_base(
            nombre="Warren",
            nudos=(
                (0, 0.0, 0.0),
                (1, 2.0, 0.0),
                (2, 4.0, 0.0),
                (3, 1.0, 2.0),
                (4, 3.0, 2.0),
            ),
        )
        for barra, nudo_i, nudo_j in (
            ("B1", 0, 1),
            ("B2", 1, 2),
            ("B3", 3, 4),
            ("B4", 0, 3),
            ("B5", 2, 4),
            ("B6", 3, 1),
            ("B7", 1, 4),
        ):
            armadura.agregar_barra(barra, nudo_i, nudo_j)
        return armadura

    @classmethod
    def preset_pratt(cls):
        """Puente Pratt de 2 paneles: diagonales hacia el centro (a tracción).

        Returns
        -------
        Armadura2D
            Diagonales ``3-1`` y ``5-1``.
        """
        armadura = cls._cordones_pratt_howe(nombre="Pratt")
        armadura.agregar_barra("B8", 3, 1)
        armadura.agregar_barra("B9", 5, 1)
        return armadura

    @classmethod
    def preset_howe(cls):
        """Puente Howe de 2 paneles: diagonales hacia los apoyos (a compresión).

        Returns
        -------
        Armadura2D
            Diagonales ``4-0`` y ``4-2``.
        """
        armadura = cls._cordones_pratt_howe(nombre="Howe")
        armadura.agregar_barra("B8", 4, 0)
        armadura.agregar_barra("B9", 4, 2)
        return armadura

    @classmethod
    def _puente_base(cls, nombre, nudos):
        """Nudos, apoyos y carga comunes de Warren / Pratt / Howe."""
        armadura = cls(nombre=nombre)
        for nudo, x, y in nudos:
            armadura.agregar_nodo(nudo, x, y)
        armadura.agregar_apoyo(0, "fijo")
        armadura.agregar_apoyo(2, "movil")
        armadura.agregar_carga(1, fx=0.0, fy=-50.0)
        armadura._base_ref = 4.0
        armadura._altura_ref = 2.0
        return armadura

    @classmethod
    def _cordones_pratt_howe(cls, nombre):
        """Misma geometría de 6 nudos, cuerdas y verticales; cambian las diagonales."""
        armadura = cls._puente_base(
            nombre=nombre,
            nudos=(
                (0, 0.0, 0.0),
                (1, 2.0, 0.0),
                (2, 4.0, 0.0),
                (3, 0.0, 2.0),
                (4, 2.0, 2.0),
                (5, 4.0, 2.0),
            ),
        )
        for barra, nudo_i, nudo_j in (
            ("B1", 0, 1),
            ("B2", 1, 2),
            ("B3", 3, 4),
            ("B4", 4, 5),
            ("B5", 0, 3),
            ("B6", 1, 4),
            ("B7", 2, 5),
        ):
            armadura.agregar_barra(barra, nudo_i, nudo_j)
        return armadura

    def __repr__(self):
        return (
            f"Armadura2D(nombre={self._nombre!r}, "
            f"nudos={len(self._nodos)}, barras={len(self._barras)})"
        )

    def _exigir_nudo(self, nudo, nombre):
        nudo = _entero(nudo, nombre)
        if nudo not in self._nodos:
            raise ValueError(f"No existe el nudo {nudo}.")
        return nudo

    def _barra(self, barra):
        barra = _id_barra(barra)
        if barra not in self._barras:
            raise ValueError(f"No existe la barra {barra!r}.")
        return self._barras[barra]

    def _carga(self, nudo):
        return self._cargas.get(nudo, (0.0, 0.0))

    def _delta(self, nudo_i, nudo_j):
        x_i, y_i = self._nodos[nudo_i]
        x_j, y_j = self._nodos[nudo_j]
        return x_j - x_i, y_j - y_i

    def _longitud_entre(self, nudo_i, nudo_j):
        dx, dy = self._delta(nudo_i, nudo_j)
        return math.hypot(dx, dy)

    def _unitario(self, nudo_i, nudo_j):
        longitud = self._longitud_entre(nudo_i, nudo_j)
        if longitud == 0.0:
            raise ValueError(
                f"Los nudos {nudo_i} y {nudo_j} coinciden (longitud 0)."
            )
        dx, dy = self._delta(nudo_i, nudo_j)
        return dx / longitud, dy / longitud

    def _n_reacciones(self):
        total = 0
        for tipo in self._apoyos.values():
            total += 2 if tipo == "fijo" else 1
        return total

    def _clasificar(self, fuerza):
        if fuerza > self.EPS_FUERZA_NULA:
            return "tension"
        if fuerza < -self.EPS_FUERZA_NULA:
            return "compresion"
        return "nula"

    def _fuerza_barra(self, barra, nudo_i, nudo_j, fuerza):
        longitud = self._longitud_entre(nudo_i, nudo_j)
        ux, uy = self._unitario(nudo_i, nudo_j)
        return FuerzaBarra(
            id=barra,
            nudo_i=nudo_i,
            nudo_j=nudo_j,
            fuerza=fuerza,
            tipo=self._clasificar(fuerza),
            longitud=longitud,
            angulo=math.atan2(uy, ux) if longitud else 0.0,
            coseno=ux,
            seno=uy,
        )

    def _chequear(self, fuerzas, reacciones):
        sum_fx = 0.0
        sum_fy = 0.0
        sum_mz = 0.0
        for nudo, (x, y) in self._nodos.items():
            fx, fy = self._carga(nudo)
            sum_fx += fx
            sum_fy += fy
            sum_mz += x * fy - y * fx
        mapa_r = {item.nudo: item for item in reacciones}
        for nudo, item in mapa_r.items():
            x, y = self._nodos[nudo]
            sum_fx += item.rx
            sum_fy += item.ry
            sum_mz += x * item.ry - y * item.rx

        contrib_x = {nudo: 0.0 for nudo in self._nodos}
        contrib_y = {nudo: 0.0 for nudo in self._nodos}
        for barra in fuerzas:
            ux, uy = barra.coseno, barra.seno
            contrib_x[barra.nudo_i] += barra.fuerza * ux
            contrib_y[barra.nudo_i] += barra.fuerza * uy
            contrib_x[barra.nudo_j] += barra.fuerza * (-ux)
            contrib_y[barra.nudo_j] += barra.fuerza * (-uy)

        residuos = []
        for nudo in sorted(self._nodos):
            fx, fy = self._carga(nudo)
            rec = mapa_r.get(nudo)
            rx = rec.rx if rec is not None else 0.0
            ry = rec.ry if rec is not None else 0.0
            res_x = contrib_x[nudo] + rx + fx
            res_y = contrib_y[nudo] + ry + fy
            residuos.append((nudo, res_x, res_y))

        tol = self.TOLERANCIA_EQUILIBRIO
        ok = (
            abs(sum_fx) <= tol
            and abs(sum_fy) <= tol
            and abs(sum_mz) <= tol
            and all(abs(rx) <= tol and abs(ry) <= tol for _, rx, ry in residuos)
        )
        return ChequeoEquilibrio(
            sum_fx=sum_fx,
            sum_fy=sum_fy,
            sum_mz=sum_mz,
            ok=ok,
            residuos_nodos=tuple(residuos),
        )
