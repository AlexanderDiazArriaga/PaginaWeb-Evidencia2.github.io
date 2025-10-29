import tkinter as tk
from tkinter import messagebox, Toplevel, OptionMenu, StringVar, Frame
from datetime import datetime
import xml.etree.ElementTree as ET
import os


from database import init_db, session
# Importamos TODOS los modelos necesarios de la BD local
from models import Paciente, PacientesLocal, Medico, Receta, Medicamento, EnviosEmail

# --- Imports de Funciones (sin cambios) ---
from xml_generator import generar_xml
from google_drive import subir_a_drive
from funciones.generar_pdf import generar_pdf
from funciones.encriptar_pdf import encriptar_pdf
from funciones.generar_contraseña import generar_contraseña
from funciones.email_utils import enviar_correo, enviar_correo_con_adjunto
from sync_manager import sincronizar_pacientes_desde_drive

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

init_db() # Esto inicializa 'recetas.db'

CARPETA_DRIVE_ID = 'TU_ID_DE_CARPETA_DE_RECETAS' # (Usa tu ID real)

# Autenticación de Google Drive
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)


# --- Variables Globales ---
pacientes_local_dict = {} # Almacena los objetos PacientesLocal por nombre



def cargar_pacientes_al_dropdown():
    """Consulta la BD local (tabla pacientes_local) y actualiza el menú."""
    global pacientes_local_dict
    pacientes_local_dict.clear()
    
    try:
        pacientes_sincronizados = session.query(PacientesLocal).all()
    except Exception as e:
        messagebox.showerror("Error", f"Error al leer la tabla 'pacientes_local': {e}")
        return

    nombres_pacientes = ["-- Seleccione un paciente Sincronizado --"]
    if pacientes_sincronizados:
        for p in pacientes_sincronizados:
            nombres_pacientes.append(p.nombre)
            pacientes_local_dict[p.nombre] = p
            
    paciente_seleccionado_var.set(nombres_pacientes[0])
    menu = dropdown_pacientes["menu"]
    menu.delete(0, "end")
    
    for nombre in nombres_pacientes:
        menu.add_command(label=nombre, 
                         command=tk._setit(paciente_seleccionado_var, nombre))



def get_or_create_receta_paciente(paciente_sync):
    """
    Sincroniza un paciente de 'pacientes_local' a 'pacientes' (la tabla de recetas).
    Busca por correo. Si no existe, lo crea. Si existe, lo actualiza.
    """
    paciente_receta = session.query(Paciente).filter_by(correo=paciente_sync.correo).first()
    
    if not paciente_receta:
        paciente_receta = Paciente(
            nombre=paciente_sync.nombre,
            edad=paciente_sync.edad,
            genero=paciente_sync.genero,
            correo=paciente_sync.correo
        )
        session.add(paciente_receta)
    else:
        paciente_receta.nombre = paciente_sync.nombre
        paciente_receta.edad = paciente_sync.edad
        paciente_receta.genero = paciente_sync.genero
    
    session.commit()
    return paciente_receta


def guardar_receta():
    """Genera la receta para el paciente sincronizado seleccionado."""
    
    nombre_paciente_sel = paciente_seleccionado_var.get()
    if nombre_paciente_sel == "-- Seleccione un paciente Sincronizado --":
        messagebox.showerror("Error", "Debe seleccionar un paciente.")
        return
        
    paciente_sync = pacientes_local_dict[nombre_paciente_sel]

    paciente_para_receta = get_or_create_receta_paciente(paciente_sync)

    medico_cedula = entry_cedula.get()
    medico = session.query(Medico).filter_by(cedula=medico_cedula).first()
    if not medico:
        medico = Medico(
            nombre=entry_medico.get(),
            cedula=medico_cedula,
            especialidad=""
        )
        session.add(medico)
    else:
        medico.nombre = entry_medico.get()

    receta = Receta(
        paciente=paciente_para_receta, 
        medico=medico,
        diagnostico=entry_diagnostico.get(),
        fecha=datetime.now()
    )
    session.add(receta)

    med = Medicamento(
        receta=receta,
        nombre=entry_m1.get(),
        dosis=entry_d1.get(),
        frecuencia=entry_f1.get()
    )
    session.add(med)
    session.commit() # Guardamos todo en 'recetas.db'

    receta_data = {
        'paciente': {'nombre': paciente_para_receta.nombre, 'edad': paciente_para_receta.edad, 'genero': paciente_para_receta.genero},
        'medico': {'nombre': medico.nombre, 'cedula': medico.cedula},
        'diagnostico': receta.diagnostico,
        'medicamentos': [{'nombre': med.nombre, 'dosis': med.dosis, 'frecuencia': med.frecuencia}]
    }
    archivo_xml = generar_xml(receta_data)

    try:
        subir_a_drive(archivo_xml, CARPETA_DRIVE_ID, drive)
    except Exception as e:
        messagebox.showwarning("Error de Drive", f"No se pudo subir el XML a Drive: {e}")

    pdf_path = generar_pdf(receta, [med], filename="receta.pdf")
    password = generar_contraseña(paciente_para_receta)
    pdf_encriptar = encriptar_pdf("receta.pdf", "receta_segura.pdf", password)
    
    
    try:
        enviar_correo_con_adjunto(
            destinatario=paciente_para_receta.correo,
            asunto="Tu receta medica (archivo seguro)",
            cuerpo="Adjunto encontrarás tu receta médica en formato PDF. Está protegida con contraseña.",
            archivo_pdf=pdf_encriptar
        )
        log_envio = EnviosEmail(id_receta=receta.id, correo=paciente_para_receta.correo, estatus="ENVIADO", tipo_correo="PDF")
        session.add(log_envio)
    except Exception as e:
        print(f"Error al enviar PDF: {e}")
        log_envio = EnviosEmail(id_receta=receta.id, correo=paciente_para_receta.correo, estatus="ERROR", tipo_correo="PDF", error_msg=str(e))
        session.add(log_envio)

    try:
        enviar_correo(
            destinatario=paciente_para_receta.correo,
            asunto="Contraseña para abrir tu receta",
            cuerpo=f"Hola {paciente_para_receta.nombre},\n\nLa contraseña para abrir tu receta es: {password}"
        )
        log_envio = EnviosEmail(id_receta=receta.id, correo=paciente_para_receta.correo, estatus="ENVIADO", tipo_correo="PASSWORD")
        session.add(log_envio)
    except Exception as e:
        print(f"Error al enviar contraseña: {e}")
        log_envio = EnviosEmail(id_receta=receta.id, correo=paciente_para_receta.correo, estatus="ERROR", tipo_correo="PASSWORD", error_msg=str(e))
        session.add(log_envio)

    session.commit() # Guarda los logs de correo
    messagebox.showinfo("Éxito", f"Receta para {paciente_para_receta.nombre} guardada y enviada.\nArchivo: {archivo_xml}")

    if os.path.exists(pdf_path): os.remove(pdf_path)
    if os.path.exists(pdf_encriptar): os.remove(pdf_encriptar)
    if os.path.exists(archivo_xml): os.remove(archivo_xml)


def ejecutar_sincronizacion_pacientes():
    """Función Tarea 9: Sincroniza pacientes desde la Web (usando XMLs)."""
    messagebox.showinfo("Iniciando Sincronización", "Descargando y procesando pacientes desde Google Drive...")
    try:
        stats = sincronizar_pacientes_desde_drive(
            drive, 
            pending_folder_id="1bYCxy_j-r3XB7NndQmJWXrvK28EdEO-9", 
            processed_folder_id="1TC157xpBV8JZWXdC-buSAjNFjiz70AaP",
            errors_folder_id="16m6kBKYunHcqNZSdAPIdUXdAATpcZ6U4"
        )
        messagebox.showinfo("Sincronización Completa", 
                            f"Procesados: {stats['procesados']}\n"
                            f"Errores: {stats['errores']}\n"
                            f"Duplicados: {stats['duplicados']}")
        
        cargar_pacientes_al_dropdown()
        
    except Exception as e:
        messagebox.showerror("Error de Sincronización", f"Ocurrió un error general: {e}")
        print(f"Error de Sincronización: {e}")

root = tk.Tk()
root.title("Recetario Médico (App Local)")

frame_paciente = Frame(root, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
frame_paciente.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

tk.Label(frame_paciente, text="Paciente (Sincronizado desde Web):", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, sticky="w")

paciente_seleccionado_var = StringVar(root)
dropdown_pacientes = OptionMenu(frame_paciente, paciente_seleccionado_var, "-- Cargando --")
dropdown_pacientes.grid(row=1, column=0, sticky="ew", pady=5)

tk.Button(frame_paciente, text="Refrescar Lista", command=cargar_pacientes_al_dropdown).grid(row=1, column=1, sticky="ew", pady=2, padx=5)

frame_receta = Frame(root, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
frame_receta.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")


tk.Label(frame_receta, text="Nombre del Médico").grid(row=0, column=0)
entry_medico = tk.Entry(frame_receta); entry_medico.grid(row=0, column=1)
tk.Label(frame_receta, text="Cédula").grid(row=1, column=0)
entry_cedula = tk.Entry(frame_receta); entry_cedula.grid(row=1, column=1)

tk.Label(frame_receta, text="Diagnóstico").grid(row=2, column=0)
entry_diagnostico = tk.Entry(frame_receta); entry_diagnostico.grid(row=2, column=1)

tk.Label(frame_receta, text="Medicamento").grid(row=3, column=0)
entry_m1 = tk.Entry(frame_receta); entry_m1.grid(row=3, column=1)
tk.Label(frame_receta, text="Dosis").grid(row=4, column=0)
entry_d1 = tk.Entry(frame_receta); entry_d1.grid(row=4, column=1)
tk.Label(frame_receta, text="Frecuencia").grid(row=5, column=0)
entry_f1 = tk.Entry(frame_receta); entry_f1.grid(row=5, column=1)

frame_botones = Frame(root)
frame_botones.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

tk.Button(frame_botones, text="Generar y Enviar Receta", command=guardar_receta, bg="#C5E1A5", font=('Helvetica', 12, 'bold')).pack(fill=tk.X, pady=5)
tk.Button(frame_botones, text="Sincronizar Pacientes (XML)", command=ejecutar_sincronizacion_pacientes, bg="#81D4FA").pack(fill=tk.X, pady=5)


cargar_pacientes_al_dropdown() 
root.mainloop()

session.close()