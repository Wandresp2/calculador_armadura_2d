"""Pruebas del solver de armaduras 2D. Ejecutar con: pytest -v"""

import math

import matplotlib

matplotlib.use("Agg")

import pytest
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Polygon

from armadura_2d_andresdperezc import (
    Armadura2D,
    FuerzaBarra,
    Reaccion,
    ResultadoArmadura,
)

SQRT13 = math.sqrt(13)


@pytest.fixture(autouse=True)
def _cerrar_figuras():
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


def _fuerzas(resultado):
    return {barra.id: barra for barra in resultado.fuerzas}


def _reacciones(resultado):
    return {item.nudo: item for item in resultado.reacciones}


def test_preset_triangulo_reacciones_de_libro():
    resultado = Armadura2D.preset_triangulo().resolver()
    rec = _reacciones(resultado)
    assert rec[0].rx == pytest.approx(0.0)
    assert rec[0].ry == pytest.approx(25.0)
    assert rec[1].rx == pytest.approx(0.0)
    assert rec[1].ry == pytest.approx(25.0)


def test_preset_triangulo_fuerzas_de_libro():
    resultado = Armadura2D.preset_triangulo().resolver()
    barras = _fuerzas(resultado)
    assert isinstance(barras["B1"], FuerzaBarra)
    assert barras["B1"].tipo == "tension"
    assert barras["B1"].fuerza == pytest.approx(50.0 / 3.0)
    assert barras["B2"].tipo == "compresion"
    assert barras["B2"].fuerza == pytest.approx(-(25.0 / 3.0) * SQRT13)
    assert barras["B3"].tipo == "compresion"
    assert barras["B3"].fuerza == pytest.approx(barras["B2"].fuerza)


def test_longitudes_triangulo():
    armadura = Armadura2D.preset_triangulo()
    assert armadura.longitud("B1") == pytest.approx(4.0)
    assert armadura.longitud("B2") == pytest.approx(SQRT13)
    assert armadura.longitud("B3") == pytest.approx(SQRT13)
    assert armadura.angulo("B1") == pytest.approx(0.0)


def test_equilibrio_triangulo():
    armadura = Armadura2D.preset_triangulo()
    resultado = armadura.resolver()
    assert resultado.equilibrio.ok
    chequeo = armadura.verificar_equilibrio(resultado)
    assert chequeo.ok
    assert chequeo.sum_fx == pytest.approx(0.0, abs=1e-8)
    assert chequeo.sum_fy == pytest.approx(0.0, abs=1e-8)
    assert chequeo.sum_mz == pytest.approx(0.0, abs=1e-8)
    for _nudo, res_x, res_y in chequeo.residuos_nodos:
        assert res_x == pytest.approx(0.0, abs=1e-8)
        assert res_y == pytest.approx(0.0, abs=1e-8)


def test_resultado_tipos():
    resultado = Armadura2D.preset_triangulo().resolver()
    assert isinstance(resultado, ResultadoArmadura)
    assert isinstance(resultado.reacciones[0], Reaccion)
    assert len(resultado.fuerzas) == 3
    assert len(resultado.reacciones) == 2


def test_construir_a_mano_coincide_con_preset():
    armadura = Armadura2D(nombre="manual")
    armadura.agregar_nodo(0, 0.0, 0.0)
    armadura.agregar_nodo(1, 4.0, 0.0)
    armadura.agregar_nodo(2, 2.0, 3.0)
    armadura.agregar_barra("B1", 0, 1)
    armadura.agregar_barra("B2", 0, 2)
    armadura.agregar_barra("B3", 1, 2)
    armadura.agregar_apoyo(0, "fijo")
    armadura.agregar_apoyo(1, "movil")
    armadura.agregar_carga(2, fx=0.0, fy=-50.0)
    barras = _fuerzas(armadura.resolver())
    assert barras["B1"].fuerza == pytest.approx(50.0 / 3.0)


def test_nudo_repetido():
    armadura = Armadura2D()
    armadura.agregar_nodo(0, 0.0, 0.0)
    with pytest.raises(ValueError, match="ya existe"):
        armadura.agregar_nodo(0, 1.0, 1.0)


def test_barra_a_nudo_inexistente():
    armadura = Armadura2D()
    armadura.agregar_nodo(0, 0.0, 0.0)
    with pytest.raises(ValueError, match="No existe el nudo"):
        armadura.agregar_barra("B1", 0, 1)


def test_barra_longitud_cero():
    armadura = Armadura2D()
    armadura.agregar_nodo(0, 1.0, 1.0)
    armadura.agregar_nodo(1, 1.0, 1.0)
    with pytest.raises(ValueError, match="longitud 0"):
        armadura.agregar_barra("B1", 0, 1)


def test_barra_duplicada_mismos_nudos():
    armadura = Armadura2D.preset_triangulo()
    with pytest.raises(ValueError, match="Ya existe la barra"):
        armadura.agregar_barra("B9", 1, 0)


def test_hiperestatica_segundo_fijo():
    armadura = Armadura2D.preset_triangulo()
    armadura.agregar_apoyo(2, "fijo")
    with pytest.raises(ValueError, match="hiperestática"):
        armadura.resolver()


def test_hipostatica_sin_movil():
    armadura = Armadura2D()
    armadura.agregar_nodo(0, 0.0, 0.0)
    armadura.agregar_nodo(1, 4.0, 0.0)
    armadura.agregar_nodo(2, 2.0, 3.0)
    armadura.agregar_barra("B1", 0, 1)
    armadura.agregar_barra("B2", 0, 2)
    armadura.agregar_barra("B3", 1, 2)
    armadura.agregar_apoyo(0, "fijo")
    armadura.agregar_carga(2, fy=-50.0)
    with pytest.raises(ValueError, match="hipostática"):
        armadura.resolver()


def test_tipo_apoyo_ilegal():
    armadura = Armadura2D()
    armadura.agregar_nodo(0, 0.0, 0.0)
    with pytest.raises(ValueError, match="fijo"):
        armadura.agregar_apoyo(0, "empotrado")


def test_carga_en_nudo_inexistente():
    armadura = Armadura2D()
    with pytest.raises(ValueError, match="No existe el nudo"):
        armadura.agregar_carga(2, fy=-50.0)


@pytest.mark.parametrize("nudo", [True, 1.5, "0", 1.0])
def test_nudo_id_invalido(nudo):
    armadura = Armadura2D()
    with pytest.raises(ValueError):
        armadura.agregar_nodo(nudo, 0.0, 0.0)


def test_sistema_singular_nudos_colineales():
    armadura = Armadura2D.preset_triangulo()
    armadura.mover_nodo(2, 2.0, 0.0)
    with pytest.raises(ValueError, match="singular"):
        armadura.resolver()


def test_reemplazar_carga_cambia_reacciones():
    armadura = Armadura2D.preset_triangulo()
    armadura.reemplazar_carga(2, fx=0.0, fy=-20.0)
    rec = _reacciones(armadura.resolver())
    assert rec[0].ry == pytest.approx(10.0)
    assert rec[1].ry == pytest.approx(10.0)


def test_definir_apoyos_invierte_extremos():
    armadura = Armadura2D.preset_triangulo()
    armadura.definir_apoyos(1, 0)
    rec = _reacciones(armadura.resolver())
    assert rec[1].rx == pytest.approx(0.0)
    assert rec[1].ry == pytest.approx(25.0)
    assert rec[0].ry == pytest.approx(25.0)
    assert rec[0].rx == pytest.approx(0.0)


def _barra_entre(resultado, nudo_i, nudo_j):
    par = frozenset((nudo_i, nudo_j))
    for barra in resultado.fuerzas:
        if frozenset((barra.nudo_i, barra.nudo_j)) == par:
            return barra
    raise AssertionError(f"No hay barra entre {nudo_i} y {nudo_j}.")


PRESETS_ISOSTATICOS = [
    (Armadura2D.preset_triangulo, 3, 3),
    (Armadura2D.preset_warren, 5, 7),
    (Armadura2D.preset_pratt, 6, 9),
    (Armadura2D.preset_howe, 6, 9),
]


@pytest.mark.parametrize("factory, nudos, barras", PRESETS_ISOSTATICOS)
def test_presets_isostaticos_y_equilibrio(factory, nudos, barras):
    armadura = factory()
    resultado = armadura.resolver()
    assert resultado.equilibrio.ok
    assert len(resultado.fuerzas) == barras
    assert len(resultado.equilibrio.residuos_nodos) == nudos
    assert barras + 3 == 2 * nudos
    rec = _reacciones(resultado)
    assert rec[0].ry + rec[2 if nudos > 3 else 1].ry == pytest.approx(50.0)
    for _nudo, res_x, res_y in resultado.equilibrio.residuos_nodos:
        assert res_x == pytest.approx(0.0, abs=1e-8)
        assert res_y == pytest.approx(0.0, abs=1e-8)


def test_pratt_diagonales_a_traccion():
    resultado = Armadura2D.preset_pratt().resolver()
    for nudo_i, nudo_j in ((3, 1), (5, 1)):
        barra = _barra_entre(resultado, nudo_i, nudo_j)
        assert barra.tipo == "tension"
        assert barra.fuerza > 0


def test_howe_diagonales_a_compresion():
    resultado = Armadura2D.preset_howe().resolver()
    for nudo_i, nudo_j in ((4, 0), (4, 2)):
        barra = _barra_entre(resultado, nudo_i, nudo_j)
        assert barra.tipo == "compresion"
        assert barra.fuerza < 0


def test_warren_resuelve_sin_gui():
    resultado = Armadura2D.preset_warren().resolver()
    assert len(resultado.fuerzas) == 7
    assert resultado.equilibrio.ok


@pytest.mark.parametrize(
    "factory",
    [
        Armadura2D.preset_triangulo,
        Armadura2D.preset_warren,
        Armadura2D.preset_pratt,
        Armadura2D.preset_howe,
    ],
)
def test_graficar_devuelve_figura(factory):
    figura = factory().graficar()
    assert isinstance(figura, Figure)
    assert len(figura.axes) == 1
    assert figura.axes[0].get_legend() is not None
    parches = figura.axes[0].patches
    assert any(isinstance(p, Circle) for p in parches)
    assert any(isinstance(p, Polygon) for p in parches)


def test_graficar_con_resultado_explicito():
    armadura = Armadura2D.preset_triangulo()
    resultado = armadura.resolver()
    figura = armadura.graficar(resultado)
    assert isinstance(figura, Figure)


def test_graficar_resultado_invalido():
    with pytest.raises(ValueError, match="ResultadoArmadura"):
        Armadura2D.preset_triangulo().graficar(resultado="no")


def test_graficar_sin_nudos():
    with pytest.raises(ValueError, match="nudos"):
        Armadura2D().graficar()


def test_snapshot_y_reemplazar_coordenadas():
    armadura = Armadura2D.preset_triangulo()
    nudos = armadura.snapshot_nodos()
    assert nudos[0] == (0, 0.0, 0.0)
    assert ("B1", 0, 1) in armadura.snapshot_barras()
    armadura.reemplazar_coordenadas({0: (0.0, 0.0), 1: (8.0, 0.0), 2: (4.0, 6.0)})
    assert armadura.longitud("B1") == pytest.approx(8.0)
    resultado = armadura.resolver()
    assert resultado.equilibrio.ok
    with pytest.raises(ValueError, match="exactamente"):
        armadura.reemplazar_coordenadas({0: (0.0, 0.0)})


def test_definir_cargas_sustituye_conjunto():
    armadura = Armadura2D.preset_triangulo()
    armadura.definir_cargas([(2, 0.0, -20.0)])
    rec = _reacciones(armadura.resolver())
    assert rec[0].ry == pytest.approx(10.0)


def _armadura_rodillo_pared():
    """Pin en (0, 0), rodillo de pared en (0, 3), carga de 50 kN en (4, 0)."""
    armadura = Armadura2D(nombre="pared")
    armadura.agregar_nodo(0, 0.0, 0.0)
    armadura.agregar_nodo(1, 0.0, 3.0)
    armadura.agregar_nodo(2, 4.0, 0.0)
    armadura.agregar_barra("B1", 0, 1)
    armadura.agregar_barra("B2", 0, 2)
    armadura.agregar_barra("B3", 1, 2)
    armadura.agregar_apoyo(0, "fijo")
    armadura.agregar_apoyo(1, "movil_pared")
    armadura.agregar_carga(2, fy=-50.0)
    return armadura


def test_rodillo_en_pared_reacciones_y_barras():
    resultado = _armadura_rodillo_pared().resolver()
    barras = _fuerzas(resultado)
    rec = _reacciones(resultado)
    assert barras["B1"].fuerza == pytest.approx(-50.0)
    assert barras["B1"].tipo == "compresion"
    assert barras["B2"].fuerza == pytest.approx(-200.0 / 3.0)
    assert barras["B3"].fuerza == pytest.approx(250.0 / 3.0)
    assert barras["B3"].tipo == "tension"
    assert rec[0].rx == pytest.approx(200.0 / 3.0)
    assert rec[0].ry == pytest.approx(50.0)
    assert rec[1].rx == pytest.approx(-200.0 / 3.0)
    assert rec[1].ry == pytest.approx(0.0)
    assert resultado.equilibrio.ok


def test_rodillo_pared_a_la_altura_del_fijo_es_singular():
    armadura = Armadura2D.preset_triangulo()
    armadura.definir_apoyos(0, 1, "movil_pared")
    with pytest.raises(ValueError, match="rodillo de pared"):
        armadura.resolver()


def test_definir_apoyos_rechaza_movil_inclinado():
    armadura = Armadura2D.preset_triangulo()
    with pytest.raises(ValueError, match="movil_pared"):
        armadura.definir_apoyos(0, 1, "inclinado")


def test_ecuaciones_del_triangulo_incluyen_la_carga():
    from armadura_2d_andresdperezc import SistemaEcuaciones

    sistema = Armadura2D.preset_triangulo().ecuaciones()
    assert isinstance(sistema, SistemaEcuaciones)
    assert sistema.incognitas == ("N_B1", "N_B2", "N_B3", "Rx_0", "Ry_0", "Ry_1")
    assert len(sistema.ecuaciones) == 6
    fy_cuspide = next(
        eq for eq in sistema.ecuaciones if eq.nudo == 2 and eq.eje == "y"
    )
    assert fy_cuspide.carga == pytest.approx(-50.0)
    assert "N_B2" in fy_cuspide.texto
    assert "N_B3" in fy_cuspide.texto
    assert "50" in fy_cuspide.texto
    assert fy_cuspide.texto.endswith("= 0")


def test_graficar_nudo_devuelve_figura():
    armadura = Armadura2D.preset_triangulo()
    resultado = armadura.resolver()
    figura = armadura.graficar_nudo(2, resultado)
    assert isinstance(figura, Figure)
    assert "2" in figura.axes[0].get_title()
    with pytest.raises(ValueError, match="No existe el nudo"):
        armadura.graficar_nudo(9)


def test_problema_beer_6_1_coincide_con_el_libro():
    """Misma álgebra que el problema resuelto 6.1 (lb y ft, unidades coherentes)."""
    armadura = Armadura2D(nombre="beer-6.1")
    for nudo, x, y in (
        (0, 0.0, 8.0),
        (1, 12.0, 8.0),
        (2, 24.0, 8.0),
        (3, 6.0, 0.0),
        (4, 18.0, 0.0),
    ):
        armadura.agregar_nodo(nudo, x, y)
    for barra, i, j in (
        ("AB", 0, 1),
        ("BC", 1, 2),
        ("AD", 0, 3),
        ("DB", 3, 1),
        ("DE", 3, 4),
        ("BE", 1, 4),
        ("EC", 4, 2),
    ):
        armadura.agregar_barra(barra, i, j)
    armadura.agregar_apoyo(2, "fijo")
    armadura.agregar_apoyo(4, "movil")
    armadura.agregar_carga(0, fy=-2000.0)
    armadura.agregar_carga(1, fy=-1000.0)
    resultado = armadura.resolver()
    barras = _fuerzas(resultado)
    rec = _reacciones(resultado)
    assert barras["AB"].fuerza == pytest.approx(1500.0)
    assert barras["AD"].fuerza == pytest.approx(-2500.0)
    assert barras["DB"].fuerza == pytest.approx(2500.0)
    assert barras["DE"].fuerza == pytest.approx(-3000.0)
    assert barras["BE"].fuerza == pytest.approx(-3750.0)
    assert barras["BC"].fuerza == pytest.approx(5250.0)
    assert barras["EC"].fuerza == pytest.approx(-8750.0)
    assert rec[2].rx == pytest.approx(0.0)
    assert rec[2].ry == pytest.approx(-7000.0)
    assert rec[4].ry == pytest.approx(10000.0)
    assert resultado.equilibrio.ok
    fy_a = next(eq for eq in armadura.ecuaciones().ecuaciones if eq.nudo == 0 and eq.eje == "y")
    assert "N_AD" in fy_a.texto
    assert "2000" in fy_a.texto
