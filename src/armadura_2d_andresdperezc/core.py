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
    "EcuacionNudo",
    "SistemaEcuaciones",
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
            "El tipo de apoyo debe ser 'fijo', 'movil' (piso, Ry) "
            "o 'movil_pared' (pared, Rx); "
            f"se recibió {valor!r}."
        )
    return valor


def _numero_corto(valor):
    """Entero si el valor cae en uno; si no, cuatro decimales."""
    if abs(valor - round(valor)) < 5e-4:
        return str(int(round(valor)))
    return f"{valor:.4f}"


def _pieza_ecuacion(coef, nombre, es_primero):
    """Un término con signo, listo para unir en ΣF = 0. ``None`` si es nulo."""
    if abs(coef) < 5e-5:
        return None
    magnitud = abs(coef)
    if nombre and abs(magnitud - 1.0) < 5e-4:
        cuerpo = nombre
    elif nombre:
        cuerpo = f"{_numero_corto(magnitud)} {nombre}"
    else:
        cuerpo = _numero_corto(magnitud)
    if coef < 0:
        return f"− {cuerpo}"
    if es_primero:
        return cuerpo
    return f"+ {cuerpo}"


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

    Si el grado de libertad no existe, esa componente vale 0:
    rodillo de piso → ``rx`` = 0; rodillo de pared → ``ry`` = 0.
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
class EcuacionNudo:
    """Una ecuación de equilibrio, ΣFx = 0 o ΣFy = 0, en un nudo.

    ``texto`` ya incluye el signo de la carga y cierra con ``= 0``.
    ``coeficientes`` sigue el orden de ``SistemaEcuaciones.incognitas``.
    ``carga`` es la componente externa en kN (positiva hacia +x o +y).
    """

    nudo: int
    """Identificador del nudo."""

    eje: str
    """``x`` o ``y``."""

    texto: str
    """Ecuación escrita, con N > 0 en tensión."""

    coeficientes: tuple
    """Coeficientes de las incógnitas, en el orden del sistema."""

    carga: float
    """Carga externa de este eje, en kN."""


@dataclass(frozen=True)
class SistemaEcuaciones:
    """Sistema completo de equilibrio nodal, antes de sustituir la solución.

    Cada fila es un nudo (primero ΣFx, luego ΣFy). Las incógnitas son las
    fuerzas de barra y las reacciones que sí existen.
    """

    incognitas: tuple
    """Nombres de las columnas, en el orden de ``resolver``."""

    ecuaciones: tuple
    """Tupla de ``EcuacionNudo``."""

    texto: str
    """Sistema escrito, una ecuación por línea."""


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

    TIPOS_APOYO = ("fijo", "movil", "movil_pared")
    """Pin (Rx, Ry), rodillo en piso (Ry) y rodillo en pared (Rx)."""

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
            ``(nudo, tipo)`` con ``tipo`` igual a ``"fijo"``, ``"movil"``
            (piso, solo Ry) o ``"movil_pared"`` (pared, solo Rx).
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
        """Agrega un apoyo en un nudo.

        Parameters
        ----------
        nudo : int
        tipo : {"fijo", "movil", "movil_pared"}
            ``fijo`` aporta Rx y Ry. ``movil`` es un rodillo sobre piso
            horizontal (solo Ry). ``movil_pared`` es un rodillo sobre pared
            vertical (solo Rx).

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

    def definir_apoyos(self, nudo_fijo, nudo_movil, tipo_movil="movil"):
        """Deja exactamente un apoyo fijo y un móvil en nudos existentes.

        Parameters
        ----------
        nudo_fijo, nudo_movil : int
            Deben ser nudos distintos. El fijo aporta Rx y Ry.
        tipo_movil : {"movil", "movil_pared"}, optional
            ``movil`` es rodillo en piso (solo Ry). ``movil_pared`` es
            rodillo en pared vertical (solo Rx). Por defecto, piso.

        Raises
        ------
        ValueError
            Nudo inexistente, ambos ids iguales o tipo de móvil ilegal.
        """
        nudo_fijo = self._exigir_nudo(nudo_fijo, "nudo_fijo")
        nudo_movil = self._exigir_nudo(nudo_movil, "nudo_movil")
        if nudo_fijo == nudo_movil:
            raise ValueError(
                "El apoyo fijo y el móvil deben estar en nudos distintos."
            )
        if tipo_movil not in ("movil", "movil_pared"):
            raise ValueError(
                "El apoyo móvil debe ser 'movil' (piso, Ry) o "
                "'movil_pared' (pared, Rx); "
                f"se recibió {tipo_movil!r}."
            )
        self._apoyos = {nudo_fijo: "fijo", nudo_movil: tipo_movil}

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

        a_mat, b_vec, columnas = self._matriz()
        try:
            x = np.linalg.solve(a_mat, b_vec)
        except np.linalg.LinAlgError as exc:
            raise ValueError(
                "El sistema de equilibrio es singular "
                "(geometría degenerada o apoyos mal colocados)."
                + self._pista_singular()
            ) from exc

        fuerzas = []
        rx_ry = {nudo: [0.0, 0.0] for nudo in self._apoyos}
        for col, (_nombre, tipo, payload) in enumerate(columnas):
            if tipo == "barra":
                barra, nudo_i, nudo_j = payload
                fuerzas.append(
                    self._fuerza_barra(barra, nudo_i, nudo_j, float(x[col]))
                )
            elif tipo == "rx":
                rx_ry[payload][0] = float(x[col])
            else:
                rx_ry[payload][1] = float(x[col])
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

    def ecuaciones(self):
        """Escribe el sistema ΣFx = 0 y ΣFy = 0 de cada nudo.

        No sustituye la solución. El convenio es el del solver: N > 0 es
        tensión (la barra tira de cada nudo hacia el otro extremo) y la
        carga entra con su signo (fy > 0 hacia arriba).

        Returns
        -------
        SistemaEcuaciones

        Raises
        ------
        ValueError
            Si no hay nudos o alguna barra tiene longitud 0.
        """
        if not self._nodos:
            raise ValueError("La armadura no tiene nudos.")
        a_mat, _b_vec, columnas = self._matriz()
        nombres = tuple(nombre for nombre, _tipo, _payload in columnas)
        nudos = sorted(self._nodos)
        ecuaciones = []
        for k, nudo in enumerate(nudos):
            fx, fy = self._carga(nudo)
            for eje, carga, fila in (("x", fx, 2 * k), ("y", fy, 2 * k + 1)):
                coeficientes = tuple(float(a_mat[fila, col]) for col in range(a_mat.shape[1]))
                texto = self._texto_ecuacion(coeficientes, nombres, carga)
                ecuaciones.append(
                    EcuacionNudo(
                        nudo=nudo,
                        eje=eje,
                        texto=texto,
                        coeficientes=coeficientes,
                        carga=carga,
                    )
                )
        lineas = [
            "Convenio: N > 0 es tensión (la barra tira de cada nudo hacia el otro extremo).",
            "Incógnitas: " + ", ".join(nombres) if nombres else "Incógnitas: (ninguna)",
            "",
        ]
        for ecuacion in ecuaciones:
            lineas.append(f"Nudo {ecuacion.nudo}, ΣF{ecuacion.eje}:  {ecuacion.texto}")
        lineas.append("")
        lineas.append(
            "Esas filas son el sistema A x = b. "
            "La carga está en el lado izquierdo, con su signo."
        )
        return SistemaEcuaciones(
            incognitas=nombres,
            ecuaciones=tuple(ecuaciones),
            texto="\n".join(lineas),
        )

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
            elif tipo_apoyo == "movil_pared":
                self._dibujar_apoyo_pared(ax, x, y, span, Circle, Polygon)

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
                ax,
                x,
                y,
                fx,
                fy,
                span,
                f_max,
                self.COLOR_CARGA,
                hacia_nudo=True,
                etiqueta=f"{math.hypot(fx, fy):.1f} kN",
            )
            hubo_carga = True
        if hubo_carga:
            ax.plot([], [], color=self.COLOR_CARGA, lw=1.8, label="carga")

        hubo_reaccion = False
        for rec in resultado.reacciones:
            if math.hypot(rec.rx, rec.ry) <= self.EPS_FUERZA_NULA:
                continue
            x, y = self._nodos[rec.nudo]
            tipo_apoyo = self._apoyos.get(rec.nudo, "fijo")
            partes = []
            if tipo_apoyo in ("fijo", "movil_pared"):
                partes.append(f"Rx {rec.rx:.1f}")
            if tipo_apoyo in ("fijo", "movil"):
                partes.append(f"Ry {rec.ry:.1f}")
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
                etiqueta="\n".join(partes),
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
        margen = 0.62 * span
        ax.set_xlim(min(xs) - margen, max(xs) + margen)
        ax.set_ylim(min(ys) - margen, max(ys) + margen)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.92)
        return fig

    def graficar_plano(self):
        """Dibuja la geometría actual, sin resolver el equilibrio.

        Muestra nudos, barras con su longitud, apoyos y cargas sobre los
        ejes x e y. Sirve para ver la armadura mientras se está armando,
        aunque todavía no sea isostática.

        Returns
        -------
        matplotlib.figure.Figure

        Raises
        ------
        ValueError
            Si no hay nudos.
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, Polygon

        if not self._nodos:
            raise ValueError("La armadura no tiene nudos.")

        span = self._span_dibujo()
        fig, ax = plt.subplots(figsize=(6.4, 6.2), layout="constrained")
        color_barra = "#3D5A80"

        for barra_id, (nudo_i, nudo_j) in self._barras.items():
            x_i, y_i = self._nodos[nudo_i]
            x_j, y_j = self._nodos[nudo_j]
            ax.plot(
                [x_i, x_j],
                [y_i, y_j],
                color=color_barra,
                linewidth=2.6,
                solid_capstyle="round",
                zorder=2,
            )
            largo = self._longitud_entre(nudo_i, nudo_j)
            mx, my = (x_i + x_j) / 2.0, (y_i + y_j) / 2.0
            dx, dy = x_j - x_i, y_j - y_i
            hipot = largo or 1.0
            nx, ny = -dy / hipot, dx / hipot
            off = 0.05 * span
            ax.text(
                mx + off * nx,
                my + off * ny,
                f"{barra_id}\n{largo:.2f} m",
                ha="center",
                va="center",
                fontsize=8,
                color="#1C2333",
                zorder=4,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.88),
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
                y + 1.8 * radio_nudo,
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
            elif tipo_apoyo == "movil_pared":
                self._dibujar_apoyo_pared(ax, x, y, span, Circle, Polygon)

        cargas = [
            (nudo, fx, fy)
            for nudo, (fx, fy) in self._cargas.items()
            if math.hypot(fx, fy) > self.EPS_FUERZA_NULA
        ]
        f_max = max((math.hypot(fx, fy) for _nudo, fx, fy in cargas), default=1.0)
        if f_max <= 0.0:
            f_max = 1.0
        for nudo, fx, fy in cargas:
            x, y = self._nodos[nudo]
            self._flecha(
                ax,
                x,
                y,
                fx,
                fy,
                span,
                f_max,
                self.COLOR_CARGA,
                hacia_nudo=True,
                etiqueta=f"{math.hypot(fx, fy):.1f} kN",
            )
        if cargas:
            ax.plot([], [], color=self.COLOR_CARGA, lw=1.8, label="carga")
            ax.legend(loc="upper right", fontsize=8, framealpha=0.92)

        ax.axhline(0.0, color="#C5CDD6", lw=0.8, zorder=0)
        ax.axvline(0.0, color="#C5CDD6", lw=0.8, zorder=0)
        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_title("Plano de la armadura")
        ax.grid(True, alpha=0.28)
        xs = [xy[0] for xy in self._nodos.values()]
        ys = [xy[1] for xy in self._nodos.values()]
        margen = 0.62 * span
        ax.set_xlim(min(xs) - margen, max(xs) + margen)
        ax.set_ylim(min(ys) - margen, max(ys) + margen)
        return fig

    def graficar_nudo(self, nudo, resultado=None):
        """Dibuja el cuerpo libre de un nudo.

        Cada barra sale del nudo en el sentido supuesto de tensión (la barra
        tira hacia el otro extremo). Si se pasa el resultado, el rótulo lleva
        la fuerza ya calculada y el color de tensión o compresión. Las
        reacciones se dibujan en su sentido positivo (Rx hacia +x, Ry hacia +y).

        Parameters
        ----------
        nudo : int
        resultado : ResultadoArmadura, optional

        Returns
        -------
        matplotlib.figure.Figure

        Raises
        ------
        ValueError
            Nudo inexistente o ``resultado`` de otro tipo.
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle

        nudo = self._exigir_nudo(nudo, "nudo")
        if resultado is not None and not isinstance(resultado, ResultadoArmadura):
            raise ValueError(
                "resultado debe ser un ResultadoArmadura; "
                f"se recibió {type(resultado)!r}."
            )
        fuerzas = {}
        reacciones = {}
        if resultado is not None:
            fuerzas = {barra.id: barra for barra in resultado.fuerzas}
            reacciones = {item.nudo: item for item in resultado.reacciones}

        fig, ax = plt.subplots(figsize=(4.6, 4.4), layout="constrained")
        ax.add_patch(
            Circle(
                (0.0, 0.0),
                0.07,
                facecolor="#F6F3EC",
                edgecolor="#0B1F3A",
                linewidth=1.4,
                zorder=5,
            )
        )
        ax.text(
            0.0,
            0.14,
            str(nudo),
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color="#0B1F3A",
            zorder=6,
        )

        for barra, (nudo_i, nudo_j) in self._barras.items():
            if nudo == nudo_i:
                ux, uy = self._unitario(nudo_i, nudo_j)
            elif nudo == nudo_j:
                ux, uy = self._unitario(nudo_j, nudo_i)
            else:
                continue
            dato = fuerzas.get(barra)
            color = self._color_tipo(dato.tipo) if dato is not None else "#0B1F3A"
            ax.annotate(
                "",
                xy=(ux, uy),
                xytext=(0.0, 0.0),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=color,
                    lw=1.8,
                    mutation_scale=12,
                ),
                zorder=4,
            )
            texto = f"N_{barra}"
            if dato is not None:
                texto = f"N_{barra}\n{dato.fuerza:.1f} kN"
            ax.text(
                ux * 1.22 - uy * 0.32,
                uy * 1.22 + ux * 0.32,
                texto,
                ha="center",
                va="center",
                fontsize=8,
                color=color,
                zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92),
            )

        tipo = self._apoyos.get(nudo)
        rec = reacciones.get(nudo)
        if tipo in ("fijo", "movil_pared"):
            texto = f"Rx_{nudo}"
            if rec is not None:
                texto = f"Rx_{nudo}\n{rec.rx:.1f} kN"
            self._flecha_cuerpo_libre(ax, 0.62, 0.0, self.COLOR_REACCION, texto, 0.0, -0.34)
        if tipo in ("fijo", "movil"):
            texto = f"Ry_{nudo}"
            if rec is not None:
                texto = f"Ry_{nudo}\n{rec.ry:.1f} kN"
            self._flecha_cuerpo_libre(ax, 0.0, 0.62, self.COLOR_REACCION, texto, -0.42, 0.0)

        fx, fy = self._carga(nudo)
        if math.hypot(fx, fy) > self.EPS_FUERZA_NULA:
            mag = math.hypot(fx, fy)
            ux, uy = fx / mag, fy / mag
            ax.annotate(
                "",
                xy=(0.0, 0.0),
                xytext=(-ux, -uy),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=self.COLOR_CARGA,
                    lw=1.8,
                    mutation_scale=12,
                ),
                zorder=4,
            )
            ax.text(
                -ux * 1.22,
                -uy * 1.22,
                f"{fx:.1f}, {fy:.1f} kN",
                ha="center",
                va="center",
                fontsize=8,
                color=self.COLOR_CARGA,
                zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92),
            )

        ax.set_aspect("equal")
        ax.set_xlim(-2.15, 2.15)
        ax.set_ylim(-2.05, 2.15)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(f"Cuerpo libre del nudo {nudo}")
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

    def _flecha(self, ax, x, y, fx, fy, span, f_max, color, hacia_nudo, etiqueta=None):
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
        if etiqueta:
            if hacia_nudo:
                px, py = cola
            else:
                px = cabeza[0] + 0.18 * (cabeza[0] - cola[0])
                py = cabeza[1] + 0.18 * (cabeza[1] - cola[1])
            ax.text(
                px,
                py,
                etiqueta,
                ha="center",
                va="center",
                fontsize=8,
                color=color,
                zorder=8,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9),
            )

    def _flecha_cuerpo_libre(self, ax, dx, dy, color, etiqueta, ox, oy):
        ax.annotate(
            "",
            xy=(dx, dy),
            xytext=(0.0, 0.0),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=1.8,
                mutation_scale=12,
            ),
            zorder=4,
        )
        ax.text(
            dx + ox,
            dy + oy,
            etiqueta,
            ha="center",
            va="center",
            fontsize=8,
            color=color,
            zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92),
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

    def _dibujar_apoyo_pared(self, ax, x, y, span, circle_cls, polygon_cls):
        t = 0.08 * span
        triangulo = polygon_cls(
            [(x, y), (x + 0.75 * t, y - 0.55 * t), (x + 0.75 * t, y + 0.55 * t)],
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
                    (x + 0.75 * t + radio, y + signo * 0.28 * t),
                    radio,
                    facecolor="#F6F3EC",
                    edgecolor="#0B1F3A",
                    linewidth=1.0,
                    zorder=3,
                )
            )
        x_muro = x + 0.75 * t + 2.6 * radio
        ax.plot(
            [x_muro, x_muro],
            [y - 1.15 * t, y + 1.15 * t],
            color="#0B1F3A",
            lw=1.4,
            zorder=3,
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

    def _columnas(self):
        """Incógnitas en el orden de ``resolver``: barras, luego reacciones."""
        columnas = []
        for barra, (nudo_i, nudo_j) in self._barras.items():
            columnas.append((f"N_{barra}", "barra", (barra, nudo_i, nudo_j)))
        for nudo in sorted(self._apoyos):
            tipo = self._apoyos[nudo]
            if tipo == "fijo":
                columnas.append((f"Rx_{nudo}", "rx", nudo))
                columnas.append((f"Ry_{nudo}", "ry", nudo))
            elif tipo == "movil_pared":
                columnas.append((f"Rx_{nudo}", "rx", nudo))
            elif tipo == "movil":
                columnas.append((f"Ry_{nudo}", "ry", nudo))
            else:
                raise ValueError(
                    f"Tipo de apoyo desconocido en el nudo {nudo}: {tipo!r}."
                )
        return columnas

    def _matriz(self):
        """Arma A y b de A x = −F. Las filas van nudo a nudo, ΣFx y luego ΣFy."""
        nudos = sorted(self._nodos)
        fila = {nudo: 2 * k for k, nudo in enumerate(nudos)}
        columnas = self._columnas()
        a_mat = np.zeros((2 * len(nudos), len(columnas)), dtype=float)
        b_vec = np.zeros(2 * len(nudos), dtype=float)
        for nudo in nudos:
            fx, fy = self._carga(nudo)
            b_vec[fila[nudo]] = -fx
            b_vec[fila[nudo] + 1] = -fy
        for col, (_nombre, tipo, payload) in enumerate(columnas):
            if tipo == "barra":
                _barra, nudo_i, nudo_j = payload
                ux, uy = self._unitario(nudo_i, nudo_j)
                a_mat[fila[nudo_i], col] += ux
                a_mat[fila[nudo_i] + 1, col] += uy
                a_mat[fila[nudo_j], col] += -ux
                a_mat[fila[nudo_j] + 1, col] += -uy
            elif tipo == "rx":
                a_mat[fila[payload], col] = 1.0
            else:
                a_mat[fila[payload] + 1, col] = 1.0
        return a_mat, b_vec, columnas

    def _pista_singular(self):
        fijos = [nudo for nudo, tipo in self._apoyos.items() if tipo == "fijo"]
        paredes = [
            nudo for nudo, tipo in self._apoyos.items() if tipo == "movil_pared"
        ]
        for pared in paredes:
            y_pared = self._nodos[pared][1]
            for fijo in fijos:
                if abs(y_pared - self._nodos[fijo][1]) <= 1e-9:
                    return (
                        " El rodillo de pared está a la misma altura que el "
                        "apoyo fijo: su reacción horizontal pasa por ese punto "
                        "y el equilibrio no puede separarla. Sube o baja el "
                        "nudo del rodillo."
                    )
        return ""

    def _texto_ecuacion(self, coeficientes, nombres, carga):
        piezas = []
        for coef, nombre in zip(coeficientes, nombres):
            pieza = _pieza_ecuacion(coef, nombre, not piezas)
            if pieza is not None:
                piezas.append(pieza)
        carga_txt = _pieza_ecuacion(carga, "", not piezas)
        if carga_txt is not None:
            piezas.append(carga_txt)
        if not piezas:
            return "0 = 0"
        return " ".join(piezas) + " = 0"

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
