#!/usr/bin/env python3
"""
Actualiza automáticamente las fuentes de datos con documentos oficiales y luego
reconstruye el sitio (scripts/construir_datos.py).

Fuentes (documentos públicos con formato fijo):
  1. BCRD — tasa del día (compra y venta):
     https://cdn.bancentral.gov.do/documents/estadisticas/mercado-cambiario/documents/tasaus_mc.pdf
  2. DGII — tasa de cambio del dólar, serie diaria y promedio mensual (fuente BCRD):
     https://www.dgii.gov.do/estadisticas/tasaCambio/1Dlar/DolarAAAA.pdf

Diseño a prueba de fallos: si una fuente no responde o cambia de formato, se
conservan los datos existentes y el proceso termina sin borrar nada.

Uso:
  python scripts/actualizar_datos.py            # actualización normal
  python scripts/actualizar_datos.py --desde 2019   # carga histórica diaria (primera vez)
"""
import argparse, csv, io, re, sys, datetime as dt
from pathlib import Path

import requests
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "public" / "data" / "macro" / "fuente"
DAILY = SRC / "tipo_cambio_diario.csv"
MONTHLY = SRC / "tipo_cambio_mensual.csv"

BCRD_HOY = "https://cdn.bancentral.gov.do/documents/estadisticas/mercado-cambiario/documents/tasaus_mc.pdf"
DGII = ["https://www.dgii.gov.do/estadisticas/tasaCambio/1Dlar/Dolar{y}.pdf",
        "https://ws945695e.dgii.gov.do/estadisticas/tasaCambio/1Dlar/Dolar{y}.pdf"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; TBRL-datos/1.0)"}
LO, HI = 30.0, 150.0  # rango de validación de la tasa RD$/US$


def log(msg):
    print(msg, flush=True)


def fetch(url):
    r = requests.get(url, headers=UA, timeout=45)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise ValueError("la respuesta no es un PDF")
    return r.content


def valid(v):
    return v is not None and LO < v < HI


# ---------- 1. BCRD: tasa del día ----------
def parse_bcrd_hoy(pdf_bytes):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = " ".join((p.extract_text() or "") for p in pdf.pages)
    text = re.sub(r"\s+", " ", text)
    m = re.search(r"al cierre del (\d{1,2}) de ([a-zA-Záéíóú]+) de (\d{4}).{0,40}?RD\$\s*([\d.,]+)\s*/\s*US\$\s*y\s*RD\$\s*([\d.,]+)", text, re.I)
    if not m:
        raise ValueError("no se encontró el patrón de tasas en el PDF del BCRD")
    d, mes, y, c, v = m.groups()
    fecha = dt.date(int(y), MESES.index(mes.lower()) + 1, int(d)).isoformat()
    compra, venta = float(c.replace(",", "")), float(v.replace(",", ""))
    if not (valid(compra) and valid(venta)):
        raise ValueError(f"valores fuera de rango: {compra} / {venta}")
    return fecha, compra, venta


# ---------- 2. DGII: serie diaria y promedios mensuales ----------
def parse_dgii_year(pdf_bytes, year):
    """Devuelve ({fecha: compra}, {AAAA-MM: promedio}) usando la posición x de cada columna de mes."""
    daily, monthly = {}, {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        cols = {}
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
            page_cols = {}
            for w in words:
                t = w["text"].strip().lower()
                if t in MESES:
                    page_cols[MESES.index(t) + 1] = (w["x0"] + w["x1"]) / 2
            if page_cols:
                cols = page_cols  # si una página no repite el encabezado, se usan las columnas anteriores
            if not cols:
                continue
            centers = sorted(cols.items(), key=lambda kv: kv[1])
            half_gap = (min(b[1] - a[1] for a, b in zip(centers, centers[1:])) / 2) if len(centers) > 1 else 40
            # agrupa palabras por fila
            # agrupa palabras por fila (tolerancia vertical de 3 pt)
            grouped, current, last_top = [], [], None
            for w in sorted(words, key=lambda w: w["top"]):
                if last_top is not None and w["top"] - last_top > 3:
                    grouped.append(current)
                    current = []
                current.append(w)
                last_top = w["top"] if last_top is None or w["top"] - last_top > 3 else last_top
            if current:
                grouped.append(current)
            for ws in grouped:
                ws.sort(key=lambda w: w["x0"])
                label = ws[0]["text"].strip().rstrip(".").lower()
                is_avg = label.startswith("prom")
                if not (is_avg or label.isdigit()):
                    continue
                for w in ws[1:]:
                    try:
                        v = float(w["text"].replace(",", ""))
                    except ValueError:
                        continue
                    if not valid(v):
                        continue
                    xc = (w["x0"] + w["x1"]) / 2
                    month, cx = min(centers, key=lambda kv: abs(kv[1] - xc))
                    if abs(cx - xc) > half_gap:
                        continue
                    if is_avg:
                        monthly[f"{year}-{month:02d}"] = v
                    else:
                        day = int(label)
                        try:
                            daily[dt.date(year, month, day).isoformat()] = v
                        except ValueError:
                            pass
    return daily, monthly


# ---------- almacenamiento ----------
def load(path, key="fecha"):
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {r[key]: r for r in csv.DictReader(f)}


def save(path, rows, header):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for k in sorted(rows):
            w.writerow({h: rows[k].get(h, "") for h in header})
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", type=int, help="año inicial para cargar la serie diaria histórica de la DGII")
    args = ap.parse_args()
    today = dt.date.today()
    daily = load(DAILY)
    monthly = load(MONTHLY)
    changes = 0

    # 1) tasa del día del BCRD
    try:
        fecha, compra, venta = parse_bcrd_hoy(fetch(BCRD_HOY))
        prev = daily.get(fecha, {})
        if prev.get("compra") != f"{compra}" or prev.get("venta") != f"{venta}":
            daily[fecha] = {"fecha": fecha, "compra": f"{compra}", "venta": f"{venta}"}
            changes += 1
        log(f"BCRD: {fecha} compra {compra} · venta {venta}")
    except Exception as e:
        log(f"AVISO BCRD (se conservan los datos): {e}")

    # 2) DGII: años a revisar
    years = list(range(args.desde, today.year + 1)) if args.desde else sorted({today.year, (today - dt.timedelta(days=40)).year})
    for y in years:
        pdf = None
        for tpl in DGII:
            try:
                pdf = fetch(tpl.format(y=y))
                break
            except Exception as e:
                log(f"AVISO DGII {y} ({tpl.split('/')[2]}): {e}")
        if not pdf:
            continue
        try:
            d, mo = parse_dgii_year(pdf, y)
        except Exception as e:
            log(f"AVISO DGII {y}: no se pudo leer ({e})")
            continue
        n_d = 0
        for fecha, v in d.items():
            if dt.date.fromisoformat(fecha).weekday() >= 5 or fecha > today.isoformat():
                continue  # fines de semana repiten el valor del viernes
            row = daily.get(fecha)
            if not row:
                daily[fecha] = {"fecha": fecha, "compra": f"{v}", "venta": ""}
                n_d += 1
            elif not row.get("compra"):
                row["compra"] = f"{v}"
                n_d += 1
        n_m = 0
        current = f"{today.year}-{today.month:02d}"
        for k, v in mo.items():
            if k >= current:
                continue  # solo meses completos
            if monthly.get(k, {}).get("usd_dop_promedio") != f"{v}":
                monthly[k] = {"fecha": k, "usd_dop_promedio": f"{v}"}
                n_m += 1
        log(f"DGII {y}: {len(d)} días leídos ({n_d} nuevos) · {len(mo)} promedios ({n_m} actualizados)")
        changes += n_d + n_m

    save(DAILY, daily, ["fecha", "compra", "venta"])
    save(MONTHLY, monthly, ["fecha", "usd_dop_promedio"])
    log(f"Cambios en fuentes: {changes}")

    sys.path.insert(0, str(ROOT / "scripts"))
    import construir_datos
    construir_datos.main()


if __name__ == "__main__":
    main()
