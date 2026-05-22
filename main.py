import json
import queue
import threading
import time
from datetime import datetime, timedelta, timezone

from PID_bomba import bomba
from tank import TanqueConValvulas, Valvula
from forecasting import (
    analyze_series,
    forecast_next_value,
    load_consumption_series,
    load_forecasting_pipeline,
    select_day_series,
)


MAX_MW = 0.01
MAX_KW = MAX_MW * 1000.0


def calcular_potencia_kw(rpm, rpm_max):
    if rpm_max <= 0:
        return 0.0
    return round((rpm / rpm_max) * MAX_KW, 3)


def calcular_energia_kwh(potencia_kw, tiempo_segundos):
    return round(potencia_kw * (tiempo_segundos / 3600.0), 6)


def construir_documento_logstash(evento):
    return json.dumps(evento, ensure_ascii=True)


def persistir_json(path, payload):
    with open(path, "a", encoding="utf-8") as archivo:
        archivo.write(payload + "\n")


def solicitar_dia_manual():
    while True:
        valor = input("Ingrese fecha (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(valor, "%Y-%m-%d")
            return valor
        except ValueError:
            print("Fecha invalida. Ejemplo valido: 2007-01-01")


def esperar_comando_siguiente():
    while True:
        comando = input("Comando [n=next, q=quit]: ").strip().lower()
        if comando in ("", "n", "next"):
            return True
        if comando in ("q", "quit"):
            return False
        print("Comando invalido. Use n o q.")


def es_fecha_valida(valor):
    try:
        datetime.strptime(valor, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def crear_lector_comandos():
    cola = queue.Queue()

    def leer():
        while True:
            try:
                linea = input().strip()
            except EOFError:
                break
            cola.put(linea)
            if linea.lower() in ("q", "quit"):
                break

    hilo = threading.Thread(target=leer, daemon=True)
    hilo.start()
    return cola


def leer_ultimo_comando(cola):
    comando = None
    try:
        while True:
            comando = cola.get_nowait()
    except queue.Empty:
        return comando


def extraer_dia_comando(comando):
    valor = comando.strip()
    if not valor:
        return None
    if valor.lower().startswith("dia "):
        valor = valor[4:].strip()
    if es_fecha_valida(valor):
        return valor
    return None


def parsear_comando(comando):
    valor = comando.strip().lower()
    if valor in ("q", "quit"):
        return "quit", None
    if valor in ("n", "next"):
        return "next", None
    dia = extraer_dia_comando(comando)
    if dia:
        return "day", dia
    return "invalid", None


def listar_dias_disponibles(series):
    dias = sorted({timestamp.date() for timestamp in series.index})
    return [dia.isoformat() for dia in dias]


def siguiente_dia(dia_actual, dias_disponibles):
    if not dias_disponibles:
        return None
    try:
        indice = dias_disponibles.index(dia_actual)
    except ValueError:
        return dias_disponibles[0]
    if indice + 1 < len(dias_disponibles):
        return dias_disponibles[indice + 1]
    return None


def esperar_dia_desde_comandos(cola, dia_actual, dias_disponibles):
    print("Comandos: n=next dia, YYYY-MM-DD para elegir dia, q para salir.")
    while True:
        comando = leer_ultimo_comando(cola)
        if comando:
            accion, valor = parsear_comando(comando)
            if accion == "quit":
                return None
            if accion == "next":
                return siguiente_dia(dia_actual, dias_disponibles)
            if accion == "day":
                return valor
            print("Comando invalido. Use n, YYYY-MM-DD o q.")
        time.sleep(0.2)


def kw_a_mw(valor_kw):
    return round(valor_kw / 1000.0, 6)


def rpm_setpoint_desde_mw(consumo_mw, rpm_max):
    if consumo_mw <= 0:
        return 0.0
    return min(rpm_max, (consumo_mw / MAX_MW) * rpm_max)


def ejecutar_simulacion(
    csv_path="household_power_consumption.csv",
    tiempo_update=1.0,
    logstash_path="logstash_events.jsonl",
    modo_interactivo=False,
    modo_comandos=True,
    mostrar_json=False,
    tiempo_real=True,
):
    if tiempo_update <= 0:
        raise ValueError("tiempo_update debe ser mayor que 0.")

    turbina = bomba(MaxRPM=4000)
    embalse = TanqueConValvulas(
        diametro=10,
        altura=12,
        nivel_maximo=2000,
        valvulas=[Valvula("Entrada", 20), Valvula("Salida", 15)],
    )
    embalse.abrir_valvula(0)
    embalse.cerrar_valvula(1)

    series = load_consumption_series(csv_path)
    stats = analyze_series(series)
    print(
        "Dataset resumen - filas: {rows}, inicio: {start}, fin: {end}, min: {min}, max: {max}, media: {mean}".format(
            **stats
        )
    )

    pipeline = load_forecasting_pipeline()
    dia = solicitar_dia_manual()
    dias_disponibles = listar_dias_disponibles(series)
    cola_comandos = None
    if modo_comandos:
        cola_comandos = crear_lector_comandos()
        print("Comandos: n=next dia, YYYY-MM-DD para cambiar dia, q para salir.")

    energia_acumulada_kwh = 0.0
    eventos = []

    while True:
        day_series = select_day_series(series, dia)
        if day_series.empty:
            print("No hay datos para el dia seleccionado.")
            if not modo_comandos or cola_comandos is None:
                return eventos
            nuevo_dia = esperar_dia_desde_comandos(cola_comandos, dia, dias_disponibles)
            if not nuevo_dia:
                return eventos
            dia = nuevo_dia
            continue

        primer_timestamp = day_series.index[0]
        history = series.loc[:primer_timestamp].values
        pred_kw = forecast_next_value(pipeline, history, prediction_length=1)
        consumo_predicho_kw = round(float(pred_kw), 6)
        consumo_predicho_mw = kw_a_mw(consumo_predicho_kw)
        consigna_rpm = rpm_setpoint_desde_mw(consumo_predicho_mw, turbina.MaxRPM)

        cambiar_dia = None
        for timestamp, consumo_kw in day_series.items():
            consumo_real_kw = round(float(consumo_kw), 6)

            pasos_por_hora = max(1, int(3600 / tiempo_update))
            for paso in range(pasos_por_hora):
                turbina.PID(
                    turbina.RPM,
                    Man_Auto=False,
                    SetpointAuto=consigna_rpm,
                    delta_seconds=tiempo_update,
                )
                turbina.update(tiempo_update)
                embalse.update(tiempo_update)

                potencia_kw = calcular_potencia_kw(turbina.RPM, turbina.MaxRPM)
                energia_kwh = calcular_energia_kwh(potencia_kw, tiempo_update)
                energia_acumulada_kwh = round(energia_acumulada_kwh + energia_kwh, 6)

                evento_timestamp = timestamp + timedelta(seconds=paso * tiempo_update)
                evento = {
                    "@timestamp": evento_timestamp.replace(tzinfo=timezone.utc).isoformat(),
                    "source": "gemelo-digital-hidro",
                    "component": "central_hidroelectrica",
                    "turbina": turbina.get_state(),
                    "embalse": embalse.get_state(),
                    "operacion": {
                        "consumo_real_kw": consumo_real_kw,
                        "consumo_predicho_kw": consumo_predicho_kw,
                        "consigna_rpm": round(consigna_rpm, 2),
                        "potencia_kw": potencia_kw,
                        "energia_acumulada_kwh": energia_acumulada_kwh,
                    },
                }
                evento["logstash_document"] = construir_documento_logstash(evento)
                eventos.append(evento)

                if mostrar_json:
                    print(evento["logstash_document"])
                persistir_json(logstash_path, evento["logstash_document"])

                if tiempo_real:
                    time.sleep(tiempo_update)

                if modo_comandos and cola_comandos is not None:
                    comando = leer_ultimo_comando(cola_comandos)
                    if comando:
                        accion, valor = parsear_comando(comando)
                        if accion == "quit":
                            return eventos
                        if accion == "next":
                            nuevo_dia = siguiente_dia(dia, dias_disponibles)
                            if nuevo_dia:
                                cambiar_dia = nuevo_dia
                                break
                            print("No hay mas dias disponibles.")
                        elif accion == "day":
                            cambiar_dia = valor
                            break
                        else:
                            print("Comando invalido. Use n, YYYY-MM-DD o q.")

                if modo_interactivo and not modo_comandos:
                    if not esperar_comando_siguiente():
                        return eventos

            if cambiar_dia:
                break

        if cambiar_dia:
            dia = cambiar_dia
            continue

        break

    return eventos


if __name__ == "__main__":
    ejecutar_simulacion()