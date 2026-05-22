# Spec Driven Development

## Constitución: Definir marco fundamental
Crear un gemelo digital de una central hidroeléctrica que simule embalse, turbina y control de caudal en tiempo real. El sistema debe generar potencia instantánea en MW y energía acumulada en MWh, registrar cada ciclo operativo, alimentar Elasticsearch y visualizarse en Kibana. El objetivo final es predecir el próximo consumo energético y ajustar la generación necesaria.

## Especificación: Detallar requisitos exactos
- Integrar [PID_bomba.py](PID_bomba.py) como modelo de turbina y [tank.py](tank.py) como modelo de embalse.
- Implementar un `main.py` que orqueste la simulación completa.
- Calcular la potencia generada de forma proporcional a la velocidad de la turbina.
- Registrar por iteración: timestamp, nivel del embalse, velocidad de turbina, apertura de válvula, caudal, potencia MW, energía MWh y consumo estimado.
- Generar documentos JSON listos para Logstash.
- Indexar eventos en Elasticsearch y visualizarlos en Kibana.
- Entrenar un modelo de time series forecasting con HuggingFace para predecir el siguiente consumo.
- Usar la predicción como referencia para ajustar la operación del sistema.

## Clarificación: Alinear objetivos y dudas
Decisiones cerradas para el MVP:
- Métrica principal: ambas, potencia instantánea y energía acumulada.
- Horizonte de predicción: próximo paso de tiempo.
- Dataset de consumo: sintético para validar el flujo end-to-end.

Supuestos:
- La simulación será discreta y ejecutada por ciclos.
- El primer entregable prioriza la integración completa sobre la precisión física.
- El modelo predictivo se usará como apoyo al control, no como sustituto del PID.

## Plan: Organizar secuencia de trabajo
1. Unificar la simulación en `main.py`.
2. Definir el esquema de evento y su exportación JSON.
3. Conectar la salida con Logstash, Elasticsearch y Kibana.
4. Analizar el dataset y limpiarlo.
5. Entrenar el modelo de forecasting.
6. Integrar la predicción en la lógica de control.
7. Validar el sistema completo con escenarios de prueba.

## Tareas: Asignar actividades concretas
- [x] Crear `main.py` para orquestar turbina, embalse y cálculo de energía.
- [x] Ajustar la simulación para exponer variables operativas consistentes.
- [x] Definir el documento JSON que consumirá Logstash.
- Configurar el índice y la visualización base en Elasticsearch y Kibana.
- Preparar el dataset sintético.
- Entrenar y evaluar el modelo de predicción.
- Conectar la predicción con el control de la central.
- Documentar parámetros, fórmulas y supuestos del MVP.
