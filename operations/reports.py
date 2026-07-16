
########## TRIPS PDF & EXCEL REPORT#########

from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import A4
from django.http import HttpResponse
from .models import Trip

def trips_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="trips_report.pdf"'

    pdf = SimpleDocTemplate(response, pagesize=A4)
    data = [["Date", "Vehicle", "Driver", "Amount"]]

    for t in Trip.objects.all():
        data.append([
            t.trip_date.strftime("%d-%m-%Y"),
            str(t.vehicle),
            str(t.driver),
            t.amount
        ])

    table = Table(data)
    pdf.build([table])
    return response

from openpyxl import Workbook

def trips_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Trips"

    ws.append(["Date", "Vehicle", "Driver", "Amount"])

    for t in Trip.objects.all():
        ws.append([
            t.trip_date,
            str(t.vehicle),
            str(t.driver),
            t.amount
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="trips.xlsx"'
    wb.save(response)
    return response


######### VEHICLE EXPENSE REPORT #########

from masters.models import Expense

def expenses_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="expenses_report.pdf"'

    pdf = SimpleDocTemplate(response, pagesize=A4)
    data = [["Date", "Vehicle", "Type", "Amount"]]

    for e in Expense.objects.all():
        data.append([
            e.date.strftime("%d-%m-%Y"),
            str(e.vehicle),
            e.expense_type,
            e.amount
        ])

    pdf.build([Table(data)])
    return response

def expenses_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Expenses"

    ws.append(["Date", "Vehicle", "Type", "Amount"])

    for e in Expense.objects.all():
        ws.append([e.date, str(e.vehicle), e.expense_type, e.amount])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="expenses.xlsx"'
    wb.save(response)
    return response

######### PROFIT STATEMENT PDF #########

from django.db.models import Sum

def profit_pdf(request):
    total_freight = Trip.objects.aggregate(Sum("amount"))["amount__sum"] or 0
    total_expense = Expense.objects.aggregate(Sum("amount"))["amount__sum"] or 0
    profit = total_freight - total_expense

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="profit_statement.pdf"'

    pdf = SimpleDocTemplate(response, pagesize=A4)
    data = [
        ["Total Freight", total_freight],
        ["Total Expense", total_expense],
        ["Net Profit", profit],
    ]

    pdf.build([Table(data)])
    return response
