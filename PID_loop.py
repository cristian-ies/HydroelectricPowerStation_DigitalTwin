# PID Control / Closed Loop (Proportional-Integral-Derivative)
# regula variable como velocidad, temperatura, presión y flujo en procesos industriales.


def PID(self, input, Man_Auto = False, SetpointMan = 0.0, SetpointAuto = 0.0):
    """
        Calcula la salida de un controlador PID (Proporcional, Integral, Derivativo).

        Args:
            Man_Auto (bool): Modo manual (True) o automático (False).
            SetpointMan (bool): Ignorado si Man_Auto es True. Modo manual de setpoint (True) o automático (False).
            SetpointAuto (float): El valor del setpoint en modo automático.

        Returns:
            None

        El método calcula la salida del controlador PID utilizando el valor actual (input) y el setpoint (SetpointAuto).
        Se almacena el histórico de velocidades en self.anteriores y se limita a 100 elementos.
        Se calculan los componentes P, I y D del controlador y se suman para obtener la salida.
        La salida se limita al rango de 0 a 100.

        """
    if Man_Auto == False:     
        # Si el PID está en modo automático...

        # Almaceno el vector velocidad en una lista de 100 elementos.
        self.anteriores.append(input)
        if len(self.anteriores) > 100:
            self.anteriores = self.anteriores[-100:]

        SP = SetpointAuto        
        E = SP - input
        self.error = E 
        
        #error es la diferencia entre lo que tengo, y mi setpoint actual. Usamos la lista para ello. 
        E_accu = [(SP - elem) for elem in self.anteriores[-20:]]
        self.error_accu = E_accu
        
        kP = 10.0
        kI = 0.0001
        kD = 0.01

        #La acción proporcional es el error multiplicado por una constante
        aP = self.error * kP
        
        #La acción integral es el área de los valores, dividido por la constante
        aI = (kP * (sum(self.error_accu) / (len(self.error_accu)*0.002) * kI))

        #La acción derivativa es la proyección a futuro (pendiente) del error, multiplicado por una constante
        if len(self.anteriores)>2:
            aD = (self.error_accu[-1]-self.error_accu[-2])*kD*kP
        else:
            aD = 0.0
        
        #sumamos las componentes de las acciones Proporcional, Integral y Derivativa
        Salida = self.Valvula + aP + aI + aD

        #Limitamos la válvula de salida
        if Salida < 0:
            self.Valvula = 0
        elif Salida > 100:
            self.Valvula = 100         
        else:
            self.Valvula = Salida

    else:
        # Si estamos en modo "Manual", la válvula se pone en la posición que definimos en el setpoint.
        self.Valvula = SetpointMan