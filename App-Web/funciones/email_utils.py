import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate
from email import encoders
import os
from dotenv import load_dotenv

# Cargar variables de entorno (p.ej., desde un archivo .env)
load_dotenv() 

# Usamos variables de entorno para no quemar credenciales
REMITENTE_EMAIL = os.getenv("REMITENTE_EMAIL") # p.ej., "tu_correo@gmail.com"
REMITENTE_PASSWORD = os.getenv("APP_PASSWORD") # p.ej., "rwco uerp zgvp cwyq"
REMITENTE_NOMBRE = "Recetario Médico"

def get_smtp_settings(email_destino):
    """Devuelve (host, puerto) basado en el dominio."""
    domain = email_destino.split('@')[-1].lower()
    if "gmail" in domain:
        return "smtp.gmail.com", 587
    elif "outlook" in domain or "hotmail" in domain:
        return "smtp.office365.com", 587
    else:
        # Default a Gmail si no se reconoce
        return "smtp.gmail.com", 587

#Enviar correo SIN adjunto
def enviar_correo(destinatario, asunto, cuerpo):
    # La lógica de "try/except" se mueve a app_web.py para la auditoría
    # Esta función ahora lanzará la excepción si falla.
    
    msg = MIMEMultipart()
    msg['From'] = formataddr((REMITENTE_NOMBRE, REMITENTE_EMAIL))
    msg['To'] = destinatario
    msg['Subject'] = Header(asunto, 'utf-8')
    msg['Date'] = formatdate(localtime=True)

    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    host, port = get_smtp_settings(destinatario)
    
    server = smtplib.SMTP(host, port)
    server.ehlo()
    server.starttls()
    server.login(REMITENTE_EMAIL, REMITENTE_PASSWORD)
    server.send_message(msg)
    server.quit()


#Enviar correo CON adjunto PDF
def enviar_correo_con_adjunto(destinatario, asunto, cuerpo, archivo_pdf):
    # La lógica de "try/except" se mueve a app_web.py para la auditoría
    
    msg = MIMEMultipart()
    msg['From'] = formataddr((REMITENTE_NOMBRE, REMITENTE_EMAIL))
    msg['To'] = destinatario
    msg['Subject'] = Header(asunto, 'utf-8')
    msg['Date'] = formatdate(localtime=True)

    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    # Adjuntar PDF
    with open(archivo_pdf, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={os.path.basename(archivo_pdf)}"
    )
    msg.attach(part)

    host, port = get_smtp_settings(destinatario)

    server = smtplib.SMTP(host, port)
    server.ehlo()
    server.starttls()
    server.login(REMITENTE_EMAIL, REMITENTE_PASSWORD)
    server.send_message(msg)
    server.quit()