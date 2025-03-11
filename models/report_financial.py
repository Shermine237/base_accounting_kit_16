# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


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


class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport QWeb"""
        if not data.get('form'):
            raise UserError('Form content is missing, this report cannot be printed.')

        report = self.env['account.report'].browse(data['form']['account_report_id'][0])
        company = self.env['res.company'].browse(data['form']['company_id'][0])

        # Calcul des totaux
        lines = report._get_financial_report_pdf_lines(data['form'])
        sum_debit = sum(line.get('debit', 0.0) for line in lines if line.get('level') == 1)
        sum_credit = sum(line.get('credit', 0.0) for line in lines if line.get('level') == 1)
        sum_balance = sum(line.get('balance', 0.0) for line in lines if line.get('level') == 1)
        sum_balance_cmp = sum(line.get('balance_cmp', 0.0) for line in lines if line.get('level') == 1)

        return {
            'doc_ids': docids,
            'doc_model': 'account.report',
            'data': data,
            'docs': report,
            'lines': lines,
            'sum_debit': sum_debit,
            'sum_credit': sum_credit,
            'sum_balance': sum_balance,
            'sum_balance_cmp': sum_balance_cmp,
            'company': company,
        }
