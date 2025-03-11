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

    # Champs spécifiques aux rapports comptables
    account_type_ids = fields.Many2many('account.account.type', string='Account Types',
                                      help="Only accounts of this type will be included in the report")
    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    def _build_contexts(self, data):
        """Étend le contexte du rapport avec les données comptables"""
        result = super(AccountCommonAccountReport, self)._build_contexts(data)
        
        # Ajout des filtres comptables spécifiques
        if data['form'].get('account_type_ids'):
            result['account_type_ids'] = data['form']['account_type_ids']
        if data['form'].get('analytic_account_ids'):
            result['analytic_account_ids'] = data['form']['analytic_account_ids']
        if data['form'].get('analytic_tag_ids'):
            result['analytic_tag_ids'] = data['form']['analytic_tag_ids']
            
        return result

    def _get_report_values(self, docids, data=None):
        """Étend les valeurs du rapport avec les données comptables"""
        if not data.get('form'):
            raise UserError(_('Form content is missing, this report cannot be printed.'))

        report_values = super(AccountCommonAccountReport, self)._get_report_values(docids, data)
        
        # Ajout des données comptables spécifiques
        report_values.update({
            'account_types': self.env['account.account.type'].browse(data['form'].get('account_type_ids', [])),
            'analytic_accounts': self.env['account.analytic.account'].browse(data['form'].get('analytic_account_ids', [])),
            'analytic_tags': self.env['account.analytic.tag'].browse(data['form'].get('analytic_tag_ids', [])),
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
        if data['form'].get('account_type_ids'):
            domain.append(('account_id.user_type_id', 'in', data['form']['account_type_ids']))
        if data['form'].get('analytic_account_ids'):
            domain.append(('analytic_account_id', 'in', data['form']['analytic_account_ids']))
        if data['form'].get('analytic_tag_ids'):
            domain.append(('analytic_tag_ids', 'in', data['form']['analytic_tag_ids']))
            
        return domain
