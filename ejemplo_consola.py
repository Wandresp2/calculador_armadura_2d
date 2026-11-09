"""Uso de la librería SIN interfaz gráfica: la lógica no depende de Streamlit.

Preparación (una vez, desde la carpeta del proyecto)::

    python -m venv .venv
    .venv\\Scripts\\Activate.ps1
    python -m pip install -e .

Ejecutar::

    python ejemplo_consola.py
"""

from pathlib import Path

try:
    from armadura_2d_andresdperezc import Armadura2D
except ImportError:
    raise SystemExit(
        "No se encontró la librería 'armadura_2d_andresdperezc'.\n"
        "Desde la carpeta del proyecto, con el entorno virtual activo, ejecute:\n"
        "  python -m pip install -e ."
    ) from None

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _imprimir(armadura):
    resultado = armadura.resolver()
    print(f"\n=== {armadura.nombre} ===")
    print(f"  equilibrio ok: {resultado.equilibrio.ok}")
    print(
        "  ΣFx = {0.sum_fx:.3e} kN   ΣFy = {0.sum_fy:.3e} kN   "
        "ΣM = {0.sum_mz:.3e} kN·m".format(resultado.equilibrio)
    )
    print("  Reacciones (kN):")
    for rec in resultado.reacciones:
        print(f"    nudo {rec.nudo}:  Rx = {rec.rx:8.3f}   Ry = {rec.ry:8.3f}")
    print("  Barras:")
    for barra in resultado.fuerzas:
        print(
            f"    {barra.id:4}  {barra.nudo_i}–{barra.nudo_j}  "
            f"L = {barra.longitud:6.3f} m  "
            f"N = {barra.fuerza:8.3f} kN  {barra.tipo}"
        )
    return resultado


def main():
    triangulo = Armadura2D.preset_triangulo()
    resultado_t = _imprimir(triangulo)
    print("  Valores de libro: Ry = 25 kN; B1 = +50/3 kN (tensión);")
    print("  B2 y B3 = -(25/3)√13 kN (compresión).")

    pratt = Armadura2D.preset_pratt()
    resultado_p = _imprimir(pratt)
    print("  En Pratt las diagonales hacia el centro van a tracción.")

    howe = Armadura2D.preset_howe()
    _imprimir(howe)
    print("  En Howe las diagonales hacia los apoyos van a compresión.")

    carpeta = Path(__file__).resolve().parent / "examples"
    carpeta.mkdir(exist_ok=True)
    for armadura, resultado, nombre in (
        (triangulo, resultado_t, "triangulo.png"),
        (pratt, resultado_p, "pratt.png"),
    ):
        figura = armadura.graficar(resultado)
        ruta = carpeta / nombre
        figura.savefig(ruta, dpi=120)
        plt.close(figura)
        print(f"\nFigura guardada (backend Agg, sin ventana): {ruta}")

    print("\nEste script no usa Streamlit: el paquete funciona solo con pip.")


if __name__ == "__main__":
    main()
