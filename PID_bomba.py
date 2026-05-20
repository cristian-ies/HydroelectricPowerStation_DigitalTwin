import time
import types
from PID_loop import PID

class bomba:
    def __init__(self, MaxRPM) -> None:
        self.MaxRPM = MaxRPM #velocidad maxima

        self.RPM = 0 #RPM actuales
        self.Valvula = 0

        self.anteriores=[] #necesario para que el PID funcione
        # Bind external PID function as an instance method
        self.PID = types.MethodType(PID, self)


    def update(self, tiempo):
        # Limitamos entre 0 y velocidad máxima 
        self.RPM += (-10 + (self.Valvula*1.8)) * tiempo #Si la valvula está cerrada, pierde velocidad

        if self.RPM < 0:
            self.RPM = 0
        elif self.RPM > self.MaxRPM:
            self.RPM = self.MaxRPM
        


# ------------- COMIENZA PROGRAMA ----------------
M1 = bomba(MaxRPM=4000)
consigna = 1500 # la velocidad a la que quiero que llegue
tiempo = 0.05 # tiempo de update en segundos

try:
    while True:
        # Quitarle el # a lo que quieras probar:
        # --------------------------------------
        # Nota: En modo manual, el lazo NO regula, entonces se "pasa" de la velocidad pedida. Es como si
        # nosotros controlaramos la apertura de la válvula con una perilla, a mano.

        # 1. PID manual, válvula al 30% fija
        #M1.PID(M1.RPM, Man_Auto=True,SetpointMan=30)
        # 2. PID manual, válvula al 0% fija
        #M1.PID(M1.RPM, Man_Auto=True,SetpointMan=0)
        # 3. PID manual, válvula al 100% fija
        #M1.PID(M1.RPM, Man_Auto=True,SetpointMan=100)

        #En modo automático, la válvula se controla sola, sin intervención.
        # 4. PID automático
        #M1.PID(M1.RPM, Man_Auto=False,SetpointAuto=consigna)

        # ---------------- Uodate y print ---------------
        M1.update(tiempo)
        print(f"Consigna: {consigna} - Velocidad real: {M1.RPM:.2f} - Posicion comando: {M1.Valvula:.2f}           ",end='\r')
        time.sleep(tiempo)

except KeyboardInterrupt:
    print("Simulación terminada.")