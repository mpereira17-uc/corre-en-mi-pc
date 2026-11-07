"""Convierte el HTML de requisitos de Steam en datos ordenados."""
import html
import re
import unicodedata

from . import hardware

ETIQUETAS = {
    "so": "so", "os": "so", "sistema operativo": "so", "sistema": "so",
    "procesador": "cpu", "processor": "cpu", "cpu": "cpu",
    "memoria": "ram", "memory": "ram", "ram": "ram", "memoria ram": "ram",
    "graficos": "gpu", "graphics": "gpu", "tarjeta grafica": "gpu", "video": "gpu",
    "tarjeta de video": "gpu", "gpu": "gpu",
    "directx": "directx", "version de directx": "directx",
    "almacenamiento": "disco", "storage": "disco", "espacio en disco": "disco",
    "disco duro": "disco", "hard drive": "disco", "hard disk space": "disco",
    "disco": "disco",
    "red": "red", "network": "red",
    "tarjeta de sonido": "sonido", "sound card": "sonido",
    "notas adicionales": "notas", "additional notes": "notas", "notas": "notas",
    "vr support": "notas", "compatibilidad con rv": "notas",
}

CAMPOS = ["so", "cpu", "ram", "gpu", "directx", "disco", "red", "sonido", "notas"]


def _sin_tildes(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower().strip()


def _texto(fragmento):
    t = re.sub(r"<[^>]+>", " ", fragmento)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip("  ")


def _trozos(bloque):
    """Separa el HTML en líneas: cada <li> o cada salto <br>."""
    if "<li" in bloque.lower():
        partes = re.findall(r"<li[^>]*>(.*?)(?=<li|</ul>|$)", bloque, flags=re.I | re.S)
    else:
        partes = re.split(r"<br\s*/?>", bloque, flags=re.I)
    return [_texto(p) for p in partes if _texto(p)]


def parsear(bloque):
    """Lee un bloque de requisitos (mínimos o recomendados) de Steam.

    Devuelve un diccionario con las claves de CAMPOS que se encontraron.
    """
    if not bloque or not isinstance(bloque, str):
        return {}
    resultado = {}
    for linea in _trozos(bloque):
        if ":" in linea:
            etiqueta, valor = linea.split(":", 1)
            clave = ETIQUETAS.get(_sin_tildes(etiqueta))
            valor = valor.strip()
            if clave and valor:
                if clave == "notas" and "notas" in resultado:
                    resultado["notas"] += " " + valor
                else:
                    resultado.setdefault(clave, valor)
                continue
            if _sin_tildes(etiqueta) in ("minimo", "minimum", "recomendado", "recommended"):
                if valor.strip():
                    linea = valor.strip()
                else:
                    continue
        # Líneas sin etiqueta, como "Requiere un procesador de 64 bits".
        if len(linea) > 3 and not _sin_tildes(linea).rstrip(":") in ("minimo", "minimum", "recomendado", "recommended"):
            resultado["notas"] = (resultado.get("notas", "") + " " + linea).strip()
    for clave in list(resultado):
        resultado[clave] = resultado[clave][:400]
    return resultado


def resumir(req):
    """Añade lo que se puede comparar: puntaje de GPU y CPU, RAM y disco en GB."""
    gpus = hardware.buscar_gpus(req.get("gpu", ""))
    cpus = hardware.buscar_cpus(req.get("cpu", ""))
    g = hardware.elegir_requisito(gpus)
    c = hardware.elegir_requisito(cpus)
    return {
        "gpu_pts": g[1] if g else None,
        "gpu_ref": g[0] if g else None,
        "gpu_modelos": [n for n, _ in gpus],
        "cpu_pts": c[1] if c else None,
        "cpu_ref": c[0] if c else None,
        "cpu_modelos": [n for n, _ in cpus],
        "ram_gb": hardware.numero_gb(req.get("ram")),
        "disco_gb": hardware.numero_gb(req.get("disco")),
    }


def de_steam(pc_requirements):
    """Recibe el campo pc_requirements de appdetails y devuelve mínimos y recomendados."""
    if isinstance(pc_requirements, list) or not pc_requirements:
        return None
    minimo = parsear(pc_requirements.get("minimum", ""))
    recomendado = parsear(pc_requirements.get("recommended", ""))
    if not minimo and not recomendado:
        return None
    salida = {}
    if minimo:
        salida["min"] = {"texto": minimo, **resumir(minimo)}
    if recomendado:
        salida["rec"] = {"texto": recomendado, **resumir(recomendado)}
    return salida
