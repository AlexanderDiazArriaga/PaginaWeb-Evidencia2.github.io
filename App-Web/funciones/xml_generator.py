import xml.etree.ElementTree as ET
from datetime import datetime

def generar_xml(receta_data):
    receta = ET.Element('receta')
    
    paciente = ET.SubElement(receta, 'paciente')
    ET.SubElement(paciente, 'nombre').text = receta_data['paciente']['nombre']
    ET.SubElement(paciente, 'edad').text = str(receta_data['paciente']['edad'])
    ET.SubElement(paciente, 'genero').text = receta_data['paciente']['genero']

    medico = ET.SubElement(receta, 'medico')
    ET.SubElement(medico, 'nombre').text = receta_data['medico']['nombre']
    ET.SubElement(medico, 'cedula').text = receta_data['medico']['cedula']

    ET.SubElement(receta, 'diagnostico').text = receta_data['diagnostico']

    medicamentos = ET.SubElement(receta, 'medicamentos')
    for med in receta_data['medicamentos']:
        m = ET.SubElement(medicamentos, 'medicamento')
        ET.SubElement(m, 'nombre').text = med['nombre']
        ET.SubElement(m, 'dosis').text = med['dosis']
        ET.SubElement(m, 'frecuencia').text = med['frecuencia']

    fecha_str = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"receta_{receta_data['paciente']['nombre'].replace(' ', '_')}_{fecha_str}.xml"
    tree = ET.ElementTree(receta)
    tree.write(filename, encoding='utf-8', xml_declaration=True)
    return filename