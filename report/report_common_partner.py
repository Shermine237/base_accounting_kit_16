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

from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountCommonPartnerReport(models.TransientModel):
    _name = 'account.common.partner.report'
    _description = 'Account Common Partner Report'
    _inherit = "account.common.report"

    # Champs spécifiques aux rapports avec partenaires
    result_selection = fields.Selection([
        ('customer', 'Receivable Accounts'),
        ('supplier', 'Payable Accounts'),
        ('customer_supplier', 'Receivable and Payable Accounts')
    ], string="Partner Type", required=True, default='customer')

    partner_ids = fields.Many2many('res.partner', string='Partners',
                                help="Only selected partners will be included in the report. "
                                     "Leave empty to include all partners.")
    partner_category_ids = fields.Many2many('res.partner.category', string='Partner Tags',
                                        help="Only partners with these tags will be included in the report.")

    def _build_contexts(self, data):
        """Étend le contexte du rapport avec les données partenaires"""
        result = super(AccountCommonPartnerReport, self)._build_contexts(data)
        
        # Ajout des filtres partenaires
        result.update({
            'result_selection': data['form'].get('result_selection', 'customer'),
            'partner_ids': data['form'].get('partner_ids', []),
            'partner_category_ids': data['form'].get('partner_category_ids', []),
        })
        
        return result

    def _get_report_values(self, docids, data=None):
        """Étend les valeurs du rapport avec les données partenaires"""
        if not data.get('form'):
            raise UserError(_('Form content is missing, this report cannot be printed.'))

        report_values = super(AccountCommonPartnerReport, self)._get_report_values(docids, data)
        
        # Ajout des données partenaires
        report_values.update({
            'result_selection': data['form'].get('result_selection', 'customer'),
            'selected_partners': self.env['res.partner'].browse(data['form'].get('partner_ids', [])),
            'partner_categories': self.env['res.partner.category'].browse(data['form'].get('partner_category_ids', [])),
        })
        
        return report_values

    def _get_domain(self, data):
        """Construit le domaine de recherche pour les écritures partenaires"""
        domain = super(AccountCommonPartnerReport, self)._get_domain(data)
        
        # Filtre sur le type de compte (client/fournisseur)
        if data['form']['result_selection'] == 'customer':
            domain.append(('account_id.internal_type', '=', 'receivable'))
        elif data['form']['result_selection'] == 'supplier':
            domain.append(('account_id.internal_type', '=', 'payable'))
        else:  # customer_supplier
            domain.append(('account_id.internal_type', 'in', ['receivable', 'payable']))
            
        # Filtre sur les partenaires sélectionnés
        if data['form'].get('partner_ids'):
            domain.append(('partner_id', 'in', data['form']['partner_ids']))
            
        # Filtre sur les catégories de partenaires
        if data['form'].get('partner_category_ids'):
            domain.append(('partner_id.category_id', 'in', data['form']['partner_category_ids']))
            
        return domain

    def pre_print_report(self, data):
        """Préparation des données avant impression"""
        data['form'].update(self.read(['result_selection', 'partner_ids', 'partner_category_ids'])[0])
        return data
