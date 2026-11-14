"""Genera las 20 facturas ficticias de proveedores en PDF y su hoja de respuestas.

Salida:
  data/facturas/FAC-01.pdf ... FAC-20.pdf   lo que la IA va a leer en la Fase 2
  data/facturas/esperado.json               lo que cada factura DICE, para medir a la IA

17 facturas cuadran. 3 traen un error sembrado a propósito, como los que
le llegan a Diana en la vida real. Las 3 usan formatos distintos, porque
cada proveedor manda la factura a su manera.

Correr desde la raíz del repo:  python scripts/generar_facturas.py
"""

import json
import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from fpdf import FPDF

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data"
SALIDA = DATOS / "facturas"

IVA = Decimal("0.19")
CENTAVO = Decimal("0.01")

# Qué le vende cada proveedor a Faro (por prefijo de referencia).
SURTIDO = {
    "900452318-4": ["FAR-FA", "FAR-FI", "FAR-FC", "FAR-TE"],  # Andina: surtido general
    "830129774-1": ["FAR-PF", "FAR-DF"],                      # Frenos del Norte
    "901238876-0": ["FAR-AC", "FAR-FA"],                      # Lubricantes Sabana
    "800987123-5": ["FAR-BU", "FAR-BO", "FAR-BT"],            # Eléctricos Prado
    "901577402-9": ["FAR-AM", "FAR-RO"],                      # Suspensiones Técnicas
    "860045332-2": ["FAR-CR", "FAR-BA", "FAR-EM"],            # El Ruiseñor
}

# Los 3 errores sembrados: número de factura y qué se daña.
ERRORES = {
    6: "total_mal",      # el total no es subtotal + IVA
    13: "item_mal",      # un renglón: cantidad x precio no da su subtotal
    20: "suma_mal",      # la suma de los renglones no da el subtotal
}


def pesos(valor: Decimal) -> str:
    """Formato colombiano: punto para miles, coma para decimales. 1234567.5 -> $1.234.567,50"""
    texto = f"{valor:,.2f}"
    return "$" + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def armar_factura(n: int, proveedor: dict, productos: list[dict], azar: random.Random) -> dict:
    prefijos = SURTIDO[proveedor["nit"]]
    candidatos = [p for p in productos if p["referencia"][:6] in prefijos]
    elegidos = azar.sample(candidatos, k=min(len(candidatos), azar.randint(1, 4)))

    items = []
    for p in elegidos:
        cantidad = azar.choice([2, 4, 5, 6, 10, 12, 20, 24])
        precio = Decimal(str(p["costo"]))  # el proveedor le vende a Faro al costo
        items.append({
            "referencia": p["referencia"],
            "descripcion": f'{p["nombre"]} {p["marca"]}',
            "cantidad": cantidad,
            "precio_unitario": precio,
            "subtotal": cantidad * precio,
        })

    subtotal = sum((i["subtotal"] for i in items), Decimal("0"))
    iva = (subtotal * IVA).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    total = subtotal + iva

    error = ERRORES.get(n)
    if error == "total_mal":
        total += Decimal("90000")             # un dígito mal digitado en el total
    elif error == "item_mal":
        items[0]["subtotal"] += Decimal("10000")  # el renglón 1 no cuadra
        subtotal += Decimal("10000")              # y el subtotal lo arrastra
        iva = (subtotal * IVA).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        total = subtotal + iva
    elif error == "suma_mal":
        subtotal -= Decimal("50000")          # el subtotal no es la suma de los renglones
        iva = (subtotal * IVA).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        total = subtotal + iva

    fecha = date(2026, 10, 1) + timedelta(days=azar.randint(0, 40))
    prefijo_num = proveedor["razon_social"].split()[0][:3].upper()
    return {
        "archivo": f"FAC-{n:02d}.pdf",
        "numero": f"{prefijo_num}-{azar.randint(1000, 9999)}",
        "proveedor_nit": proveedor["nit"],
        "proveedor_nombre": proveedor["razon_social"],
        "fecha": fecha,
        "items": items,
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
        "error_sembrado": error,
    }


def dibujar_pdf(f: dict, estilo: int, ruta: Path) -> None:
    """Tres formatos distintos, como pasa con proveedores reales."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 15)

    # Encabezado: cambia de lugar y de etiqueta según el estilo.
    if estilo == 0:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 9, f["proveedor_nombre"], new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f'NIT {f["proveedor_nit"]}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 7, f'FACTURA ELECTRÓNICA DE VENTA No. {f["numero"]}', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f'Fecha de expedición: {f["fecha"]:%d/%m/%Y}', new_x="LMARGIN", new_y="NEXT")
    elif estilo == 1:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(110, 6, f["proveedor_nombre"].upper())
        pdf.cell(0, 6, f'Factura: {f["numero"]}', align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(110, 5, f'Nit: {f["proveedor_nit"]}  Régimen común')
        pdf.cell(0, 5, f'Fecha: {f["fecha"]:%Y-%m-%d}', align="R", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f'Fecha {f["fecha"]:%d-%m-%Y}  |  Documento {f["numero"]}', align="R",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, f["proveedor_nombre"], align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f'Identificación tributaria: {f["proveedor_nit"]}', align="C",
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Adquiriente: Faro Repuestos SAS  NIT 901345678-2  Bogotá D.C.",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Tabla de renglones: el orden de columnas también cambia.
    if estilo == 1:
        columnas = [("Cant", 15, "cantidad"), ("Código", 30, "referencia"),
                    ("Descripción", 75, "descripcion"), ("Vr. Unit", 35, "precio_unitario"),
                    ("Vr. Total", 35, "subtotal")]
    else:
        columnas = [("Referencia", 30, "referencia"), ("Descripción", 75, "descripcion"),
                    ("Cantidad", 20, "cantidad"), ("Precio unitario", 32, "precio_unitario"),
                    ("Subtotal", 33, "subtotal")]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    for titulo, ancho, _ in columnas:
        pdf.cell(ancho, 7, titulo, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for item in f["items"]:
        for _, ancho, campo in columnas:
            valor = item[campo]
            if isinstance(valor, Decimal):
                pdf.cell(ancho, 7, pesos(valor), border=1, align="R")
            else:
                pdf.cell(ancho, 7, str(valor), border=1)
        pdf.ln()

    # Totales
    pdf.ln(3)
    etiquetas = (["Subtotal", "IVA 19%", "TOTAL A PAGAR"] if estilo != 2
                 else ["Valor bruto", "Impuesto (IVA)", "Neto a pagar"])
    for etiqueta, valor in zip(etiquetas, [f["subtotal"], f["iva"], f["total"]]):
        pdf.set_font("Helvetica", "B" if etiqueta == etiquetas[-1] else "", 10)
        pdf.cell(150, 7, etiqueta, align="R")
        pdf.cell(40, 7, pesos(valor), align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, "Forma de pago: crédito 30 días. Esta factura se asimila en sus efectos "
                         "a la letra de cambio. Documento ficticio para pruebas de Faro Copiloto.")
    pdf.output(str(ruta))


def a_json(valor):
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    raise TypeError(type(valor))


def main() -> None:
    azar = random.Random(2026)  # semilla fija: siempre salen las mismas 20 facturas
    productos = json.loads((DATOS / "productos.json").read_text(encoding="utf-8"))
    proveedores = json.loads((DATOS / "proveedores.json").read_text(encoding="utf-8"))
    SALIDA.mkdir(exist_ok=True)

    esperado = []
    for n in range(1, 21):
        proveedor = proveedores[(n - 1) % len(proveedores)]
        factura = armar_factura(n, proveedor, productos, azar)
        dibujar_pdf(factura, estilo=n % 3, ruta=SALIDA / factura["archivo"])
        esperado.append(factura)

    (SALIDA / "esperado.json").write_text(
        json.dumps(esperado, default=a_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Listo: {len(esperado)} facturas en {SALIDA}")


if __name__ == "__main__":
    main()
