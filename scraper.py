#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json, re, datetime, os, sys

URL = "https://aceid.mywire.org/listado/"

def extraer_canales():
    with sync_playwright() as p:
        print("[*] Iniciando Chromium...")
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox','--disable-setuid-sandbox',
                  '--disable-dev-shm-usage','--disable-gpu']
        )
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page.set_default_timeout(15000)

        # Interceptar peticiones para capturar IDs de la API
        ids_api = []
        def on_response(response):
            try:
                if "json" in response.headers.get("content-type",""):
                    body = response.json()
                    text = json.dumps(body)
                    found = re.findall(r'\b[0-9a-f]{40}\b', text)
                    ids_api.extend(found)
                    if found:
                        print(f"[*] API capturada: {response.url} → {len(found)} IDs")
            except:
                pass
        page.on("response", on_response)

        print(f"[*] Cargando {URL}...")
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            print(f"[!] {e}")

        page.wait_for_timeout(3000)

        # Interceptar clipboard
        page.evaluate("""
            window.__ids = [];
            Object.defineProperty(navigator, 'clipboard', {
                value: { writeText: t => { window.__ids.push(t); return Promise.resolve(); } },
                configurable: true
            });
        """)

        # Obtener nombres
        nombres = page.eval_on_selector_all("h5", "els => els.map(e => e.innerText.trim())")
        print(f"[*] Canales: {len(nombres)}")

        # Pulsar botones copiar
        botones = page.query_selector_all("button")
        copiar = [b for b in botones if "copiar" in (b.inner_text() or "").lower()]
        print(f"[*] Botones copiar: {len(copiar)}")
        for btn in copiar:
            try:
                btn.click(timeout=2000)
                page.wait_for_timeout(60)
            except:
                pass

        page.wait_for_timeout(1000)

        ids_clipboard = page.evaluate("window.__ids") or []
        print(f"[*] IDs clipboard: {len(ids_clipboard)}")

        # IDs en HTML
        html = page.content()
        ids_html = re.findall(r'\b[0-9a-f]{40}\b', html)
        print(f"[*] IDs HTML: {len(ids_html)}")

        browser.close()

        # Combinar todas las fuentes
        todos = list(dict.fromkeys(ids_clipboard + ids_api + ids_html))
        print(f"[*] Total únicos: {len(todos)}")

        canales = []
        for i, ace_id in enumerate(todos):
            nombre = nombres[i] if i < len(nombres) else f"Canal {i+1}"
            canales.append({"nombre": nombre, "id": ace_id, "link": f"acestream://{ace_id}"})

        return canales

if __name__ == "__main__":
    print("="*50)
    canales = extraer_canales()

    resultado = {
        "actualizado": datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
        "total": len(canales),
        "canales": canales
    }

    os.makedirs("docs", exist_ok=True)
    with open("docs/canales.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"[✓] {len(canales)} canales guardados")
    if len(canales) == 0:
        print("[!] 0 canales — los IDs no están en el HTML estático")
        sys.exit(0)  # No falla el workflow
