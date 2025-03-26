# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class AccountReportGeneralLedger(models.TransientModel):
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
