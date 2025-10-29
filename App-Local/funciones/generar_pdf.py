# archivo: pdf_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generar_pdf(receta, medicamentos, filename="receta.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 12)

    y = 750
    c.drawString(50, y, f"Receta Médica")
    y -= 30
    c.drawString(50, y, f"Paciente: {receta.paciente.nombre}")
    y -= 20
    c.drawString(50, y, f"Edad: {receta.paciente.edad}")
    y -= 20
    c.drawString(50, y, f"Género: {receta.paciente.genero}")
    y -= 20
    c.drawString(50, y, f"Médico: {receta.medico.nombre}")
    y -= 20
    c.drawString(50, y, f"Diagnóstico: {receta.diagnostico}")
    y -= 40

    c.drawString(50, y, "Medicamentos:")
    y -= 20

    for med in medicamentos:
        c.drawString(70, y, f"- {med.nombre}, Dosis: {med.dosis}, Frecuencia: {med.frecuencia}")
        y -= 20

    c.save()
    return filename
