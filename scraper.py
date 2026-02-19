#!/usr/bin/env python3
"""
Scraper de IDs Acestream - ejecutado por GitHub Actions
Genera canales.json con todos los canales y sus IDs completos
"""

from playwright.sync_api import sync_playwright
import json, re, datetime, os

URL = "https://aceid.mywire.org/listado/"

def extraer_canales():
    with sync_playwright() as p:
        print("[*] Iniciando navegador...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        print(f"[*] Cargando {URL}...")
        page.goto(URL, timeout=30000)
        page.wait_for_timeout(4000)

        # Interceptar clipboard para capturar IDs al pulsar "Copiar"
        page.evaluate("""
            window.__ids = [];
            window.__nombres = [];
            const orig = navigator.clipboard.writeText.bind(navigator.clipboard);
            navigator.clipboard.writeText = function(text) {
                window.__ids.push(text);
                return Promise.resolve();
            };
        """)

        # Obtener nombres de canales
        nombres = page.eval_on_selector_all(
            "h5", "els => els.map(e => e.innerText.trim())"
        )
        print(f"[*] Canales: {len(nombres)}")

        # Pulsar todos los botones "Copiar ID"
        botones = page.query_selector_all("button")
        copiar = [b for b in botones if "copiar" in (b.inner_text() or "").lower()
                  and "id" in (b.inner_text() or "").lower()]

        # Si no filtra bien, coger todos los de copiar
        if len(copiar) < 10:
            copiar = [b for b in botones if "copiar" in (b.inner_text() or "").lower()]

        print(f"[*] Botones copiar encontrados: {len(copiar)}")

        for i, btn in enumerate(copiar):
            try:
                btn.scroll_into_view_if_needed()
                btn.click()
                page.wait_for_timeout(80)
            except:
                pass

        page.wait_for_timeout(1000)
        ids = page.evaluate("window.__ids")
        print(f"[*] IDs capturados: {len(ids)}")

        # Fallback: buscar en el HTML
        if len(ids) < 5:
            print("[*] Fallback: buscando en HTML...")
            html = page.content()
            ids = list(dict.fromkeys(re.findall(r'\b[0-9a-f]{40}\b', html)))
            print(f"[*] IDs en HTML: {len(ids)}")

        browser.close()

        # Emparejar nombres con IDs
        canales = []
        ids_unicos = list(dict.fromkeys(ids))
        for i, ace_id in enumerate(ids_unicos):
            nombre = nombres[i] if i < len(nombres) else f"Canal {i+1}"
            canales.append({
                "nombre": nombre,
                "id": ace_id,
                "link": f"acestream://{ace_id}"
            })

        return canales

if __name__ == "__main__":
    print("=" * 50)
    print("  Scraper IDs Acestream")
    print("=" * 50)

    canales = extraer_canales()

    if not canales:
        print("[!] Sin canales. Saliendo.")
        exit(1)

    resultado = {
        "actualizado": datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
        "total": len(canales),
        "canales": canales
    }

    os.makedirs("docs", exist_ok=True)
    with open("docs/canales.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\n[✓] {len(canales)} canales guardados en docs/canales.json")
