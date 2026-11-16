"""Clics del plano de la armadura propia. No abre Streamlit."""

from plano_ui import ajustar_malla, clasificar_punto, efecto_clic, firma_seleccion


def _nodo(nudo, x, y):
    return {"nudo": nudo, "x (m)": x, "y (m)": y}


def _base(**cambios):
    estado = {
        "modo": "Nudo",
        "customdata": "rejilla",
        "x": 1.2,
        "y": 2.4,
        "nodos": [],
        "barras": [],
        "fijo": None,
        "movil": None,
        "tipo_movil": "movil",
        "cargas": [],
        "origen": None,
        "horizontal": 0.0,
        "vertical_abajo": 0.0,
        "apoyo": "fijo",
    }
    estado.update(cambios)
    return efecto_clic(
        estado["modo"],
        estado["customdata"],
        estado["x"],
        estado["y"],
        estado["nodos"],
        estado["barras"],
        estado["fijo"],
        estado["movil"],
        estado["tipo_movil"],
        estado["cargas"],
        estado["origen"],
        estado["horizontal"],
        estado["vertical_abajo"],
        estado["apoyo"],
    )


def test_el_clic_de_nudo_cae_en_la_malla():
    assert ajustar_malla(1.2) == 1.0
    assert ajustar_malla(2.4) == 2.5
    resultado = _base()
    assert resultado["cambio"] is True
    assert resultado["nodos"] == [_nodo(0, 1.0, 2.5)]


def test_no_crea_dos_nudos_en_el_mismo_cruce():
    resultado = _base(nodos=[_nodo(0, 1.0, 2.5)], x=1.0, y=2.5)
    assert resultado["cambio"] is False
    assert len(resultado["nodos"]) == 1


def test_la_barra_pide_dos_nudos_distintos():
    nodos = [_nodo(0, 0, 0), _nodo(1, 4, 0)]
    primero = _base(modo="Barra", customdata="nudo:0", nodos=nodos)
    assert primero["cambio"] is False
    assert primero["origen"] == 0
    segundo = _base(
        modo="Barra", customdata="nudo:1", nodos=nodos, origen=0
    )
    assert segundo["cambio"] is True
    assert segundo["barras"] == [{"barra": "B1", "nudo i": 0, "nudo j": 1}]
    assert segundo["origen"] is None
    mismo = _base(modo="Barra", customdata="nudo:0", nodos=nodos, origen=0)
    assert mismo["cambio"] is False


def test_no_repite_una_barra():
    nodos = [_nodo(0, 0, 0), _nodo(1, 4, 0)]
    barras = [{"barra": "B1", "nudo i": 1, "nudo j": 0}]
    resultado = _base(
        modo="Barra", customdata="nudo:1", nodos=nodos, barras=barras, origen=0
    )
    assert resultado["cambio"] is False
    assert len(resultado["barras"]) == 1


def test_el_apoyo_no_puede_ocupar_el_otro():
    nodos = [_nodo(0, 0, 0), _nodo(1, 4, 0)]
    conflicto = _base(
        modo="Apoyo",
        customdata="nudo:1",
        nodos=nodos,
        movil=1,
        apoyo="fijo",
    )
    assert conflicto["cambio"] is False
    puesto = _base(
        modo="Apoyo",
        customdata="nudo:0",
        nodos=nodos,
        apoyo="movil_pared",
    )
    assert puesto["movil"] == 0
    assert puesto["tipo_movil"] == "movil_pared"


def test_la_carga_queda_en_el_nudo_pulsado():
    nodos = [_nodo(2, 2, 3)]
    resultado = _base(
        modo="Carga",
        customdata="nudo:2",
        nodos=nodos,
        horizontal=3,
        vertical_abajo=50,
    )
    assert resultado["cambio"] is True
    assert resultado["cargas"] == [
        {
            "nudo": 2,
            "horizontal →+ (kN)": 3.0,
            "vertical hacia abajo (kN)": 50.0,
        }
    ]


def test_la_cuadrilla_no_crea_una_barra():
    resultado = _base(modo="Barra", customdata="rejilla", nodos=[_nodo(0, 0, 0)])
    assert resultado["cambio"] is False
    assert resultado["barras"] == []


def test_clasificar_y_firma():
    assert clasificar_punto("nudo:4") == ("nudo", 4)
    assert clasificar_punto(["rejilla"]) == ("rejilla", None)
    firma = firma_seleccion(
        {"customdata": "nudo:1", "x": 4, "y": 0},
        "Carga",
        0,
        50,
        "fijo",
    )
    assert firma[0] == "Carga"
    assert firma[4:] == (0.0, 50.0, "fijo")
