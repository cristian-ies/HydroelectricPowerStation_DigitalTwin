# PID Control / Closed Loop (Proportional-Integral-Derivative)
# regula variable como velocidad, temperatura, presión y flujo en procesos industriales.


def PID(self, input, Man_Auto=False, SetpointMan=0.0, SetpointAuto=0.0, delta_seconds=1.0):
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
            if delta_seconds <= 0:
                delta_seconds = 1.0

            if Man_Auto == False:     
                # Si el PID está en modo automático...

                if not hasattr(self, "last_setpoint"):
                    self.last_setpoint = None

                if self.last_setpoint is None or abs(SetpointAuto - self.last_setpoint) > 1e-9:
                    self.integral = 0.0
                    self.last_error = 0.0
                    self.anteriores = []
                    self.last_setpoint = SetpointAuto

                # Almaceno el vector velocidad en una lista de 100 elementos.
                self.anteriores.append(input)
                if len(self.anteriores) > 30:
                    self.anteriores = self.anteriores[-30:]

                SP = SetpointAuto        
                E = SP - input
                self.error = E 

                # Si cambia el signo del error, reiniciamos el integral para evitar arrastre.
                if self.last_error != 0 and (E > 0) != (self.last_error > 0):
                    self.integral = 0.0

                # Integramos y derivamos el error real, no la salida anterior.
                self.integral += E * delta_seconds
                self.integral = max(min(self.integral, 100000.0), -100000.0)

                if len(self.anteriores) > 1:
                    derivada = (E - self.last_error) / delta_seconds
                else:
                    derivada = 0.0
                self.last_error = E

                kP = 0.1
                kI = 0.005   #  0.0021
                kD = 0.003

                #La acción proporcional es el error multiplicado por una constante
                aP = self.error * kP

                #La acción integral corrige el error estacionario.
                aI = kI * self.integral

                #La acción derivativa amortigua el cambio brusco del error.
                aD = kD * derivada
                
                # Sumamos las componentes del PID para obtener la posición de la válvula.
                Salida = aP + aI + aD

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