# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models
from odoo.tools.translate import _


class AccountingReport(models.TransientModel):
    _name = "cash.flow.report"
    _description = "Cash Flow Report"
    _inherit = "account.common.report"

    account_report_id = fields.Many2one('account.financial.report',
                                         string='Account Reports',
                                         required=True)
    date_from_cmp = fields.Date(string='Comparison Start Date')
    date_to_cmp = fields.Date(string='Comparison End Date')
    filter_cmp = fields.Selection([('filter_no', 'No Filters'),
                                   ('filter_date', 'Date')], string='Filter by',
                                  required=True, default='filter_date')

    def _build_comparison_context(self, data):
        result = {}
        if self.filter_cmp == 'filter_date':
            result['date_from'] = self.date_from_cmp
            result['date_to'] = self.date_to_cmp
        return result

    def _build_contexts(self, data):
        """
        Construction du contexte pour le rapport Cash Flow
        """
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def pre_print_report(self, data):
        """
        Préparation des données avant l'impression du rapport
        """
        data['form'].update(self.read(['account_report_id'])[0])
        return data

    def _print_report(self, data):
        data['form'].update(self.read(['date_from_cmp', 'date_to_cmp',
                                        'journal_ids', 'filter_cmp',
                                        'account_report_id', 'target_move'])[0])
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        return self.env.ref(
            'base_accounting_kit_16.action_report_cash_flow').report_action(
            self, data=data, config=False)

    def check_report(self):
        """
        Surcharge de la méthode check_report pour générer le rapport Cash Flow
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['account_report_id', 'date_from_cmp', 'date_to_cmp', 'journal_ids', 'filter_cmp', 'target_move'])[0]
        for field in ['account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        return self._print_report(data)
