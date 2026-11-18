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


def test_la_malla_crece_en_las_cuatro_direcciones():
    from plano_ui import limites_malla, puntos_malla

    vacia = limites_malla([])
    assert vacia[0] < 0 and vacia[2] < 0
    un_nudo = limites_malla([{"nudo": 0, "x (m)": 1, "y (m)": 1}])
    assert un_nudo[0] <= 1 - 4 and un_nudo[1] >= 1 + 4
    assert un_nudo[2] <= 1 - 4 and un_nudo[3] >= 1 + 4
    lejos = limites_malla(
        [
            {"nudo": 0, "x (m)": 0, "y (m)": 0},
            {"nudo": 1, "x (m)": 20, "y (m)": -12},
        ]
    )
    assert lejos[0] <= -4
    assert lejos[1] >= 24
    assert lejos[2] <= -16
    assert lejos[3] >= 4
    xs, ys = puntos_malla([{"nudo": 1, "x (m)": 20, "y (m)": -12}])
    assert (24.0, -16.0) in set(zip(xs, ys))


def test_el_encuadre_de_lectura_no_abre_la_malla_de_cuatro_metros():
    from plano_ui import limites_encuadre

    x0, x1, y0, y1 = limites_encuadre(
        [
            {"nudo": 0, "x (m)": 0, "y (m)": 0},
            {"nudo": 1, "x (m)": 4, "y (m)": 0},
            {"nudo": 2, "x (m)": 2, "y (m)": 3},
        ]
    )
    assert -4 < x0 < 0
    assert 4 < x1 < 8
    assert -4 < y0 < 0
    assert 3 < y1 < 7


def test_no_convierte_un_nudo_en_otro():
    resultado = _base(
        nodos=[_nodo(0, 1.0, 2.5)], customdata="nudo:0", x=1.0, y=2.5
    )
    assert resultado["cambio"] is False
    assert resultado["nodos"] == [_nodo(0, 1.0, 2.5)]


def test_la_carga_sustituye_la_del_mismo_nudo():
    previa = [
        {
            "nudo": 2,
            "horizontal →+ (kN)": 1.0,
            "vertical hacia abajo (kN)": 10.0,
        }
    ]
    resultado = _base(
        modo="Carga",
        customdata="nudo:2",
        nodos=[_nodo(2, 2, 3)],
        cargas=previa,
        horizontal=0,
        vertical_abajo=50,
    )
    assert resultado["cambio"] is True
    assert resultado["cargas"] == [
        {
            "nudo": 2,
            "horizontal →+ (kN)": 0.0,
            "vertical hacia abajo (kN)": 50.0,
        }
    ]


def test_cambia_el_movil_de_piso_a_pared():
    nodos = [_nodo(0, 0, 0), _nodo(1, 4, 0)]
    resultado = _base(
        modo="Apoyo",
        customdata="nudo:1",
        nodos=nodos,
        fijo=0,
        movil=1,
        tipo_movil="movil",
        apoyo="movil_pared",
    )
    assert resultado["cambio"] is True
    assert resultado["movil"] == 1
    assert resultado["tipo_movil"] == "movil_pared"


def test_elige_el_otro_extremo_aunque_el_primero_siga_marcado():
    from plano_ui import elegir_punto

    puntos = [
        {"customdata": "nudo:0", "x": 0, "y": 0},
        {"customdata": "nudo:1", "x": 4, "y": 0},
    ]
    elegido = elegir_punto(puntos, "Barra", origen=0)
    assert elegido["customdata"] == "nudo:1"
    assert elegir_punto(
        [{"customdata": "rejilla", "x": 1, "y": 1}, {"customdata": "nudo:2", "x": 2, "y": 2}],
        "Apoyo",
        None,
    )["customdata"] == "nudo:2"
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
