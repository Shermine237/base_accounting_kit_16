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

        # Format pour les titres (niveau 0)
        title_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'font_size': 12,
            'bg_color': '#F0F0F0'
        })

        # Format pour les sous-titres (niveau > 0)
        subtitle_format = workbook.add_format({
            'align': 'left',
            'font_size': 12,
            'italic': True
        })

        # Format pour les nombres
        number_format = workbook.add_format({
            'align': 'right',
            'font_size': 12,
            'num_format': '#,##0.00'
        })

        # Format pour les totaux
        total_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'font_size': 12,
            'num_format': '#,##0.00',
            'top': 1
        })

        # Création de la feuille Excel
        sheet = workbook.add_worksheet('Financial Report')
        sheet.set_column('A:A', 50)  # Largeur colonne description
        sheet.set_column('B:E', 20)  # Largeur colonnes montants

        # En-têtes
        headers = ['Description']
        if data.get('form', {}).get('show_debit_credit'):
            headers.extend(['Debit', 'Credit'])
        if data.get('form', {}).get('show_balance'):
            headers.append('Balance')
        if data.get('form', {}).get('enable_filter'):
            headers.append(data.get('form', {}).get('label_filter', 'Comparison'))

        # Écriture des en-têtes
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # Récupération des données du rapport
        form_data = data.get('form', {})
        report_lines = report_obj.get_account_lines(form_data)

        # Écriture des lignes
        row = 1
        for line in report_lines:
            # Indentation pour la hiérarchie
            level = line.get('level', 0)
            indent = '    ' * level
            name = indent + line.get('name', '')

            # Choix du format selon le niveau
            if level == 0:
                current_format = title_format
                number_fmt = total_format
            else:
                current_format = subtitle_format
                number_fmt = number_format

            # Description
            sheet.write(row, 0, name, current_format)
            
            col = 1
            # Debit/Credit si activé
            if form_data.get('show_debit_credit'):
                sheet.write(row, col, line.get('debit', 0.0), number_fmt)
                sheet.write(row, col + 1, line.get('credit', 0.0), number_fmt)
                col += 2

            # Balance si activé
            if form_data.get('show_balance'):
                sheet.write(row, col, line.get('balance', 0.0), number_fmt)
                col += 1

            # Comparaison si activée
            if form_data.get('enable_filter'):
                sheet.write(row, col, line.get('balance_cmp', 0.0), number_fmt)
                col += 1
            
            row += 1

            # Détails partenaire si activé
            if line.get('partner_id') and form_data.get('show_partner'):
                sheet.write(row, 0, indent + '    ' + line.get('partner_name', ''), line_format)
                col = 1
                if form_data.get('show_debit_credit'):
                    sheet.write(row, col, line.get('debit', 0.0), number_format)
                    sheet.write(row, col + 1, line.get('credit', 0.0), number_format)
                    col += 2
                if form_data.get('show_balance'):
                    sheet.write(row, col, line.get('balance', 0.0), number_format)
                    col += 1
                if form_data.get('enable_filter'):
                    sheet.write(row, col, line.get('balance_cmp', 0.0), number_format)
                row += 1

            # Détails analytique si activé
            if line.get('analytic_id') and form_data.get('show_analytic'):
                sheet.write(row, 0, indent + '    ' + line.get('analytic_name', ''), line_format)
                col = 1
                if form_data.get('show_debit_credit'):
                    sheet.write(row, col, line.get('debit', 0.0), number_format)
                    sheet.write(row, col + 1, line.get('credit', 0.0), number_format)
                    col += 2
                if form_data.get('show_balance'):
                    sheet.write(row, col, line.get('balance', 0.0), number_format)
                    col += 1
                if form_data.get('enable_filter'):
                    sheet.write(row, col, line.get('balance_cmp', 0.0), number_format)
                row += 1

            # Détails journal si activé
            if line.get('journal_id') and form_data.get('show_journal'):
                sheet.write(row, 0, indent + '    ' + line.get('journal_name', ''), line_format)
                col = 1
                if form_data.get('show_debit_credit'):
                    sheet.write(row, col, line.get('debit', 0.0), number_format)
                    sheet.write(row, col + 1, line.get('credit', 0.0), number_format)
                    col += 2
                if form_data.get('show_balance'):
                    sheet.write(row, col, line.get('balance', 0.0), number_format)
                    col += 1
                if form_data.get('enable_filter'):
                    sheet.write(row, col, line.get('balance_cmp', 0.0), number_format)
                row += 1
