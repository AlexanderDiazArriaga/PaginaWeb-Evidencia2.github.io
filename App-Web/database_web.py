from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_web import Base

engine = create_engine('sqlite:///web.db')
Session = sessionmaker(bind=engine)
session = Session()

def init_db_web():
    Base.metadata.create_all(engine)
    print("Base de datos WEB y tablas creadas/actualizadas.")