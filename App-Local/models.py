from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# --- Modelos existentes (para recetas) ---
class Paciente(Base):
    __tablename__ = 'pacientes'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    edad = Column(Integer)
    genero = Column(String)
    correo = Column(String)
    recetas = relationship("Receta", back_populates="paciente")

class Medico(Base):
    __tablename__ = 'medicos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    cedula = Column(String)
    especialidad = Column(String)
    recetas = relationship("Receta", back_populates="medico")

class Receta(Base):
    __tablename__ = 'recetas'
    id = Column(Integer, primary_key=True)
    id_paciente = Column(Integer, ForeignKey('pacientes.id'))
    id_medico = Column(Integer, ForeignKey('medicos.id'))
    diagnostico = Column(String)
    fecha = Column(Date)
    paciente = relationship("Paciente", back_populates="recetas")
    medico = relationship("Medico", back_populates="recetas")
    medicamentos = relationship("Medicamento", back_populates="receta")

class Medicamento(Base):
    __tablename__ = 'medicamentos'
    id = Column(Integer, primary_key=True)
    id_receta = Column(Integer, ForeignKey('recetas.id'))
    nombre = Column(String)
    dosis = Column(String)
    frecuencia = Column(String)
    receta = relationship("Receta", back_populates="medicamentos")

# --- TAREA 8: Nuevo Modelo de Auditoría de Correos ---
class EnviosEmail(Base):
    __tablename__ = 'envios_email'
    id_envio = Column(Integer, primary_key=True)
    id_receta = Column(Integer, ForeignKey('recetas.id'))
    correo = Column(String)
    fecha_envio = Column(DateTime, default=datetime.now)
    estatus = Column(String) # "ENVIADO", "ERROR"
    tipo_correo = Column(String) # "PDF", "PASSWORD"
    error_msg = Column(Text, nullable=True)

# --- ACTIVIDAD 9: Nuevos Modelos de Sincronización ---
class PacientesLocal(Base):
    __tablename__ = 'pacientes_local'
    id_local = Column(Integer, primary_key=True)
    id_externo = Column(Integer, unique=True, nullable=False) # ID de la BD Web
    nombre = Column(String(100))
    edad = Column(Integer)
    genero = Column(String(1))
    correo = Column(String(150))
    telefono = Column(String(20), nullable=True)
    # Aquí puedes agregar los campos de dirección si lo deseas
    synced_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class SyncArchivos(Base):
    __tablename__ = 'sync_archivos'
    id = Column(Integer, primary_key=True)
    nombre_archivo = Column(String(200), unique=True)
    fecha = Column(DateTime, default=datetime.now)
    estado = Column(String(20)) # "PROCESADO", "ERROR"
    detalle_error = Column(Text, nullable=True)