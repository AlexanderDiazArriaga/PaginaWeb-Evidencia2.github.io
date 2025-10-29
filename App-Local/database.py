from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Importamos la Base actualizada de models.py
from models import Base 

# Crea una base de datos SQLite llamada recetas.db
engine = create_engine('sqlite:///recetas.db')
Session = sessionmaker(bind=engine)
session = Session()

def init_db():
    # Esto creará TODAS las tablas que heredan de Base (incluidas las nuevas)
    Base.metadata.create_all(engine)
    print("Base de datos y tablas creadas/actualizadas correctamente.")