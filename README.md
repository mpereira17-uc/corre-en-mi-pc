# ¿Corre en mi PC?

Página en español que muestra los requisitos mínimos y recomendados de los juegos más jugados de Steam y dice si tu computador los corre.

- Se actualiza sola cada día con GitHub Actions (`.github/workflows/publicar.yml`).
- Los datos salen de las APIs públicas de Steam y SteamSpy, sin claves.
- El PC del visitante se guarda solo en su navegador.

## Cómo funciona por dentro

| Archivo | Qué hace |
|---|---|
| `generar.py` | Orquesta todo: lee Steam, guarda `data/juegos.json` y genera `docs/`. |
| `cemp/steam.py` | Lista de juegos populares y detalles de cada uno. |
| `cemp/requisitos.py` | Convierte el HTML de requisitos de Steam en datos. |
| `cemp/hardware.py` | Puntuaciones aproximadas de tarjetas gráficas y procesadores. |
| `cemp/sitio.py` | Genera las páginas: portada, ficha por juego, listas por tarjeta y RAM. |
| `assets/` | Estilos, JavaScript del comparador, fuentes (licencia OFL) e icono. |
| `config.json` | URL del sitio, cuántos juegos, código de afiliado de Instant Gaming y Ko-fi. |

## Probar en local

```
python -m unittest discover -s tests -t .
CEMP_FIXTURES=tests/fixtures CEMP_JUEGOS=/tmp/j.json CEMP_EXCLUIDOS=/tmp/e.json CEMP_SALIDA=/tmp/docs python generar.py
```

`docs/` no se guarda en el repositorio: se genera en cada ejecución y se publica en GitHub Pages.
