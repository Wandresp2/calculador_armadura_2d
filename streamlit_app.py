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
    mapa = {nudo: (fx, -fy) for nudo, fx, fy in armadura.snapshot_cargas()}
    filas = []
    for nudo in ids:
        fx, abajo = mapa.get(nudo, (0.0, 0.0))
        filas.append(
            {
                "nudo": nudo,
                "horizontal →+ (kN)": float(fx),
                "vertical hacia abajo (kN)": float(abajo),
            }
        )
    return filas


def _apoyos_por_defecto(nombre):
    armadura = _fabrica(nombre)
    fijo = movil = None
    for nudo, tipo in armadura.snapshot_apoyos():
        if tipo == "fijo":
            fijo = nudo
        elif tipo == "movil":
            movil = nudo
    return fijo, movil


def _armar(nombre, coords, nudo_fijo, nudo_movil, filas_carga):
    armadura = _fabrica(nombre)
    armadura.reemplazar_coordenadas(coords)
    armadura.definir_apoyos(int(nudo_fijo), int(nudo_movil))
    cargas = []
    for fila in filas_carga:
        nudo = int(fila["nudo"])
        fx = float(fila["horizontal →+ (kN)"])
        abajo = float(fila["vertical hacia abajo (kN)"])
        cargas.append((nudo, fx, -abajo))
    armadura.definir_cargas(cargas)
    return armadura


def main():
    st.set_page_config(
        page_title="Armaduras 2D",
        page_icon="△",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.title("Analizador de armaduras 2D")
    st.caption(
        "GUI de Streamlit sobre la librería `armadura-2d-andresdperezc`. "
        "El paquete no depende de esta interfaz. Unidades: kN y m. "
        "+ tensión / − compresión."
    )

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

    with st.expander("Notas de uso"):
        st.markdown(
            """
**Mecánica vectorial** (isostáticas 2D).

- Apoyos: fijo (Rx, Ry) y móvil vertical (Ry).
- Cargas solo en nudos.
- La GUI convierte “hacia abajo (+)” a $F_y$ negativa.
- Los sliders escalan el preset. La tabla de nudos puede afinar coordenadas.
- Cambiar preset o sliders recarga la geometría escalada.
- No se pueden añadir ni quitar barras (eso queda para un futuro CAD).

Sin diámetro, esfuerzo, pórticos ni 3D.
Si el desarrollo se **expande**, hay que **validarlo** de nuevo.
            """
        )

    ids_nudos = [nudo for nudo, _x, _y in prototipo.snapshot_nodos()]
    coords_base = _coords_escaladas(nombre, base, altura)
    filas_nodos = [
        {"nudo": nudo, "x (m)": coords_base[nudo][0], "y (m)": coords_base[nudo][1]}
        for nudo in ids_nudos
    ]
    fijo_def, movil_def = _apoyos_por_defecto(nombre)

    col_izq, col_der = st.columns((1.05, 1.2))
    with col_izq:
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
        st.subheader("Apoyos")
        c1, c2 = st.columns(2)
        nudo_fijo = c1.selectbox(
            "Fijo (Rx, Ry)",
            ids_nudos,
            index=ids_nudos.index(fijo_def) if fijo_def in ids_nudos else 0,
            key=f"fijo_{nombre}",
        )
        nudo_movil = c2.selectbox(
            "Móvil (Ry)",
            ids_nudos,
            index=ids_nudos.index(movil_def) if movil_def in ids_nudos else 1,
            key=f"movil_{nombre}",
        )
        st.subheader("Cargas")
        cargas_edit = st.data_editor(
            _cargas_gui_por_defecto(nombre),
            hide_index=True,
            num_rows="fixed",
            disabled=["nudo"],
            key=f"cargas_{nombre}",
            column_config={
                "nudo": st.column_config.NumberColumn(format="%d"),
                "horizontal →+ (kN)": st.column_config.NumberColumn(
                    min_value=-CARGA_MAX,
                    max_value=CARGA_MAX,
                    step=1.0,
                    format="%.2f",
                ),
                "vertical hacia abajo (kN)": st.column_config.NumberColumn(
                    min_value=0.0,
                    max_value=CARGA_MAX,
                    step=1.0,
                    format="%.2f",
                ),
            },
        )

    coords = {
        int(fila["nudo"]): (float(fila["x (m)"]), float(fila["y (m)"]))
        for fila in _filas(nodos_edit)
    }

    try:
        armadura = _armar(
            nombre, coords, nudo_fijo, nudo_movil, _filas(cargas_edit)
        )
        resultado = armadura.resolver()
        error = None
    except ValueError as exc:
        armadura = None
        resultado = None
        error = str(exc)

    with col_izq:
        st.subheader("Longitudes (calculadas)")
        if armadura is not None:
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
        else:
            st.info("Corrija la geometría para ver longitudes.")

    with col_der:
        st.subheader("Diagrama")
        if error:
            st.error(error)
        else:
            _mostrar_figura(armadura.graficar(resultado))
            eq = resultado.equilibrio
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Equilibrio", "sí" if eq.ok else "no")
            m2.metric("Σ Fx (kN)", f"{eq.sum_fx:.2e}")
            m3.metric("Σ Fy (kN)", f"{eq.sum_fy:.2e}")
            m4.metric("Σ M (kN·m)", f"{eq.sum_mz:.2e}")

    if resultado is not None:
        st.subheader("Fuerzas internas")
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


main()
