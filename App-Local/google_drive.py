from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Tu función original
def subir_a_drive(filepath, carpeta_id, drive_instance):
    archivo = drive_instance.CreateFile({'title': filepath, 'parents':[{'id': carpeta_id}]})
    archivo.SetContentFile(filepath)
    archivo.Upload()
    print(f"Archivo {filepath} subido a Drive.")

# Tu función original (modificada para listar archivos)
def listar_archivos_en_carpeta(carpeta_id, drive_instance):
    archivos = drive_instance.ListFile({'q': f"'{carpeta_id}' in parents and trashed=false"}).GetList()
    return archivos

# Nueva función para descargar
def descargar_archivo(file_drive, path_local):
    file_drive.GetContentFile(path_local)
    print(f"Archivo {file_drive['title']} descargado a {path_local}")

# Nueva función para mover archivos
def mover_archivo_drive(file_drive, carpeta_destino_id):
    # Pydrive mover es un poco extraño: se quita el padre anterior y se añade uno nuevo
    file_drive['parents'] = [{'id': carpeta_destino_id}]
    file_drive.Upload() # Se 're-sube' para actualizar los metadatos/padres
    print(f"Archivo {file_drive['title']} movido a carpeta {carpeta_destino_id}")