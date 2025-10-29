from datetime import datetime
import random
import string

def generar_contraseña(paciente):
    base = paciente.nombre[:3].upper()
    random_part = ''.join(random.choices(string.digits, k=4))
    return base + random_part
