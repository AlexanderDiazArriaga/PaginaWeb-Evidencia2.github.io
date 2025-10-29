from PyPDF2 import PdfReader, PdfWriter

def encriptar_pdf(input_pdf, output_pdf, password):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    return output_pdf