# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class AccountReportGeneralLedgerXlsx(models.TransientModel):
    _name = "account.report.general.ledger.xlsx"
    _description = "General Ledger Report Excel"
    _inherit = "account.report.general.ledger"
    
    def _export_excel_report(self, data):
        """
        Export le rapport Grand Livre au format Excel
        :param data: Données du rapport
        :return: Action pour générer le rapport Excel
        """
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby', 'display_account', 'account_ids', 'analytic_account_ids'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        return {
            'type': 'ir.actions.report',
            'report_name': 'base_accounting_kit_16.general_ledger_xlsx',
            'report_type': 'xlsx',
            'data': data,
        }
