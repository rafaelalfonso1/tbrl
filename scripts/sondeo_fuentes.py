"""Sondeo de fuentes candidatas (solo lectura). Imprime la estructura en el log de GitHub Actions.
Se ejecuta a mano: Actions → Sondeo de fuentes → Run workflow. No modifica el repositorio."""
import io, re, sys, html
from urllib.parse import urljoin
import requests

H = {"User-Agent": "Mozilla/5.0 (TBRL datos; +https://thebusinessresearchlab.com)"}
PAGES = [
    "https://www.bancentral.gov.do/",
    "https://www.bancentral.gov.do/a/CustomView/2536-sector-monetario-y-financiero",
    "https://www.bancentral.gov.do/a/d/2532-mercado-cambiario",
    "https://www.one.gob.do/datos-y-estadisticas/temas/estadisticas-economicas/estadisticas-sectoriales/estadisticas-bancarias-valores-y-de-seguros/",
    "https://www.creditopublico.gob.do/",
    "https://www.creditopublico.gob.do/inversionistas/subastas",
    "https://www.simv.gob.do/",
    "https://www.sb.gob.do/estadisticas/",
]
KEY = re.compile(r"interbanc|activa|pasiva|tasa|bolsa|valores|subasta|resultado|fondo|cuota|reserva|remesa|imae|monetari|letras|cartera", re.I)
FILE = re.compile(r"\.(xlsx?|csv|pdf)(\?|$)", re.I)


def get(url):
    r = requests.get(url, headers=H, timeout=60)
    print(f"  {r.status_code} {r.headers.get('content-type','')} {len(r.content):,} bytes  ({r.url})")
    r.raise_for_status()
    return r


def dump_xlsx(data):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    for ws in wb.worksheets[:4]:
        print(f"    hoja «{ws.title}» {ws.max_row}x{ws.max_column}")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= 14:
                break
            cells = [str(c)[:18] for c in row[:12] if c is not None]
            if cells:
                print("     ", " | ".join(cells))


def main():
    files = []
    for url in PAGES:
        print(f"\n=== {url}")
        try:
            r = get(url)
        except Exception as e:
            print("  ERROR", e)
            continue
        text = r.text
        plain = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text)))
        for kw in ["política monetaria", "Interb", "Activa B.M", "Pasiva B.M", "Tasa del dólar", "Reservas"]:
            for m in list(re.finditer(re.escape(kw), plain, re.I))[:2]:
                print(f"  [{kw}] …{plain[max(0,m.start()-80):m.end()+120]}…")
        links = re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.I | re.S)
        n = 0
        for href, label in links:
            label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(label))).strip()
            full = urljoin(r.url, href.strip())
            if FILE.search(full) or KEY.search(label + " " + href):
                print(f"  -> {label[:90]!r}  {full}")
                n += 1
                if FILE.search(full) and re.search(r"xlsx?|csv", full, re.I) and KEY.search(label + full):
                    files.append(full)
            if n >= 80:
                print("  … (más enlaces omitidos)")
                break
    print("\n=== Archivos de datos")
    seen = set()
    for f in files:
        if f in seen or len(seen) >= 18:
            continue
        seen.add(f)
        print(f"\n--- {f}")
        try:
            r = get(f)
            if re.search(r"\.csv", f, re.I):
                print("   ", r.text[:600])
            else:
                dump_xlsx(r.content)
        except Exception as e:
            print("  ERROR", e)


if __name__ == "__main__":
    main()
