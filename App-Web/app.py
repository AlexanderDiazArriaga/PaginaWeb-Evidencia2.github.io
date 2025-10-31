from flask import Flask, render_template, request, redirect, url_for, flash
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime
import os # Necesario para los PDF

# Imports de la BD Web
from database_web import init_db_web, session
from models_web import PacientesWeb, Medico, Receta, Medicamento, EnviosEmail

# Imports para Tarea 9 (Sincronización de Pacientes)
from xml_patient_generator import generar_xml_paciente
from google_drive import subir_a_drive 

# --- IMPORTS PARA GENERAR RECETAS (Tarea 8) ---
# (Asegúrate de que estos archivos estén en App_Web/funciones/)
from funciones.generar_pdf import generar_pdf
from funciones.encriptar_pdf import encriptar_pdf
from funciones.generar_contraseña import generar_contraseña
from funciones.email_utils import enviar_correo, enviar_correo_con_adjunto
from funciones.xml_generator import generar_xml as generar_xml_receta # Renombrado para claridad


app = Flask(__name__)
app.secret_key = "supersecretkey" # Necesario para los mensajes flash

# IDs de Drive (DEBES CAMBIAR ESTOS VALORES POR LOS TUYOS)
CARPETA_PACIENTES_PENDIENTES_ID = "1bYCxy_j-r3XB7NndQmJWXrvK28EdEO-9" 
CARPETA_RECETAS_XML_ID = "1V9u5wTG0ZfRFIYrHckOgcw0Xw-9Ch6Q4" # (La misma que usa la App Local)

# Autenticación de Google Drive
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Inicializar BD Web (creará las nuevas tablas si no existen)
init_db_web()

@app.route('/')
def index():
    # Cargamos los pacientes para el menú desplegable
    pacientes = session.query(PacientesWeb).all()
    return render_template('index.html', pacientes=pacientes)

# --- RUTA TAREA 9 (Sincronizar Paciente) ---
@app.route('/guardar_paciente', methods=['POST'])
def guardar_paciente():
    archivo_xml = None
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
        
        # 2. Generar XML de Paciente
        session.refresh(paciente) 
        archivo_xml = generar_xml_paciente(paciente, operacion="ALTA")
        
        # 3. Subir XML a Google Drive (Carpeta PENDIENTES)
        subir_a_drive(archivo_xml, CARPETA_PACIENTES_PENDIENTES_ID, drive)
        
        flash(f"Paciente {paciente.nombre} guardado (ID: {paciente.id}) y XML subido a Drive.", "success")
        
    except Exception as e:
        session.rollback()
        flash(f"Error al guardar paciente: {e}", "error")
        
    finally:
        # 4. Limpiar archivo XML temporal
        if archivo_xml and os.path.exists(archivo_xml):
            os.remove(archivo_xml)
            
    return redirect(url_for('index'))

# --- RUTA TAREA 8 (Generar Receta) ---
# (Esta es la ruta que te estaba dando el error 404)
@app.route('/guardar_receta', methods=['POST'])
def guardar_receta_web():
    pdf_path = None
    pdf_encriptar = None
    archivo_xml_receta = None
    
    try:
        # 1. Obtener el paciente de la BD Web
        paciente_id = int(request.form['paciente_id'])
        paciente = session.query(PacientesWeb).get(paciente_id)

        if not paciente:
            flash("Error: Paciente no encontrado.", "error")
            return redirect(url_for('index'))

        # 2. Obtener o crear al Médico (lógica de main.py local)
        medico_cedula = request.form['medico_cedula']
        medico = session.query(Medico).filter_by(cedula=medico_cedula).first()
        if not medico:
            medico = Medico(
                nombre=request.form['medico_nombre'],
                cedula=medico_cedula,
                especialidad="" # Campo opcional
            )
            session.add(medico)
        else:
            # Opcional: actualizar nombre del médico si ya existe
            medico.nombre = request.form['medico_nombre']


        # 3. Crear la Receta y Medicamento (lógica de main.py local)
        receta = Receta(
            paciente=paciente,
            medico=medico,
            diagnostico=request.form['diagnostico'],
            fecha=datetime.now()
        )
        session.add(receta)
        
        med = Medicamento(
            receta=receta,
            nombre=request.form['med_nombre'],
            dosis=request.form['med_dosis'],
            frecuencia=request.form['med_frecuencia']
        )
        session.add(med)
        session.commit() # Guardamos todo en la BD Web

        # 4. Generar XML de la Receta (Igual que la App Local)
        receta_data_xml = {
            'paciente': {'nombre': paciente.nombre, 'edad': paciente.edad, 'genero': paciente.genero},
            'medico': {'nombre': medico.nombre, 'cedula': medico.cedula},
            'diagnostico': receta.diagnostico,
            'medicamentos': [{'nombre': med.nombre, 'dosis': med.dosis, 'frecuencia': med.frecuencia}]
        }
        archivo_xml_receta = generar_xml_receta(receta_data_xml)
        subir_a_drive(archivo_xml_receta, CARPETA_RECETAS_XML_ID, drive)

        # 5. Generar y Encriptar PDF
        session.refresh(receta) # Para que cargue la relación 'medicamentos'
        pdf_path = generar_pdf(receta, receta.medicamentos, filename=f"receta_web_{receta.id}.pdf")
        password = generar_contraseña(paciente) # Usa el objeto 'paciente'
        pdf_encriptar = encriptar_pdf(pdf_path, f"receta_segura_{receta.id}.pdf", password)
        
        # 6. Enviar Correos y Auditar
        # Enviar PDF
        try:
            enviar_correo_con_adjunto(
                destinatario=paciente.correo,
                asunto="Tu receta medica (archivo seguro)",
                cuerpo="Adjunto encontrarás tu receta médica en formato PDF. Está protegida con contraseña.",
                archivo_pdf=pdf_encriptar
            )
            log_envio = EnviosEmail(id_receta=receta.id, correo=paciente.correo, estatus="ENVIADO", tipo_correo="PDF")
            session.add(log_envio)
        except Exception as e:
            log_envio = EnviosEmail(id_receta=receta.id, correo=paciente.correo, estatus="ERROR", tipo_correo="PDF", error_msg=str(e))
            session.add(log_envio)

        # Enviar Contraseña
        try:
            enviar_correo(
                destinatario=paciente.correo,
                asunto="Contraseña para abrir tu receta",
                cuerpo=f"Hola {paciente.nombre},\n\nLa contraseña para abrir tu receta es: {password}"
            )
            log_envio = EnviosEmail(id_receta=receta.id, correo=paciente.correo, estatus="ENVIADO", tipo_correo="PASSWORD")
            session.add(log_envio)
        except Exception as e:
            log_envio = EnviosEmail(id_receta=receta.id, correo=paciente.correo, estatus="ERROR", tipo_correo="PASSWORD", error_msg=str(e))
            session.add(log_envio)

        session.commit() # Guarda los logs de correo

        flash(f"Receta para {paciente.nombre} generada y enviada.", "success")
        
    except Exception as e:
        session.rollback()
        flash(f"Error al generar la receta: {e}", "error")
        
    finally:
        # 7. Limpiar archivos temporales
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)
        if pdf_encriptar and os.path.exists(pdf_encriptar):
            os.remove(pdf_encriptar)
        if archivo_xml_receta and os.path.exists(archivo_xml_receta):
            os.remove(archivo_xml_receta)
            
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
