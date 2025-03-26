# -*- coding: utf-8 -*-
from odoo import models
import json


class GeneralLedgerXlsx(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.general_ledger_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'General Ledger Report Excel'

    def generate_xlsx_report(self, workbook, data, objects):
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

        # Création d'une feuille de calcul pour le rapport
        sheet = workbook.add_worksheet('General Ledger')
        sheet.set_column(0, 0, 12)  # Date
        sheet.set_column(1, 1, 15)  # Journal
        sheet.set_column(2, 2, 20)  # Partner
        sheet.set_column(3, 3, 40)  # Label
        sheet.set_column(4, 4, 15)  # Debit
        sheet.set_column(5, 5, 15)  # Credit
        sheet.set_column(6, 6, 15)  # Balance

        # En-tête du rapport
        company_name = self.env.user.company_id.name
        sheet.merge_range('A1:G1', company_name, header_format)
        sheet.merge_range('A2:G2', 'General Ledger Report', header_format)

        # Filtres utilisés
        y_offset = 3
        sheet.write(y_offset, 0, 'Date From:', subtitle_format)
        sheet.write(y_offset, 1, data['form'].get('date_from') or '')
        sheet.write(y_offset, 3, 'Date To:', subtitle_format)
        sheet.write(y_offset, 4, data['form'].get('date_to') or '')
        y_offset += 1

        # Entêtes des colonnes
        y_offset += 1
        sheet.write(y_offset, 0, 'Date', title_format)
        sheet.write(y_offset, 1, 'Journal', title_format)
        sheet.write(y_offset, 2, 'Partner', title_format)
        sheet.write(y_offset, 3, 'Label', title_format)
        sheet.write(y_offset, 4, 'Debit', title_format)
        sheet.write(y_offset, 5, 'Credit', title_format)
        sheet.write(y_offset, 6, 'Balance', title_format)
        y_offset += 1

        # Récupération des données du rapport
        initial_balance = data['form'].get('initial_balance', False)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form'].get('display_account', 'movement')
        
        # Récupération des comptes
        account_ids = data['form'].get('account_ids', [])
        accounts = self.env['account.account'].browse(account_ids) if account_ids else self.env['account.account'].search([])
        
        # Contexte pour la requête
        used_context = data['form'].get('used_context', {})
        
        # Pour chaque compte
        for account in accounts:
            # Vérifier si le compte doit être affiché selon le critère choisi
            if display_account == 'movement' and not account.code.startswith('6'):
                continue
            elif display_account == 'not_zero' and account.balance == 0:
                continue
                
            # Affichage du compte
            sheet.write(y_offset, 0, account.code, subtitle_format)
            sheet.write(y_offset, 1, account.name, subtitle_format)
            sheet.write(y_offset, 6, account.balance, number_format if account.balance >= 0 else negative_number_format)
            y_offset += 1
            
            # Récupération des mouvements du compte
            domain = [('account_id', '=', account.id)]
            if used_context.get('date_from'):
                domain.append(('date', '>=', used_context['date_from']))
            if used_context.get('date_to'):
                domain.append(('date', '<=', used_context['date_to']))
            if used_context.get('state') == 'posted':
                domain.append(('move_id.state', '=', 'posted'))
                
            # Tri des mouvements
            order = 'date' if sortby == 'sort_date' else 'journal_id, partner_id'
            moves = self.env['account.move.line'].search(domain, order=order)
            
            # Solde initial
            balance = 0
            if initial_balance and used_context.get('date_from'):
                init_domain = [
                    ('account_id', '=', account.id),
                    ('date', '<', used_context['date_from'])
                ]
                if used_context.get('state') == 'posted':
                    init_domain.append(('move_id.state', '=', 'posted'))
                init_moves = self.env['account.move.line'].search(init_domain)
                balance = sum(init_moves.mapped('balance'))
                
                # Affichage du solde initial
                sheet.write(y_offset, 3, 'Initial Balance', subtitle_format)
                sheet.write(y_offset, 6, balance, number_format if balance >= 0 else negative_number_format)
                y_offset += 1
            
            # Affichage des mouvements
            for move in moves:
                balance += move.balance
                sheet.write(y_offset, 0, move.date.strftime('%Y-%m-%d'))
                sheet.write(y_offset, 1, move.journal_id.name)
                sheet.write(y_offset, 2, move.partner_id.name if move.partner_id else '')
                sheet.write(y_offset, 3, move.name)
                sheet.write(y_offset, 4, move.debit, number_format)
                sheet.write(y_offset, 5, move.credit, number_format)
                sheet.write(y_offset, 6, balance, number_format if balance >= 0 else negative_number_format)
                y_offset += 1
            
            # Affichage du total du compte
            sheet.write(y_offset, 3, 'Total ' + account.name, subtitle_format)
            sheet.write(y_offset, 4, sum(moves.mapped('debit')), total_format)
            sheet.write(y_offset, 5, sum(moves.mapped('credit')), total_format)
            sheet.write(y_offset, 6, balance, total_format)
            y_offset += 2  # Espace entre les comptes
