# -*- coding: utf-8 -*-
from odoo import models
import json


class ReportFinancialXlsx(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Financial Report Excel'

    def generate_xlsx_report(self, workbook, data, objects):
        report_obj = self.env['account.financial.report'].with_context(
            data.get('form', {}).get('used_context', {}))
        
        # Format pour les en-têtes
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'bg_color': '#D3D3D3'
        })

        # Format pour les lignes
        line_format = workbook.add_format({
            'align': 'left',
            'font_size': 12
        })

        # Format pour les nombres
        number_format = workbook.add_format({
            'align': 'right',
            'font_size': 12,
            'num_format': '#,##0.00'
        })

        # Création de la feuille Excel
        sheet = workbook.add_worksheet('Financial Report')
        sheet.set_column('A:A', 50)  # Largeur colonne description
        sheet.set_column('B:D', 20)  # Largeur colonnes montants

        # En-têtes
        headers = ['Description', 'Balance']
        if data.get('form', {}).get('debit_credit'):
            headers.insert(1, 'Debit')
            headers.insert(2, 'Credit')

        # Écriture des en-têtes
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # Récupération des données du rapport
        report_lines = report_obj.get_account_lines(data.get('form', {}))

        # Écriture des lignes
        row = 1
        for line in report_lines:
            # Description
            sheet.write(row, 0, line.get('name', ''), line_format)
            
            col = 1
            # Debit/Credit si activé
            if data.get('form', {}).get('debit_credit'):
                sheet.write(row, col, line.get('debit', 0.0), number_format)
                sheet.write(row, col + 1, line.get('credit', 0.0), number_format)
                col += 2

            # Balance
            sheet.write(row, col, line.get('balance', 0.0), number_format)
            
            row += 1
