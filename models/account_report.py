# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountReport(models.Model):
    _name = "account.report"
    _description = "Account Report"

    name = fields.Char(string='Report Name', required=True, translate=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    parent_id = fields.Many2one('account.report', string='Parent Report')
    children_ids = fields.One2many('account.report', 'parent_id', string='Children Reports')
    
    # Filtres standards
    filter_date_range = fields.Boolean(string='Date Range Filter', default=True)
    filter_unfold_all = fields.Boolean(string='Unfold All Filter', default=True)
    filter_journals = fields.Boolean(string='Journals Filter', default=True)
    filter_multi_company = fields.Boolean(string='Multi-company Filter', default=True)
    
    # Filtres spécifiques
    filter_partner = fields.Boolean(string='Partner Filter')
    filter_account_type = fields.Boolean(string='Account Type Filter')
    filter_comparison = fields.Boolean(string='Comparison Filter')
    filter_analytic_groupby = fields.Boolean(string='Analytic Groupby Filter')

    @api.model
    def _get_financial_report_lines(self, options):
        """Méthode pour générer les lignes du rapport financier"""
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
            'name': _('Assets'),
            'level': 1,
            'columns': self._get_balance_columns(account_type='asset', options=options),
        }
        lines.append(assets)
        
        # Passifs
        liabilities = {
            'name': _('Liabilities'),
            'level': 1,
            'columns': self._get_balance_columns(account_type='liability', options=options),
        }
        lines.append(liabilities)
        
        return lines

    def _get_profit_loss_lines(self, options):
        """Génère les lignes pour le compte de résultat"""
        lines = []
        # Revenus
        income = {
            'name': _('Income'),
            'level': 1,
            'columns': self._get_balance_columns(account_type='income', options=options),
        }
        lines.append(income)
        
        # Dépenses
        expense = {
            'name': _('Expenses'),
            'level': 1,
            'columns': self._get_balance_columns(account_type='expense', options=options),
        }
        lines.append(expense)
        
        return lines

    def _get_cash_flow_lines(self, options):
        """Génère les lignes pour le tableau des flux de trésorerie"""
        lines = []
        # Flux opérationnels
        operating = {
            'name': _('Operating Activities'),
            'level': 1,
            'columns': self._get_cash_flow_columns('operating', options),
        }
        lines.append(operating)
        
        # Flux d'investissement
        investing = {
            'name': _('Investing Activities'),
            'level': 1,
            'columns': self._get_cash_flow_columns('investing', options),
        }
        lines.append(investing)
        
        # Flux de financement
        financing = {
            'name': _('Financing Activities'),
            'level': 1,
            'columns': self._get_cash_flow_columns('financing', options),
        }
        lines.append(financing)
        
        return lines

    def _get_balance_columns(self, account_type, options):
        """Calcule les colonnes de solde pour un type de compte donné"""
        self.ensure_one()
        columns = []
        
        if options.get('comparison', {}).get('periods'):
            for period in options['comparison']['periods']:
                balance = self._compute_balance(account_type, period)
                columns.append({
                    'name': balance,
                    'no_format': balance,
                    'class': 'number',
                })
        
        # Solde de la période courante
        balance = self._compute_balance(account_type, options.get('date'))
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
        
        if options.get('comparison', {}).get('periods'):
            for period in options['comparison']['periods']:
                amount = self._compute_cash_flow(activity_type, period)
                columns.append({
                    'name': amount,
                    'no_format': amount,
                    'class': 'number',
                })
        
        # Montant de la période courante
        amount = self._compute_cash_flow(activity_type, options.get('date'))
        columns.append({
            'name': amount,
            'no_format': amount,
            'class': 'number',
        })
        
        return columns

    def _compute_balance(self, account_type, period):
        """Calcule le solde pour un type de compte et une période donnés"""
        domain = [
            ('account_id.internal_type', '=', account_type),
        ]
        
        if period.get('date_from'):
            domain.append(('date', '>=', period['date_from']))
        if period.get('date_to'):
            domain.append(('date', '<=', period['date_to']))
            
        if period.get('journal_ids'):
            domain.append(('journal_id', 'in', period['journal_ids']))
            
        balance = sum(self.env['account.move.line'].search(domain).mapped('balance'))
        return balance

    def _compute_cash_flow(self, activity_type, period):
        """Calcule le montant des flux de trésorerie pour un type d'activité et une période donnés"""
        domain = []
        
        if activity_type == 'operating':
            domain.append(('account_id.internal_type', 'in', ['receivable', 'payable']))
        elif activity_type == 'investing':
            domain.append(('account_id.internal_type', '=', 'other'))
        elif activity_type == 'financing':
            domain.append(('account_id.internal_type', '=', 'other'))
            
        if period.get('date_from'):
            domain.append(('date', '>=', period['date_from']))
        if period.get('date_to'):
            domain.append(('date', '<=', period['date_to']))
            
        amount = sum(self.env['account.move.line'].search(domain).mapped('balance'))
        return amount
