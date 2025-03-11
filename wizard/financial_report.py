# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import json
import io
import xlsxwriter

class AccountFinancialReportWizard(models.TransientModel):
    _name = 'account.financial.report.wizard'
    _description = 'Financial Report Wizard'

    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date', required=True,
                           default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(string='End Date', required=True,
                         default=lambda self: fields.Date.context_today(self))
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                  ('all', 'All Entries')], string='Target Moves', required=True, default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                 default=lambda self: self.env['account.journal'].search([]))
    display_account = fields.Selection([('all', 'All'), ('movement', 'With movements'),
                                      ('not_zero', 'With balance is not equal to 0')],
                                     string='Display Accounts', required=True, default='movement')
    enable_filter = fields.Boolean(string='Enable Comparison')
    debit_credit = fields.Boolean(string='Display Debit/Credit Columns')
    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    filter_cmp = fields.Selection([('filter_no', 'No Filters'),
                                 ('filter_date', 'Date')], string='Filter by', default='filter_date')
    label_filter = fields.Char(string='Compare Label', default='Previous Period')
    report_type = fields.Selection([
        ('bs', 'Balance Sheet'),
        ('pl', 'Profit and Loss'),
        ('cf', 'Cash Flow Statement'),
        ('partner_ledger', 'Partner Ledger'),
        ('general_ledger', 'General Ledger'),
        ('trial_balance', 'Trial Balance'),
        ('aged_receivable', 'Aged Receivable'),
        ('aged_payable', 'Aged Payable'),
    ], string='Report Type', required=True)

    @api.onchange('enable_filter')
    def onchange_enable_filter(self):
        if self.enable_filter:
            self.date_from_cmp = self.date_from - timedelta(days=365)
            self.date_to_cmp = self.date_to - timedelta(days=365)

    def _get_report_base_filename(self):
        reports = {
            'bs': 'Balance Sheet',
            'pl': 'Profit and Loss',
            'cf': 'Cash Flow Statement',
            'partner_ledger': 'Partner Ledger',
            'general_ledger': 'General Ledger',
            'trial_balance': 'Trial Balance',
            'aged_receivable': 'Aged Receivable',
            'aged_payable': 'Aged Payable',
        }
        return reports.get(self.report_type, 'Financial Report')

    def _get_report_values(self):
        self.ensure_one()
        data = {
            'ids': self.env.context.get('active_ids', []),
            'model': self.env.context.get('active_model', 'ir.ui.menu'),
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'journal_ids': self.journal_ids.ids,
                'target_move': self.target_move,
                'display_account': self.display_account,
                'enable_filter': self.enable_filter,
                'debit_credit': self.debit_credit,
                'date_from_cmp': self.date_from_cmp,
                'date_to_cmp': self.date_to_cmp,
                'filter_cmp': self.filter_cmp,
                'label_filter': self.label_filter,
                'company_id': self.company_id.id,
            }
        }
        return data

    def action_view_report(self):
        self.ensure_one()
        data = self._get_report_values()
        report_name = f'base_accounting_kit_16.{self.report_type}_report'
        return self.env.ref(report_name).report_action(self, data=data)

    def action_print_pdf(self):
        self.ensure_one()
        data = self._get_report_values()
        report_name = f'base_accounting_kit_16.{self.report_type}_report'
        return self.env.ref(f'{report_name}_pdf').report_action(self, data=data)

    def action_export_excel(self):
        self.ensure_one()
        data = self._get_report_values()
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Add report-specific Excel generation logic here based on self.report_type
        self._generate_excel_report(workbook, data)
        
        workbook.close()
        output.seek(0)
        
        filename = f"{self._get_report_base_filename()}_{fields.Date.today()}.xlsx"
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&field=excel_file&download=true&filename={filename}',
            'target': 'self',
            'res_id': self.id,
        }

    def _generate_excel_report(self, workbook, data):
        report_methods = {
            'bs': self._generate_balance_sheet_excel,
            'pl': self._generate_profit_loss_excel,
            'cf': self._generate_cash_flow_excel,
            'partner_ledger': self._generate_partner_ledger_excel,
            'general_ledger': self._generate_general_ledger_excel,
            'trial_balance': self._generate_trial_balance_excel,
            'aged_receivable': self._generate_aged_partner_excel,
            'aged_payable': self._generate_aged_partner_excel,
        }
        method = report_methods.get(self.report_type)
        if method:
            method(workbook, data)
        else:
            raise UserError(_('Report type %s not supported for Excel export') % self.report_type)

    def _generate_balance_sheet_excel(self, workbook, data):
        sheet = workbook.add_worksheet('Balance Sheet')
        # Implement balance sheet specific Excel formatting and data population
        pass

    def _generate_profit_loss_excel(self, workbook, data):
        sheet = workbook.add_worksheet('Profit and Loss')
        # Implement profit and loss specific Excel formatting and data population
        pass

    def _generate_cash_flow_excel(self, workbook, data):
        sheet = workbook.add_worksheet('Cash Flow')
        # Implement cash flow specific Excel formatting and data population
        pass

    def _generate_partner_ledger_excel(self, workbook, data):
        sheet = workbook.add_worksheet('Partner Ledger')
        # Implement partner ledger specific Excel formatting and data population
        pass

    def _generate_general_ledger_excel(self, workbook, data):
        sheet = workbook.add_worksheet('General Ledger')
        # Implement general ledger specific Excel formatting and data population
        pass

    def _generate_trial_balance_excel(self, workbook, data):
        sheet = workbook.add_worksheet('Trial Balance')
        # Implement trial balance specific Excel formatting and data population
        pass

    def _generate_aged_partner_excel(self, workbook, data):
        report_name = 'Aged Receivable' if self.report_type == 'aged_receivable' else 'Aged Payable'
        sheet = workbook.add_worksheet(report_name)
        # Implement aged partner specific Excel formatting and data population
        pass
