import os
import xml.etree.ElementTree as ET
from lxml import etree # Para validación XSD
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Imports locales
from database import session
from models import PacientesLocal, SyncArchivos
from google_drive import listar_archivos_en_carpeta, descargar_archivo, mover_archivo_drive

XSD_PATH = "paciente.xsd" # Ruta al XSD

def validar_xml(xml_path):
    """Valida un XML contra el XSD. Devuelve (True, None) o (False, error_msg)."""
    try:
        xml_doc = etree.parse(xml_path)
        xsd_doc = etree.parse(XSD_PATH)
        xml_schema = etree.XMLSchema(xsd_doc)
        
        xml_schema.assertValid(xml_doc) # Lanza excepción si es inválido
        return True, None
    except etree.XMLSchemaError as e:
        return False, f"Error en el XSD: {e}"
    except etree.DocumentInvalid as e:
        return False, f"XML inválido: {e}"
    except Exception as e:
        return False, f"Error inesperado al validar: {e}"

def procesar_paciente_xml(xml_path, checksum):
    """Parsea el XML y lo inserta/actualiza en la BD Local."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    try:
        id_externo = int(root.find('id').text)
        nombre = root.find('nombre').text
        edad = int(root.find('edad').text)
        genero = root.find('genero').text
        correo = root.find('correo').text
        
        telefono_node = root.find('telefono')
        telefono = telefono_node.text if telefono_node is not None else None
        
        fecha_evento_str = root.find('metadatos/fecha_evento').text
        fecha_evento = datetime.fromisoformat(fecha_evento_str)

        # Regla de Sincronización: "El más reciente gana"
        paciente_local = session.query(PacientesLocal).filter_by(id_externo=id_externo).first()
        
        if paciente_local:
            # ACTUALIZAR (Update)
            if paciente_local.synced_at < fecha_evento: # Comparamos fecha del XML vs BD
                paciente_local.nombre = nombre
                paciente_local.edad = edad
                paciente_local.genero = genero
                paciente_local.correo = correo
                paciente_local.telefono = telefono
                paciente_local.synced_at = fecha_evento
                session.commit()
                return "ACTUALIZADO"
            else:
                return "OMITIDO (Antiguo)"
        else:
            # INSERTAR (Alta)
            nuevo_paciente = PacientesLocal(
                id_externo=id_externo,
                nombre=nombre,
                edad=edad,
                genero=genero,
                correo=correo,
                telefono=telefono,
                synced_at=fecha_evento
            )
            session.add(nuevo_paciente)
            session.commit()
            return "INSERTADO"
            
    except Exception as e:
        session.rollback()
        raise Exception(f"Error al procesar datos del XML: {e}")

def sincronizar_pacientes_desde_drive(drive, pending_folder_id, processed_folder_id, errors_folder_id):
    """Flujo principal de sincronización (Actividad 9)."""
    
    archivos_pendientes = listar_archivos_en_carpeta(pending_folder_id, drive)
    
    stats = {"procesados": 0, "errores": 0, "duplicados": 0}
    
    if not archivos_pendientes:
        return stats

    temp_dir = "temp_xmls" # Directorio temporal
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for file_drive in archivos_pendientes:
        nombre_archivo = file_drive['title']
        
        # 1. Idempotencia: Verificar si ya fue procesado
        archivo_log = session.query(SyncArchivos).filter_by(nombre_archivo=nombre_archivo).first()
        if archivo_log:
            # Ya se procesó (bien o mal), moverlo para evitar re-procesamiento
            if archivo_log.estado == "PROCESADO":
                mover_archivo_drive(file_drive, processed_folder_id)
            else:
                mover_archivo_drive(file_drive, errors_folder_id)
            stats['duplicados'] += 1
            continue

        path_local_xml = os.path.join(temp_dir, nombre_archivo)
        
        try:
            # 2. Descargar
            descargar_archivo(file_drive, path_local_xml)
            
            # 3. Validar XSD
            es_valido, error_validacion = validar_xml(path_local_xml)
            if not es_valido:
                raise Exception(f"Validación XSD fallida: {error_validacion}")

            # (Opcional) Validar Checksum
            checksum_xml = ET.parse(path_local_xml).find('metadatos/checksum').text
            # (Aquí iría tu lógica para recalcular el checksum del contenido y compararlo)
            
            # 4. Insertar/Actualizar en BD Local
            resultado = procesar_paciente_xml(path_local_xml, checksum_xml)
            
            # 5. Registrar en Log BD (SyncArchivos)
            log = SyncArchivos(
                nombre_archivo=nombre_archivo,
                estado="PROCESADO",
                detalle_error=resultado # Guardamos si fue INSERT/UPDATE/OMITIDO
            )
            session.add(log)
            session.commit()
            
            # 6. Mover a "procesados" en Drive
            mover_archivo_drive(file_drive, processed_folder_id)
            stats['procesados'] += 1

        except Exception as e:
            session.rollback()
            # 5. Registrar Error en Log BD
            log_error = SyncArchivos(
                nombre_archivo=nombre_archivo,
                estado="ERROR",
                detalle_error=str(e)
            )
            session.add(log_error)
            session.commit()
            
            # 6. Mover a "errores" en Drive
            mover_archivo_drive(file_drive, errors_folder_id)
            stats['errores'] += 1
            print(f"Error procesando {nombre_archivo}: {e}")
            
        finally:
            # Limpiar archivo temporal
            if os.path.exists(path_local_xml):
                os.remove(path_local_xml)
                
    return stats