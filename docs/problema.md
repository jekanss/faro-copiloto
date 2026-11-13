\# El problema de Faro



\## Contexto

Faro es una distribuidora de repuestos automotrices en Bogotá: 25 empleados, 8 vendedores y unas 3.000 referencias. No tiene área de sistemas; un proveedor externo de TI le da soporte.



\## Los tres problemas



\### 1. Las facturas de proveedores se digitan a mano

Diana Ruiz, auxiliar contable, digita unas 400 facturas al mes. Cada una le toma cerca de 6 minutos: unas 40 horas al mes. Un total mal digitado termina en un pago equivocado o en un descuadre que ella tiene que perseguir.

Quién lo sufre: Diana (tiempo y responsabilidad por los errores) y Rosa (paga esas horas y esos errores).



\### 2. Los vendedores no encuentran la información técnica

Fichas técnicas, garantías y políticas están en PDFs sueltos. Para saber si un repuesto sirve para un vehículo o si una garantía aplica, el vendedor busca a mano o llama a bodega. El cliente espera unos 10 minutos y a veces recibe una respuesta equivocada.

Quién lo sufre: los 8 vendedores, Camilo (jefe comercial) y el cliente final.



\### 3. Una cotización tarda demasiado

Armar una cotización exige revisar inventario, precios y fichas en sitios distintos. Toma unos 30 minutos y no se puede hacer desde el celular. Mientras tanto, el cliente compra en otra parte.

Quién lo sufre: Camilo y sus vendedores (ventas perdidas) y Rosa (ingresos).



\## Por qué no basta con ChatGPT para todos

\- No conoce el inventario, los precios ni las fichas de Faro: respondería con datos genéricos o inventados.

\- No valida: puede leer mal un total y nadie lo detecta.

\- Los datos de clientes y proveedores saldrían a una herramienta sin control de quién ve qué. Es el miedo de Rosa y además lo exige la Ley 1581.

\- No deja registro de costo, aciertos ni errores: no hay cómo medir si sirve.



ChatGPT sí basta para tareas sueltas que no tocan datos de Faro: redactar un correo, resumir un texto público o generar ideas.



\## Cómo sabremos que funcionó



| Problema | Línea base (supuesta, se mide al iniciar cada fase) | Meta |

|---|---|---|

| Facturas | 6 min por factura, 40 h al mes | Diana solo revisa las dudosas: menos de 1 min por factura y ningún total errado sin marcar |

| Consultas técnicas | 10 min y llamada a bodega | Respuesta en menos de 30 segundos, con la fuente citada y 85% o más de aciertos en el set de evaluación |

| Cotizaciones | 30 min, solo desde el computador | Menos de 5 min desde el celular, con aprobación del vendedor antes de enviar |



Para Rosa: el costo mensual de la IA tiene que ser menor que el costo de las horas ahorradas.



\## Lo que este proyecto no hace

\- No reemplaza el ERP ni la contabilidad de Faro.

\- No envía nada a un cliente sin que una persona lo apruebe.

\- No toma decisiones de pago.

