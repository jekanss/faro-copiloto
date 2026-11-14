# Criterio: qué camino de IA aplica a cada problema de Faro

Para: Rosa Molina, gerente general
Pregunta: "¿Por qué no simplemente compramos ChatGPT para todos?"

## La respuesta corta

Para algunas tareas, ChatGPT basta y no vale la pena construir nada. Para otras, no basta: necesita los datos de Faro, tiene que entregar un resultado exacto a otro sistema o tiene que actuar con permisos. Y hay tareas que no necesitan IA en absoluto. Este documento dice cuál es cuál.

## Los 6 caminos, del más barato al más caro

| Camino | Cuándo se usa | Ejemplo en Faro |
|---|---|---|
| No usar IA | Hay una regla exacta o el dato ya está en la base | Cuántas unidades quedan |
| Prompt | Tarea de texto general, sin datos de la empresa o con muy pocos | Redactar un aviso |
| Salida estructurada | El resultado va a otro sistema y tiene que salir en un formato fijo | Leer una factura |
| RAG | La respuesta está en documentos de Faro que cambian | Garantía de un producto |
| Agente | Varios pasos, con decisiones y acciones | Armar y enviar una cotización |
| Fine-tuning | Un estilo propio que nada más logró | Tono de los vendedores |

Regla: se empieza por el camino más bajo y solo se sube cuando ese no alcanza. Cada peldaño cuesta más plata, más mantenimiento y más riesgo.

## Las 4 preguntas para decidir

1. ¿Hay una regla exacta o el dato ya está en una base? Entonces no hace falta IA.
2. ¿El resultado lo recibe otro sistema? Entonces salida estructurada.
3. ¿Necesita documentos de Faro que cambian? Entonces RAG.
4. ¿Son varios pasos, con decisiones o acciones? Entonces agente.

## Los 10 casos de Faro

| # | Caso | Camino | Por qué |
|---|---|---|---|
| 1 | Digitar las 400 facturas de proveedores al mes | Salida estructurada | Se extraen siempre los mismos campos para el sistema contable. Las reglas verifican que cuadren y lo dudoso va a Diana |
| 2 | Cuántas unidades quedan de una referencia | No usar IA | Es una consulta a la base de datos. Exacta y gratis |
| 3 | Qué garantía tiene un producto y qué condiciones pide | RAG | La respuesta está en las fichas técnicas, que el modelo no conoce |
| 4 | Armar la cotización para un taller y enviarla | Agente | Consulta inventario, revisa fichas, arma el borrador y pide aprobación antes de enviar |
| 5 | Redactar el aviso del horario de diciembre | Prompt | Tarea de texto general. Aquí ChatGPT basta |
| 6 | Calcular el IVA de una factura | No usar IA | Es una fórmula fija. La IA podría equivocarse en una cuenta que una fórmula nunca falla |
| 7 | Separar 200 correos al día en pedido, reclamo o pregunta de precio | Salida estructurada | Clasificar es llenar un campo con una de 3 opciones fijas. Es un solo paso, no hace falta agente |
| 8 | Bot de WhatsApp con el tono de los vendedores | Fine-tuning, como último recurso | Solo porque ya se probaron prompts con ejemplos y no funcionó. Enseña estilo, no datos |
| 9 | Resumen de la política de devoluciones para un vendedor nuevo | Prompt | Es un documento corto y una sola vez: se pega en la pregunta. RAG se justifica con muchos documentos y muchas preguntas |
| 10 | Avisar cuando un producto baje de 5 unidades | No usar IA | Es una regla: si el stock es menor que 5, se envía una alerta. Un agente aquí es gastar plata en algo que un "si" resuelve |

## Lo que significa para Faro

- Casos 5 y 9: ChatGPT para el equipo es suficiente. No se construye nada.
- Casos 2, 6 y 10: se resuelven con el sistema que ya existe o con una regla. Sin costo de IA.
- Casos 1, 3, 4 y 7: aquí está Faro Copiloto, porque necesitan los datos de Faro, resultados exactos o permisos.
- Caso 8: queda en espera. Primero se mide si los otros resuelven el problema.

Sobre la preocupación de Rosa por los datos: en los casos 5 y 9 solo se usa ChatGPT con datos que no son sensibles. Los datos de los clientes y los costos nunca se pegan en una herramienta pública: viven en Faro Copiloto, con permisos por rol.
