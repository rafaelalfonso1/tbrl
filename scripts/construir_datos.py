#!/usr/bin/env python3
"""
Construye todos los datos publicados del sitio a partir de las fuentes en
public/data/macro/fuente/:

  tipo_cambio_mensual.csv    fecha (AAAA-MM), usd_dop_promedio
  tipo_cambio_diario.csv     fecha (AAAA-MM-DD), compra, venta
  indicadores_mensuales.csv  fecha (AAAA-MM), tpm, inflacion_interanual, tasa_activa, tasa_pasiva,
                             tasa_interbancaria, reservas_brutas, imae_interanual

Genera:
  public/data/macro/series.json              (lo lee el Centro de datos)
  public/data/macro/descargas/*.csv / *.xlsx (descargas públicas)
  public/data/markets.json                   (sincroniza la página de mercados)

No necesita internet. Se ejecuta solo (GitHub Action) o a mano:
  python scripts/construir_datos.py
"""
import csv, json, datetime as dt
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "public"
SRC = PUB / "data" / "macro" / "fuente"
OUT = PUB / "data" / "macro" / "descargas"
SERIES_JSON = PUB / "data" / "macro" / "series.json"
MARKETS_JSON = PUB / "data" / "markets.json"

FUENTE_BCRD = "Banco Central de la República Dominicana (BCRD)"
URL_BCRD = "https://www.bancentral.gov.do/"
URL_DGII = "https://www.dgii.gov.do/estadisticas/tasaCambio/1Dlar/"
URL_BCRD_TASAS = "https://www.bancentral.gov.do/a/d/2536-sector-monetario-y-financiero"
from fuentes_bcrd import ARCHIVOS as XLS_BCRD  # enlaces directos a los Excel oficiales


def read_csv(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x) if x not in (None, "") else None
    except ValueError:
        return None


def series_from(rows, key):
    return [[r["fecha"], num(r.get(key))] for r in rows if r.get("fecha")]


def weekly_from_daily(daily):
    """Promedio semanal (semana que inicia el lunes) de la tasa de compra y venta."""
    weeks = OrderedDict()
    for r in daily:
        d = dt.date.fromisoformat(r["fecha"])
        monday = (d - dt.timedelta(days=d.weekday())).isoformat()
        w = weeks.setdefault(monday, {"compra": [], "venta": []})
        for k in ("compra", "venta"):
            v = num(r.get(k))
            if v is not None:
                w[k].append(v)
    out = []
    for monday, w in weeks.items():
        c = round(sum(w["compra"]) / len(w["compra"]), 4) if w["compra"] else None
        v = round(sum(w["venta"]) / len(w["venta"]), 4) if w["venta"] else None
        out.append([monday, c, v])
    return out


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # BOM: Excel abre bien los acentos
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(["" if x is None else x for x in r])


def write_xlsx(path, sheets, meta):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    wb = Workbook()
    ws = wb.active
    ws.title = "Léeme"
    navy = PatternFill("solid", fgColor="2C4856")
    ws["A1"] = "The Business Research Lab — Datos macroeconómicos de República Dominicana"
    ws["A1"].font = Font(bold=True, size=14, color="2C4856")
    r = 3
    for k, v in meta:
        ws.cell(r, 1, k).font = Font(bold=True)
        ws.cell(r, 2, v)
        r += 1
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 90
    for name, header, rows, fmt in sheets:
        for ch in '[]:*?/\\':
            name = name.replace(ch, "-")
        s = wb.create_sheet(name[:31])
        s.append(header)
        for c in s[1]:
            c.font = Font(bold=True, color="F7F4EB")
            c.fill = navy
            c.alignment = Alignment(horizontal="center")
        for row in rows:
            s.append(row)
        for col in range(2, len(header) + 1):
            for cell in s.iter_cols(min_col=col, max_col=col, min_row=2):
                for c in cell:
                    c.number_format = fmt
        s.column_dimensions["A"].width = 14
        for i in range(2, len(header) + 1):
            s.column_dimensions[chr(64 + i)].width = 22
        s.freeze_panes = "A2"
    wb.save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    fx_m = read_csv(SRC / "tipo_cambio_mensual.csv")
    fx_d = read_csv(SRC / "tipo_cambio_diario.csv")
    ind = read_csv(SRC / "indicadores_mensuales.csv")
    fx_d.sort(key=lambda r: r["fecha"])
    fx_m.sort(key=lambda r: r["fecha"])
    ind.sort(key=lambda r: r["fecha"])

    fx_monthly = series_from(fx_m, "usd_dop_promedio")
    tpm = series_from(ind, "tpm")
    infl = series_from(ind, "inflacion_interanual")
    # recorta nulos al inicio/fin (los huecos intermedios se conservan)
    def trim(s):
        while s and s[0][1] is None: s = s[1:]
        while s and s[-1][1] is None: s = s[:-1]
        return s
    tpm, infl = trim(tpm), trim(infl)
    extra = {k: trim(series_from(ind, k)) for k in
             ("tasa_activa", "tasa_pasiva", "tasa_interbancaria", "reservas_brutas", "imae_interanual")}
    weekly = weekly_from_daily(fx_d)
    daily = [[r["fecha"], num(r.get("compra")), num(r.get("venta"))] for r in fx_d]

    series = [
        {"id": "tipo_cambio_usd_dop_mensual", "nombre": "Tipo de cambio USD/DOP", "frecuencia": "Mensual",
         "descripcion": "Promedio mensual de la tasa de referencia del mercado spot (compra), pesos por dólar.",
         "hoja": "TC USD-DOP mensual", "unidad": "RD$ por US$", "decimales": 2, "fuente": FUENTE_BCRD + ", serie publicada por la DGII",
         "fuente_url": URL_DGII, "datos": fx_monthly},
        {"id": "tasa_politica_monetaria_mensual", "nombre": "Tasa de política monetaria (TPM)", "frecuencia": "Mensual",
         "descripcion": "Tasa de interés de política monetaria vigente en cada mes, según la serie oficial del BCRD.",
         "hoja": "TPM mensual", "unidad": "% anual", "decimales": 2, "fuente": FUENTE_BCRD, "fuente_url": URL_BCRD, "datos": tpm, "escalonada": True},
        {"id": "inflacion_interanual_mensual", "nombre": "Inflación interanual (IPC)", "frecuencia": "Mensual",
         "descripcion": "Variación interanual del índice de precios al consumidor. Banda sombreada: rango meta 4.0% ± 1.0%.",
         "hoja": "Inflación interanual", "unidad": "%", "decimales": 2, "fuente": FUENTE_BCRD, "fuente_url": URL_BCRD, "datos": infl, "banda": [3.0, 5.0]},
        {"id": "tasa_interbancaria_mensual", "nombre": "Tasa interbancaria", "frecuencia": "Mensual",
         "descripcion": "Tasa promedio ponderada de las operaciones interbancarias en pesos: el costo del dinero entre bancos.",
         "hoja": "Tasa interbancaria", "unidad": "% anual", "decimales": 2, "fuente": FUENTE_BCRD, "fuente_url": URL_BCRD_TASAS,
         "datos": extra["tasa_interbancaria"]},
        {"id": "tasa_activa_bm_mensual", "nombre": "Tasa activa de la banca múltiple", "frecuencia": "Mensual",
         "descripcion": "Tasa de interés promedio ponderada de los préstamos nuevos de los bancos múltiples, en moneda nacional.",
         "hoja": "Tasa activa BM", "unidad": "% anual", "decimales": 2, "fuente": FUENTE_BCRD, "fuente_url": URL_BCRD_TASAS,
         "datos": extra["tasa_activa"]},
        {"id": "tasa_pasiva_bm_mensual", "nombre": "Tasa pasiva de la banca múltiple", "frecuencia": "Mensual",
         "descripcion": "Tasa de interés promedio ponderada que pagan los bancos múltiples por los depósitos, en moneda nacional.",
         "hoja": "Tasa pasiva BM", "unidad": "% anual", "decimales": 2, "fuente": FUENTE_BCRD, "fuente_url": URL_BCRD_TASAS,
         "datos": extra["tasa_pasiva"]},
        {"id": "reservas_internacionales_brutas_mensual", "nombre": "Reservas internacionales brutas", "frecuencia": "Mensual",
         "descripcion": "Reservas internacionales brutas del Banco Central al cierre de cada mes.",
         "hoja": "Reservas brutas", "unidad": "US$ millones", "decimales": 1, "fuente": FUENTE_BCRD, "fuente_url": XLS_BCRD["reservas_brutas"],
         "datos": extra["reservas_brutas"]},
        {"id": "imae_interanual_mensual", "nombre": "Actividad económica (IMAE)", "frecuencia": "Mensual",
         "descripcion": "Variación interanual del Indicador Mensual de Actividad Económica, serie original: el pulso mensual del PIB.",
         "hoja": "IMAE interanual", "unidad": "%", "decimales": 2, "fuente": FUENTE_BCRD, "fuente_url": XLS_BCRD["imae_interanual"],
         "datos": extra["imae_interanual"]},
    ]
    series = [x for x in series if x["datos"]]
    if len(weekly) >= 8:
        series.insert(1, {"id": "tipo_cambio_usd_dop_semanal", "nombre": "Tipo de cambio USD/DOP", "frecuencia": "Semanal",
            "descripcion": "Promedio semanal (semana que inicia el lunes) de la tasa de referencia de compra.",
            "hoja": "TC USD-DOP semanal", "unidad": "RD$ por US$", "decimales": 2, "fuente": FUENTE_BCRD, "fuente_url": URL_BCRD,
            "datos": [[w[0], w[1]] for w in weekly]})

    # ---- descargas por serie ----
    for s in series:
        hdr = ["fecha", s["id"]]
        write_csv(OUT / f"{s['id']}.csv", hdr, s["datos"])
        write_xlsx(OUT / f"{s['id']}.xlsx",
                   [(s["hoja"], ["fecha", f"{s['nombre']} ({s['unidad']})"], s["datos"], "0.00")],
                   [("Serie", f"{s['nombre']} — {s['frecuencia']}"), ("Descripción", s["descripcion"]),
                    ("Unidad", s["unidad"]), ("Fuente", s["fuente"]), ("Enlace", s["fuente_url"]),
                    ("Actualizado", today), ("Elaboración", "The Business Research Lab (TBRL)")])
        s["descargas"] = {"csv": f"data/macro/descargas/{s['id']}.csv", "xlsx": f"data/macro/descargas/{s['id']}.xlsx"}

    # diario (solo descarga)
    write_csv(OUT / "tipo_cambio_usd_dop_diario.csv", ["fecha", "compra", "venta"], daily)

    # ---- conjunto completo mensual (formato ancho) ----
    months = sorted({p[0] for s in series if s["frecuencia"] == "Mensual" for p in s["datos"]})
    lookup = {s["id"]: dict(s["datos"]) for s in series}
    mensuales = [x for x in series if x["frecuencia"] == "Mensual"]
    wide = [[m] + [lookup[x["id"]].get(m) for x in mensuales] for m in months]
    hdr = ["fecha"] + [x["id"].replace("_mensual", "") for x in mensuales]
    write_csv(OUT / "tbrl_datos_macro_rd_mensual.csv", hdr, wide)
    sheets = [("Mensual (todas)", ["fecha"] + [f"{x['nombre']} ({x['unidad']})" for x in mensuales], wide, "0.00")]
    for s in series:
        sheets.append((s["hoja"], ["fecha", f"{s['nombre']} ({s['unidad']})"], s["datos"], "0.00"))
    if daily:
        sheets.append(("Tipo de cambio diario", ["fecha", "Compra (RD$/US$)", "Venta (RD$/US$)"], daily, "0.0000"))
    write_xlsx(OUT / "tbrl_datos_macro_rd.xlsx", sheets,
               [("Contenido", "Tipo de cambio USD/DOP (mensual, semanal y diario), tasa de política monetaria, inflación, "
                              "tasas de interés (interbancaria, activa y pasiva), reservas internacionales e IMAE."),
                ("Fuente", FUENTE_BCRD + "; serie mensual del tipo de cambio publicada por la DGII."),
                ("Actualizado", today), ("Elaboración", "The Business Research Lab (TBRL)"),
                ("Uso", "Libre uso citando la fuente: «Fuente: BCRD · Elaboración TBRL». No constituye asesoría de inversión.")])

    payload = {"actualizado": today, "series": series, "descargas": {
        "csv": "data/macro/descargas/tbrl_datos_macro_rd_mensual.csv",
        "xlsx": "data/macro/descargas/tbrl_datos_macro_rd.xlsx",
        "diario_csv": "data/macro/descargas/tipo_cambio_usd_dop_diario.csv"}}
    SERIES_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- sincroniza la página de inteligencia de mercado ----
    if MARKETS_JSON.exists():
        m = json.loads(MARKETS_JSON.read_text(encoding="utf-8"))
        m["fxHistory"] = [{"date": d, "value": v} for d, v in fx_monthly[-12:] if v is not None]
        tpm_nn = [p for p in tpm if p[1] is not None]
        m["tpmHistory"] = [{"date": d, "value": v} for d, v in tpm_nn[-12:]]
        if tpm_nn:
            m["policy"]["tpm"] = tpm_nn[-1][1]
        infl_nn = [p for p in infl if p[1] is not None]
        if infl_nn:
            y, mo = infl_nn[-1][0].split("-")
            meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"]
            m["policy"]["inflationYoY"] = infl_nn[-1][1]
            m["policy"]["inflationDate"] = f"{meses[int(mo) - 1]} {y}"
        last = next((r for r in reversed(fx_d) if num(r.get("compra")) and num(r.get("venta"))), None)
        if last and last["fecha"] >= m["fx"].get("date", ""):
            m["fx"].update({"buy": num(last["compra"]), "sell": num(last["venta"]), "date": last["fecha"]})
        m["updated"] = today
        MARKETS_JSON.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK · {len(series)} series · {len(fx_monthly)} meses de tipo de cambio · {len(weekly)} semanas · {len(daily)} días")


if __name__ == "__main__":
    main()
