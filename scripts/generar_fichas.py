"""Genera una ficha técnica en PDF por cada producto del catálogo.

Salida: data/fichas/FAR-XX-NNN.pdf (25 fichas)

Son los documentos que los vendedores hoy buscan a mano o preguntan
a bodega, y los que va a consultar el RAG en la Fase 3. Traen a propósito
lo que hace difícil buscar bien:
  - productos parecidos (3 filtros de aceite, 3 pastillas de freno)
  - compatibilidad con rango de años, no solo el modelo del carro
  - garantías distintas por marca, con condiciones y exclusiones
  - datos en tabla, que se parten mal si el documento se corta sin cuidado

Las fichas NO traen costos ni precios: eso vive en otro lado y tiene permisos.

Correr desde la raíz del repo:  python scripts/generar_fichas.py
"""

import json
from pathlib import Path

from fpdf import FPDF

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data"
SALIDA = DATOS / "fichas"

# Años en que cada modelo es compatible. Un Spark GT 2010 no es un Spark GT 2015.
ANOS = {
    "Chevrolet Spark GT": "2011 a 2021", "Chevrolet Sail": "2013 a 2020",
    "Renault Logan": "2015 a 2024", "Renault Sandero": "2015 a 2024",
    "Renault Duster": "2016 a 2023", "Toyota Hilux": "2016 a 2024",
    "Toyota Fortuner": "2017 a 2024", "Mazda 2": "2015 a 2023",
    "Mazda 3": "2014 a 2024", "Mazda CX-30": "2020 a 2024",
    "Kia Picanto": "2012 a 2023", "Hyundai i10": "2014 a 2022",
    "Nissan Frontier": "2016 a 2023",
}

# Garantía por marca, con sus condiciones. Así la escriben los fabricantes.
GARANTIA = {
    "Mann-Filter": "6 meses o 10.000 km, lo que ocurra primero. Cubre defectos de fabricación.",
    "Bosch": "6 meses desde la fecha de compra. Cubre defectos de fabricación y materiales.",
    "Fram": "6 meses. Se pierde si el filtro se instala con un aceite fuera de especificación.",
    "Brembo": "12 meses o 20.000 km. No cubre desgaste normal ni cristalización por frenado brusco.",
    "Valeo": "12 meses. En kits de embrague: 12 meses o 30.000 km, excluye daños por patinar el embrague.",
    "NGK": "12 meses. Se pierde si se instala con un torque distinto al indicado.",
    "Gates": "24 meses o 60.000 km, solo si lo instaló un taller y se presenta la factura de instalación.",
    "Monroe": "24 meses o 40.000 km. Garantía limitada: no cubre uso en competencia ni vehículos de carga pesada.",
    "SKF": "12 meses. Requiere cambiar el rodamiento completo, no solo la pista.",
    "MAC": "18 meses. Para hacerla válida se exige prueba de carga en un punto autorizado.",
    "Mobil": "No aplica garantía de desempeño. Solo se recibe en devolución sellado y sin abrir.",
}

# Especificaciones propias de cada referencia.
SPECS = {
    "FAR-FA-001": {"Tipo": "Roscado", "Rosca": "3/4-16 UNF", "Altura": "79 mm", "Válvula antirretorno": "Sí"},
    "FAR-FA-002": {"Tipo": "Roscado", "Rosca": "M20x1,5", "Altura": "86 mm", "Válvula antirretorno": "Sí"},
    "FAR-FA-003": {"Tipo": "Elemento (cartucho)", "Diámetro": "72 mm", "Altura": "102 mm", "Válvula antirretorno": "No aplica"},
    "FAR-FI-001": {"Forma": "Panel rectangular", "Medidas": "245 x 180 x 42 mm", "Material": "Celulosa"},
    "FAR-FI-002": {"Forma": "Panel rectangular", "Medidas": "215 x 160 x 38 mm", "Material": "Celulosa con prefiltro"},
    "FAR-FC-001": {"Combustible": "Diésel", "Separador de agua": "Sí", "Presión máxima": "6 bar"},
    "FAR-PF-001": {"Compuesto": "Semimetálico", "Sensor de desgaste": "No", "Espesor": "16,5 mm", "Eje": "Delantero"},
    "FAR-PF-002": {"Compuesto": "Cerámico", "Sensor de desgaste": "Sí, incluido", "Espesor": "17,8 mm", "Eje": "Delantero"},
    "FAR-PF-003": {"Compuesto": "Orgánico de bajo metal", "Sensor de desgaste": "No", "Espesor": "17 mm", "Eje": "Delantero"},
    "FAR-DF-001": {"Tipo": "Ventilado", "Diámetro": "319 mm", "Espesor mínimo": "26 mm", "Se vende": "Por unidad, se recomienda cambiar en par"},
    "FAR-BU-001": {"Electrodo": "Iridio", "Rosca": "14 mm", "Calibración": "0,8 mm", "Vida útil": "Hasta 100.000 km"},
    "FAR-BU-002": {"Electrodo": "Níquel", "Rosca": "14 mm", "Calibración": "0,9 mm", "Vida útil": "Hasta 20.000 km"},
    "FAR-BO-001": {"Tipo": "Bobina independiente (lápiz)", "Conector": "3 pines", "Voltaje": "12 V"},
    "FAR-CR-001": {"Incluye": "Correa, tensor y polea guía", "Dientes": "123", "Cambio sugerido": "Cada 60.000 km"},
    "FAR-CR-002": {"Tipo": "Poly-V", "Canales": "6", "Longitud": "1.230 mm"},
    "FAR-BA-001": {"Impulsor": "Metálico", "Incluye empaque": "Sí", "Cambio sugerido": "Junto con la correa de repartición"},
    "FAR-TE-001": {"Temperatura de apertura": "82 °C", "Incluye empaque": "Sí"},
    "FAR-AM-001": {"Tipo": "Gas, McPherson", "Lado": "Izquierdo o derecho (universal)", "Se vende": "Por unidad"},
    "FAR-AM-002": {"Tipo": "Gas, telescópico", "Lado": "Izquierdo o derecho", "Se vende": "Por unidad"},
    "FAR-AM-003": {"Tipo": "Gas de alta presión, uso mixto", "Lado": "Izquierdo o derecho", "Se vende": "Por unidad"},
    "FAR-RO-001": {"Tipo": "Doble hilera de bolas", "Con ABS": "Sí, anillo magnético integrado", "Se vende": "Por unidad"},
    "FAR-EM-001": {"Incluye": "Disco, prensa y balinera", "Diámetro del disco": "200 mm", "Estrías": "26"},
    "FAR-EM-002": {"Incluye": "Disco, prensa, balinera y volante bimasa", "Diámetro del disco": "250 mm", "Estrías": "24"},
    "FAR-BT-001": {"Voltaje": "12 V", "Capacidad": "45 Ah", "Corriente de arranque (CCA)": "380 A", "Borne positivo": "Derecho"},
    "FAR-AC-001": {"Viscosidad": "10W-30", "Base": "Semisintético", "Presentación": "Galón (3,785 L)", "Norma": "API SP"},
}

# Notas de instalación por categoría: lo que un vendedor tiene que advertir.
NOTAS = {
    "Filtros": "Cambiar junto con el aceite. Lubricar el empaque antes de instalar y apretar a mano.",
    "Frenos": "Cambiar siempre por eje completo. Asentar las pastillas con frenadas suaves los primeros 200 km.",
    "Encendido": "Instalar con el motor frío. Respetar el torque del fabricante del vehículo.",
    "Motor": "Instalación exclusiva en taller. Una correa de repartición mal instalada puede dañar el motor.",
    "Refrigeración": "Usar refrigerante nuevo y purgar el sistema después de instalar.",
    "Suspensión": "Cambiar en par por eje. Hacer alineación después de la instalación.",
    "Transmisión": "Instalación exclusiva en taller. Revisar el volante del motor antes de instalar el kit.",
    "Eléctrico": "Desconectar primero el borne negativo. Verificar que la posición del borne positivo coincide.",
    "Lubricantes": "Revisar el manual del vehículo antes de cambiar de viscosidad.",
}


def dibujar_ficha(p: dict, ruta: Path) -> None:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "FARO REPUESTOS SAS  |  Ficha técnica", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 9, f'{p["nombre"]} {p["marca"]}', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f'Referencia Faro: {p["referencia"]}   Categoría: {p["categoria"]}',
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def titulo(texto: str) -> None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, texto, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

    titulo("Especificaciones")
    for clave, valor in SPECS[p["referencia"]].items():
        pdf.cell(60, 6, clave, border=1)
        pdf.cell(0, 6, valor, border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    titulo("Vehículos compatibles")
    if p["vehiculos_compatibles"]:
        for vehiculo in p["vehiculos_compatibles"]:
            pdf.cell(0, 6, f"- {vehiculo}, modelos {ANOS[vehiculo]}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.multi_cell(0, 6, "Uso general. Verificar la viscosidad recomendada en el manual del vehículo.")
    pdf.ln(4)

    titulo("Garantía")
    pdf.multi_cell(0, 6, GARANTIA[p["marca"]])
    pdf.ln(4)

    titulo("Notas de instalación")
    pdf.multi_cell(0, 6, NOTAS[p["categoria"]])

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, "Documento ficticio para pruebas de Faro Copiloto.")
    pdf.output(str(ruta))


def main() -> None:
    productos = json.loads((DATOS / "productos.json").read_text(encoding="utf-8"))
    SALIDA.mkdir(exist_ok=True)
    for p in productos:
        dibujar_ficha(p, SALIDA / f'{p["referencia"]}.pdf')
    print(f"Listo: {len(productos)} fichas en {SALIDA}")


if __name__ == "__main__":
    main()
