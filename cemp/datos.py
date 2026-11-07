"""Guarda y actualiza la base de juegos (data/juegos.json)."""
import datetime as dt
import json
import os
import re
import time
import unicodedata

from . import requisitos, steam

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO = os.environ.get("CEMP_JUEGOS", os.path.join(RAIZ, "data", "juegos.json"))
EXCLUIDOS = os.environ.get("CEMP_EXCLUIDOS", os.path.join(RAIZ, "data", "excluidos.json"))

# Descriptores de contenido de Steam: 3 = contenido sexual solo para adultos, 4 = desnudez frecuente.
DESCRIPTORES_ADULTOS = {3, 4}


def hoy():
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def slugify(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:70].strip("-") or "juego"


def leer(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defecto


def guardar(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, ruta)


def es_para_adultos(data):
    ids = set((data.get("content_descriptors") or {}).get("ids") or [])
    return bool(ids & DESCRIPTORES_ADULTOS)


def ficha(data, slug):
    """Convierte la respuesta de Steam en el registro que guardamos."""
    req = requisitos.de_steam(data.get("pc_requirements"))
    if not req:
        return None
    precio = data.get("price_overview") or {}
    return {
        "id": int(data["steam_appid"]),
        "slug": slug,
        "nombre": str(data.get("name", "")).strip()[:120],
        "imagen": data.get("header_image", ""),
        "descripcion": re.sub(r"\s+", " ", str(data.get("short_description", ""))).strip()[:300],
        "generos": [g.get("description", "") for g in (data.get("genres") or [])][:4],
        "desarrolladores": (data.get("developers") or [])[:2],
        "fecha": (data.get("release_date") or {}).get("date", ""),
        "proximamente": bool((data.get("release_date") or {}).get("coming_soon")),
        "gratis": bool(data.get("is_free")),
        "precio": precio.get("final_formatted", ""),
        "descuento": int(precio.get("discount_percent") or 0),
        "req": req,
        "actualizado": hoy(),
    }


def actualizar(config, pausa=1.6):
    """Descarga lo nuevo y refresca los juegos más viejos. Devuelve un resumen."""
    juegos = {str(j["id"]): j for j in leer(ARCHIVO, [])}
    excluidos = leer(EXCLUIDOS, {})
    limite_dias = dt.date.fromisoformat(hoy()) - dt.timedelta(days=30)
    excluidos = {k: v for k, v in excluidos.items() if dt.date.fromisoformat(v) > limite_dias}

    ids = steam.ids_populares(config.get("max_juegos", 300))
    for pos, appid in enumerate(ids, start=1):
        if str(appid) in juegos:
            juegos[str(appid)]["puesto"] = pos
    puestos = {appid: pos for pos, appid in enumerate(ids, start=1)}

    nuevos = [a for a in ids if str(a) not in juegos and str(a) not in excluidos]
    viejos = sorted(juegos.values(), key=lambda j: j.get("actualizado", ""))
    cola = nuevos + [j["id"] for j in viejos if j.get("actualizado") != hoy()]
    cola = cola[: config.get("detalles_por_ejecucion", 150)]

    usados = {j["slug"] for j in juegos.values()}
    resumen = {"nuevos": 0, "actualizados": 0, "excluidos": 0, "errores": 0, "limite": False}
    for appid in cola:
        try:
            data = steam.detalles(appid)
        except steam.LimiteSteam:
            resumen["limite"] = True
            print("Steam pidió esperar (429). Sigo en la próxima ejecución.")
            break
        except Exception as e:
            resumen["errores"] += 1
            print(f"Error con {appid}: {e}")
            continue
        finally:
            if not os.environ.get("CEMP_FIXTURES"):
                time.sleep(pausa)
        if not data or data.get("type") != "game" or es_para_adultos(data):
            excluidos[str(appid)] = hoy()
            juegos.pop(str(appid), None)
            resumen["excluidos"] += 1
            continue
        previo = juegos.get(str(appid))
        if previo:
            slug = previo["slug"]
        else:
            base = slugify(str(data.get("name", appid)))
            slug = base if base not in usados else f"{base}-{appid}"
            usados.add(slug)
        nueva = ficha(data, slug)
        if not nueva:
            excluidos[str(appid)] = hoy()
            resumen["excluidos"] += 1
            continue
        nueva["puesto"] = puestos.get(appid, previo.get("puesto", 999) if previo else 999)
        juegos[str(appid)] = nueva
        resumen["actualizados" if previo else "nuevos"] += 1

    # Los que salieron de las listas siguen publicados (sus páginas ya están en Google).
    for j in juegos.values():
        if j["id"] not in puestos:
            j["puesto"] = 999
    lista = sorted(juegos.values(), key=lambda j: (j.get("puesto", 999), j["nombre"].lower()))
    guardar(ARCHIVO, lista)
    guardar(EXCLUIDOS, excluidos)
    resumen["total"] = len(lista)
    return lista, resumen
