import types

from PID_loop import PID


class bomba:
    def __init__(self, MaxRPM) -> None:
        self.MaxRPM = MaxRPM  # velocidad maxima

        self.RPM = 0  # RPM actuales
        self.Valvula = 0

        self.anteriores = []  # necesario para que el PID funcione
        self.integral = 0.0
        self.last_error = 0.0
        self.PID = types.MethodType(PID, self)

    def update(self, tiempo):
        self.RPM += (-25 + (self.Valvula * 1.8)) * tiempo

        if self.RPM < 0:
            self.RPM = 0
        elif self.RPM > self.MaxRPM:
            self.RPM = self.MaxRPM

    def get_state(self):
        return {
            "rpm": round(self.RPM, 2),
            "valvula_pct": round(self.Valvula, 2),
            "rpm_max": self.MaxRPM,
        }


if __name__ == "__main__":
    import time

    M1 = bomba(MaxRPM=4000)
    consigna = 1500
    tiempo = 0.5

    try:
        while True:
            M1.PID(M1.RPM, Man_Auto=False, SetpointAuto=consigna)
            M1.update(tiempo)
            print(
                f"Consigna: {consigna} - Velocidad real: {M1.RPM:.2f} - Posicion comando: {M1.Valvula:.2f}           ",
                end='\r',
            )
            time.sleep(tiempo)

    except KeyboardInterrupt:
        print("Simulación terminada.")