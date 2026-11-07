"""Genera el sitio estático en docs/ a partir de data/juegos.json."""
import datetime as dt
import html
import json
import os
import shutil
from urllib.parse import urlencode

from . import hardware
from .datos import RAIZ, slugify

ROTULOS = {
    "so": "Sistema operativo", "cpu": "Procesador", "ram": "Memoria RAM",
    "gpu": "Tarjeta gráfica", "directx": "DirectX", "disco": "Almacenamiento",
    "red": "Internet", "sonido": "Sonido", "notas": "Notas",
}
ORDEN_FILAS = ["so", "cpu", "gpu", "ram", "disco", "directx", "red", "notas"]

# Tarjetas con página propia "Juegos que corren con ..."
GPUS_CON_PAGINA = [
    "Intel UHD Graphics 630", "Intel Iris Xe", "Radeon Vega 8", "GT 1030", "GTX 750 Ti",
    "GTX 1050 Ti", "GTX 1060", "GTX 1650", "GTX 1660 Super", "RTX 2060", "RTX 3050",
    "RTX 3060", "RTX 3070", "RTX 4060", "RTX 4070", "RTX 5060", "RX 580", "RX 6600",
    "RX 7600", "Arc A750",
]
RAM_CON_PAGINA = [4, 8, 16]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def esc(t):
    return html.escape(str(t if t is not None else ""), quote=True)


def fecha_larga(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def slug_gpu(nombre):
    return "juegos-para-" + slugify(nombre)


class Sitio:
    def __init__(self, config, juegos, salida=None):
        self.cfg = config
        self.juegos = [j for j in juegos if j.get("req")]
        self.salida = salida or os.path.join(RAIZ, "docs")
        self.base = config["url_base"].rstrip("/")
        self.hoy = dt.datetime.now(dt.timezone.utc).date().isoformat()
        self.paginas = []  # para el sitemap

    # ---------- piezas comunes ----------
    def icono(self, nombre):
        trazos = {
            "chip": '<rect x="7" y="7" width="10" height="10" rx="1.5"/><path d="M9.5 3v4M14.5 3v4M9.5 17v4M14.5 17v4M3 9.5h4M3 14.5h4M17 9.5h4M17 14.5h4"/>',
            "buscar": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
            "flecha": '<path d="M5 12h14M13 6l6 6-6 6"/>',
            "externo": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
            "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
            "x": '<path d="M6 6l12 12M18 6 6 18"/>',
        }[nombre]
        return (f'<svg class="i" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
                f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{trazos}</svg>')

    def pagina(self, archivo, titulo, descripcion, cuerpo, clase="", jsonld=None, prioridad="0.6"):
        canon = f"{self.base}/" if archivo == "index.html" else f"{self.base}/{archivo}"
        self.paginas.append((canon, prioridad))
        ld = ""
        for bloque in jsonld or []:
            # json.dumps escapa comillas; además evitamos que "</" cierre el script.
            ld += '<script type="application/ld+json">' + json.dumps(bloque, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e") + "</script>\n"
        nav = [("index.html", "Juegos"), ("tarjetas-graficas.html", "Por tarjeta gráfica"),
               ("mi-pc.html", "Mi PC"), ("como-funciona.html", "Cómo funciona")]
        enlaces = "".join(
            f'<a href="{a}"{" aria-current=\"page\"" if a == archivo else ""}>{esc(t)}</a>' for a, t in nav)
        csp = ("default-src 'self'; img-src 'self' https: data:; script-src 'self'; style-src 'self'; "
               "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'")
        doc = f"""<!doctype html>
<html lang="es-CO">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(descripcion)}">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(descripcion)}">
<meta property="og:url" content="{esc(canon)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_CO">
<meta name="theme-color" content="#0d1014">
<link rel="icon" href="assets/icono.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/chakra-petch-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/estilo.css">
{ld}</head>
<body class="{esc(clase)}">
<a class="saltar" href="#contenido">Saltar al contenido</a>
<header class="cabecera">
  <div class="envoltura cabecera__fila">
    <a class="marca" href="index.html">{self.icono("chip")}<span>¿Corre en mi PC?</span></a>
    <nav class="menu" aria-label="Principal">{enlaces}</nav>
    <a class="mipc-chip" href="mi-pc.html" data-mipc-chip>Configura tu PC</a>
  </div>
</header>
<main id="contenido">
{cuerpo}
</main>
<footer class="pie">
  <div class="envoltura pie__fila">
    <p>Requisitos tomados de Steam y actualizados cada día. La comparación es aproximada: revisa siempre la ficha oficial del juego.</p>
    <p>Algunos enlaces son de afiliado: si compras, la página gana una comisión y a ti no te cuesta más. <a href="como-funciona.html">Cómo funciona</a> · <a href="como-funciona.html#privacidad">Privacidad</a></p>
    <p class="pie__fecha">Última actualización: {fecha_larga(self.hoy)}</p>
  </div>
</footer>
<script src="assets/app.js" defer></script>
</body>
</html>
"""
        ruta = os.path.join(self.salida, archivo)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(doc)

    def datos_req(self, j):
        """Atributos data-* que usa app.js para calcular si el juego corre."""
        partes = []
        for nivel in ("min", "rec"):
            r = j["req"].get(nivel) or {}
            for clave, campo in (("g", "gpu_pts"), ("c", "cpu_pts"), ("r", "ram_gb")):
                v = r.get(campo)
                if v is not None:
                    partes.append(f'data-{nivel}-{clave}="{esc(v)}"')
        return " ".join(partes)

    def formulario_pc(self, titulo="Tu PC", compacto=False):
        opciones_ram = "".join(f'<option value="{g}">{g} GB</option>' for g in (2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64))
        return f"""<form class="pc{' pc--compacto' if compacto else ''}" data-pc-form novalidate>
  <h2 class="pc__titulo">{esc(titulo)}</h2>
  <label class="campo">
    <span>Tarjeta gráfica</span>
    <input name="gpu" list="lista-gpu" autocomplete="off" placeholder="Ej.: GTX 1650" spellcheck="false">
  </label>
  <label class="campo">
    <span>Procesador</span>
    <input name="cpu" list="lista-cpu" autocomplete="off" placeholder="Ej.: Ryzen 5 3600" spellcheck="false">
  </label>
  <label class="campo">
    <span>Memoria RAM</span>
    <select name="ram"><option value="">Elige</option>{opciones_ram}</select>
  </label>
  <datalist id="lista-gpu"></datalist>
  <datalist id="lista-cpu"></datalist>
  <div class="pc__acciones">
    <button class="boton" type="submit">Guardar mi PC</button>
    <a class="enlace-suave" href="mi-pc.html#como-saber">¿No sabes qué tienes?</a>
  </div>
  <p class="pc__estado" data-pc-estado role="status" aria-live="polite"></p>
</form>"""

    def fila_juego(self, j, mostrar_puesto=True):
        m = j["req"].get("min") or {}
        gpu = m.get("gpu_ref")
        ram = m.get("ram_gb")
        meta = []
        if gpu:
            meta.append(f"Gráfica mín. {esc(gpu)}")
        if ram:
            meta.append(f"{ram:g} GB RAM")
        puesto = f'<span class="fila__puesto">{j["puesto"]}</span>' if mostrar_puesto and j.get("puesto", 999) < 999 else '<span class="fila__puesto">·</span>'
        return f"""<li class="fila" data-n="{esc(j['nombre'].lower())}" {self.datos_req(j)}>
  <a href="requisitos-{esc(j['slug'])}.html">
    {puesto}
    <img src="{esc(j['imagen'])}" alt="" width="120" height="56" loading="lazy" decoding="async">
    <span class="fila__texto"><strong>{esc(j['nombre'])}</strong><small>{' · '.join(meta) or 'Ver requisitos'}</small></span>
    <span class="veredicto" data-veredicto>Ver</span>
  </a>
</li>"""

    # ---------- páginas ----------
    def portada(self):
        filas = "\n".join(self.fila_juego(j) for j in self.juegos)
        atajos = " ".join(f'<a href="{slug_gpu(g)}.html">{esc(g)}</a>' for g in
                          ("GTX 1650", "GTX 1060", "RTX 3060", "RTX 4060", "RX 580", "Intel UHD Graphics 630"))
        cuerpo = f"""<section class="portada envoltura">
  <div class="portada__texto">
    <h1>¿Tu PC aguanta el juego?</h1>
    <p class="entrada">Dinos qué tarjeta gráfica, procesador y RAM tienes. Te mostramos al instante qué juegos de Steam corren y con qué calidad.</p>
    <label class="buscador">
      {self.icono("buscar")}
      <span class="oculto">Buscar un juego</span>
      <input type="search" data-buscar placeholder="Busca un juego: Cyberpunk, Elden Ring, Valorant…" autocomplete="off" spellcheck="false">
    </label>
    <p class="atajos"><span>Listas por tarjeta:</span> {atajos}</p>
  </div>
  {self.formulario_pc()}
</section>
<section class="envoltura listado" aria-labelledby="t-lista">
  <div class="listado__cabeza">
    <h2 id="t-lista">Los {len(self.juegos)} juegos más jugados en Steam</h2>
    <div class="filtros" role="group" aria-label="Filtrar">
      <button type="button" class="filtro" aria-pressed="true" data-filtro="todos">Todos</button>
      <button type="button" class="filtro" aria-pressed="false" data-filtro="si">Corren</button>
      <button type="button" class="filtro" aria-pressed="false" data-filtro="rec">Corren en alto</button>
      <button type="button" class="filtro" aria-pressed="false" data-filtro="no">No corren</button>
    </div>
  </div>
  <p class="listado__aviso" data-sin-pc>Guarda tu PC arriba para ver en cada juego si corre.</p>
  <ol class="filas" data-lista>
{filas}
  </ol>
  <p class="vacio" data-vacio hidden>No hay juegos con ese filtro. Prueba con otro nombre o quita el filtro.</p>
</section>"""
        ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "¿Corre en mi PC?",
               "url": self.base + "/", "inLanguage": "es-CO"}]
        self.pagina("index.html", "¿Corre en mi PC? Requisitos de juegos y si tu computador los aguanta",
                    "Mira los requisitos mínimos y recomendados de los juegos de Steam y descubre al instante si tu PC los corre. En español, gratis y actualizado cada día.",
                    cuerpo, "inicio", ld, "1.0")

    def tabla_requisitos(self, j):
        mn = (j["req"].get("min") or {}).get("texto", {})
        rc = (j["req"].get("rec") or {}).get("texto", {})
        filas = []
        for clave in ORDEN_FILAS:
            a, b = mn.get(clave), rc.get(clave)
            if not a and not b:
                continue
            filas.append(f'<tr><th scope="row">{ROTULOS[clave]}</th><td data-l="Mínimo">{esc(a or "—")}</td><td data-l="Recomendado">{esc(b or "—")}</td></tr>')
        tiene_rec = bool(rc)
        cabeza = '<tr><th scope="col"><span class="oculto">Componente</span></th><th scope="col">Mínimos</th><th scope="col">Recomendados</th></tr>'
        nota = "" if tiene_rec else '<p class="nota">Steam no publica requisitos recomendados para este juego.</p>'
        return f'<div class="tabla-envoltura"><table class="tabla"><thead>{cabeza}</thead><tbody>{"".join(filas)}</tbody></table></div>{nota}'

    def preguntas(self, j):
        n = j["nombre"]
        mn = j["req"].get("min") or {}
        rc = j["req"].get("rec") or {}
        qa = []
        if mn.get("ram_gb") or rc.get("ram_gb"):
            r = f"Como mínimo pide {mn['ram_gb']:g} GB de RAM" if mn.get("ram_gb") else "Steam no indica la RAM mínima"
            if rc.get("ram_gb"):
                r += f", y para jugar con buena calidad se recomiendan {rc['ram_gb']:g} GB"
            qa.append((f"¿Cuánta RAM necesita {n}?", r + "."))
        if mn.get("texto", {}).get("gpu"):
            r = f"La gráfica mínima que indica Steam es: {mn['texto']['gpu']}"
            if rc.get("texto", {}).get("gpu"):
                r += f". La recomendada es: {rc['texto']['gpu']}"
            qa.append((f"¿Qué tarjeta gráfica necesita {n}?", r + "."))
        if mn.get("disco_gb"):
            qa.append((f"¿Cuánto pesa {n}?", f"Necesitas unos {mn['disco_gb']:g} GB libres en el disco, según la ficha de Steam."))
        if mn.get("gpu_pts") is not None and mn["gpu_pts"] <= hardware.GPUS["GTX 1050 Ti"]:
            qa.append((f"¿{n} corre en un PC de gama baja?", "Sí, sus requisitos mínimos de gráfica son bajos: una GTX 1050 Ti o similar alcanza para jugarlo en calidad baja."))
        return qa

    def similares(self, j, n=6):
        base = (j["req"].get("min") or {}).get("gpu_pts")
        if base is None:
            return []
        otros = [o for o in self.juegos if o["id"] != j["id"] and (o["req"].get("min") or {}).get("gpu_pts") is not None]
        otros.sort(key=lambda o: (abs(o["req"]["min"]["gpu_pts"] - base), o.get("puesto", 999)))
        return otros[:n]

    def enlace_ig(self, nombre):
        igr = self.cfg.get("instant_gaming_igr")
        if not igr:
            return ""
        return "https://www.instant-gaming.com/es/busquedas/?" + urlencode({"q": nombre, "igr": igr})

    def ficha_juego(self, j):
        n = j["nombre"]
        mn = j["req"].get("min") or {}
        rc = j["req"].get("rec") or {}
        compras = [f'<a class="tienda" href="https://store.steampowered.com/app/{j["id"]}/" rel="noopener" target="_blank">'
                   f'<span>Steam</span><strong>{esc("Gratis" if j.get("gratis") else (j.get("precio") or "Ver precio"))}</strong>'
                   f'{"<em>-" + str(j["descuento"]) + "%</em>" if j.get("descuento") else ""}{self.icono("externo")}</a>']
        ig = self.enlace_ig(n)
        if ig and not j.get("gratis"):
            compras.append(f'<a class="tienda" href="{esc(ig)}" rel="sponsored noopener" target="_blank">'
                           f'<span>Instant Gaming</span><strong>Buscar clave</strong>{self.icono("externo")}</a>')
        qa = self.preguntas(j)
        faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in qa)
        sim = self.similares(j)
        sim_html = "".join(self.fila_juego(o, mostrar_puesto=False) for o in sim)
        componentes = []
        for clave, rotulo, campo in (("g", "Tarjeta gráfica", "gpu"), ("c", "Procesador", "cpu"), ("r", "Memoria RAM", "ram")):
            componentes.append(
                f'<div class="medidor" data-medidor="{clave}" '
                f'data-min-nombre="{esc(mn.get(campo + "_ref") or "")}" '
                f'data-rec-nombre="{esc(rc.get(campo + "_ref") or "")}">'
                f'<div class="medidor__cabeza"><span>{rotulo}</span><span class="medidor__estado" data-estado>—</span></div>'
                f'<div class="medidor__barra"><span class="medidor__relleno" data-relleno></span>'
                f'<span class="medidor__marca medidor__marca--min" data-marca-min hidden></span>'
                f'<span class="medidor__marca medidor__marca--rec" data-marca-rec hidden></span></div>'
                f'<p class="medidor__detalle" data-detalle></p></div>')
        ld = [{
            "@context": "https://schema.org", "@type": "VideoGame", "name": n,
            "url": f"{self.base}/requisitos-{j['slug']}.html", "image": j.get("imagen"),
            "gamePlatform": "PC", "operatingSystem": mn.get("texto", {}).get("so", "Windows"),
            "applicationCategory": "Game", "genre": j.get("generos") or None,
            "memoryRequirements": mn.get("texto", {}).get("ram"),
            "processorRequirements": mn.get("texto", {}).get("cpu"),
            "storageRequirements": mn.get("texto", {}).get("disco"),
        }]
        ld[0] = {k: v for k, v in ld[0].items() if v}
        if qa:
            ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]})
        sub = " · ".join(x for x in [", ".join(j.get("desarrolladores") or []), j.get("fecha", "")] if x)
        cuerpo = f"""<div class="envoltura ficha">
  <nav class="migas" aria-label="Ruta"><a href="index.html">Juegos</a><span aria-hidden="true">/</span><span>{esc(n)}</span></nav>
  <header class="ficha__cabeza">
    <img class="ficha__portada" src="{esc(j['imagen'])}" alt="Portada de {esc(n)}" width="460" height="215" fetchpriority="high">
    <div>
      <h1>Requisitos de {esc(n)} para PC</h1>
      <p class="entrada">{esc(j.get('descripcion') or 'Requisitos mínimos y recomendados, y si tu computador lo corre.')}</p>
      <p class="sub">{esc(sub)}</p>
    </div>
  </header>
  <section class="juicio" data-juicio {self.datos_req(j)} aria-labelledby="t-juicio">
    <div class="juicio__cabeza">
      <h2 id="t-juicio" data-juicio-titulo>¿Lo corre tu PC?</h2>
      <p class="juicio__texto" data-juicio-texto>Guarda tu tarjeta gráfica, procesador y RAM para saberlo.</p>
    </div>
    <div class="medidores" data-medidores hidden>{"".join(componentes)}
      <p class="medidores__leyenda"><span class="ley ley--min"></span>Mínimo <span class="ley ley--rec"></span>Recomendado <span class="ley ley--tu"></span>Tu PC</p>
    </div>
    <div data-juicio-form>{self.formulario_pc("Escribe tu PC", compacto=True)}</div>
    <button type="button" class="enlace-suave" data-cambiar-pc hidden>Cambiar mi PC</button>
  </section>
  <section aria-labelledby="t-req">
    <h2 id="t-req">Requisitos mínimos y recomendados</h2>
    {self.tabla_requisitos(j)}
    <p class="fuente">Fuente: ficha oficial de Steam, revisada el {fecha_larga(j.get('actualizado', self.hoy))}.</p>
  </section>
  <section aria-labelledby="t-comprar">
    <h2 id="t-comprar">Dónde conseguirlo</h2>
    <div class="tiendas">{"".join(compras)}</div>
    <p class="nota">El precio de Steam es el de Colombia al momento de la revisión. Puede cambiar.</p>
  </section>
  {f'<section aria-labelledby="t-faq"><h2 id="t-faq">Preguntas frecuentes</h2><div class="faq">{faq_html}</div></section>' if qa else ''}
  {f'<section aria-labelledby="t-sim"><h2 id="t-sim">Juegos con requisitos parecidos</h2><ol class="filas filas--cortas">{sim_html}</ol></section>' if sim else ''}
</div>"""
        desc_ram = f" Pide {mn['ram_gb']:g} GB de RAM como mínimo." if mn.get("ram_gb") else ""
        self.pagina(f"requisitos-{j['slug']}.html", f"Requisitos de {n} para PC: mínimos, recomendados y si lo corres",
                    f"Requisitos mínimos y recomendados de {n} en PC.{desc_ram} Compara con tu tarjeta gráfica, procesador y RAM en segundos.",
                    cuerpo, "juego", ld, "0.8")

    def juegos_para_gpu(self, nombre):
        pts = hardware.GPUS[nombre]
        alto, minimo = [], []
        for j in self.juegos:
            mn = (j["req"].get("min") or {}).get("gpu_pts")
            rc = (j["req"].get("rec") or {}).get("gpu_pts")
            if rc is not None and pts >= rc:
                alto.append(j)
            elif mn is not None and pts >= mn:
                minimo.append(j)
        def lista(js):
            return "".join(self.fila_juego(x) for x in js) or '<li class="vacio">Ninguno por ahora.</li>'
        cuerpo = f"""<div class="envoltura ficha">
  <nav class="migas" aria-label="Ruta"><a href="tarjetas-graficas.html">Por tarjeta gráfica</a><span aria-hidden="true">/</span><span>{esc(nombre)}</span></nav>
  <h1>Juegos que corren con una {esc(nombre)}</h1>
  <p class="entrada">De los {len(self.juegos)} juegos más jugados en Steam, {len(alto) + len(minimo)} piden una gráfica igual o menor que la {esc(nombre)}. Aquí solo miramos la tarjeta gráfica: revisa también procesador y RAM en la ficha de cada juego.</p>
  <section aria-labelledby="t-alto"><h2 id="t-alto">En calidad recomendada ({len(alto)})</h2><ol class="filas">{lista(alto)}</ol></section>
  <section aria-labelledby="t-bajo"><h2 id="t-bajo">Solo en requisitos mínimos ({len(minimo)})</h2><ol class="filas">{lista(minimo)}</ol></section>
</div>"""
        self.pagina(f"{slug_gpu(nombre)}.html", f"Juegos que corren con una {nombre} (lista actualizada)",
                    f"Lista de juegos de Steam que corren con una tarjeta gráfica {nombre}, en calidad recomendada o en mínimos. Actualizada cada día.",
                    cuerpo, "lista", None, "0.7")
        return len(alto) + len(minimo)

    def juegos_para_ram(self, gb):
        js = [j for j in self.juegos if (j["req"].get("min") or {}).get("ram_gb") is not None and j["req"]["min"]["ram_gb"] <= gb]
        cuerpo = f"""<div class="envoltura ficha">
  <nav class="migas" aria-label="Ruta"><a href="tarjetas-graficas.html">Por componente</a><span aria-hidden="true">/</span><span>{gb} GB de RAM</span></nav>
  <h1>Juegos que corren con {gb} GB de RAM</h1>
  <p class="entrada">{len(js)} de los juegos más jugados en Steam piden {gb} GB de RAM o menos en sus requisitos mínimos. La RAM es solo una parte: mira también la tarjeta gráfica.</p>
  <ol class="filas">{"".join(self.fila_juego(x) for x in js) or '<li class="vacio">Ninguno por ahora.</li>'}</ol>
</div>"""
        self.pagina(f"juegos-con-{gb}-gb-de-ram.html", f"Juegos que corren con {gb} GB de RAM en PC",
                    f"Juegos de Steam que funcionan con {gb} GB de RAM según sus requisitos mínimos. Lista en español actualizada cada día.",
                    cuerpo, "lista", None, "0.6")

    def indice_gpus(self):
        filas = []
        for nombre in GPUS_CON_PAGINA:
            total = self.juegos_para_gpu(nombre)
            filas.append(f'<li><a href="{slug_gpu(nombre)}.html"><strong>{esc(nombre)}</strong><span>{total} juegos</span>{self.icono("flecha")}</a></li>')
        ram = "".join(f'<li><a href="juegos-con-{g}-gb-de-ram.html"><strong>{g} GB de RAM</strong>{self.icono("flecha")}</a></li>' for g in RAM_CON_PAGINA)
        for g in RAM_CON_PAGINA:
            self.juegos_para_ram(g)
        cuerpo = f"""<div class="envoltura ficha">
  <h1>Qué juegos corren con tu tarjeta gráfica</h1>
  <p class="entrada">Elige tu tarjeta y mira la lista de juegos que aguanta. Si la tuya no está, configúrala en <a href="mi-pc.html">Mi PC</a> y la lista principal te dirá cuáles corren.</p>
  <ul class="rejilla">{"".join(filas)}</ul>
  <h2>Por memoria RAM</h2>
  <ul class="rejilla">{ram}</ul>
</div>"""
        self.pagina("tarjetas-graficas.html", "Juegos que corren con tu tarjeta gráfica: listas por modelo",
                    "Listas de juegos que corren con GTX 1650, RTX 3060, RX 580 y otras tarjetas gráficas populares en Colombia.",
                    cuerpo, "lista", None, "0.8")

    def mi_pc(self):
        cuerpo = f"""<div class="envoltura ficha ficha--estrecha">
  <h1>Mi PC</h1>
  <p class="entrada">Guarda aquí tu equipo una sola vez. Se queda en este navegador y en cada juego verás si corre.</p>
  {self.formulario_pc("Tu equipo")}
  <section id="como-saber" aria-labelledby="t-saber">
    <h2 id="t-saber">Cómo saber qué tiene tu computador</h2>
    <h3>En Windows 10 y 11</h3>
    <ol class="pasos">
      <li>Pulsa las teclas <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Esc</kbd> para abrir el Administrador de tareas.</li>
      <li>Entra en la pestaña <strong>Rendimiento</strong>.</li>
      <li>En <strong>CPU</strong> verás el nombre del procesador, arriba a la derecha.</li>
      <li>En <strong>Memoria</strong> verás cuántos GB de RAM tienes.</li>
      <li>En <strong>GPU</strong> verás la tarjeta gráfica. Si aparecen dos, usa la que no dice «Intel» o «UHD»: esa es la dedicada.</li>
    </ol>
    <h3>Otra forma: dxdiag</h3>
    <ol class="pasos">
      <li>Pulsa <kbd>Windows</kbd> + <kbd>R</kbd>, escribe <code>dxdiag</code> y pulsa Enter.</li>
      <li>En la pestaña <strong>Sistema</strong> salen el procesador y la memoria.</li>
      <li>En la pestaña <strong>Pantalla</strong> sale el nombre de la tarjeta gráfica.</li>
    </ol>
    <p class="nota">Si tu modelo no aparece en la lista, elige el más parecido. Por ejemplo, una «RTX 3060 Laptop» rinde algo menos que la RTX 3060 de escritorio.</p>
  </section>
</div>"""
        self.pagina("mi-pc.html", "Mi PC: guarda tu tarjeta gráfica, procesador y RAM",
                    "Guarda tu PC y mira qué juegos corre. Además, cómo saber qué tarjeta gráfica, procesador y RAM tienes en Windows.",
                    cuerpo, "mipc", None, "0.7")

    def como_funciona(self):
        cuerpo = f"""<div class="envoltura ficha ficha--estrecha prosa">
  <h1>Cómo funciona</h1>
  <p class="entrada">Cada día un programa revisa los juegos más jugados y más vendidos de Steam y copia sus requisitos de la ficha oficial. Nadie los escribe a mano.</p>
  <h2>De dónde salen los datos</h2>
  <p>La lista de juegos sale de las listas públicas de Steam (más jugados, más vendidos y novedades) y de SteamSpy. Los requisitos, los precios en Colombia y las portadas salen de la tienda de Steam. Si Steam cambia un requisito, aquí se actualiza en uno o dos días.</p>
  <h2>Cómo comparamos tu PC</h2>
  <p>Cada tarjeta gráfica y cada procesador tiene una puntuación aproximada, tomada de comparativas públicas de rendimiento. Si un juego pide «GTX 970 o RX 480», basta con que tu equipo iguale a la más débil de las dos. La RAM se compara en GB.</p>
  <p>Es una guía, no una promesa: los controladores, la temperatura, la resolución y si usas un portátil cambian el resultado. Cuando no reconocemos un modelo, lo decimos y te mostramos el texto original de Steam.</p>
  <h2>Cómo se mantiene la página</h2>
  <p>Algunos enlaces de compra son de afiliado (por ejemplo, Instant Gaming). Si compras desde ahí, la página recibe una pequeña comisión y a ti no te cuesta más. Los enlaces de afiliado nunca cambian el resultado de la comparación.</p>
  {f'<p>Si la página te sirve, puedes apoyarla en <a href="{esc(self.cfg["kofi"])}" rel="noopener" target="_blank">Ko-fi</a>.</p>' if self.cfg.get("kofi") else ''}
  <h2 id="privacidad">Privacidad</h2>
  <p>Tu PC se guarda solo en tu navegador (almacenamiento local). No se envía a ningún servidor, no usamos cookies de seguimiento y no pedimos cuentas ni correos.</p>
</div>"""
        self.pagina("como-funciona.html", "Cómo funciona ¿Corre en mi PC?",
                    "De dónde salen los requisitos, cómo comparamos tu PC y cómo se mantiene la página.",
                    cuerpo, "prosa", None, "0.4")

    def no_encontrada(self):
        cuerpo = """<div class="envoltura ficha ficha--estrecha"><h1>Esta página no existe</h1>
<p class="entrada">Puede que el juego haya cambiado de nombre. Búscalo desde la portada.</p>
<p><a class="boton" href="index.html">Ir a la lista de juegos</a></p></div>"""
        self.pagina("404.html", "Página no encontrada · ¿Corre en mi PC?", "La página que buscas no existe.", cuerpo, "prosa")
        self.paginas.pop()

    # ---------- archivos extra ----------
    def copiar_assets(self):
        destino = os.path.join(self.salida, "assets")
        shutil.copytree(os.path.join(RAIZ, "assets"), destino, dirs_exist_ok=True)
        datos = {"gpus": hardware.GPUS, "cpus": hardware.CPUS}
        with open(os.path.join(destino, "hardware.json"), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))

    def mapa(self):
        urls = "".join(f"<url><loc>{esc(u)}</loc><lastmod>{self.hoy}</lastmod><priority>{p}</priority></url>"
                       for u, p in self.paginas)
        with open(os.path.join(self.salida, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        with open(os.path.join(self.salida, "robots.txt"), "w", encoding="utf-8") as f:
            f.write(f"User-agent: *\nAllow: /\nSitemap: {self.base}/sitemap.xml\n")
        with open(os.path.join(self.salida, "_headers"), "w", encoding="utf-8") as f:
            f.write("/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n"
                    "  Referrer-Policy: strict-origin-when-cross-origin\n"
                    "  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()\n")

    def generar(self):
        if os.path.isdir(self.salida):
            shutil.rmtree(self.salida)
        os.makedirs(self.salida)
        self.copiar_assets()
        self.portada()
        for j in self.juegos:
            self.ficha_juego(j)
        self.indice_gpus()
        self.mi_pc()
        self.como_funciona()
        self.no_encontrada()
        self.mapa()
        return len(self.paginas)
