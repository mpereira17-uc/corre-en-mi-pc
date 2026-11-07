"""Pruebas: se corren en cada ejecución antes de tocar datos reales."""
import json
import os
import shutil
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix="cemp-")
# Nunca escribir en data/ real durante las pruebas.
os.environ["CEMP_FIXTURES"] = os.path.join(AQUI, "fixtures")
os.environ["CEMP_JUEGOS"] = os.path.join(TMP, "juegos.json")
os.environ["CEMP_EXCLUIDOS"] = os.path.join(TMP, "excluidos.json")

from cemp import hardware, requisitos, datos  # noqa: E402
from cemp.sitio import Sitio  # noqa: E402

CONFIG = {"url_base": "https://ejemplo.test/corre", "max_juegos": 50, "detalles_por_ejecucion": 50,
          "instant_gaming_igr": "prueba-1", "kofi": "https://ko-fi.com/prueba"}


class Hardware(unittest.TestCase):
    def test_gpu_variantes(self):
        self.assertEqual([n for n, _ in hardware.buscar_gpus("NVIDIA GeForce RTX 3060 Ti 8GB")], ["RTX 3060 Ti"])
        self.assertEqual([n for n, _ in hardware.buscar_gpus("GTX1060 6GB / RX580")], ["GTX 1060", "RX 580"])
        self.assertEqual([n for n, _ in hardware.buscar_gpus("Radeon RX 5700XT")], ["RX 5700 XT"])
        self.assertEqual(hardware.buscar_gpus("256 mb video memory"), [])

    def test_cpu_variantes(self):
        self.assertEqual([n for n, _ in hardware.buscar_cpus("Intel Core i5-4460 or AMD FX-6300")], ["i5-4460", "FX-6300"])
        self.assertEqual([n for n, _ in hardware.buscar_cpus("Ryzen 7 5800X3D")], ["Ryzen 7 5800X3D"])
        self.assertEqual([n for n, _ in hardware.buscar_cpus("Intel Core i5-7500")], ["i5-7500"])  # no confundir con i5-750

    def test_gb(self):
        self.assertEqual(hardware.numero_gb("8 GB de RAM"), 8)
        self.assertEqual(hardware.numero_gb("512 MB RAM"), 0.5)
        self.assertEqual(hardware.numero_gb("1,5 GB"), 1.5)
        self.assertIsNone(hardware.numero_gb("mucha"))

    def test_mas_debil(self):
        self.assertEqual(hardware.puntaje_requisito(hardware.buscar_gpus("GTX 1060 or RX 570 or Arc A380")), 90)
        self.assertEqual(hardware.puntaje_requisito(hardware.buscar_gpus("Intel Arc A380")), 60)
        self.assertEqual(hardware.elegir_requisito(hardware.buscar_gpus("GTX 970 / RX 470"))[0], "GTX 970")


class Requisitos(unittest.TestCase):
    def test_formato_lista(self):
        data = json.load(open(os.path.join(AQUI, "fixtures", "app_1001.json")))["1001"]["data"]
        r = requisitos.de_steam(data["pc_requirements"])
        self.assertEqual(r["min"]["texto"]["so"], "Windows 10 64-bit")
        self.assertEqual(r["min"]["ram_gb"], 12)
        self.assertEqual(r["min"]["disco_gb"], 70)
        self.assertIn("64 bits", r["min"]["texto"]["notas"])
        self.assertEqual(r["rec"]["gpu_modelos"], ["RTX 2060 Super", "RX 5700 XT"])

    def test_formato_br_ingles(self):
        data = json.load(open(os.path.join(AQUI, "fixtures", "app_1002.json")))["1002"]["data"]
        r = requisitos.de_steam(data["pc_requirements"])
        self.assertEqual(r["min"]["texto"]["cpu"], "2 Ghz")
        self.assertIsNone(r["min"]["gpu_pts"])
        self.assertEqual(r["min"]["ram_gb"], 2)
        self.assertNotIn("rec", r)

    def test_vacio(self):
        self.assertIsNone(requisitos.de_steam([]))
        self.assertIsNone(requisitos.de_steam({"minimum": ""}))


class Completo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.juegos, cls.resumen = datos.actualizar(CONFIG)
        cls.salida = os.path.join(TMP, "docs")
        cls.paginas = Sitio(CONFIG, cls.juegos, salida=cls.salida).generar()

    def leer(self, nombre):
        with open(os.path.join(self.salida, nombre), encoding="utf-8") as f:
            return f.read()

    def test_filtra(self):
        ids = [j["id"] for j in self.juegos]
        self.assertEqual(ids, [1001, 1002, 1003])  # sin adultos, sin DLC, sin fallidos
        self.assertEqual(self.resumen["excluidos"], 3)

    def test_paginas(self):
        for nombre in ["index.html", "requisitos-ciudad-neon-2077.html", "mi-pc.html", "tarjetas-graficas.html",
                       "juegos-para-gtx-1650.html", "juegos-con-8-gb-de-ram.html", "como-funciona.html",
                       "404.html", "sitemap.xml", "robots.txt", "assets/hardware.json", "assets/app.js"]:
            self.assertTrue(os.path.exists(os.path.join(self.salida, nombre)), nombre)

    def test_escapa_html(self):
        todo = self.leer("index.html") + self.leer("requisitos-tiros-libres-script-alert-1-script.html")
        self.assertNotIn("<script>alert", todo)
        self.assertIn("&lt;script&gt;", todo)

    def test_afiliado_y_precio(self):
        f = self.leer("requisitos-ciudad-neon-2077.html")
        self.assertIn('rel="sponsored noopener"', f)
        self.assertIn("igr=prueba-1", f)
        self.assertIn("COL$ 199.000", f)
        gratis = self.leer("requisitos-tiros-libres-script-alert-1-script.html")
        self.assertNotIn("instant-gaming", gratis)  # no mandar a comprar un juego gratis

    def test_lista_gpu(self):
        f = self.leer("juegos-para-gtx-1650.html")
        self.assertIn("Tiros Libres", f)      # GTX 1650 = recomendada
        self.assertNotIn("Ciudad Neón", f)     # pide GTX 1060 o RX 580 (100); la Arc A380 no cuenta

    def test_mapa(self):
        mapa = self.leer("sitemap.xml")
        self.assertIn("https://ejemplo.test/corre/requisitos-granja-tranquila.html", mapa)
        self.assertNotIn("404.html", mapa)


if __name__ == "__main__":
    unittest.main()
