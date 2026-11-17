# Mediciones de la extracción de facturas

Modelo gpt-5-mini, 20 facturas ficticias (3 con errores sembrados), 16 nov 2026.

| Esfuerzo | Perfectas | Cuadre | USD por factura | Segundos por factura |
|---|---|---|---|---|
| medium | 20/20 | 20/20 | 0.0022 | 13 |
| low | 20/20 | 20/20 | 0.0013 | 6.7 |
| minimal | 20/20 | 20/20 | 0.0007 | 4.1 |

Decisión: low por defecto (variable OPENAI_REASONING_EFFORT). Los PDF de prueba son digitales y limpios; minimal se reconsidera al medir facturas escaneadas reales.

Límite: 0 errores en 20 facturas solo garantiza, con 95% de confianza, un error real menor al 15% (regla del tres).