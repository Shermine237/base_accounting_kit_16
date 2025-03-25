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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountAgedTrialBalance(models.TransientModel):
    _name = 'account.aged.trial.balance'
    _description = 'Account Aged Trial balance Report'
    _inherit = 'account.common.partner.report'

    period_length = fields.Integer(string='Period Length (days)', required=True,
                                   default=30)
    journal_ids = fields.Many2many('account.journal', string='Journals',
                                   required=True)
    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))

    def _build_contexts(self, data):
        """
        Construction du contexte pour le rapport Aged Partner Balance
        """
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = False
        result['strict_range'] = True if result['date_from'] else False
        result['result_selection'] = 'result_selection' in data['form'] and data['form']['result_selection'] or False
        return result

    def pre_print_report(self, data):
        """
        Préparation des données avant l'impression du rapport
        """
        data['form'].update(self.read(['period_length'])[0])
        return data

    def _print_report(self, data):
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = datetime.strptime(str(data['form']['date_from']), "%Y-%m-%d")

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (
                        str((5 - (i + 1)) * period_length) + '-' + str(
                    (5 - i) * period_length)) or (
                                 '+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)
        return self.env.ref(
            'base_accounting_kit_16.action_report_aged_partner_balance').with_context(
            landscape=True).report_action(self, data=data)

    def check_report(self):
        """
        Surcharge de la méthode check_report pour générer le rapport Aged Partner Balance
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'period_length', 'journal_ids', 'target_move', 'result_selection'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)
