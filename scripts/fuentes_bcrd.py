"""
Lectores de las series mensuales que el Banco Central (BCRD) publica en Excel.
Cada función recibe los bytes del archivo y devuelve {"AAAA-MM": valor}.
Si el BCRD cambia el formato de un archivo, la función lanza un error y la
actualización conserva los datos anteriores de esa serie (no rompe el sitio).
"""
import io
import re
import unicodedata

CDN = "https://cdn.bancentral.gov.do/documents/estadisticas"
ARCHIVOS = {
    "tpm": f"{CDN}/sector-monetario-y-financiero/documents/Serie_TPM.xlsx",
    "inflacion_interanual": f"{CDN}/precios/documents/ipc_base_2019-2020.xls",
    "tasa_activa": f"{CDN}/sector-monetario-y-financiero/documents/tbm_activad.xlsx",
    "tasa_pasiva": f"{CDN}/sector-monetario-y-financiero/documents/tbm_pasivad.xlsx",
    "tasa_interbancaria": f"{CDN}/sector-monetario-y-financiero/documents/operaciones_interb.xls",
    "reservas_brutas": f"{CDN}/sector-externo/documents/reservas_internacionales.xlsx",
    "imae_interanual": f"{CDN}/sector-real/documents/imae_2018.xlsx",
}
DESDE = "2015-01"  # se publican las series desde esta fecha

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
MES_CORTO = {m[:3]: i + 1 for i, m in enumerate(MESES)}
MES_CORTO["set"] = 9


def _norm(x):
    s = unicodedata.normalize("NFKD", str(x if x is not None else "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def _mes(x):
    """Número de mes a partir de 'Enero', 'Febrero ', 'ENE', 'Sept', '*Noviembre 2/' … o None."""
    t = re.match(r"[a-z]*", _norm(x).lstrip("* ")).group(0)
    if t in MESES:
        return MESES.index(t) + 1
    if 3 <= len(t) <= 4 and t[:3] in MES_CORTO:
        return MES_CORTO[t[:3]]
    return None


def _anio(x):
    m = re.match(r"^\*?\s*((?:19|20)\d\d)(?:\.0)?\b", _norm(x))
    return int(m.group(1)) if m else None


def _num(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _filas(data, xls=False, hoja=0):
    if xls:
        import xlrd
        sh = xlrd.open_workbook(file_contents=data).sheet_by_index(hoja)
        return [sh.row_values(i) for i in range(sh.nrows)]
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    return [list(r) for r in wb.worksheets[hoja].iter_rows(values_only=True)]


def _col(filas, patron, desde=0, hasta=12):
    """Índice de la primera columna cuyo encabezado (filas desde..hasta) coincide con el patrón."""
    for r in filas[desde:hasta]:
        for j, v in enumerate(r):
            if re.search(patron, _norm(v)):
                return j
    raise ValueError(f"no se encontró la columna «{patron}»")


def _redondear(d, n=4):
    return {k: round(v, n) for k, v in d.items() if v is not None and k >= DESDE}


def tpm(data):
    """Serie_TPM.xlsx: Año | Mes | TPM | … (en fracción: 0.055 = 5.50 %)."""
    f = _filas(data)
    c = _col(f, r"politica monetaria", desde=3)
    out, y = {}, None
    for r in f:
        y = _anio(r[0]) or y
        m = _mes(r[1]) if len(r) > 1 else None
        v = _num(r[c]) if len(r) > c else None
        if y and m and v is not None:
            out[f"{y}-{m:02d}"] = v * 100 if v < 1 else v
    return _redondear(out, 2)


def inflacion_interanual(data):
    """ipc_base_2019-2020.xls: Año | Mes | Índice | Var. mensual | con dic. | 12 meses | …"""
    f = _filas(data, xls=True)
    c = _col(f, r"12 meses")  # primera columna «12 meses» = variación interanual
    out, y = {}, None
    for r in f:
        y = _anio(r[0]) or y
        m = _mes(r[1])
        v = _num(r[c])
        if y and m and v is not None:
            out[f"{y}-{m:02d}"] = v
    return _redondear(out, 2)


def _tasas_bm(data, patron_col):
    """tbm_activad / tbm_pasivad: 'Enero 2026', 'Febrero', … ; al final, filas diarias del mes en curso (se omiten)."""
    f = _filas(data)
    c = _col(f, patron_col)
    out, y = {}, None
    for r in f:
        txt = _norm(r[0])
        if not txt or txt.startswith("*"):
            continue  # cifras del mes en curso / preliminares
        ym = re.search(r"((?:19|20)\d\d)", txt)
        m = _mes(r[0])
        if m and ym:
            y = int(ym.group(1))
        v = _num(r[c]) if len(r) > c else None
        if y and m and v is not None:
            out[f"{y}-{m:02d}"] = v
    return _redondear(out, 2)


def tasa_activa(data):
    return _tasas_bm(data, r"^ponderado$")


def tasa_pasiva(data):
    return _tasas_bm(data, r"^ponderado$")


def tasa_interbancaria(data):
    """operaciones_interb.xls: sección 'Mensual' con filas de año y luego meses; columna 'Tasa Promedio'."""
    f = _filas(data, xls=True)
    c = _col(f, r"tasa promedio")
    out, y, mensual = {}, None, False
    for r in f:
        a, b = r[1] if len(r) > 1 else "", r
        if _norm(a) == "mensual":
            mensual = True
            continue
        if not mensual:
            continue
        if _anio(a) and _num(r[c]) is None:
            y = _anio(a)
            continue
        if "*" in str(a):
            continue  # mes en curso (parcial)
        m = _mes(a)
        v = _num(r[c])
        if y and m and v is not None:
            out[f"{y}-{m:02d}"] = v
    return _redondear(out, 2)


def reservas_brutas(data):
    """reservas_internacionales.xlsx: años en columnas; dentro de cada año, la columna 'RESERVAS BRUTAS'."""
    f = _filas(data)
    fila_anio = next(i for i, r in enumerate(f[:15]) if _norm(r[0]) == "ano")
    anios = [(j, _anio(v)) for j, v in enumerate(f[fila_anio]) if _anio(v)]
    out = {}
    for k, (j, y) in enumerate(anios):
        fin = anios[k + 1][0] if k + 1 < len(anios) else j + 4
        col = None
        for jj in range(j, fin):
            etiqueta = " ".join(_norm(f[i][jj]) for i in range(fila_anio + 1, fila_anio + 4) if jj < len(f[i]))
            if "bruta" in etiqueta and "activo" not in etiqueta:
                col = jj
                break
        if col is None:
            col = j  # años antiguos: BRUTAS es la primera columna del bloque
        for r in f[fila_anio + 1:]:
            m = _mes(r[0])
            v = _num(r[col]) if len(r) > col else None
            if m and v is not None:
                out[f"{y}-{m:02d}"] = v
    return _redondear(out, 1)


def imae_interanual(data):
    """imae_2018.xlsx: Año | Mes | Índice original | Var. interanual | …
    El año no siempre aparece en la columna A; cada bloque anual cierra con una fila «Promedio AAAA»."""
    f = _filas(data)
    c = _col(f, r"interanual")
    out, pendientes, y = {}, [], None
    for r in f:
        t = _norm(r[0])
        if t.startswith("promedio") and _anio(t.split()[-1]):
            ya = _anio(t.split()[-1])
            for m, v in pendientes:
                out[f"{ya}-{m:02d}"] = v
            pendientes, y = [], ya + 1
            continue
        y = _anio(r[0]) or y
        m = _mes(r[1]) if len(r) > 1 else None
        v = _num(r[c]) if len(r) > c else None
        if m and v is not None:
            if y:
                out[f"{y}-{m:02d}"] = v
            else:
                pendientes.append((m, v))
    return _redondear(out, 2)


LECTORES = {k: globals()[k] for k in ARCHIVOS}
