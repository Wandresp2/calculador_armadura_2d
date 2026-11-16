"""
streamlit_app.py — GUI web del analizador de armaduras 2D.

Solo CONSUME la API pública de ``armadura_2d_andresdperezc``. El paquete no
importa Streamlit: se puede reemplazar esta app por un notebook o un
script sin tocar core.py.

Preparación (una vez, desde la carpeta del proyecto)::

    python -m venv .venv
    .venv\\Scripts\\Activate.ps1
    python -m pip install -e ".[gui]"

Ejecutar::

    streamlit run streamlit_app.py
"""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import streamlit as st

try:
    from armadura_2d_andresdperezc import Armadura2D
except ImportError:
    raise SystemExit(
        "No se encontró la librería 'armadura_2d_andresdperezc'.\n"
        "Desde la carpeta del proyecto, con el entorno virtual activo, ejecute:\n"
        '  python -m pip install -e ".[gui]"'
    ) from None

PRESETS = {
    "Triángulo": Armadura2D.preset_triangulo,
    "Warren": Armadura2D.preset_warren,
    "Pratt": Armadura2D.preset_pratt,
    "Howe": Armadura2D.preset_howe,
}

TIPOS_MOVIL = {
    "Piso horizontal (solo Ry)": "movil",
    "Pared vertical (solo Rx)": "movil_pared",
}

BASE_MIN, BASE_MAX = 1.0, 20.0
ALTURA_MIN, ALTURA_MAX = 0.5, 10.0
CARGA_MAX = 200.0

_TIPO = {
    "tension": "tensión",
    "compresion": "compresión",
    "nula": "nula",
}


def _mostrar_figura(figura):
    st.pyplot(figura, clear_figure=True)
    plt.close(figura)


def _filas(editado):
    if hasattr(editado, "to_dict"):
        return editado.to_dict("records")
    return list(editado)


def _fabrica(nombre):
    return PRESETS[nombre]()


def _id_entero(valor):
    if valor is None or valor == "":
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(
            f"El identificador debe ser un entero; se recibió {valor!r}."
        ) from None
    if numero != numero:
        return None
    if not numero.is_integer():
        raise ValueError(
            f"El identificador debe ser un entero; se recibió {valor!r}."
        )
    return int(numero)


def _numero(valor, defecto=0.0):
    if valor is None or valor == "":
        return defecto
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"Se esperaba un número; se recibió {valor!r}.") from None
    if numero != numero:
        return defecto
    return numero


def _coords_escaladas(nombre, base, altura):
    armadura = _fabrica(nombre)
    base_ref = armadura.base_ref or 4.0
    altura_ref = armadura.altura_ref or 2.0
    fx = base / base_ref
    fy = altura / altura_ref
    return {
        nudo: (x * fx, y * fy)
        for nudo, x, y in armadura.snapshot_nodos()
    }


def _cargas_gui_por_defecto(nombre):
    armadura = _fabrica(nombre)
    ids = [nudo for nudo, _x, _y in armadura.snapshot_nodos()]
    mapa = {nudo: (fx, fy) for nudo, fx, fy in armadura.snapshot_cargas()}
    filas = []
    for nudo in ids:
        fx, fy = mapa.get(nudo, (0.0, 0.0))
        filas.append(
            {
                "nudo": nudo,
                "horizontal →+ (kN)": float(fx),
                "vertical hacia abajo (kN)": float(-fy),
            }
        )
    return filas


def _apoyos_por_defecto(nombre):
    armadura = _fabrica(nombre)
    fijo = movil = None
    tipo = "movil"
    for nudo, apoyo in armadura.snapshot_apoyos():
        if apoyo == "fijo":
            fijo = nudo
        else:
            movil = nudo
            tipo = apoyo
    return fijo, movil, tipo


def _fuentes_de(armadura):
    nodos = [
        {"nudo": nudo, "x (m)": x, "y (m)": y}
        for nudo, x, y in armadura.snapshot_nodos()
    ]
    barras = [
        {"barra": barra, "nudo i": i, "nudo j": j}
        for barra, i, j in armadura.snapshot_barras()
    ]
    mapa = {nudo: (fx, fy) for nudo, fx, fy in armadura.snapshot_cargas()}
    cargas = []
    for nudo, _x, _y in armadura.snapshot_nodos():
        fx, fy = mapa.get(nudo, (0.0, 0.0))
        cargas.append(
            {
                "nudo": nudo,
                "horizontal →+ (kN)": float(fx),
                "vertical hacia abajo (kN)": float(-fy),
            }
        )
    fijo, movil, tipo = None, None, "movil"
    for nudo, apoyo in armadura.snapshot_apoyos():
        if apoyo == "fijo":
            fijo = nudo
        else:
            movil = nudo
            tipo = apoyo
    return nodos, barras, cargas, fijo, movil, tipo


def _armar_preset(nombre, coords, nudo_fijo, nudo_movil, tipo_movil, filas_carga):
    armadura = _fabrica(nombre)
    armadura.reemplazar_coordenadas(coords)
    armadura.definir_apoyos(int(nudo_fijo), int(nudo_movil), tipo_movil)
    armadura.definir_cargas(_cargas_desde_filas(filas_carga))
    return armadura


def _cargas_desde_filas(filas_carga):
    cargas = []
    for fila in filas_carga:
        nudo = _id_entero(fila.get("nudo"))
        if nudo is None:
            continue
        fx = _numero(fila.get("horizontal →+ (kN)"))
        abajo = _numero(fila.get("vertical hacia abajo (kN)"))
        cargas.append((nudo, fx, -abajo))
    return cargas


def _armar_propia(filas_nodos, filas_barras, nudo_fijo, nudo_movil, tipo_movil, filas_carga):
    armadura = Armadura2D(nombre="Propia")
    vistos = set()
    for fila in filas_nodos:
        nudo = _id_entero(fila.get("nudo"))
        if nudo is None:
            continue
        if nudo in vistos:
            raise ValueError(f"El nudo {nudo} está repetido.")
        vistos.add(nudo)
        armadura.agregar_nodo(
            nudo, _numero(fila.get("x (m)")), _numero(fila.get("y (m)"))
        )
    if not vistos:
        raise ValueError("Agrega al menos un nudo con su posición.")
    usadas = set()
    for indice, fila in enumerate(filas_barras, start=1):
        nudo_i = _id_entero(fila.get("nudo i"))
        nudo_j = _id_entero(fila.get("nudo j"))
        if nudo_i is None or nudo_j is None:
            continue
        barra = str(fila.get("barra") or "").strip() or f"B{indice}"
        if barra in usadas:
            raise ValueError(f"La barra {barra!r} está repetida.")
        usadas.add(barra)
        armadura.agregar_barra(barra, nudo_i, nudo_j)
    armadura.definir_apoyos(int(nudo_fijo), int(nudo_movil), tipo_movil)
    armadura.definir_cargas(_cargas_desde_filas(filas_carga))
    return armadura


def _resolver(armadura):
    try:
        return armadura, armadura.resolver(), None
    except ValueError as exc:
        return armadura, None, str(exc)


def _columnas_carga():
    return {
        "nudo": st.column_config.NumberColumn(format="%d", disabled=True),
        "horizontal →+ (kN)": st.column_config.NumberColumn(
            min_value=-CARGA_MAX,
            max_value=CARGA_MAX,
            step=1.0,
            format="%.2f",
        ),
        "vertical hacia abajo (kN)": st.column_config.NumberColumn(
            min_value=-CARGA_MAX,
            max_value=CARGA_MAX,
            step=1.0,
            format="%.2f",
            help="Positivo hacia abajo. Un valor negativo empuja hacia arriba.",
        ),
    }


def _elegir_apoyos(ids, fijo_def, movil_def, tipo_def, clave):
    st.subheader("Apoyos")
    st.caption(
        "Hay un apoyo fijo y un apoyo móvil. "
        "El fijo no se mueve: aparecen Rx y Ry. "
        "El móvil en piso se desliza a izquierda y derecha: solo Ry. "
        "El móvil en pared se desliza arriba y abajo: solo Rx, "
        "y tiene que quedar más arriba o más abajo que el fijo."
    )
    c1, c2, c3 = st.columns(3)
    nudo_fijo = c1.selectbox(
        "Fijo (Rx y Ry)",
        ids,
        index=ids.index(fijo_def) if fijo_def in ids else 0,
        key=f"fijo_{clave}",
    )
    nudo_movil = c2.selectbox(
        "Móvil",
        ids,
        index=ids.index(movil_def) if movil_def in ids else min(1, len(ids) - 1),
        key=f"movil_{clave}",
    )
    etiquetas = list(TIPOS_MOVIL)
    tipo_inicial = etiquetas[0]
    for etiqueta, codigo in TIPOS_MOVIL.items():
        if codigo == tipo_def:
            tipo_inicial = etiqueta
    tipo_etiqueta = c3.selectbox(
        "Tipo de móvil",
        etiquetas,
        index=etiquetas.index(tipo_inicial),
        key=f"tipo_{clave}",
    )
    return nudo_fijo, nudo_movil, TIPOS_MOVIL[tipo_etiqueta]


def _tabla_cargas(filas, clave, fija=True):
    st.subheader("Cargas en los nudos")
    st.caption(
        "La horizontal positiva va hacia la derecha. "
        "La vertical positiva va hacia abajo. "
        "Un número negativo en la vertical empuja hacia arriba."
    )
    return st.data_editor(
        filas,
        hide_index=True,
        num_rows="fixed" if fija else "dynamic",
        disabled=["nudo"] if fija else [],
        key=clave,
        column_config=_columnas_carga(),
    )


def _bloque_precargada():
    nombre = st.radio(
        "Armadura precargada",
        list(PRESETS),
        horizontal=True,
    )
    prototipo = _fabrica(nombre)
    base_ref = float(prototipo.base_ref or 4.0)
    altura_ref = float(prototipo.altura_ref or 2.0)
    if st.session_state.get("preset_activo") != nombre:
        st.session_state.preset_activo = nombre
        st.session_state.base = base_ref
        st.session_state.altura = altura_ref

    fila = st.columns(2)
    with fila[0]:
        base = st.slider(
            "Base (m)",
            min_value=BASE_MIN,
            max_value=BASE_MAX,
            step=0.1,
            key="base",
        )
    with fila[1]:
        altura = st.slider(
            "Altura (m)",
            min_value=ALTURA_MIN,
            max_value=ALTURA_MAX,
            step=0.1,
            key="altura",
        )
    st.caption(
        "Los deslizadores escalan la armadura desde el origen. "
        "La tabla de nudos afina cada posición. Las barras no cambian: "
        "siguen uniendo los mismos nudos."
    )

    ids = [nudo for nudo, _x, _y in prototipo.snapshot_nodos()]
    coords_base = _coords_escaladas(nombre, base, altura)
    filas_nodos = [
        {"nudo": nudo, "x (m)": coords_base[nudo][0], "y (m)": coords_base[nudo][1]}
        for nudo in ids
    ]
    st.subheader("Nudos")
    nodos_edit = st.data_editor(
        filas_nodos,
        hide_index=True,
        num_rows="fixed",
        disabled=["nudo"],
        key=f"nodos_{nombre}_{base}_{altura}",
        column_config={
            "nudo": st.column_config.NumberColumn(format="%d"),
            "x (m)": st.column_config.NumberColumn(format="%.3f", step=0.1),
            "y (m)": st.column_config.NumberColumn(format="%.3f", step=0.1),
        },
    )
    fijo_def, movil_def, tipo_def = _apoyos_por_defecto(nombre)
    nudo_fijo, nudo_movil, tipo_movil = _elegir_apoyos(
        ids, fijo_def, movil_def, tipo_def, nombre
    )
    cargas_edit = _tabla_cargas(
        _cargas_gui_por_defecto(nombre), f"cargas_{nombre}", fija=True
    )
    coords = {
        int(fila["nudo"]): (float(fila["x (m)"]), float(fila["y (m)"]))
        for fila in _filas(nodos_edit)
    }
    try:
        armadura = _armar_preset(
            nombre, coords, nudo_fijo, nudo_movil, tipo_movil, _filas(cargas_edit)
        )
        return _resolver(armadura)
    except ValueError as exc:
        return None, None, str(exc)


def _asegurar_propia():
    if "propia_version" in st.session_state:
        return
    nodos, barras, cargas, fijo, movil, tipo = _fuentes_de(
        Armadura2D.preset_triangulo()
    )
    st.session_state.propia_version = 0
    st.session_state.nodos_fuente = nodos
    st.session_state.barras_fuente = barras
    st.session_state.cargas_fuente = cargas
    st.session_state.fijo_fuente = fijo
    st.session_state.movil_fuente = movil
    st.session_state.tipo_fuente = tipo


def _reiniciar_propia(armadura):
    nodos, barras, cargas, fijo, movil, tipo = _fuentes_de(armadura)
    st.session_state.propia_version += 1
    st.session_state.nodos_fuente = nodos
    st.session_state.barras_fuente = barras
    st.session_state.cargas_fuente = cargas
    st.session_state.fijo_fuente = fijo
    st.session_state.movil_fuente = movil
    st.session_state.tipo_fuente = tipo
    st.rerun()


def _vista_parcial(filas_nodos, filas_barras, nudo_fijo, nudo_movil, tipo_movil, filas_carga):
    """Arma lo que ya se puede dibujar, aunque el cálculo todavía no cierre."""
    armadura = Armadura2D(nombre="Propia")
    avisos = []
    ids = set()
    for fila in filas_nodos:
        try:
            nudo = _id_entero(fila.get("nudo"))
        except ValueError as exc:
            avisos.append(str(exc))
            continue
        if nudo is None:
            continue
        if nudo in ids:
            avisos.append(f"El nudo {nudo} está repetido; en el plano queda la primera posición.")
            continue
        armadura.agregar_nodo(
            nudo, _numero(fila.get("x (m)")), _numero(fila.get("y (m)"))
        )
        ids.add(nudo)

    usadas = set()
    for indice, fila in enumerate(filas_barras, start=1):
        try:
            nudo_i = _id_entero(fila.get("nudo i"))
            nudo_j = _id_entero(fila.get("nudo j"))
        except ValueError as exc:
            avisos.append(str(exc))
            continue
        if nudo_i is None or nudo_j is None:
            continue
        barra = str(fila.get("barra") or "").strip() or f"B{indice}"
        if nudo_i not in ids or nudo_j not in ids:
            avisos.append(f"La barra {barra} une nudos que todavía no están en la tabla.")
            continue
        if barra in usadas:
            avisos.append(f"La barra {barra!r} está repetida.")
            continue
        try:
            armadura.agregar_barra(barra, nudo_i, nudo_j)
            usadas.add(barra)
        except ValueError as exc:
            avisos.append(str(exc))

    fijo_ok = nudo_fijo in ids
    movil_ok = nudo_movil in ids and nudo_movil != nudo_fijo
    if fijo_ok and movil_ok:
        armadura.definir_apoyos(int(nudo_fijo), int(nudo_movil), tipo_movil or "movil")
    else:
        if fijo_ok:
            armadura.agregar_apoyo(int(nudo_fijo), "fijo")
        if movil_ok:
            armadura.agregar_apoyo(int(nudo_movil), tipo_movil or "movil")

    for nudo, fx, fy in _cargas_desde_filas(filas_carga or []):
        if nudo not in ids or (fx == 0.0 and fy == 0.0):
            continue
        try:
            armadura.agregar_carga(nudo, fx, fy)
        except ValueError as exc:
            avisos.append(str(exc))
    return armadura, avisos


def _bloque_propia():
    _asegurar_propia()
    st.caption(
        "A la izquierda escribes nudos, barras, apoyos y cargas. "
        "A la derecha el plano cartesiano muestra cómo va quedando: "
        "cada barra lleva su longitud. "
        "Las fuerzas se calculan más abajo, cuando la armadura se puede resolver."
    )
    acciones = st.columns(2)
    if acciones[0].button("Empezar desde el triángulo", key="btn_triangulo"):
        _reiniciar_propia(Armadura2D.preset_triangulo())
    if acciones[1].button("Vaciar", key="btn_vaciar"):
        st.session_state.propia_version += 1
        st.session_state.nodos_fuente = []
        st.session_state.barras_fuente = []
        st.session_state.cargas_fuente = []
        st.session_state.fijo_fuente = None
        st.session_state.movil_fuente = None
        st.session_state.tipo_fuente = "movil"
        st.rerun()

    version = st.session_state.propia_version
    col_form, col_plano = st.columns((1.15, 0.95), vertical_alignment="top")
    with col_form:
        st.subheader("Nudos")
        nodos_edit = st.data_editor(
            st.session_state.nodos_fuente,
            hide_index=True,
            num_rows="dynamic",
            key=f"nodos_p_{version}",
            column_config={
                "nudo": st.column_config.NumberColumn(
                    format="%d", step=1, help="Identificador entero. Puede ser 0."
                ),
                "x (m)": st.column_config.NumberColumn(format="%.3f", step=0.1),
                "y (m)": st.column_config.NumberColumn(format="%.3f", step=0.1),
            },
        )
        st.subheader("Barras")
        barras_edit = st.data_editor(
            st.session_state.barras_fuente,
            hide_index=True,
            num_rows="dynamic",
            key=f"barras_p_{version}",
            column_config={
                "barra": st.column_config.TextColumn(
                    help="Por ejemplo B1. Si se deja vacía, se numera sola."
                ),
                "nudo i": st.column_config.NumberColumn(format="%d", step=1),
                "nudo j": st.column_config.NumberColumn(format="%d", step=1),
            },
        )
        filas_nodos = _filas(nodos_edit)
        filas_barras = _filas(barras_edit)
        try:
            ids = []
            for fila in filas_nodos:
                nudo = _id_entero(fila.get("nudo"))
                if nudo is not None and nudo not in ids:
                    ids.append(nudo)
            error_ids = None
        except ValueError as exc:
            ids = []
            error_ids = str(exc)

        nudo_fijo = nudo_movil = None
        tipo_movil = st.session_state.tipo_fuente or "movil"
        cargas_edit = []
        if error_ids:
            st.error(error_ids)
        elif len(ids) < 2:
            st.info("Agrega al menos dos nudos y una barra para poder calcular.")
        else:
            nudo_fijo, nudo_movil, tipo_movil = _elegir_apoyos(
                ids,
                st.session_state.fijo_fuente,
                st.session_state.movil_fuente,
                st.session_state.tipo_fuente,
                f"propia_{version}",
            )
            st.session_state.fijo_fuente = nudo_fijo
            st.session_state.movil_fuente = nudo_movil
            st.session_state.tipo_fuente = tipo_movil

            mapa = {}
            for fila in st.session_state.cargas_fuente:
                try:
                    nudo = _id_entero(fila.get("nudo"))
                except ValueError:
                    nudo = None
                if nudo is not None:
                    mapa[nudo] = fila
            filas_carga = []
            for nudo in ids:
                previa = mapa.get(nudo, {})
                filas_carga.append(
                    {
                        "nudo": nudo,
                        "horizontal →+ (kN)": _numero(previa.get("horizontal →+ (kN)")),
                        "vertical hacia abajo (kN)": _numero(
                            previa.get("vertical hacia abajo (kN)")
                        ),
                    }
                )
            cargas_edit = _tabla_cargas(
                filas_carga, f"cargas_p_{version}_{tuple(ids)}"
            )
            st.session_state.cargas_fuente = _filas(cargas_edit)

    with col_plano:
        st.subheader("Plano")
        st.caption(
            "Ejes en metros. El número de cada barra es su longitud. "
            "Los apoyos y las cargas aparecen cuando ya están definidos."
        )
        try:
            vista, avisos = _vista_parcial(
                filas_nodos,
                filas_barras,
                nudo_fijo,
                nudo_movil,
                tipo_movil,
                _filas(cargas_edit) if cargas_edit else [],
            )
        except ValueError as exc:
            vista, avisos = None, [str(exc)]
        if vista is not None and vista.snapshot_nodos():
            _mostrar_figura(vista.graficar_plano())
        else:
            st.info("El plano aparece en cuanto agregues el primer nudo.")
        for aviso in avisos[:4]:
            st.caption(aviso)

    if error_ids or len(ids) < 2:
        return None, None, error_ids
    try:
        armadura = _armar_propia(
            filas_nodos,
            filas_barras,
            nudo_fijo,
            nudo_movil,
            tipo_movil,
            _filas(cargas_edit),
        )
        return _resolver(armadura)
    except ValueError as exc:
        return None, None, str(exc)


def _longitudes(armadura):
    st.subheader("Longitudes")
    st.caption("Salen de las coordenadas. No se escriben a mano.")
    if armadura is None:
        st.info("Cuando la armadura sea válida, aquí aparecen las longitudes.")
        return
    st.dataframe(
        [
            {
                "barra": barra,
                "nudos": f"{i}–{j}",
                "L (m)": round(armadura.longitud(barra), 4),
            }
            for barra, i, j in armadura.snapshot_barras()
        ],
        hide_index=True,
    )


def _resultados(resultado):
    st.header("3. Resultados")
    st.markdown(
        "Positivo es **tensión** (la barra se estira). "
        "Negativo es **compresión** (la barra se acorta). "
        "En las reacciones, positivo es hacia la derecha y hacia arriba."
    )
    st.subheader("Fuerzas en las barras")
    st.dataframe(
        [
            {
                "barra": barra.id,
                "nudos": f"{barra.nudo_i}–{barra.nudo_j}",
                "N (kN)": round(barra.fuerza, 4),
                "tipo": _TIPO[barra.tipo],
                "L (m)": round(barra.longitud, 4),
            }
            for barra in resultado.fuerzas
        ],
        hide_index=True,
    )
    st.subheader("Reacciones")
    st.dataframe(
        [
            {
                "nudo": rec.nudo,
                "Rx (kN)": round(rec.rx, 4),
                "Ry (kN)": round(rec.ry, 4),
            }
            for rec in resultado.reacciones
        ],
        hide_index=True,
    )


def _ecuaciones(armadura, resultado):
    sistema = armadura.ecuaciones()
    st.header("4. Sistema de ecuaciones")
    st.markdown(
        "Hay **dos ecuaciones por nudo**: la suma de fuerzas en x y la suma "
        "de fuerzas en y. El programa las escribe todas y las resuelve juntas."
    )
    st.markdown(
        "En el cuerpo libre, la flecha de cada barra apunta como si la barra "
        "estuviera a **tensión**: tira del nudo hacia el otro extremo. "
        "Las reacciones apuntan en su sentido positivo (Rx a la derecha, Ry hacia arriba). "
        "La carga roja entra con el sentido real. "
        "Si el número de una barra sale negativo, esa barra está a compresión y en realidad empuja."
    )
    if sistema.incognitas:
        st.caption("Incógnitas, en orden: " + ", ".join(sistema.incognitas))

    residuos = {
        nudo: (res_x, res_y)
        for nudo, res_x, res_y in resultado.equilibrio.residuos_nodos
    }
    por_nudo = {}
    for ecuacion in sistema.ecuaciones:
        por_nudo.setdefault(ecuacion.nudo, []).append(ecuacion)

    for nudo, grupo in por_nudo.items():
        st.markdown(f"**Nudo {nudo}**")
        col_fig, col_txt = st.columns((1, 1.15), vertical_alignment="center")
        with col_fig:
            _mostrar_figura(armadura.graficar_nudo(nudo, resultado))
        with col_txt:
            st.code("\n\n".join(ecuacion.texto for ecuacion in grupo), language=None)
            res_x, res_y = residuos.get(nudo, (0.0, 0.0))
            st.caption(
                "Al sustituir la solución, el residuo de este nudo es "
                f"ΣFx = {res_x:.2e} kN y ΣFy = {res_y:.2e} kN."
            )

    st.subheader("Sistema completo")
    st.code(sistema.texto, language=None)


def _intro():
    st.title("Analizador de armaduras 2D")
    st.markdown(
        "Este programa calcula las fuerzas de las barras de una armadura plana "
        "y las reacciones de los apoyos, de modo que la estructura quede en equilibrio."
    )
    st.markdown(
        "Puedes partir de una armadura precargada o armar la tuya: "
        "defines los nudos y sus distancias, las barras que los unen, "
        "las cargas en los nudos y los dos apoyos. "
        "Después ves la figura con los valores, la tabla de resultados "
        "y el sistema de ecuaciones que produjo esos números."
    )
    st.caption("Unidades: kN y m. Hacia arriba es positivo. En las barras, + tensión y − compresión.")


def main():
    st.set_page_config(
        page_title="Armaduras 2D",
        page_icon="△",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _intro()
    st.divider()

    st.header("1. Datos de la armadura")
    modo = st.radio(
        "Cómo quieres definirla",
        ["Precargada", "Propia"],
        horizontal=True,
    )
    if modo == "Precargada":
        armadura, resultado, error = _bloque_precargada()
    else:
        armadura, resultado, error = _bloque_propia()

    _longitudes(armadura)
    st.divider()

    st.header("2. Armadura")
    st.markdown(
        "Cada barra muestra su nombre y su fuerza. "
        "El color distingue tensión, compresión y fuerza nula. "
        "Las flechas rojas son cargas y las azules son reacciones."
    )
    if error:
        st.error(error)
    elif resultado is None:
        st.info("Completa los datos para ver la armadura y el cálculo.")
    else:
        _mostrar_figura(armadura.graficar(resultado))
        eq = resultado.equilibrio
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Equilibrio", "sí" if eq.ok else "revisar")
        m2.metric("Σ Fx (kN)", f"{eq.sum_fx:.2e}")
        m3.metric("Σ Fy (kN)", f"{eq.sum_fy:.2e}")
        m4.metric("Σ M (kN·m)", f"{eq.sum_mz:.2e}")
        st.caption(
            "Esas tres sumas son el equilibrio de toda la armadura: "
            "fuerzas horizontales, fuerzas verticales y momentos. "
            "En una solución correcta quedan en cero."
        )

    if resultado is None:
        return

    st.divider()
    _resultados(resultado)
    st.divider()
    _ecuaciones(armadura, resultado)


main()
