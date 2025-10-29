from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


def subir_a_drive(filepath, carpeta_id, drive_instance):
    """Sube un archivo usando la instancia 'drive' provista."""
    try:
        archivo = drive_instance.CreateFile({'title': filepath, 'parents':[{'id': carpeta_id}]})
        archivo.SetContentFile(filepath)
        archivo.Upload()
        print(f"Archivo {filepath} subido a Drive.")
    except Exception as e:
        print(f"Error al subir {filepath} a Drive: {e}")
        raise e

def listar_archivos_en_carpeta(carpeta_id, drive_instance):
    """Lista archivos en una carpeta de Drive."""
    archivos = drive_instance.ListFile({'q': f"'{carpeta_id}' in parents and trashed=false"}).GetList()
    return archivos

def descargar_archivo(file_drive, path_local):
    """Descarga un archivo específico de Drive."""
    file_drive.GetContentFile(path_local)
    print(f"Archivo {file_drive['title']} descargado a {path_local}")

def mover_archivo_drive(file_drive, carpeta_destino_id):
    """Mueve un archivo de Drive a una nueva carpeta."""
    try:
        file_drive['parents'] = [{'id': carpeta_destino_id}]
        file_drive.Upload()
        print(f"Archivo {file_drive['title']} movido a carpeta {carpeta_destino_id}")
    except Exception as e:
        print(f"Error al mover {file_drive['title']}: {e}")