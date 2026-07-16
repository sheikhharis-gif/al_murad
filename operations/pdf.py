from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_invoice_pdf(invoice):
    file_name = f"invoice_job_{invoice.job.job_number}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)

    y = 800
    c.drawString(50, y, f"Invoice - Job #{invoice.job.job_number}")
    y -= 30
    c.drawString(50, y, f"Client: {invoice.job.client}")
    y -= 40

    for trip in invoice.job.trips.all():
        c.drawString(
            50, y,
            f"Bilty: {trip.bilty_number} | Vehicle: {trip.vehicle} | Freight: {trip.freight}"
        )
        y -= 20

    y -= 20
    c.drawString(50, y, f"TOTAL: {invoice.total_amount()}")

    c.save()
    return file_name
