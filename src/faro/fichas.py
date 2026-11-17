"""Ingesta de fichas técnicas: del PDF a pedazos (chunks) listos para volverse vectores."""

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

SECCIONES = ("Especificaciones", "Vehículos compatibles", "Garantía", "Notas de instalación")
PIE = "Documento ficticio para pruebas de Faro Copiloto."


@dataclass(frozen=True)
class Fragmento:
    referencia: str
    producto: str
    categoria: str
    seccion: str
    texto: str              # lo que se le muestra al vendedor y se cita
    texto_para_buscar: str  # con cabecera: lo que se convierte en vector


def leer_texto(ruta: Path) -> str:
    return "\n".join(pagina.extract_text() for pagina in PdfReader(ruta).pages)


def partir_ficha(texto: str) -> list[Fragmento]:
    lineas = [l.strip() for l in texto.splitlines() if l.strip() and l.strip() != PIE]
    if len(lineas) < 3:
        raise ValueError("La ficha no trae cabecera completa")

    producto = lineas[1]
    cabecera = re.search(r"Referencia Faro:\s*(\S+)\s+Categoría:\s*(.+)", lineas[2])
    if not cabecera:
        raise ValueError(f"No encontré referencia y categoría en: {lineas[2]!r}")
    referencia, categoria = cabecera.group(1), cabecera.group(2).strip()

    partes: dict[str, list[str]] = {}
    actual = None
    for linea in lineas[3:]:
        if linea in SECCIONES:
            actual = linea
            partes[actual] = []
        elif actual is None:
            raise ValueError(f"{referencia}: texto antes de la primera sección: {linea!r}")
        else:
            partes[actual].append(linea)

    return [
        Fragmento(
            referencia=referencia,
            producto=producto,
            categoria=categoria,
            seccion=seccion,
            texto="\n".join(cuerpo),
            texto_para_buscar=f"{producto} ({referencia}, {categoria}). {seccion}: " + " ".join(cuerpo),
        )
        for seccion, cuerpo in partes.items()
    ]