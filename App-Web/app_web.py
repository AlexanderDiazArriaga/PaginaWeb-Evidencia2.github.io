from flask import Flask, render_template, request, redirect, url_for, flash
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from database_web import init_db_web, session
from models_web import PacientesWeb
from xml_patient_generator import generar_xml_paciente
# Copia tu google_drive.py a la carpeta App_Web
from google_drive import subir_a_drive 

app = Flask(__name__)
app.secret_key = "supersecretkey"

# IDs de Drive (DEBES CAMBIAR ESTOS VALORES)
CARPETA_PACIENTES_PENDIENTES_ID = "1bYCxy_j-r3XB7NndQmJWXrvK28EdEO-9" 

# Autenticación de Google Drive (requerirá autenticación la primera vez)
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Inicializar BD Web
init_db_web()

@app.route('/')
def index():
    pacientes = session.query(PacientesWeb).all()
    return render_template('index.html', pacientes=pacientes)

@app.route('/guardar_paciente', methods=['POST'])
def guardar_paciente():
    try:
        # 1. Guardar en BD Web
        paciente = PacientesWeb(
            nombre=request.form['nombre'],
            edad=int(request.form['edad']),
            genero=request.form['genero'],
            correo=request.form['correo'],
            telefono=request.form['telefono']
        )
        session.add(paciente)
        session.commit()
        
        # 2. Generar XML
        # (Necesitamos el ID, así que refrescamos el objeto)
        session.refresh(paciente) 
        archivo_xml = generar_xml_paciente(paciente, operacion="ALTA")
        
        # 3. Subir XML a Google Drive (Carpeta PENDIENTES)
        subir_a_drive(archivo_xml, CARPETA_PACIENTES_PENDIENTES_ID, drive)
        
        flash(f"Paciente {paciente.nombre} guardado (ID: {paciente.id}) y XML subido a Drive.", "success")
        
    except Exception as e:
        session.rollback()
        flash(f"Error al guardar paciente: {e}", "error")
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)