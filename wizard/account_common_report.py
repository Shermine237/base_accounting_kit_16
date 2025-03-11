# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountCommonReport(models.TransientModel):
    _name = 'account.common.report'
    _description = 'Account Common Report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                               default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', required=True, default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals',
                                 required=True)
    display_account = fields.Selection([
        ('all', 'All'),
        ('movement', 'With movements'),
        ('not_zero', 'With balance not equal to 0')
    ], string='Display Accounts', required=True, default='movement')

    def _build_contexts(self, data):
        """Construit le contexte pour le rapport"""
        result = {
            'journal_ids': data['form']['journal_ids'],
            'state': data['form']['target_move'],
            'date_from': data['form'].get('date_from'),
            'date_to': data['form'].get('date_to'),
            'strict_range': True if data['form'].get('date_from') else False,
            'company_id': data['form']['company_id'][0]
        }
        return result

    def check_report(self):
        """Point d'entrée pour la génération du rapport"""
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move',
                                'display_account', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                          lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)

    def pre_print_report(self, data):
        """Préparation des données avant impression"""
        data['form'].update(self.read(['display_account'])[0])
        return data

    def _print_report(self, data):
        """Méthode à surcharger dans les classes filles"""
        raise UserError(_('Méthode _print_report non implémentée'))
