# -*- coding: utf-8 -*-
from odoo import models
import json


class ReportFinancialXlsx(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Financial Report Excel'

    def generate_xlsx_report(self, workbook, data, objects):
        # Dans Odoo 16, le modèle account.financial.report.wizard est utilisé pour générer les rapports
        report_wizard = self.env['account.financial.report.wizard'].browse(data.get('wizard_id', False))
        if not report_wizard:
            return
            
        # Format pour les en-têtes
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'bg_color': '#D3D3D3'
        })

        # Format pour les titres
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 12
        })

        # Format pour les sous-titres
        subtitle_format = workbook.add_format({
            'bold': True,
            'font_size': 10
        })

        # Format pour les nombres
        number_format = workbook.add_format({
            'num_format': '#,##0.00'
        })

        # Format pour les nombres négatifs
        negative_number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'font_color': 'red'
        })

        # Format pour les totaux
        total_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00',
            'top': 1
        })

        # Création d'une feuille de calcul
        sheet = workbook.add_worksheet('Financial Report')
        sheet.set_column(0, 0, 40)  # Largeur de la colonne des noms
        sheet.set_column(1, 5, 20)  # Largeur des colonnes de chiffres

        # Récupération des données du rapport
        form_data = data.get('form', {})
        company_id = form_data.get('company_id', False)
        date_from = form_data.get('date_from', False)
        date_to = form_data.get('date_to', False)
        enable_filter = form_data.get('enable_filter', False)
        debit_credit = form_data.get('debit_credit', False)
        account_report_id = form_data.get('account_report_id', False)
        
        # Préparation des en-têtes
        headers = ['Name']
        if debit_credit:
            headers.extend(['Debit', 'Credit'])
        headers.append('Balance')
        if enable_filter:
            headers.append(form_data.get('label_filter', 'Comparison'))

        # Écriture des en-têtes
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # Récupération des données du rapport
        try:
            # Utilisation de la nouvelle API pour obtenir les lignes de rapport
            report_id = account_report_id and account_report_id[0]
            if not report_id:
                return
                
            # Obtenir le modèle de rapport financier
            report_model = self.env['account.financial.report'].browse(report_id)
            
            # Préparer le contexte pour le rapport
            context = {
                'date_from': date_from,
                'date_to': date_to,
                'company_id': company_id and company_id[0],
                'enable_filter': enable_filter,
                'debit_credit': debit_credit,
            }
            
            # Obtenir les lignes du rapport via une méthode personnalisée
            report_lines = self._get_account_lines(report_model, form_data)

            # Écriture des lignes
            row = 1
            for line in report_lines:
                # Indentation pour la hiérarchie
                level = line.get('level', 0)
                indent = '    ' * level
                name = indent + line.get('name', '')

                # Choix du format selon le niveau
                if level == 0:
                    name_format = title_format
                    amount_format = total_format
                else:
                    name_format = subtitle_format if level == 1 else None
                    amount_format = number_format

                # Écriture du nom
                sheet.write(row, 0, name, name_format)

                # Écriture des montants
                col = 1
                if debit_credit:
                    sheet.write(row, col, line.get('debit', 0.0), amount_format)
                    col += 1
                    sheet.write(row, col, line.get('credit', 0.0), amount_format)
                    col += 1

                # Écriture du solde
                balance = line.get('balance', 0.0)
                format_to_use = negative_number_format if balance < 0 else amount_format
                sheet.write(row, col, balance, format_to_use)
                col += 1

                # Écriture de la comparaison si activée
                if enable_filter:
                    comp_balance = line.get('comp_balance', 0.0)
                    format_to_use = negative_number_format if comp_balance < 0 else amount_format
                    sheet.write(row, col, comp_balance, format_to_use)

                row += 1
        except Exception as e:
            # En cas d'erreur, écrire un message d'erreur dans la feuille
            sheet.write(1, 0, f"Error generating report: {str(e)}", workbook.add_format({'color': 'red'}))
    
    def _get_account_lines(self, report, form_data):
        """
        Méthode personnalisée pour obtenir les lignes du rapport financier
        compatible avec Odoo 16
        """
        lines = []
        
        # Récupérer les paramètres du formulaire
        company_id = form_data.get('company_id', False)
        date_from = form_data.get('date_from', False)
        date_to = form_data.get('date_to', False)
        
        # Contexte pour les calculs
        context = {
            'date_from': date_from,
            'date_to': date_to,
            'company_id': company_id and company_id[0],
        }
        
        # Récupérer les lignes de rapport de manière récursive
        self._get_report_lines(report, lines, 0, context, form_data)
        
        return lines
    
    def _get_report_lines(self, report, lines, level, context, form_data):
        """
        Méthode récursive pour générer les lignes du rapport
        """
        # Ajouter la ligne actuelle
        line = {
            'name': report.name,
            'level': level,
            'balance': 0.0,
            'debit': 0.0,
            'credit': 0.0,
        }
        
        # Calculer les montants selon le type de rapport
        if report.type == 'accounts':
            # Récupérer les comptes associés
            account_ids = self._get_accounts(report, form_data)
            line['balance'], line['debit'], line['credit'] = self._get_account_balance(account_ids, context)
        elif report.type == 'account_type':
            # Récupérer les types de comptes associés
            account_type_ids = report.account_type_ids
            account_ids = self.env['account.account'].search([('account_type', 'in', account_type_ids.mapped('name'))])
            line['balance'], line['debit'], line['credit'] = self._get_account_balance(account_ids, context)
        elif report.type == 'account_report':
            # Récupérer le rapport associé
            report_id = report.account_report_id
            if report_id:
                # Récursion pour obtenir le solde du sous-rapport
                sub_lines = []
                self._get_report_lines(report_id, sub_lines, level + 1, context, form_data)
                for sub_line in sub_lines:
                    line['balance'] += sub_line.get('balance', 0.0)
                    line['debit'] += sub_line.get('debit', 0.0)
                    line['credit'] += sub_line.get('credit', 0.0)
        elif report.type == 'sum':
            # Calculer la somme des sous-rapports
            for child in report.children_ids:
                sub_lines = []
                self._get_report_lines(child, sub_lines, level + 1, context, form_data)
                for sub_line in sub_lines:
                    line['balance'] += sub_line.get('balance', 0.0)
                    line['debit'] += sub_line.get('debit', 0.0)
                    line['credit'] += sub_line.get('credit', 0.0)
        
        # Appliquer le signe
        line['balance'] *= report.sign
        
        # Ajouter la ligne au résultat
        lines.append(line)
        
        # Ajouter les lignes des enfants
        if report.display_detail == 'detail_with_hierarchy':
            for child in report.children_ids:
                self._get_report_lines(child, lines, level + 1, context, form_data)
    
    def _get_accounts(self, report, form_data):
        """
        Récupère les comptes associés à un rapport
        """
        account_ids = []
        if report.account_ids:
            account_ids = report.account_ids
        return account_ids
    
    def _get_account_balance(self, accounts, context):
        """
        Calcule le solde, débit et crédit pour un ensemble de comptes
        """
        balance = 0.0
        debit = 0.0
        credit = 0.0
        
        if not accounts:
            return balance, debit, credit
        
        # Préparer le domaine pour la recherche des écritures
        domain = [
            ('account_id', 'in', accounts.ids),
        ]
        
        if context.get('date_from'):
            domain.append(('date', '>=', context['date_from']))
        if context.get('date_to'):
            domain.append(('date', '<=', context['date_to']))
        if context.get('company_id'):
            domain.append(('company_id', '=', context['company_id']))
        
        # Récupérer les écritures comptables
        account_moves = self.env['account.move.line'].search(domain)
        
        # Calculer les totaux
        for move in account_moves:
            balance += move.balance
            debit += move.debit
            credit += move.credit
        
        return balance, debit, credit
