# AceStream TV

Scraper automático de IDs Acestream. Se actualiza cada 6 horas via GitHub Actions.

## Configuración

1. Sube este repositorio a GitHub
2. Ve a **Settings → Pages** y selecciona rama `main`, carpeta `/docs`
3. Ve a **Actions** y ejecuta manualmente el workflow por primera vez
4. Edita la URL en `docs/index.html` con tu usuario y repo

## Archivos

- `scraper.py` — extrae los IDs de la web
- `.github/workflows/actualizar.yml` — ejecuta el scraper cada 6h
- `docs/index.html` — app web con los canales
- `docs/canales.json` — JSON generado automáticamente
