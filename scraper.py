#!/usr/bin/env python3
"""
Scraper de IDs Acestream - GitHub Actions
"""
from playwright.sync_api import sync_playwright
import json, re, datetime, os

URL = "https://aceid.mywire.org/listado/"

def extraer_canales():
    with sync_playwright() as p:
        print("[*] Iniciando navegador...")
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        page = browser.new_page()
        page.set_default_timeout(20000)

        print(f"[*] Cargando {URL}...")
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            print(f"[!] Timeout cargando: {e}")

        # Esperar máximo 5 segundos a que aparezcan h5
        try:
            page.wait_for_selector("h5", timeout=5000)
        except:
            print("[!] No aparecieron h5, continuando...")

        page.wait_for_timeout(2000)

        # Interceptar clipboard
        page.evaluate("""
            window.__ids = [];
            Object.defineProperty(navigator, 'clipboard', {
                value: {
                    writeText: function(text) {
                        window.__ids.push(text);
                        return Promise.resolve();
                    }
                },
                writable: true
            });
        """)

        # Obtener nombres
        nombres = page.eval_on_selector_all("h5", "els => els.map(e => e.innerText.trim())")
        print(f"[*] Nombres encontrados: {len(nombres)}")

        # Pulsar botones copiar con timeout corto
        botones = page.query_selector_all("button")
        copiar = [b for b in botones if "copiar" in (b.inner_text() or "").lower()]
        print(f"[*] Botones copiar: {len(copiar)}")

        for btn in copiar:
            try:
                btn.click(timeout=1000)
                page.wait_for_timeout(50)
            except:
                pass

        page.wait_for_timeout(500)
        ids = page.evaluate("window.__ids") or []
        print(f"[*] IDs por clipboard: {len(ids)}")

        # Fallback: buscar en HTML con regex
        html = page.content()
        ids_html = list(dict.fromkeys(re.findall(r'\b[0-9a-f]{40}\b', html)))
        print(f"[*] IDs en HTML: {len(ids_html)}")

        # Combinar
        todos = list(dict.fromkeys(ids + ids_html))
        print(f"[*] Total IDs únicos: {len(todos)}")

        browser.close()

        canales = []
        for i, ace_id in enumerate(todos):
            nombre = nombres[i] if i < len(nombres) else f"Canal {i+1}"
            canales.append({
                "nombre": nombre,
                "id": ace_id,
                "link": f"acestream://{ace_id}"
            })

        return canales

if __name__ == "__main__":
    print("=" * 50)
    canales = extraer_canales()

    resultado = {
        "actualizado": datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
        "total": len(canales),
        "canales": canales
    }

    os.makedirs("docs", exist_ok=True)
    with open("docs/canales.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"[✓] {len(canales)} canales guardados en docs/canales.json")
