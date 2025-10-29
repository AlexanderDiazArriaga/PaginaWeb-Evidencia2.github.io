from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Text, CHAR
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class PacientesWeb(Base):
    __tablename__ = 'pacientes_web'
    id = Column(Integer, primary_key=True) 
    nombre = Column(String(100))
    edad = Column(Integer)
    genero = Column(CHAR(1))
    correo = Column(String(150))
    telefono = Column(String(20), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
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
    
    id_paciente = Column(Integer, ForeignKey('pacientes_web.id')) 
    id_medico = Column(Integer, ForeignKey('medicos.id'))
    
    diagnostico = Column(String)
    fecha = Column(Date)
    
    paciente = relationship("PacientesWeb", back_populates="recetas") 
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

class EnviosEmail(Base):
    __tablename__ = 'envios_email'
    id_envio = Column(Integer, primary_key=True)
    id_receta = Column(Integer, ForeignKey('recetas.id'))
    correo = Column(String)
    fecha_envio = Column(DateTime, default=datetime.now)
    estatus = Column(String) # "ENVIADO", "ERROR"
    tipo_correo = Column(String) # "PDF", "PASSWORD"
    error_msg = Column(Text, nullable=True)