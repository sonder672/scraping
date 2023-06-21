import openpyxl

def save_to_excel(ids):

    workbook = openpyxl.Workbook()

    sheet = workbook.active

    sheet['A1'] = 'ID de Propiedad'

    for index, id in enumerate(ids, start=2):
        sheet[f'A{index}'] = id

    workbook.save('ids_propiedades.xlsx')