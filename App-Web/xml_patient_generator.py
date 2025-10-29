import xml.etree.ElementTree as ET
from datetime import datetime
import hashlib # Para el checksum

def generar_xml_paciente(paciente, operacion="ALTA"):
    root = ET.Element('paciente')
    
    ET.SubElement(root, 'id').text = str(paciente.id)
    ET.SubElement(root, 'nombre').text = paciente.nombre
    ET.SubElement(root, 'edad').text = str(paciente.edad)
    ET.SubElement(root, 'genero').text = paciente.genero
    ET.SubElement(root, 'correo').text = paciente.correo
    if paciente.telefono:
        ET.SubElement(root, 'telefono').text = paciente.telefono

    checksum_data = f"{paciente.id}{paciente.nombre}{paciente.updated_at.isoformat()}"
    checksum = hashlib.md5(checksum_data.encode()).hexdigest()

    metadatos = ET.SubElement(root, 'metadatos')
    ET.SubElement(metadatos, 'origen').text = "WEB"
    ET.SubElement(metadatos, 'fecha_evento').text = paciente.updated_at.isoformat()
    ET.SubElement(metadatos, 'operacion').text = operacion
    ET.SubElement(metadatos, 'checksum').text = checksum

    fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"paciente_{paciente.id}_{fecha_str}.xml"
    
    tree = ET.ElementTree(root)
    tree.write(filename, encoding='utf-8', xml_declaration=True)
    return filename