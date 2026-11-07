"""Descarga la lista de juegos populares y sus detalles desde APIs públicas (sin clave).

Si existe la variable CEMP_FIXTURES, lee archivos locales en vez de internet (pruebas).
"""
import json
import os
import time
import urllib.error
import urllib.request

AGENTE = "corre-en-mi-pc/1.0 (+https://github.com/mpereira17-uc/corre-en-mi-pc)"
MAS_JUGADOS = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
DESTACADOS = "https://store.steampowered.com/api/featuredcategories?cc=co&l=spanish"
STEAMSPY = "https://steamspy.com/api.php?request={}"
DETALLES = "https://store.steampowered.com/api/appdetails?appids={}&cc=co&l=spanish"


class LimiteSteam(Exception):
    """Steam respondió 429: hay que parar y seguir en la próxima ejecución."""


def _fixture(nombre):
    carpeta = os.environ.get("CEMP_FIXTURES")
    if not carpeta:
        return None
    ruta = os.path.join(carpeta, nombre)
    if not os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _get_json(url, intentos=3):
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise LimiteSteam(url) from e
            ultimo = e
        except Exception as e:  # red caída, JSON roto, etc.
            ultimo = e
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"No se pudo leer {url}: {ultimo}")


def ids_populares(limite=300):
    """Junta varias listas públicas y devuelve ids de Steam sin repetir, en orden."""
    if os.environ.get("CEMP_FIXTURES"):
        return [int(x) for x in (_fixture("lista.json") or [])][:limite]
    ids = []
    errores = []

    def agregar(lista):
        for x in lista:
            try:
                x = int(x)
            except (TypeError, ValueError):
                continue
            if x not in ids:
                ids.append(x)

    try:
        datos = _get_json(MAS_JUGADOS)
        agregar(r.get("appid") for r in datos.get("response", {}).get("ranks", []))
    except Exception as e:
        errores.append(f"más jugados: {e}")
    try:
        datos = _get_json(DESTACADOS)
        for cat in ("top_sellers", "new_releases", "specials"):
            agregar(i.get("id") for i in datos.get(cat, {}).get("items", []))
    except Exception as e:
        errores.append(f"destacados: {e}")
    for lista in ("top100in2weeks", "top100forever"):
        try:
            agregar(_get_json(STEAMSPY.format(lista)).keys())
        except Exception as e:
            errores.append(f"steamspy {lista}: {e}")
    for e in errores:
        print("Aviso:", e)
    return ids[:limite]


def detalles(appid):
    """Devuelve el bloque data de appdetails, o None si Steam no tiene el juego."""
    if os.environ.get("CEMP_FIXTURES"):
        crudo = _fixture(f"app_{appid}.json")
    else:
        crudo = _get_json(DETALLES.format(appid))
    bloque = (crudo or {}).get(str(appid)) or {}
    if not bloque.get("success"):
        return None
    return bloque.get("data")
