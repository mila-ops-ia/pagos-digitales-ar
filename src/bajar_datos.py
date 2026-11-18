"""Baja las fuentes oficiales: series de pagos minoristas del BCRA e IPC nacional del INDEC."""
import pathlib, urllib.request

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
BCRA = ("https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/"
        "series-informe-mensual-pagos-minoristas-{mes}.xlsx")
IPC = "https://apis.datos.gob.ar/series/api/series/?ids=148.3_INIVELNAL_DICI_M_26&format=csv&limit=1000"

def bajar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(destino, "wb") as f:
        f.write(r.read())
    print("ok", destino.name)

if __name__ == "__main__":
    import sys
    mes = sys.argv[1] if len(sys.argv) > 1 else "2026-09"   # el BCRA publica un archivo por mes
    bajar(BCRA.format(mes=mes), RAW / f"series-pagos-minoristas-{mes}.xlsx")
    bajar(IPC, RAW / "ipc_nacional.csv")
