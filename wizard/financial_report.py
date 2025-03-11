# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountFinancialReportWizard(models.TransientModel):
    _name = 'account.financial.report.wizard'
    _description = 'Financial Report Wizard'

    company_id = fields.Many2one('res.company', string='Company', required=True, 
                               default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', required=True, default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals')
    account_report_id = fields.Many2one(
        'account.financial.report', string='Account Reports', required=True)
    enable_filter = fields.Boolean(string='Enable Comparison')
    debit_credit = fields.Boolean(string='Display Debit/Credit Columns')
    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    filter_cmp = fields.Selection([
        ('filter_no', 'No Filters'),
        ('filter_date', 'Date')
    ], string='Filter by', required=True, default='filter_no')
    report_type = fields.Selection([
        ('bs', 'Balance Sheet'),
        ('pl', 'Profit and Loss'),
        ('cf', 'Cash Flow Statement'),
        ('gl', 'General Ledger'),
        ('ptl', 'Partner Ledger'),
        ('tb', 'Trial Balance'),
        ('ar', 'Aged Receivable'),
        ('ap', 'Aged Payable')
    ], string='Report Type', required=True, default='bs')

    @api.onchange('account_report_id')
    def _onchange_account_report_id(self):
        """Met à jour le type de rapport en fonction du rapport sélectionné"""
        if self.account_report_id:
            if 'balance' in self.account_report_id.name.lower():
                self.report_type = 'bs'
            elif 'profit' in self.account_report_id.name.lower():
                self.report_type = 'pl'
            elif 'cash' in self.account_report_id.name.lower():
                self.report_type = 'cf'
            elif 'partner' in self.account_report_id.name.lower():
                self.report_type = 'ptl'
            elif 'general' in self.account_report_id.name.lower():
                self.report_type = 'gl'
            elif 'trial' in self.account_report_id.name.lower():
                self.report_type = 'tb'
            elif 'receivable' in self.account_report_id.name.lower():
                self.report_type = 'ar'
            elif 'payable' in self.account_report_id.name.lower():
                self.report_type = 'ap'

    def _build_contexts(self):
        """Construit le contexte pour le rapport"""
        self.ensure_one()
        result = {
            'journal_ids': self.journal_ids.ids,
            'state': self.target_move,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'strict_range': True if self.date_from else False,
            'company_id': self.company_id.id,
        }
        
        if self.enable_filter:
            result['date_from_cmp'] = self.date_from_cmp
            result['date_to_cmp'] = self.date_to_cmp
            result['filter_cmp'] = self.filter_cmp
            
        return result

    def _print_report(self, data):
        """Génère le rapport selon le format choisi"""
        self.ensure_one()
        
        # Préparation des données
        data['form'].update(self._build_contexts())
        
        # Sélection de l'action selon le type de rapport
        if data.get('report_type') == 'xlsx':
            report_action = self.env.ref(
                'base_accounting_kit_16.action_report_financial_excel')
        else:
            report_action = self.env.ref(
                'base_accounting_kit_16.action_report_financial_pdf')
            
        return report_action.report_action(self, data=data)

    def check_report(self):
        """Point d'entrée pour la génération du rapport"""
        self.ensure_one()
        
        # Validation des dates
        if self.enable_filter and self.filter_cmp == 'filter_date':
            if not self.date_from_cmp or not self.date_to_cmp:
                raise UserError(
                    _('Please enter a valid date range for comparison'))
        
        # Préparation des données
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'journal_ids': self.journal_ids.ids,
                'target_move': self.target_move,
                'enable_filter': self.enable_filter,
                'debit_credit': self.debit_credit,
                'account_report_id': [self.account_report_id.id, 
                                    self.account_report_id.name],
                'date_from_cmp': self.date_from_cmp,
                'date_to_cmp': self.date_to_cmp,
                'filter_cmp': self.filter_cmp,
                'company_id': self.company_id.id,
                'report_type': self.report_type,
            }
        }
        
        return self._print_report(data)

    def check_report_xlsx(self):
        """Point d'entrée pour la génération du rapport Excel"""
        data = self.check_report()
        data['report_type'] = 'xlsx'
        return self._print_report(data)
