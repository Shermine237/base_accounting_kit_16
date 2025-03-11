# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class FinancialReport(models.TransientModel):
    _name = 'financial.report'
    _description = 'Financial Report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    account_report_id = fields.Many2one('account.report', string='Financial Report',
                                       required=True)
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                  ('all', 'All Entries')],
                                 string='Target Moves', required=True,
                                 default='posted')
    enable_filter = fields.Boolean(string='Enable Comparison')
    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    filter_cmp = fields.Selection([('filter_no', 'No Filters'),
                                 ('filter_date', 'Date')],
                                string='Filter by',
                                required=True, default='filter_no')
    journal_ids = fields.Many2many('account.journal', string='Journals',
                                 default=lambda self: self.env['account.journal'].search([]))

    @api.onchange('account_report_id')
    def _onchange_account_report_id(self):
        """Met à jour les filtres disponibles selon le rapport sélectionné"""
        if self.account_report_id:
            self.enable_filter = self.account_report_id.filter_comparison

    def _build_comparison_context(self, data):
        """Construit le contexte pour la comparaison"""
        result = {}
        if self.filter_cmp == 'filter_date':
            result['date_from'] = self.date_from_cmp
            result['date_to'] = self.date_to_cmp
        return result

    def _build_contexts(self, data):
        """Construit les contextes pour le rapport"""
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def check_report(self):
        """Vérifie et prépare les données pour le rapport"""
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move',
                                'company_id', 'account_report_id', 'enable_filter',
                                'filter_cmp', 'date_from_cmp', 'date_to_cmp'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'fr_FR')
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        report_lines = self._get_report_lines(data)
        data['form']['report_lines'] = report_lines
        return self.env.ref('base_accounting_kit_16.action_report_financial').report_action(self, data=data)

    def _get_report_lines(self, data):
        """Récupère les lignes du rapport"""
        report = self.account_report_id
        lines = []
        
        # Contexte pour les dates et filtres
        context = data['form']['used_context']
        comparison_context = data['form']['comparison_context']
        
        # Récupération des lignes via le modèle account.report
        lines = report._get_financial_report_lines(context)
        
        # Ajout des données de comparaison si activé
        if self.enable_filter and comparison_context:
            for line in lines:
                line['comparison'] = report._get_balance_columns(
                    line.get('account_type'),
                    comparison_context
                )
                
        return lines
