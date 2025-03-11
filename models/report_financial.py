# -*- coding: utf-8 -*-
from odoo import api, models


class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rendu du rapport"""
        if not data.get('form'):
            raise ValueError('No data provided')

        report = self.env['financial.report'].browse(docids[0])
        company = self.env.company

        return {
            'doc_ids': docids,
            'doc_model': 'financial.report',
            'data': data,
            'docs': report,
            'res_company': company,
        }
