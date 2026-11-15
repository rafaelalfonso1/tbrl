#!/usr/bin/env python3
"""
Construye los archivos del conjunto de datos inmobiliario a partir del CSV original:

  public/data/inmobiliario/tbrl_muestra_anuncios_inmobiliarios_nov2026.csv   (fuente, no se modifica)

Genera:
  public/data/inmobiliario/tbrl_muestra_anuncios_inmobiliarios_nov2026.xlsx  (Léeme + datos + resúmenes)
  public/data/inmobiliario/resumen.json                                       (lo lee el Centro de datos)

Uso:  python scripts/construir_inmobiliario.py
Para una nueva edición: copia el nuevo CSV con el mismo formato, cambia NOMBRE abajo y ejecuta.
"""
import csv, json, statistics as st
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "public" / "data" / "inmobiliario"
NOMBRE = "tbrl_muestra_anuncios_inmobiliarios_nov2026"
PAPER = "downloads/tbrl-salud-inversion-residencial-gsd-nov2026.pdf"


def pct(v, p):
    v = sorted(v)
    k = (len(v) - 1) * p / 100
    f, c = int(k), min(int(k) + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def r0(x):
    return int(x + 0.5)


def num(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None


def main():
    src = DIR / f"{NOMBRE}.csv"
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    sectors = list(OrderedDict.fromkeys(r["sector"] for r in rows))

    def resumen(op):
        out = []
        for s in sectors:
            rs = [r for r in rows if r["sector"] == s and r["operacion"] == op]
            if not rs:
                continue
            precio = [num(r["precio_usd"]) for r in rs if num(r["precio_usd"])]
            m2 = [num(r["usd_m2"]) for r in rs if num(r["usd_m2"])]
            item = {"sector": s, "n": len(rs), "precio_mediano": r0(st.median(precio))}
            if m2:
                item.update({"usd_m2_mediana": r0(st.median(m2)), "usd_m2_p25": r0(pct(m2, 25)),
                             "usd_m2_p75": r0(pct(m2, 75)), "n_m2": len(m2)})
            out.append(item)
        return out

    venta, alquiler = resumen("venta"), resumen("alquiler")
    allm2 = [num(r["usd_m2"]) for r in rows if r["operacion"] == "venta" and num(r["usd_m2"])]
    rents = [num(r["precio_usd"]) for r in rows if r["operacion"] == "alquiler"]
    data = {
        "titulo": "Muestra de anuncios de apartamentos en siete sectores del Distrito Nacional",
        "periodo": "abril–noviembre 2026",
        "fuentes": "Encuentra24 y CLIC Inmobiliaria (anuncios publicados)",
        "n_total": len(rows), "n_venta": sum(v["n"] for v in venta), "n_alquiler": sum(a["n"] for a in alquiler),
        "usd_m2_mediana_total": r0(st.median(allm2)), "renta_mediana_total": r0(st.median(rents)),
        "venta": sorted(venta, key=lambda x: -x.get("usd_m2_mediana", 0)),
        "alquiler": sorted(alquiler, key=lambda x: -x["precio_mediano"]),
        "descargas": {"csv": f"data/inmobiliario/{NOMBRE}.csv", "xlsx": f"data/inmobiliario/{NOMBRE}.xlsx"},
        "paper": PAPER,
    }
    (DIR / "resumen.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- Excel ----
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    navy = PatternFill("solid", fgColor="2C4856")
    wb = Workbook()
    ws = wb.active
    ws.title = "Léeme"
    ws["A1"] = "The Business Research Lab — " + data["titulo"]
    ws["A1"].font = Font(bold=True, size=14, color="2C4856")
    meta = [
        ("Período", data["periodo"]),
        ("Fuentes", data["fuentes"]),
        ("Registros", f"{data['n_total']} anuncios ({data['n_venta']} de venta y {data['n_alquiler']} de alquiler)"),
        ("Sectores", ", ".join(sectors)),
        ("Documento", "Salud de la inversión residencial en el Gran Santo Domingo (TBRL-2026-03), sección 4.3"),
        ("Cita sugerida", "Fuente: The Business Research Lab (2026), muestra de anuncios inmobiliarios, nov. 2026."),
        ("", ""),
        ("Columnas", ""),
        ("sector", "Sector del Distrito Nacional"),
        ("operacion", "venta o alquiler"),
        ("precio_usd", "Precio anunciado en US$ (venta: precio total; alquiler: renta mensual)"),
        ("m2", "Área anunciada en metros cuadrados (vacía si el anuncio no la indica)"),
        ("usd_m2", "Precio por m² en US$ (venta) o renta mensual por m² (alquiler)"),
        ("estado_o_habitaciones", "Venta: terminado o proyecto (en planos). Alquiler: número de habitaciones"),
        ("fuente", "Portal donde se publicó el anuncio"),
        ("", ""),
        ("Advertencias", "Son precios de oferta, no de cierre. Mezcla unidades amuebladas y sin amueblar. "
                         "No se eliminaron posibles duplicados entre portales. Algunos sectores tienen muestras pequeñas."),
        ("Uso", "Libre uso citando la fuente. No constituye asesoría financiera, legal ni fiscal."),
    ]
    for i, (k, v) in enumerate(meta, start=3):
        ws.cell(i, 1, k).font = Font(bold=True)
        ws.cell(i, 2, v).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 100

    def sheet(name, header, body, fmts):
        s = wb.create_sheet(name)
        s.append(header)
        for c in s[1]:
            c.font = Font(bold=True, color="F7F4EB")
            c.fill = navy
        for b in body:
            s.append(b)
        for col, fmt in fmts.items():
            for row in s.iter_rows(min_row=2, min_col=col, max_col=col):
                for c in row:
                    c.number_format = fmt
        for i in range(1, len(header) + 1):
            s.column_dimensions[chr(64 + i)].width = 20
        s.column_dimensions["A"].width = 22
        s.freeze_panes = "A2"
        s.auto_filter.ref = s.dimensions

    cols = ["sector", "operacion", "precio_usd", "m2", "usd_m2", "estado_o_habitaciones", "fuente"]
    body = []
    for r in rows:
        eh = r["estado_o_habitaciones"]
        body.append([r["sector"], r["operacion"], num(r["precio_usd"]), num(r["m2"]), num(r["usd_m2"]),
                     int(float(eh)) if eh.replace(".", "").isdigit() else (eh or None), r["fuente"]])
    sheet("Anuncios", cols, body, {3: "#,##0", 4: "0.00", 5: "#,##0.00"})
    sheet("Resumen venta", ["Sector", "Anuncios", "Precio mediano (US$)", "US$/m² mediana", "US$/m² P25", "US$/m² P75"],
          [[v["sector"], v["n"], v["precio_mediano"], v.get("usd_m2_mediana"), v.get("usd_m2_p25"), v.get("usd_m2_p75")] for v in data["venta"]],
          {3: "#,##0", 4: "#,##0", 5: "#,##0", 6: "#,##0"})
    sheet("Resumen alquiler", ["Sector", "Anuncios", "Renta mediana (US$/mes)", "Renta/m² mediana", "Anuncios con m²"],
          [[a["sector"], a["n"], a["precio_mediano"], a.get("usd_m2_mediana"), a.get("n_m2", 0)] for a in data["alquiler"]],
          {3: "#,##0", 4: "#,##0"})
    wb.save(DIR / f"{NOMBRE}.xlsx")
    print(f"OK · {len(rows)} anuncios · {len(sectors)} sectores")


if __name__ == "__main__":
    main()
