"""Plano con el que se arma una armadura propia, clic a clic.

No calcula fuerzas. Streamlit lo usa al lado de las tablas. La librería
no importa este módulo.
"""

from __future__ import annotations

import math

PASO_MALLA = 0.5
MARGEN_MALLA = 4.0


def ajustar_malla(valor):
    """Acerca una coordenada al múltiplo de 0,5 m más cercano."""
    return round(round(float(valor) / PASO_MALLA) * PASO_MALLA, 10)


def _entero(valor):
    if valor is None or valor == "":
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if numero != numero or not numero.is_integer():
        return None
    return int(numero)


def _real(valor, defecto=0.0):
    if valor is None or valor == "":
        return defecto
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return defecto
    if numero != numero:
        return defecto
    return numero


def ids_nodos(nodos):
    ids = []
    for fila in nodos:
        nudo = _entero(fila.get("nudo"))
        if nudo is not None and nudo not in ids:
            ids.append(nudo)
    return ids


def siguiente_nudo(nodos):
    usados = set(ids_nodos(nodos))
    nudo = 0
    while nudo in usados:
        nudo += 1
    return nudo


def siguiente_barra(barras):
    usadas = {str(fila.get("barra") or "").strip() for fila in barras}
    numero = 1
    while f"B{numero}" in usadas:
        numero += 1
    return f"B{numero}"


def _par_barra(fila):
    return _entero(fila.get("nudo i")), _entero(fila.get("nudo j"))


def hay_barra(barras, nudo_i, nudo_j):
    buscado = {nudo_i, nudo_j}
    for fila in barras:
        extremo_i, extremo_j = _par_barra(fila)
        if extremo_i is None or extremo_j is None:
            continue
        if {extremo_i, extremo_j} == buscado:
            return True
    return False


def _ocupado(nodos, x, y):
    for fila in nodos:
        if _entero(fila.get("nudo")) is None:
            continue
        if (
            abs(_real(fila.get("x (m)")) - x) < 1e-6
            and abs(_real(fila.get("y (m)")) - y) < 1e-6
        ):
            return True
    return False


def _cargas_por_nudo(cargas):
    mapa = {}
    for fila in cargas:
        nudo = _entero(fila.get("nudo"))
        if nudo is None:
            continue
        mapa[nudo] = {
            "nudo": nudo,
            "horizontal →+ (kN)": _real(fila.get("horizontal →+ (kN)")),
            "vertical hacia abajo (kN)": _real(fila.get("vertical hacia abajo (kN)")),
        }
    return mapa


def clasificar_punto(customdata):
    """Devuelve ``("nudo", id)`` o ``("rejilla", None)``."""
    if isinstance(customdata, (list, tuple)):
        customdata = customdata[0] if customdata else None
    texto = "" if customdata is None else str(customdata)
    if texto.startswith("nudo:"):
        return "nudo", _entero(texto.split(":", 1)[1])
    return "rejilla", None


def leer_puntos(estado):
    """Puntos elegidos en el gráfico de Plotly."""
    if not estado:
        return []
    seleccion = estado.get("selection") if hasattr(estado, "get") else None
    if not seleccion:
        return []
    puntos = seleccion.get("points") if hasattr(seleccion, "get") else None
    return list(puntos or [])


def elegir_punto(puntos, modo, origen):
    """Elige el punto que corresponde al clic nuevo.

    Si la selección todavía incluye el primer extremo de una barra, usa el
    otro nudo. Si hay un nudo y un punto de la cuadrícula, usa el nudo.
    """
    if not puntos:
        return None
    if modo == "Barra" and origen is not None:
        for punto in reversed(puntos):
            clase, nudo = clasificar_punto(punto.get("customdata"))
            if clase == "nudo" and nudo != origen:
                return punto
    for punto in reversed(puntos):
        clase, _nudo = clasificar_punto(punto.get("customdata"))
        if clase == "nudo":
            return punto
    return puntos[-1]


def firma_seleccion(punto, modo, horizontal, vertical_abajo, apoyo):
    if not punto:
        return None
    return (
        modo,
        str(punto.get("customdata")),
        round(_real(punto.get("x")), 4),
        round(_real(punto.get("y")), 4),
        round(float(horizontal), 4),
        round(float(vertical_abajo), 4),
        apoyo,
    )


def efecto_clic(
    modo,
    customdata,
    x,
    y,
    nodos,
    barras,
    fijo,
    movil,
    tipo_movil,
    cargas,
    origen,
    horizontal,
    vertical_abajo,
    apoyo,
):
    """Aplica un clic del plano sobre las tablas.

    No modifica las listas que recibe. ``cambio`` es verdadero solo cuando
    hay que volver a dibujar las tablas.
    """
    salida = {
        "cambio": False,
        "nodos": list(nodos),
        "barras": list(barras),
        "fijo": fijo,
        "movil": movil,
        "tipo_movil": tipo_movil or "movil",
        "cargas": list(cargas),
        "origen": origen,
        "aviso": "",
    }
    clase, nudo = clasificar_punto(customdata)
    ids = ids_nodos(salida["nodos"])

    if modo == "Nudo":
        if clase != "rejilla":
            salida["aviso"] = "Ese punto ya es un nudo. La posición exacta se afina en la tabla."
            return salida
        x_m = ajustar_malla(x)
        y_m = ajustar_malla(y)
        if _ocupado(salida["nodos"], x_m, y_m):
            salida["aviso"] = "Ya hay un nudo en ese cruce de la cuadrícula."
            return salida
        nuevo = siguiente_nudo(salida["nodos"])
        salida["nodos"] = salida["nodos"] + [
            {"nudo": nuevo, "x (m)": x_m, "y (m)": y_m}
        ]
        salida["cambio"] = True
        salida["aviso"] = f"Nudo {nuevo} en ({_fmt(x_m)}, {_fmt(y_m)}) m."
        return salida

    if clase != "nudo" or nudo not in ids:
        salida["aviso"] = "Pulsa un nudo del plano, no un punto vacío de la cuadrícula."
        return salida

    if modo == "Barra":
        if origen is None:
            salida["origen"] = nudo
            salida["aviso"] = f"Primer extremo: nudo {nudo}. Pulsa el otro nudo."
            return salida
        if origen == nudo:
            salida["aviso"] = "Elige un nudo distinto para el otro extremo."
            return salida
        if origen not in ids:
            salida["origen"] = nudo
            salida["aviso"] = f"El extremo anterior ya no está. Primer extremo: nudo {nudo}."
            return salida
        if hay_barra(salida["barras"], origen, nudo):
            salida["origen"] = None
            salida["aviso"] = f"Ya existe una barra entre {origen} y {nudo}."
            return salida
        nombre = siguiente_barra(salida["barras"])
        salida["barras"] = salida["barras"] + [
            {"barra": nombre, "nudo i": origen, "nudo j": nudo}
        ]
        salida["origen"] = None
        salida["cambio"] = True
        salida["aviso"] = f"Barra {nombre} entre {origen} y {nudo}."
        return salida

    if modo == "Apoyo":
        if apoyo == "fijo":
            if nudo == movil:
                salida["aviso"] = "Ese nudo ya es el apoyo móvil. Elige otro para el fijo."
                return salida
            if nudo == fijo:
                salida["aviso"] = f"El nudo {nudo} ya es el apoyo fijo."
                return salida
            salida["fijo"] = nudo
            salida["cambio"] = True
            salida["aviso"] = f"Apoyo fijo en el nudo {nudo}."
            return salida
        if apoyo not in ("movil", "movil_pared"):
            salida["aviso"] = "Elige si el móvil va en el piso o en la pared."
            return salida
        if nudo == fijo:
            salida["aviso"] = "Ese nudo ya es el apoyo fijo. Elige otro para el móvil."
            return salida
        if nudo == movil and (tipo_movil or "movil") == apoyo:
            salida["aviso"] = f"El nudo {nudo} ya tiene ese apoyo móvil."
            return salida
        salida["movil"] = nudo
        salida["tipo_movil"] = apoyo
        salida["cambio"] = True
        donde = "la pared" if apoyo == "movil_pared" else "el piso"
        salida["aviso"] = f"Apoyo móvil en {donde}, nudo {nudo}."
        return salida

    if modo == "Carga":
        mapa = _cargas_por_nudo(salida["cargas"])
        mapa[nudo] = {
            "nudo": nudo,
            "horizontal →+ (kN)": float(horizontal),
            "vertical hacia abajo (kN)": float(vertical_abajo),
        }
        salida["cargas"] = [mapa[clave] for clave in sorted(mapa)]
        salida["cambio"] = True
        salida["aviso"] = (
            f"Carga en el nudo {nudo}: "
            f"{_fmt(horizontal)} kN horizontal, "
            f"{_fmt(vertical_abajo)} kN hacia abajo."
        )
        return salida

    salida["aviso"] = "Elige qué quieres colocar: nudo, barra, apoyo o carga."
    return salida


def _fmt(valor):
    numero = float(valor)
    if abs(numero - round(numero)) < 5e-4:
        return str(int(round(numero)))
    return f"{numero:.1f}"


def limites_malla(nodos):
    """Rectángulo de la cuadrícula, en múltiplos de 0,5 m.

    Deja cuatro metros libres alrededor del nudo más extremo, en las
    cuatro direcciones, para poder seguir colocando nudos.
    """
    xs = [_real(fila.get("x (m)")) for fila in nodos if _entero(fila.get("nudo")) is not None]
    ys = [_real(fila.get("y (m)")) for fila in nodos if _entero(fila.get("nudo")) is not None]
    if not xs:
        return -2.0, 10.0, -2.0, 8.0
    return _encuadrar(
        min(xs) - MARGEN_MALLA,
        max(xs) + MARGEN_MALLA,
        min(ys) - MARGEN_MALLA,
        max(ys) + MARGEN_MALLA,
    )


def _encuadrar(x0, x1, y0, y1):
    return (
        ajustar_malla(math.floor(x0 / PASO_MALLA) * PASO_MALLA),
        ajustar_malla(math.ceil(x1 / PASO_MALLA) * PASO_MALLA),
        ajustar_malla(math.floor(y0 / PASO_MALLA) * PASO_MALLA),
        ajustar_malla(math.ceil(y1 / PASO_MALLA) * PASO_MALLA),
    )


def puntos_malla(nodos):
    x0, x1, y0, y1 = limites_malla(nodos)
    xs = []
    ys = []
    x = x0
    while x <= x1 + 1e-9:
        y = y0
        while y <= y1 + 1e-9:
            xs.append(ajustar_malla(x))
            ys.append(ajustar_malla(y))
            y += PASO_MALLA
        x += PASO_MALLA
    return xs, ys


def figura_plano(armadura, origen=None, recibir_nudos=True):
    """Figura de Plotly: cuadrícula, barras, nudos, apoyos y cargas.

    Los puntos grises solo se pueden pulsar al colocar un nudo. En los
    demás modos los clics caen en los nudos, para no pedir un segundo clic.
    """
    import plotly.graph_objects as go

    nodos = () if armadura is None else armadura.snapshot_nodos()
    filas = [{"nudo": nudo, "x (m)": x, "y (m)": y} for nudo, x, y in nodos]
    ocupados = {(ajustar_malla(x), ajustar_malla(y)) for _nudo, x, y in nodos}
    figura = go.Figure()
    if recibir_nudos:
        malla_x, malla_y = puntos_malla(filas)
        libres_x = []
        libres_y = []
        for x, y in zip(malla_x, malla_y):
            if (x, y) in ocupados:
                continue
            libres_x.append(x)
            libres_y.append(y)
        figura.add_trace(
            go.Scatter(
                x=libres_x,
                y=libres_y,
                mode="markers",
                name="cuadrícula 0,5 m",
                marker={"size": 7, "color": "#C5CED6"},
                customdata=["rejilla"] * len(libres_x),
                hovertemplate="x=%{x:.1f} m<br>y=%{y:.1f} m<extra></extra>",
            )
        )
    if armadura is not None:
        for barra, nudo_i, nudo_j in armadura.snapshot_barras():
            xi, yi = _xy(armadura, nudo_i)
            xj, yj = _xy(armadura, nudo_j)
            figura.add_shape(
                type="line",
                x0=xi,
                y0=yi,
                x1=xj,
                y1=yj,
                line={"color": "#3D5A80", "width": 3},
            )
            largo = armadura.longitud(barra)
            figura.add_annotation(
                x=(xi + xj) / 2.0,
                y=(yi + yj) / 2.0,
                text=f"{barra}<br>{largo:.2f} m",
                showarrow=False,
                bgcolor="white",
                font={"size": 11, "color": "#1C2333"},
            )
        tam = _tamano_simbolo(nodos)
        for nudo, tipo in armadura.snapshot_apoyos():
            x, y = _xy(armadura, nudo)
            _dibujar_apoyo(figura, x, y, tipo, tam)
        for nudo, fx, fy in armadura.snapshot_cargas():
            if math.hypot(fx, fy) <= 1e-8:
                continue
            x, y = _xy(armadura, nudo)
            magnitud = math.hypot(fx, fy)
            ux, uy = fx / magnitud, fy / magnitud
            figura.add_annotation(
                x=x,
                y=y,
                ax=x - ux * 0.9,
                ay=y - uy * 0.9,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowcolor="#A83226",
                text=f"{magnitud:.1f} kN",
                font={"color": "#A83226", "size": 11},
            )
    if nodos:
        colores = []
        for nudo, _x, _y in nodos:
            colores.append("#C9A227" if nudo == origen else "#F6F3EC")
        figura.add_trace(
            go.Scatter(
                x=[x for _nudo, x, _y in nodos],
                y=[y for _nudo, _x, y in nodos],
                mode="markers+text",
                name="nudos",
                text=[str(nudo) for nudo, _x, _y in nodos],
                textposition="top center",
                marker={
                    "size": 22,
                    "color": colores,
                    "line": {"width": 2, "color": "#0B1F3A"},
                },
                customdata=[f"nudo:{nudo}" for nudo, _x, _y in nodos],
                hovertemplate="nudo %{text}<br>x=%{x:.2f} m<br>y=%{y:.2f} m<extra></extra>",
            )
        )
    x0, x1, y0, y1 = limites_malla(filas)
    holgura = 0.35
    figura.update_layout(
        title="Plano de la armadura",
        xaxis_title="x (m)",
        yaxis_title="y (m)",
        xaxis={"range": [x0 - holgura, x1 + holgura], "constrain": "domain"},
        yaxis={
            "range": [y0 - holgura, y1 + holgura],
            "scaleanchor": "x",
            "scaleratio": 1,
            "constrain": "domain",
        },
        legend={"orientation": "h", "y": -0.15},
        margin={"l": 40, "r": 20, "t": 48, "b": 40},
        paper_bgcolor="white",
        plot_bgcolor="#F7F5F0",
        height=560,
        uirevision=f"malla-{x0}-{x1}-{y0}-{y1}",
    )
    figura.update_xaxes(gridcolor="#E2E0D8", zerolinecolor="#B7B3A8")
    figura.update_yaxes(gridcolor="#E2E0D8", zerolinecolor="#B7B3A8")
    return figura


def _tamano_simbolo(nodos):
    if len(nodos) < 2:
        return 0.42
    xs = [x for _nudo, x, _y in nodos]
    ys = [y for _nudo, _x, y in nodos]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    return max(0.45, min(0.72, 0.12 * span))


def _dibujar_apoyo(figura, x, y, tipo, tam):
    """Triángulo de apoyo, suelo o pared, en coordenadas del plano."""
    oro = "#C9A227"
    borde = "#0B1F3A"
    if tipo == "movil_pared":
        figura.add_shape(
            type="path",
            path=(
                f"M {x + 0.28 * tam} {y} "
                f"L {x + 1.15 * tam} {y - 0.62 * tam} "
                f"L {x + 1.15 * tam} {y + 0.62 * tam} Z"
            ),
            fillcolor=oro,
            line={"color": borde, "width": 1.5},
        )
        radio = 0.22 * tam
        for signo in (-1, 1):
            cx = x + 1.42 * tam
            cy = y + signo * 0.32 * tam
            figura.add_shape(
                type="circle",
                x0=cx - radio,
                y0=cy - radio,
                x1=cx + radio,
                y1=cy + radio,
                fillcolor="white",
                line={"color": borde, "width": 1.4},
            )
        muro = x + 1.72 * tam
        figura.add_shape(
            type="line",
            x0=muro,
            y0=y - 1.05 * tam,
            x1=muro,
            y1=y + 1.05 * tam,
            line={"color": borde, "width": 2.4},
        )
        figura.add_annotation(
            x=muro,
            y=y - 1.35 * tam,
            text="pared",
            showarrow=False,
            bgcolor="white",
            font={"size": 12, "color": borde},
        )
        return
    punta = y - 0.28 * tam
    base = y - 1.25 * tam
    figura.add_shape(
        type="path",
        path=f"M {x} {punta} L {x - 0.78 * tam} {base} L {x + 0.78 * tam} {base} Z",
        fillcolor=oro,
        line={"color": borde, "width": 1.5},
    )
    figura.add_shape(
        type="line",
        x0=x - 1.05 * tam,
        y0=base,
        x1=x + 1.05 * tam,
        y1=base,
        line={"color": borde, "width": 2.4},
    )
    if tipo == "movil":
        radio = 0.22 * tam
        for signo in (-1, 1):
            cx = x + signo * 0.36 * tam
            cy = base - radio
            figura.add_shape(
                type="circle",
                x0=cx - radio,
                y0=cy - radio,
                x1=cx + radio,
                y1=cy + radio,
                fillcolor="white",
                line={"color": borde, "width": 1.4},
            )
        etiqueta = "piso"
        y_etiq = base - 0.62 * tam
    else:
        for dx in (-0.72, -0.36, 0.0, 0.36, 0.72):
            figura.add_shape(
                type="line",
                x0=x + dx * tam,
                y0=base,
                x1=x + dx * tam - 0.22 * tam,
                y1=base - 0.28 * tam,
                line={"color": borde, "width": 1.5},
            )
        etiqueta = "fijo"
        y_etiq = base - 0.5 * tam
    figura.add_annotation(
        x=x,
        y=y_etiq,
        text=etiqueta,
        showarrow=False,
        bgcolor="white",
        font={"size": 12, "color": borde},
    )


def _xy(armadura, nudo):
    for identificador, x, y in armadura.snapshot_nodos():
        if identificador == nudo:
            return x, y
    raise KeyError(nudo)
