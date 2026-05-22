from math import pi


class Tanque:
    def __init__(self, diametro, altura, nivel_maximo, capacidad_litros=200000):
        self.diametro = diametro
        self.altura = altura
        self.nivel_maximo = nivel_maximo
        self.capacidad_litros = capacidad_litros
        self.litros_actual = 0
        self.nivel_actual = 0

    def llenar(self):
        pass
    
    def vaciar(self):
        pass
    
    def medirLitros(self):
        self.litros_actual = (((pi*((self.diametro/2)**2))*self.nivel_actual) / 1000)
        return self.litros_actual

    def get_state(self):
        return {
            "diametro": self.diametro,
            "altura": self.altura,
            "nivel_maximo": self.nivel_maximo,
            "capacidad_litros": round(self.capacidad_litros, 2),
            "nivel_actual": round(self.nivel_actual, 2),
            "litros_actual": round(self.litros_actual, 2),
        }

class TanqueConValvulas(Tanque):
    def __init__(self, diametro, altura, nivel_maximo, valvulas, capacidad_litros=200000):
        super().__init__(diametro, altura, nivel_maximo, capacidad_litros)
        self.valvulas = valvulas

    def abrir_valvula(self,indiceValvula):
        self.valvulas[indiceValvula].Abrir()

    def cerrar_valvula(self,indiceValvula):
        self.valvulas[indiceValvula].Cerrar()

    def update(self, delta_seconds=1.0):
        if delta_seconds <= 0:
            return

        flujo_total = sum(valvula.caudal for valvula in self.valvulas)
        self.litros_actual = self.litros_actual + (flujo_total * delta_seconds)
        if self.litros_actual < 0:
            self.litros_actual = 0
        elif self.litros_actual > self.capacidad_litros:
            self.litros_actual = self.capacidad_litros

        if self.nivel_maximo > 0:
            self.nivel_actual = round(
                (self.litros_actual / self.capacidad_litros) * self.nivel_maximo, 2
            )

    def get_state(self):
        state = super().get_state()
        state.update(
            {
                "valvulas": [valvula.get_state() for valvula in self.valvulas],
            }
        )
        return state


        
class Valvula:
    def __init__(self,tipo,caudalMax):
        assert (tipo == "Entrada" or tipo == "Salida"), "Tipo no admitido. Posibles: 'Entrada' ó 'Salida'"
        self.tipo = tipo
        self.caudalMax = caudalMax
        self.status = False #False = Cerrada, True = Abierta
        self.caudal = 0
    
    def Abrir(self):
        if self.tipo == "Entrada":
            self.caudal = self.caudalMax
        else:
            self.caudal = -self.caudalMax
            
        self.status = True
    
    def Cerrar(self):
        self.caudal = 0
        self.status = False

    def get_state(self):
        return {
            "tipo": self.tipo,
            "caudal_max": self.caudalMax,
            "status": self.status,
            "caudal": self.caudal,
        }