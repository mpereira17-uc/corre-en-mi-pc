"""Tablas de tarjetas gráficas y procesadores con una puntuación aproximada.

La puntuación es relativa y sirve solo para comparar:
- Tarjetas gráficas: GTX 1060 6 GB = 100.
- Procesadores (rendimiento en juegos): Intel Core i5-4460 = 100.

Son valores aproximados sacados de comparativas públicas de rendimiento. No son
benchmarks exactos: la página siempre lo dice y muestra el texto original de Steam.
"""
import re
import unicodedata

GPUS = {
    # NVIDIA GeForce
    "GT 710": 8, "GT 730": 10, "GT 640": 14, "GT 1030": 25,
    "GTX 460": 18, "GTX 560": 25, "GTX 560 Ti": 28, "GTX 570": 32, "GTX 580": 36,
    "GTX 650": 18, "GTX 650 Ti": 26, "GTX 660": 42, "GTX 660 Ti": 48, "GTX 670": 55,
    "GTX 680": 60, "GTX 750": 30, "GTX 750 Ti": 35, "GTX 760": 50, "GTX 770": 62,
    "GTX 780": 72, "GTX 780 Ti": 82, "GTX 950": 50, "GTX 960": 58, "GTX 970": 82,
    "GTX 980": 95, "GTX 980 Ti": 120, "GTX 1050": 48, "GTX 1050 Ti": 58,
    "GTX 1060 3GB": 92, "GTX 1060": 100, "GTX 1070": 130, "GTX 1070 Ti": 145,
    "GTX 1080": 160, "GTX 1080 Ti": 205, "GTX 1630": 45, "GTX 1650": 68,
    "GTX 1650 Super": 90, "GTX 1660": 110, "GTX 1660 Super": 125, "GTX 1660 Ti": 128,
    "RTX 2060": 150, "RTX 2060 Super": 172, "RTX 2070": 180, "RTX 2070 Super": 200,
    "RTX 2080": 215, "RTX 2080 Super": 225, "RTX 2080 Ti": 265,
    "RTX 3050": 135, "RTX 3060": 180, "RTX 3060 Ti": 225, "RTX 3070": 255,
    "RTX 3070 Ti": 270, "RTX 3080": 320, "RTX 3080 Ti": 345, "RTX 3090": 355,
    "RTX 3090 Ti": 380, "RTX 4060": 205, "RTX 4060 Ti": 245, "RTX 4070": 300,
    "RTX 4070 Super": 345, "RTX 4070 Ti": 370, "RTX 4070 Ti Super": 395,
    "RTX 4080": 445, "RTX 4080 Super": 455, "RTX 4090": 560, "RTX 5060": 240,
    "RTX 5060 Ti": 280, "RTX 5070": 360, "RTX 5070 Ti": 440, "RTX 5080": 495,
    "RTX 5090": 700,
    # AMD Radeon
    "HD 5770": 15, "HD 6870": 22, "HD 7770": 25, "HD 7850": 40, "HD 7870": 48,
    "HD 7950": 55, "HD 7970": 62, "R7 260X": 30, "R7 370": 42, "R9 270": 45,
    "R9 270X": 50, "R9 280": 58, "R9 280X": 65, "R9 290": 80, "R9 290X": 85,
    "R9 380": 70, "R9 390": 92, "R9 390X": 98, "R9 Fury": 108, "RX 460": 38,
    "RX 470": 85, "RX 480": 98, "RX 550": 28, "RX 560": 42, "RX 570": 90,
    "RX 580": 100, "RX 590": 110, "RX Vega 56": 140, "RX Vega 64": 155,
    "RX 5500 XT": 98, "RX 5600 XT": 140, "RX 5700": 160, "RX 5700 XT": 178,
    "RX 6400": 62, "RX 6500 XT": 75, "RX 6600": 165, "RX 6600 XT": 185,
    "RX 6650 XT": 195, "RX 6700": 200, "RX 6700 XT": 225, "RX 6750 XT": 235,
    "RX 6800": 280, "RX 6800 XT": 320, "RX 6900 XT": 340, "RX 6950 XT": 360,
    "RX 7600": 200, "RX 7600 XT": 210, "RX 7700 XT": 285, "RX 7800 XT": 340,
    "RX 7900 GRE": 365, "RX 7900 XT": 420, "RX 7900 XTX": 480, "RX 9060 XT": 260,
    "RX 9070": 400, "RX 9070 XT": 440,
    # Intel Arc
    "Arc A380": 60, "Arc A580": 140, "Arc A750": 165, "Arc A770": 180,
    "Arc B570": 190, "Arc B580": 215,
    # Antiguas (juegos viejos las piden)
    "GeForce 8600": 4, "9600 GT": 6, "9800 GT": 8, "GTX 260": 10, "GTX 285": 13,
    "GTX 600": 18, "HD 2600": 3, "HD 4850": 9, "HD 4870": 10, "HD 5450": 2,
    "HD 7000": 25,
    # Gráficos integrados
    "Intel HD Graphics 4000": 6, "Intel HD Graphics 520": 9, "Intel HD Graphics 620": 9,
    "Intel UHD Graphics 620": 10, "Intel UHD Graphics 630": 10, "Intel Iris Xe": 25,
    "Radeon Vega 8": 22, "Radeon Vega 11": 28, "Radeon 680M": 60, "Radeon 780M": 75,
}

CPUS = {
    # Intel
    "Core 2 Duo E8400": 25, "Core 2 Quad Q6600": 35, "Core 2 Quad Q9550": 45,
    "i3-2100": 45, "i3-3220": 50, "i3-4130": 55, "i3-4160": 56, "i3-6100": 65,
    "i3-7100": 70, "i3-8100": 90, "i3-9100": 95, "i3-10100": 120, "i3-12100": 165,
    "i3-13100": 175, "i5-750": 55, "i5-2400": 75, "i5-2500K": 82, "i5-3330": 82,
    "i5-3470": 88, "i5-3570K": 92, "i5-4440": 95, "i5-4460": 100, "i5-4590": 105,
    "i5-4670K": 108, "i5-4690K": 112, "i5-6400": 105, "i5-6500": 110, "i5-6600K": 120,
    "i5-7400": 115, "i5-7500": 120, "i5-7600K": 130, "i5-8400": 150, "i5-8600K": 165,
    "i5-9400": 155, "i5-9600K": 172, "i5-10400": 175, "i5-10600K": 195,
    "i5-11400": 200, "i5-11600K": 215, "i5-12400": 235, "i5-12600K": 280,
    "i5-13400": 255, "i5-13600K": 320, "i5-14400": 265, "i5-14600K": 335,
    "i7-920": 60, "i7-2600": 90, "i7-3770": 100, "i7-4770": 115, "i7-4790": 125,
    "i7-6700": 135, "i7-7700": 145, "i7-8700": 180, "i7-9700K": 200, "i7-10700": 220,
    "i7-11700K": 240, "i7-12700": 310, "i7-13700K": 370, "i7-14700K": 400,
    "i9-9900K": 220, "i9-10900K": 245, "i9-12900K": 345, "i9-13900K": 410,
    "i9-14900K": 420, "Core Ultra 5 245K": 330, "Core Ultra 7 265K": 390,
    "Core Ultra 9 285K": 430,
    "i3-330M": 15, "i3-530": 30, "i3-3210": 48, "i3-3250": 52, "i3-4170": 57,
    "i3-4360": 58, "i3-6300": 68, "i3-10110U": 55, "i5-760": 57, "i5-2300": 70,
    "i5-6600": 118, "i5-8500": 145, "i5-8600": 158, "i5-9500": 150, "i5-10500": 180,
    "Core 2 Duo E6600": 18, "Pentium 4": 8, "Pentium G4560": 55,
    # AMD
    "Athlon 64": 8, "Athlon X2": 14, "Athlon II X2 245": 22, "Phenom X3 8750": 20,
    "Phenom 9850": 28, "FX-4100": 40, "FX-4350": 48, "FX-8120": 62, "FX-8320": 70,
    "A6-5200": 12, "A8-7650K": 40, "Ryzen 5 3500": 165,
    "Athlon II X2": 25, "Phenom II X4 965": 50, "FX-4300": 45, "FX-6300": 60,
    "FX-8150": 65, "FX-8350": 75, "Athlon 3000G": 55, "Ryzen 3 1200": 85,
    "Ryzen 3 1300X": 95, "Ryzen 3 2200G": 90, "Ryzen 3 3200G": 100, "Ryzen 3 3100": 125,
    "Ryzen 3 3300X": 145, "Ryzen 5 1400": 105, "Ryzen 5 1500X": 115, "Ryzen 5 1600": 130,
    "Ryzen 5 2600": 145, "Ryzen 5 2600X": 150, "Ryzen 5 3600": 180, "Ryzen 5 3600X": 185,
    "Ryzen 5 4500": 175, "Ryzen 5 5500": 200, "Ryzen 5 5600": 230, "Ryzen 5 5600X": 235,
    "Ryzen 5 5600G": 205, "Ryzen 5 7600": 290, "Ryzen 5 7600X": 300, "Ryzen 5 8600G": 270,
    "Ryzen 5 9600X": 330, "Ryzen 7 1700": 140, "Ryzen 7 2700": 160, "Ryzen 7 2700X": 165,
    "Ryzen 7 3700X": 205, "Ryzen 7 3800X": 210, "Ryzen 7 5700X": 250, "Ryzen 7 5800X": 260,
    "Ryzen 7 5800X3D": 300, "Ryzen 7 7700X": 330, "Ryzen 7 7800X3D": 380,
    "Ryzen 7 9700X": 360, "Ryzen 7 9800X3D": 430, "Ryzen 9 3900X": 220,
    "Ryzen 9 5900X": 275, "Ryzen 9 5950X": 285, "Ryzen 9 7950X": 380, "Ryzen 9 9950X": 420,
}


# Nombres genéricos ("Intel Core i5" sin modelo). Solo cuentan si después no viene un número,
# para que un "i5-11500" que no está en la tabla no se lea como un i5 viejo.
CPUS_GENERICAS = {
    "Core 2 Duo": 20, "Core i3": 50, "Core i5": 80, "Core i7": 100,
    "Ryzen 3": 85, "Ryzen 5": 130, "Ryzen 7": 150,
}


def normalizar(texto):
    """Pasa a minúsculas, quita tildes y separa letras de números ("gtx1060" -> "gtx 1060")."""
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    t = t.lower().replace("(tm)", " ").replace("(r)", " ").replace("™", " ").replace("®", " ")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"([a-z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([a-z])", r"\1 \2", t)
    return " " + re.sub(r"\s+", " ", t).strip() + " "


def _patrones(tabla):
    # Primero las claves más largas, para que "rtx 3060 ti" gane a "rtx 3060".
    claves = sorted(tabla, key=lambda k: len(normalizar(k)), reverse=True)
    return [(k, normalizar(k)) for k in claves]


_GPU_PATRONES = _patrones(GPUS)
_CPU_PATRONES = _patrones(CPUS)


def _buscar(texto, patrones, tabla):
    t = normalizar(texto)
    encontrados = []
    for nombre, patron in patrones:
        pos = t.find(patron)
        if pos != -1:
            encontrados.append((pos, nombre))
            t = t.replace(patron, " | " + " " * (len(patron) - 3))  # misma longitud: no mueve posiciones
    return [(n, tabla[n]) for _, n in sorted(encontrados)]


def buscar_gpus(texto):
    """Devuelve las tarjetas conocidas que aparecen en un texto de requisitos."""
    return _buscar(texto, _GPU_PATRONES, GPUS)


def buscar_cpus(texto):
    encontrados = _buscar(texto, _CPU_PATRONES, CPUS)
    if encontrados:
        return encontrados
    t = normalizar(texto)
    for nombre, pts in sorted(CPUS_GENERICAS.items(), key=lambda e: -len(e[0])):
        clave = normalizar(nombre).strip().replace("core ", "")  # "i 5", "ryzen 5"
        if re.search(r"(^| )" + re.escape(clave) + r"(?! ?\d{3})", t.strip()):
            return [(nombre, pts)]
    if re.search(r"quad|4 core|cuatro nucleos|4 nucleos", t):
        return [("CPU de 4 núcleos", 40)]
    if re.search(r"ghz|dual|doble nucleo|pentium|athlon", t):
        return [("CPU básica", 15)]
    return []


def buscar_gpus_con_respaldo(texto):
    """Como buscar_gpus, pero si el juego solo pide "1 GB de VRAM" o "compatible con DirectX 11"
    lo cuenta como gráfica básica: cualquier tarjeta de los últimos diez años la supera."""
    encontrados = buscar_gpus(texto)
    if encontrados:
        return encontrados
    t = normalizar(texto)
    vram = numero_gb(texto)
    if (vram is not None and vram <= 2) or re.search(r"directx|shader|opengl|vulkan|compatible", t):
        return [("Gráfica básica", 8)]
    return []


SECUNDARIAS = ("Arc ", "Intel ", "Radeon Vega", "Radeon 680M", "Radeon 780M")


def elegir_requisito(encontrados):
    """Si el juego pide "GTX 970 o RX 480", basta con igualar a la más débil de las dos.

    Las Intel Arc y las integradas se ignoran cuando hay alternativas NVIDIA/AMD, porque los
    estudios suelen ponerlas como equivalentes aproximados. Devuelve (nombre, puntos) o None.
    """
    principales = [e for e in encontrados if not e[0].startswith(SECUNDARIAS)] or encontrados
    if not principales:
        return None
    return min(principales, key=lambda e: e[1])


def puntaje_requisito(encontrados):
    e = elegir_requisito(encontrados)
    return e[1] if e else None


def numero_gb(texto):
    """Lee "8 GB de RAM" -> 8.0 o "512 MB" -> 0.5. Devuelve None si no hay cifra."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(tb|gb|mb|go|mo)\b", str(texto or "").lower())
    if not m:
        return None
    valor = float(m.group(1).replace(",", "."))
    unidad = m.group(2)
    if unidad in ("mb", "mo"):
        valor = valor / 1024
    elif unidad == "tb":
        valor = valor * 1024
    return round(valor, 2)
