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


class AccountBalanceReport(models.TransientModel):
    _name = 'account.balance.report'
    _description = 'Trial Balance Report'
    _inherit = 'account.common.report'

    display_account = fields.Selection([
        ('all', 'All'),
        ('movement', 'With movements'),
        ('not_zero', 'With balance not equal to 0')],
        string='Display Accounts', required=True, default='movement')

    def _build_contexts(self, data):
        """
        Construction du contexte pour le rapport Trial Balance
        """
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['display_account'] = data['form']['display_account'] or 'all'
        return result

    def pre_print_report(self, data):
        """
        Préparation des données avant l'impression du rapport
        """
        data['form'].update(self.read(['display_account'])[0])
        return data

    def _print_report(self, data):
        data = self.pre_print_report(data)
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('base_accounting_kit_16.action_report_trial_balance').report_action(records, data=data)

    def check_report(self):
        """
        Surcharge de la méthode check_report pour générer le rapport Trial Balance
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'display_account'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)
