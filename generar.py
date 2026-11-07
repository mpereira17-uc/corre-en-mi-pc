"""Actualiza los juegos desde Steam y genera el sitio en docs/.

Uso:
  python generar.py            # descarga de Steam y genera
  python generar.py --sin-red  # solo regenera el sitio con data/juegos.json
"""
import json
import os
import sys

from cemp import datos, requisitos
from cemp.sitio import Sitio


def main():
    with open(os.path.join(datos.RAIZ, "config.json"), encoding="utf-8") as f:
        config = json.load(f)
    if "--sin-red" in sys.argv:
        juegos = datos.leer(datos.ARCHIVO, [])
        resumen = {"total": len(juegos)}
    else:
        juegos, resumen = datos.actualizar(config)
    # Recalcula la comparación con las tablas actuales (si mejoran, mejoran todos los juegos).
    for j in juegos:
        for nivel in ("min", "rec"):
            r = j.get("req", {}).get(nivel)
            if r:
                r.update(requisitos.resumir(r["texto"]))
    print("Resumen:", json.dumps(resumen, ensure_ascii=False))
    if not juegos:
        print("No hay ningún juego guardado. Algo falló al leer Steam; no publico una página vacía.")
        return 1
    paginas = Sitio(config, juegos, salida=os.environ.get("CEMP_SALIDA")).generar()
    print(f"Sitio generado: {paginas} páginas en el mapa del sitio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
