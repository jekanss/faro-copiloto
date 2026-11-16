"""Extracción de facturas con salida estructurada.

El modelo lee el PDF y llena el formulario Factura de modelos.py.
La IA transcribe; la regla cuadra() juzga después.
"""

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from faro.modelos import Factura

load_dotenv()

MODELO = os.getenv("OPENAI_MODEL", "gpt-5-mini")

INSTRUCCIONES = """Eres un digitador contable. Lee la factura de compra en PDF y llena el formulario.
Reglas:
- Copia cada número exactamente como aparece impreso. No corrijas cuentas ni recalcules nada, aunque no cuadren.
- Valores en pesos sin separadores de miles ni símbolo, con punto para los decimales: 1.234.567 se escribe 1234567 y 405.000,00 se escribe 405000.00.
- La fecha en formato AAAA-MM-DD.
- proveedor_nit es el NIT de quien vende, con guion y dígito de verificación, por ejemplo 900123456-7.
"""


def extraer_factura(ruta_pdf: str | Path) -> tuple[Factura, dict]:
    """Lee un PDF y devuelve la factura extraída y el uso de tokens."""
    ruta = Path(ruta_pdf)
    pdf_b64 = base64.b64encode(ruta.read_bytes()).decode()
    cliente = OpenAI()
    respuesta = cliente.responses.parse(
        model=MODELO,
        instructions=INSTRUCCIONES,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "filename": ruta.name,
                        "file_data": f"data:application/pdf;base64,{pdf_b64}",
                    },
                    {"type": "input_text", "text": "Extrae esta factura."},
                ],
            }
        ],
        text_format=Factura,
    )
    uso = {
        "modelo": MODELO,
        "tokens_entrada": respuesta.usage.input_tokens,
        "tokens_salida": respuesta.usage.output_tokens,
    }
    return respuesta.output_parsed, uso