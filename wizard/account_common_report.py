# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountCommonReport(models.TransientModel):
    _name = "account.common.report"
    _description = "Account Common Report"

    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                  default=lambda self: self.env['account.journal'].search([]))
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    
    # Champs de comparaison pour les rapports financiers
    date_from_cmp = fields.Date(string='Comparison Start Date')
    date_to_cmp = fields.Date(string='Comparison End Date')
    filter_cmp = fields.Selection([('filter_no', 'No Filters'),
                                ('filter_date', 'Date')], string='Filter by',
                                required=False, default='filter_no')
    enable_filter = fields.Boolean(string='Enable Comparison')
    label_filter = fields.Char(string='Column Label',
                            help="This label will be displayed on report to show the balance computed for the given comparison filter.")

    def _build_comparison_context(self, data):
        """
        Construction du contexte de comparaison
        """
        result = {}
        if data.get('form', {}).get('filter_cmp') == 'filter_date':
            result['date_from'] = data['form'].get('date_from_cmp')
            result['date_to'] = data['form'].get('date_to_cmp')
        return result

    def check_report(self):
        """
        To be implemented by each report
        :return: Action dictionary
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move',
                                'date_from_cmp', 'date_to_cmp', 'filter_cmp',
                                'enable_filter', 'label_filter'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        return self._print_report(data)

    def _build_contexts(self, data):
        """
        Construction du contexte pour le rapport
        """
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def _print_report(self, data):
        """
        To be implemented by each report
        :param data: Report data
        """
        raise NotImplementedError()

    def export_excel(self):
        """
        Méthode appelée lors du clic sur le bouton Export Excel
        À surcharger dans les classes enfants pour spécifier le rapport Excel approprié
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move',
                                'date_from_cmp', 'date_to_cmp', 'filter_cmp',
                                'enable_filter', 'label_filter'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        return self._export_excel_report(data)
    
    def _export_excel_report(self, data):
        """
        À implémenter par chaque rapport pour spécifier le rapport Excel approprié
        :param data: Données du rapport
        """
        raise NotImplementedError("Chaque rapport doit implémenter sa propre méthode _export_excel_report")
