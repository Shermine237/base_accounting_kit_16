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

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountCommonAccountReport(models.TransientModel):
    _name = 'account.common.account.report'
    _description = 'Account Common Account Report'
    _inherit = "account.common.report"

    # Champs mis à jour pour Odoo 16
    account_type = fields.Selection([
        ('asset_receivable', 'Receivable'),
        ('asset_cash', 'Bank and Cash'),
        ('asset_current', 'Current Assets'),
        ('asset_non_current', 'Non-current Assets'),
        ('asset_prepayments', 'Prepayments'),
        ('asset_fixed', 'Fixed Assets'),
        ('liability_payable', 'Payable'),
        ('liability_credit_card', 'Credit Card'),
        ('liability_current', 'Current Liabilities'),
        ('liability_non_current', 'Non-current Liabilities'),
        ('equity', 'Equity'),
        ('equity_unaffected', 'Current Year Earnings'),
        ('income', 'Income'),
        ('income_other', 'Other Income'),
        ('expense', 'Expenses'),
        ('expense_depreciation', 'Depreciation'),
        ('expense_direct_cost', 'Cost of Revenue'),
        ('off_balance', 'Off-Balance Sheet')
    ], string='Account Type')
    
    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        'account_common_report_analytic_rel',  # Nom de table unique
        'report_id', 'analytic_id',  # Noms de colonnes uniques
        string='Analytic Accounts'
    )

    def _build_contexts(self, data):
        """Étend le contexte du rapport avec les données comptables"""
        result = super(AccountCommonAccountReport, self)._build_contexts(data)
        
        if data['form'].get('account_type'):
            result['account_type'] = data['form']['account_type']
        if data['form'].get('analytic_account_ids'):
            result['analytic_account_ids'] = data['form']['analytic_account_ids']
            
        return result

    def _get_report_values(self, docids, data=None):
        """Étend les valeurs du rapport avec les données comptables"""
        if not data.get('form'):
            raise UserError(_('Form content is missing, this report cannot be printed.'))

        report_values = super(AccountCommonAccountReport, self)._get_report_values(docids, data)
        
        report_values.update({
            'analytic_accounts': self.env['account.analytic.account'].browse(
                data['form'].get('analytic_account_ids', [])),
            'account_type': data['form'].get('account_type', False),
        })
        
        return report_values

    def _get_domain(self, data):
        """Construit le domaine de recherche pour les écritures comptables"""
        domain = [
            ('company_id', '=', data['form']['company_id'][0]),
            ('move_id.state', '=', data['form']['target_move']),
        ]
        
        if data['form'].get('date_from'):
            domain.append(('date', '>=', data['form']['date_from']))
        if data['form'].get('date_to'):
            domain.append(('date', '<=', data['form']['date_to']))
        if data['form'].get('journal_ids'):
            domain.append(('journal_id', 'in', data['form']['journal_ids']))
        if data['form'].get('account_type'):
            domain.append(('account_id.account_type', '=', data['form']['account_type']))
        if data['form'].get('analytic_account_ids'):
            domain.append(('analytic_account_id', 'in', data['form']['analytic_account_ids']))
            
        return domain
