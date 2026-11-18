"""Convierte el Excel del BCRA (hojas anchas con encabezados en varias filas) en una tabla larga y ordenada.

Salida: data/pagos_largo.csv con columnas fecha, hoja, serie, medida, valor
"""
import pathlib, datetime as dt
import pandas as pd
import openpyxl, re

MEDIDA = re.compile(r'^(Cantidad|Monto|Saldo)', re.I)

BASE = pathlib.Path(__file__).resolve().parent.parent

def _texto(v):
    return " ".join(str(v).split()) if v not in (None, "") else None

def hoja_a_largo(ws):
    filas = list(ws.iter_rows(values_only=True))
    # la fila de encabezado final es la que tiene "Fecha" en alguna columna
    k = next(i for i, r in enumerate(filas[:12]) if any(_texto(c) == "Fecha" for c in r))
    ancho = max(len(r) for r in filas)
    # encabezados de varios niveles: se completan hacia la derecha (celdas combinadas)
    niveles = []
    for i in range(k + 1):
        fila = list(filas[i]) + [None] * (ancho - len(filas[i]))
        llenos, ultimo, inicio = [], None, None
        for j, c in enumerate(fila):
            t = _texto(c)
            if t:
                ultimo, inicio = t, j
            elif i == k:
                ultimo = None                      # el último nivel no se arrastra
            elif ultimo is not None and i > 0 and niveles[i - 1][j] != niveles[i - 1][inicio]:
                ultimo = None                      # no cruzar el límite del bloque de arriba
            llenos.append(ultimo)
        niveles.append(llenos)
    cols_fecha = [j for j, c in enumerate(niveles[-1]) if c == "Fecha"]
    registros = []
    for r in filas[k + 1:]:
        r = list(r) + [None] * (ancho - len(r))
        for j in range(ancho):
            if j in cols_fecha or r[j] in (None, ""):
                continue
            jf = max([c for c in cols_fecha if c < j], default=None)   # su columna de fecha
            fecha = r[jf] if jf is not None else None
            if not isinstance(fecha, dt.datetime) or not isinstance(r[j], (int, float)):
                continue
            partes = [niveles[i][j] for i in range(k + 1) if niveles[i][j]]
            medidas = [x for x in partes if MEDIDA.match(x)]
            medida = medidas[-1] if medidas else "Cantidad"
            serie = " | ".join(x for x in partes if x != medida) or medida
            registros.append((fecha.date().replace(day=1), ws.title, serie, medida, float(r[j])))
    return registros

def extraer(archivo):
    wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
    todo = []
    for ws in wb.worksheets:
        todo += hoja_a_largo(ws)
    df = pd.DataFrame(todo, columns=["fecha", "hoja", "serie", "medida", "valor"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.sort_values(["hoja", "serie", "medida", "fecha"]).reset_index(drop=True)

if __name__ == "__main__":
    archivo = sorted((BASE / "data" / "raw").glob("series-pagos-minoristas-*.xlsx"))[-1]
    df = extraer(archivo)
    df.to_csv(BASE / "data" / "pagos_largo.csv", index=False)
    print(len(df), "filas |", df[["hoja", "serie", "medida"]].drop_duplicates().shape[0], "series |",
          df.fecha.min().date(), "a", df.fecha.max().date())
