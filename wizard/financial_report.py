# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountFinancialReportWizard(models.TransientModel):
    _name = 'account.financial.report.wizard'
    _description = 'Financial Report Wizard'

    company_id = fields.Many2one('res.company', string='Company', required=True, 
                               default=lambda self: self.env.company)
    date_from = fields.Date(string='Period Start Date', required=True)
    date_to = fields.Date(string='Period End Date', required=True)
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', required=True, default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals')
    account_report_id = fields.Many2one(
        'account.financial.report', string='Account Reports', required=True)
    enable_filter = fields.Boolean(string='Enable Comparison')
    debit_credit = fields.Boolean(string='Display Debit/Credit Columns')
    date_from_cmp = fields.Date(string='Comparison Start Date')
    date_to_cmp = fields.Date(string='Comparison End Date')
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
    
    # Champs additionnels pour la vue
    name = fields.Char(string='Report Name', compute='_compute_report_name', store=True)
    show_debit_credit = fields.Boolean(string='Show Debit/Credit', default=False)
    show_balance = fields.Boolean(string='Show Balance', default=True)
    show_hierarchy = fields.Boolean(string='Show Hierarchy', default=False)
    show_partner = fields.Boolean(string='Show Partner Details', default=False)
    show_analytic = fields.Boolean(string='Show Analytic', default=False)
    show_journal = fields.Boolean(string='Show Journal', default=False)
    label_filter = fields.Char(string='Column Label', default='Comparison')
    
    @api.depends('account_report_id', 'report_type')
    def _compute_report_name(self):
        """Calcule un nom pour le rapport basé sur le type ou le rapport sélectionné"""
        for record in self:
            if record.account_report_id:
                record.name = record.account_report_id.name
            elif record.report_type:
                type_mapping = {
                    'bs': 'Balance Sheet',
                    'pl': 'Profit and Loss',
                    'cf': 'Cash Flow Statement',
                    'gl': 'General Ledger',
                    'ptl': 'Partner Ledger',
                    'tb': 'Trial Balance',
                    'ar': 'Aged Receivable',
                    'ap': 'Aged Payable'
                }
                record.name = type_mapping.get(record.report_type, 'Financial Report')
            else:
                record.name = 'Financial Report'

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

    def _build_comparison_context(self):
        """Construit le contexte pour la comparaison"""
        result = {}
        if self.enable_filter and self.filter_cmp == 'filter_date':
            result.update({
                'date_from_cmp': self.date_from_cmp,
                'date_to_cmp': self.date_to_cmp,
            })
        return result

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
            'report_type': self.report_type,
            'show_debit_credit': self.show_debit_credit,
            'show_balance': self.show_balance,
            'show_hierarchy': self.show_hierarchy,
            'show_partner': self.show_partner,
            'show_analytic': self.show_analytic,
            'show_journal': self.show_journal
        }
        
        if self.enable_filter:
            result.update(self._build_comparison_context())
            
        return result

    def check_report(self):
        """Point d'entrée pour la génération du rapport"""
        self.ensure_one()
        
        # Validation des dates
        if self.enable_filter and self.filter_cmp == 'filter_date':
            if not self.date_from_cmp or not self.date_to_cmp:
                raise UserError(_('Please provide comparison dates.'))
            if self.date_from_cmp > self.date_to_cmp:
                raise UserError(_('Comparison start date must be before end date.'))
        
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'journal_ids': self.journal_ids.ids,
                'target_move': self.target_move,
                'company_id': [self.company_id.id, self.company_id.name],
                'account_report_id': [self.account_report_id.id, self.account_report_id.name],
                'enable_filter': self.enable_filter,
                'debit_credit': self.debit_credit,
                'report_type': self.report_type,
                'show_debit_credit': self.show_debit_credit,
                'show_balance': self.show_balance,
                'show_hierarchy': self.show_hierarchy,
                'show_partner': self.show_partner,
                'show_analytic': self.show_analytic,
                'show_journal': self.show_journal,
                'name': self.name,
                'label_filter': self.label_filter if self.enable_filter else ''
            }
        }
        
        # Ajout des données de comparaison si activées
        if self.enable_filter:
            comparison_context = self._build_comparison_context()
            data['form'].update({
                'comparison_context': comparison_context,
                'date_from_cmp': comparison_context.get('date_from_cmp'),
                'date_to_cmp': comparison_context.get('date_to_cmp'),
                'filter_cmp': self.filter_cmp,
                'label_filter': self.label_filter
            })
        
        return data

    def action_view_report(self):
        """Action pour afficher le rapport dans l'interface"""
        data = self.check_report()
        report_action = self.env.ref('base_accounting_kit_16.action_report_financial')
        action = report_action.report_action(self, data=data)
        action['close_on_report_download'] = False
        return action

    def action_print_pdf(self):
        """Action pour imprimer le rapport en PDF"""
        data = self.check_report()
        report_action = self.env.ref('base_accounting_kit_16.action_report_financial_pdf')
        return report_action.report_action(self, data=data)

    def action_export_excel(self):
        """Action pour exporter le rapport en Excel"""
        data = self.check_report()
        report_action = self.env.ref('base_accounting_kit_16.action_report_financial_xlsx')
        return report_action.report_action(self, data=data)
