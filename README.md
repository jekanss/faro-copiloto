# Faro Copiloto

Asistente de IA para Faro, distribuidora de repuestos automotrices en Bogotá. Resuelve tres problemas: lee facturas de proveedores, responde consultas sobre fichas técnicas y garantías, y ayuda a los vendedores a armar cotizaciones. El detalle está en [docs/problema.md](docs/problema.md).

## Estado
Fase 1: estructura del proyecto, entorno y pruebas. Todavía no hay servicio en funcionamiento.

## Requisitos
- Python 3.11 o superior
- Git

## Instalación (menos de 10 minutos)

1. Clonar el repositorio:
   git clone https://github.com/jekanss/faro-copiloto.git
   cd faro-copiloto

2. Crear el entorno virtual:
   python -m venv .venv

3. Activarlo:
   Windows (PowerShell): .venv\Scripts\Activate.ps1
   Linux o Mac: source .venv/bin/activate

4. Instalar las dependencias:
   pip install -r requirements.txt

5. Correr las pruebas:
   pytest

Si todo está bien, pytest termina en verde con todas las pruebas aprobadas.

## Estructura
- src/faro: código de la aplicación
- tests: pruebas automáticas
- data: datos ficticios de Faro (catálogo, inventario, facturas, fichas)
- docs: documentación del proyecto

## Dónde corre y quién lo mantiene
Por ahora corre solo en el computador del desarrollador. Más adelante tendrá dos modos con el mismo código: en la nube (AWS) o en un servidor propio de Faro sin salida a internet. Lo que cambia entre los dos es la configuración, no el código.

Mantenimiento: Jean Carlos Chamorro.

## Seguridad
Las claves y contraseñas nunca se guardan en este repositorio. Irán en un archivo .env local, que está excluido por .gitignore.