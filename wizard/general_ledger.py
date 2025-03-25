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

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountReportGeneralLedger(models.TransientModel):
    _name = "account.report.general.ledger"
    _description = "General Ledger Report"
    _inherit = "account.common.report"

    initial_balance = fields.Boolean(string='Include Initial Balances',
                                     help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.')
    sortby = fields.Selection(
        [('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')],
        string='Sort by', required=True, default='sort_date')
    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')
    journal_ids = fields.Many2many('account.journal', 'account_report_general_ledger_journal_rel', 'report_id',
                                   'journal_id', string='Journals', required=True)
    account_ids = fields.Many2many('account.account',
                                   'account_report_general_ledger_account_rel',
                                   'report_id', 'account_id',
                                   string='Accounts')
    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        string='Analytic Accounts'
    )

    def _build_contexts(self, data):
        """
        Construction du contexte pour le rapport General Ledger
        """
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['account_ids'] = 'account_ids' in data['form'] and data['form']['account_ids'] or False
        result['analytic_account_ids'] = 'analytic_account_ids' in data['form'] and data['form']['analytic_account_ids'] or False
        result['initial_balance'] = 'initial_balance' in data['form'] and data['form']['initial_balance'] or False
        result['sortby'] = 'sortby' in data['form'] and data['form']['sortby'] or False
        result['display_account'] = 'display_account' in data['form'] and data['form']['display_account'] or False
        return result

    def pre_print_report(self, data):
        """
        Préparation des données avant l'impression du rapport
        """
        data['form'].update(self.read(['initial_balance', 'sortby', 'display_account', 'account_ids', 'analytic_account_ids'])[0])
        return data

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby', 'display_account'])[0])
        if data['form'].get('initial_balance') and not data['form'].get(
                'date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref(
            'base_accounting_kit_16.action_report_general_ledger').with_context(
            landscape=True).report_action(records, data=data)

    def check_report(self):
        """
        Surcharge de la méthode check_report pour générer le rapport General Ledger
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'account_ids', 'analytic_account_ids', 'initial_balance', 'sortby', 'display_account'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)
