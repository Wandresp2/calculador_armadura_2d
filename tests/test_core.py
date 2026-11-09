"""Pruebas del solver de armaduras 2D. Ejecutar con: pytest -v"""

import math

import pytest

from armadura_2d_andresdperezc import (
    Armadura2D,
    FuerzaBarra,
    Reaccion,
    ResultadoArmadura,
)

SQRT13 = math.sqrt(13)


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
