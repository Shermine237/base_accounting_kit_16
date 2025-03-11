# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import io
import xlsxwriter

class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Reports'
    _inherit = 'account.report'

    def _get_report_values(self, docids, data=None):
        """Génère les valeurs pour le rapport PDF"""
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}
        obj_account = self.env['account.financial.report'].browse(data['form']['account_report_id'][0])
        
        # Récupération des lignes du rapport
        lines = self._get_financial_report_pdf_lines(data.get('form', {}))
        
        return {
            'doc_ids': docids,
            'doc_model': 'account.financial.report',
            'data': data['form'],
            'docs': obj_account,
            'lines': lines,
        }

    def _get_financial_report_pdf_lines(self, options):
        """Génère les lignes pour le rapport PDF"""
        lines = []
        report_type = options.get('report_type', 'bs')
        
        # Récupération des données selon le type de rapport
        if report_type == 'bs':
            lines = self._get_balance_sheet_lines(options)
        elif report_type == 'pl':
            lines = self._get_profit_loss_lines(options)
        elif report_type == 'cf':
            lines = self._get_cash_flow_lines(options)
        elif report_type == 'gl':
            lines = self._get_general_ledger_lines(options)
        elif report_type == 'pl':
            lines = self._get_partner_ledger_lines(options)
        elif report_type == 'tb':
            lines = self._get_trial_balance_lines(options)
        elif report_type == 'ar':
            lines = self._get_aged_receivable_lines(options)
        elif report_type == 'ap':
            lines = self._get_aged_payable_lines(options)
        
        return lines

    def _get_balance_sheet_lines(self, options):
        """Génère les lignes du bilan"""
        lines = []
        accounts = self.env['account.account'].search([
            ('company_id', 'in', self.env.companies.ids),
            ('internal_type', 'in', ['asset', 'liability', 'equity'])
        ])
        
        for account in accounts:
            # Calcul des soldes
            domain = self._get_domain(account, options)
            balance = sum(self.env['account.move.line'].search(domain).mapped('balance'))
            
            # Création de la ligne
            lines.append({
                'id': account.id,
                'name': account.name,
                'code': account.code,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'columns': [
                    {'name': balance, 'class': 'number'},
                ],
            })
            
        return lines

    def _get_domain(self, account, options):
        """Construit le domaine de recherche selon les options"""
        domain = [
            ('account_id', '=', account.id),
            ('company_id', 'in', self.env.companies.ids),
        ]
        
        # Filtre de date
        if options.get('date'):
            domain += [
                ('date', '>=', options['date'].get('date_from')),
                ('date', '<=', options['date'].get('date_to')),
            ]
            
        # Filtre des journaux
        if options.get('journals'):
            domain += [('journal_id', 'in', options['journals'])]
            
        return domain

    def get_xlsx(self, options, response=None):
        """Export Excel utilisant les fonctionnalités standard d'Odoo"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._description)

        # Styles
        title_style = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'border': 1,
            'bg_color': '#F2F2F2'
        })
        header_style = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
            'bg_color': '#D9D9D9'
        })
        cell_style = workbook.add_format({
            'align': 'left',
            'border': 1
        })
        number_style = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00'
        })

        # En-tête
        sheet.merge_range('A1:D1', self._description, title_style)
        headers = ['Code', 'Account', 'Debit', 'Credit', 'Balance']
        for col, header in enumerate(headers):
            sheet.write(1, col, header, header_style)

        # Données
        lines = self._get_financial_report_pdf_lines(options)
        row = 2
        for line in lines:
            sheet.write(row, 0, line.get('code', ''), cell_style)
            sheet.write(row, 1, line.get('name', ''), cell_style)
            for col, column in enumerate(line.get('columns', [])):
                sheet.write(row, col + 2, column.get('name', 0), number_style)
            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response

class AccountReport(models.Model):
    _inherit = 'account.report'

    @api.model
    def _get_financial_report_pdf_lines(self, options):
        """Génère les lignes pour le rapport PDF"""
        self.ensure_one()
        lines = []
        
        # Contexte pour les dates et filtres
        context = options.get('context', {})
        comparison_context = options.get('comparison_context', {})
        
        # Récupération des lignes via les méthodes standard
        lines = self._get_financial_report_lines(options)
        
        # Ajout des données de comparaison si activé
        if comparison_context:
            for line in lines:
                line['comparison'] = self._get_balance_columns(
                    line.get('account_type'),
                    comparison_context
                )
                
        return lines

    def _get_financial_report_lines(self, options):
        """Méthode standard pour générer les lignes du rapport"""
        self.ensure_one()
        lines = []
        
        # Logique pour générer les lignes selon le type de rapport
        if self.name == 'Balance Sheet':
            lines.extend(self._get_balance_sheet_lines(options))
        elif self.name == 'Profit and Loss':
            lines.extend(self._get_profit_loss_lines(options))
        elif self.name == 'Cash Flow Statement':
            lines.extend(self._get_cash_flow_lines(options))
        
        return lines

    def _get_balance_sheet_lines(self, options):
        """Génère les lignes pour le bilan"""
        lines = []
        # Actifs
        assets = {
            'name': 'Assets',
            'level': 1,
            'columns': self._get_balance_columns('asset', options),
        }
        lines.append(assets)
        
        # Passifs
        liabilities = {
            'name': 'Liabilities',
            'level': 1,
            'columns': self._get_balance_columns('liability', options),
        }
        lines.append(liabilities)
        
        return lines

    def _get_profit_loss_lines(self, options):
        """Génère les lignes pour le compte de résultat"""
        lines = []
        # Revenus
        income = {
            'name': 'Income',
            'level': 1,
            'columns': self._get_balance_columns('income', options),
        }
        lines.append(income)
        
        # Dépenses
        expense = {
            'name': 'Expenses',
            'level': 1,
            'columns': self._get_balance_columns('expense', options),
        }
        lines.append(expense)
        
        return lines

    def _get_cash_flow_lines(self, options):
        """Génère les lignes pour le tableau des flux de trésorerie"""
        lines = []
        # Flux opérationnels
        operating = {
            'name': 'Operating Activities',
            'level': 1,
            'columns': self._get_cash_flow_columns('operating', options),
        }
        lines.append(operating)
        
        # Flux d'investissement
        investing = {
            'name': 'Investing Activities',
            'level': 1,
            'columns': self._get_cash_flow_columns('investing', options),
        }
        lines.append(investing)
        
        # Flux de financement
        financing = {
            'name': 'Financing Activities',
            'level': 1,
            'columns': self._get_cash_flow_columns('financing', options),
        }
        lines.append(financing)
        
        return lines

    def _get_balance_columns(self, account_type, options):
        """Calcule les colonnes de solde pour un type de compte donné"""
        self.ensure_one()
        columns = []
        
        # Colonnes de débit/crédit si activées
        if options.get('debit_credit'):
            debit, credit = self._compute_account_balance(account_type, options)
            columns.extend([
                {'name': debit, 'no_format': debit, 'class': 'number'},
                {'name': credit, 'no_format': credit, 'class': 'number'},
            ])
        
        # Solde de la période courante
        balance = self._compute_account_balance(account_type, options, balance_only=True)
        columns.append({
            'name': balance,
            'no_format': balance,
            'class': 'number',
        })
        
        return columns

    def _get_cash_flow_columns(self, activity_type, options):
        """Calcule les colonnes pour le tableau des flux de trésorerie"""
        self.ensure_one()
        columns = []
        
        # Montant de la période courante
        amount = self._compute_cash_flow(activity_type, options)
        columns.append({
            'name': amount,
            'no_format': amount,
            'class': 'number',
        })
        
        return columns

    def _compute_account_balance(self, account_type, options, balance_only=False):
        """Calcule le solde pour un type de compte et une période donnés"""
        domain = [
            ('account_id.internal_type', '=', account_type),
        ]
        
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
            
        if options.get('journal_ids'):
            domain.append(('journal_id', 'in', options['journal_ids']))
            
        if options.get('state') == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
            
        aml = self.env['account.move.line'].search(domain)
        
        if balance_only:
            return sum(aml.mapped('balance'))
        else:
            return sum(aml.mapped('debit')), sum(aml.mapped('credit'))

    def _compute_cash_flow(self, activity_type, options):
        """Calcule le montant des flux de trésorerie pour un type d'activité et une période donnés"""
        domain = []
        
        if activity_type == 'operating':
            domain.append(('account_id.internal_type', 'in', ['receivable', 'payable']))
        elif activity_type == 'investing':
            domain.append(('account_id.internal_type', '=', 'other'))
        elif activity_type == 'financing':
            domain.append(('account_id.internal_type', '=', 'other'))
            
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
            
        if options.get('state') == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
            
        amount = sum(self.env['account.move.line'].search(domain).mapped('balance'))
        return amount
