#!/usr/bin/env python3
"""
Scraper de IDs Acestream usando requests + BeautifulSoup
Sin navegador, mucho más rápido
"""
import requests
from bs4 import BeautifulSoup
import json, re, datetime, os

URL = "https://aceid.mywire.org/listado/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

def extraer_canales():
    print(f"[*] Descargando {URL}...")
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        html = r.text
        print(f"[*] HTML descargado: {len(html)} chars")
    except Exception as e:
        print(f"[!] Error: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Buscar nombres de canales
    nombres = [h.get_text(strip=True) for h in soup.find_all("h5")]
    print(f"[*] Nombres: {len(nombres)}")

    # Buscar IDs de 40 chars en todo el HTML
    ids = list(dict.fromkeys(re.findall(r'\b[0-9a-f]{40}\b', html)))
    print(f"[*] IDs completos en HTML: {len(ids)}")

    # Buscar también en atributos data-*
    for el in soup.find_all(attrs={"data-id": True}):
        val = el["data-id"]
        if re.match(r'^[0-9a-f]{40}$', val) and val not in ids:
            ids.append(val)

    for el in soup.find_all(attrs={"data-hash": True}):
        val = el["data-hash"]
        if re.match(r'^[0-9a-f]{40}$', val) and val not in ids:
            ids.append(val)

    # Buscar en href acestream://
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("acestream://"):
            ace_id = href.replace("acestream://", "")
            if re.match(r'^[0-9a-f]{40}$', ace_id) and ace_id not in ids:
                ids.append(ace_id)

    print(f"[*] Total IDs únicos: {len(ids)}")

    canales = []
    for i, ace_id in enumerate(ids):
        nombre = nombres[i] if i < len(nombres) else f"Canal {i+1}"
        canales.append({
            "nombre": nombre,
            "id": ace_id,
            "link": f"acestream://{ace_id}"
        })

    return canales

if __name__ == "__main__":
    print("=" * 50)
    print("  Scraper IDs Acestream (requests)")
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

    print(f"[✓] {len(canales)} canales en docs/canales.json")

    if len(canales) == 0:
        print("[!] AVISO: 0 canales. Los IDs probablemente se cargan con JS.")
        print("[!] El JSON se guarda igualmente para no romper la app.")
