# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FinancialReport(models.TransientModel):
    _name = 'financial.report'
    _description = 'Financial Report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', required=True, default='posted')
    
    # Sélection du rapport
    account_report_id = fields.Many2one(
        'account.report', string='Account Reports',
        required=True, domain=[('parent_id', '=', False)])

    # Options de filtrage
    enable_filter = fields.Boolean(string='Enable Comparison')
    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    filter_cmp = fields.Selection([
        ('filter_no', 'No Filters'),
        ('filter_date', 'Date')
    ], string='Filter by', required=True, default='filter_no')
    
    # Options d'affichage
    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        help="This option allows you to get more details about the way your balances are computed. Because it is space consuming, we do not allow to use it while doing a comparison.")

    def _build_contexts(self, data):
        """Construit le contexte pour le rapport"""
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def _build_comparison_context(self, data):
        """Construit le contexte pour la comparaison"""
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from_cmp'] or False
        result['date_to'] = data['form']['date_to_cmp'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def check_report(self):
        """Prépare les données et lance le rapport"""
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'date_from_cmp', 'date_to_cmp',
                                 'filter_cmp', 'account_report_id', 'target_move',
                                 'enable_filter', 'debit_credit'])[0]
        
        # Contexte standard
        data['form']['used_context'] = self._build_contexts(data)
        
        # Contexte de comparaison si activé
        if data['form']['enable_filter']:
            data['form']['comparison_context'] = self._build_comparison_context(data)

        return self.env.ref('base_accounting_kit_16.action_report_financial').report_action(self, data=data)
