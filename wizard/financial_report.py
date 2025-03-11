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
from odoo import api, models, fields


class AccountReport(models.Model):
    _inherit = 'account.report'

    def _get_financial_report_pdf_lines(self, options):
        """Get report lines for financial reports in PDF format."""
        lines = self._get_lines(options)
        for line in lines:
            # Ensure all monetary values are properly formatted
            for col in line.get('columns', []):
                if isinstance(col.get('no_format'), (int, float)):
                    col['name'] = self.format_value(col['no_format'])
        return lines


class FinancialReport(models.TransientModel):
    _name = "financial.report"
    _inherit = "account.common.report"
    _description = "Financial Reports"

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', required=True, default='posted')
    enable_filter = fields.Boolean(
        string='Enable Comparison',
        help="Enable the comparison with a previous period"
    )
    account_report_id = fields.Many2one(
        'account.report',
        string='Account Report',
        required=True,
        domain=[('root_report_id', '!=', False)]
    )
    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        default=True,
        help="Display debit/credit columns on report lines"
    )
    view_format = fields.Selection([
        ('vertical', 'Vertical'),
        ('horizontal', 'Horizontal')
    ], string='View Format', default='vertical')
    report_type = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel')
    ], string='Report Type', default='pdf', required=True)

    @api.onchange('account_report_id')
    def _onchange_account_report_id(self):
        """Update available options based on selected report."""
        if self.account_report_id:
            self.debit_credit = self.account_report_id.filter_journals
            self.enable_filter = self.account_report_id.filter_comparison

    def print_report(self, data=None):
        """Generate the financial report."""
        self.ensure_one()
        if not self.account_report_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Please select a report type.',
                    'type': 'danger',
                    'sticky': False,
                }
            }

        options = {
            'unfolded_lines': [],
            'date': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'filter': 'custom' if self.date_from or self.date_to else 'this_month',
                'mode': 'range',
            },
            'target_move': self.target_move,
            'company_id': self.company_id.id,
            'all_entries': self.target_move == 'all',
            'debit_credit': self.debit_credit,
            'enable_filter': self.enable_filter,
            'view_format': self.view_format,
        }

        if self.report_type == 'xlsx':
            return {
                'type': 'ir.actions.report',
                'report_type': 'xlsx',
                'report_name': 'base_accounting_kit_16.report_financial_xlsx',
                'report_file': 'base_accounting_kit_16.report_financial_xlsx',
                'data': {
                    'model': 'account.report',
                    'options': options,
                    'output_format': 'xlsx',
                    'report_name': self.account_report_id.name,
                },
                'context': {
                    'active_id': self.account_report_id.id,
                    'active_model': 'account.report',
                },
            }

        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'base_accounting_kit_16.report_financial',
            'report_file': 'base_accounting_kit_16.report_financial',
            'data': {
                'model': 'account.report',
                'options': options,
                'output_format': 'pdf',
                'report_name': self.account_report_id.name,
            },
            'context': {
                'active_id': self.account_report_id.id,
                'active_model': 'account.report',
            },
        }


class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Report'
    _inherit = 'report.report_xlsx.abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare report data."""
        data = data or {}
        if not data.get('options'):
            raise ValueError('Report options are missing.')

        report = self.env['account.report'].browse(self.env.context.get('active_id'))
        if not report:
            raise ValueError('Report not found.')

        lines = report._get_financial_report_pdf_lines(data['options'])

        return {
            'doc_ids': [report.id],
            'doc_model': 'account.report',
            'data': data,
            'docs': report,
            'lines': lines,
            'company': self.env.company,
        }

    def generate_xlsx_report(self, workbook, data, objects):
        """Generate Excel report."""
        report = self.env['account.report'].browse(self.env.context.get('active_id'))
        if not report:
            return

        options = data.get('options', {})
        lines = report._get_financial_report_pdf_lines(options)

        # Create worksheet
        sheet = workbook.add_worksheet(report.name[:31])
        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})

        # Set column widths
        sheet.set_column(0, 0, 40)  # Name
        sheet.set_column(1, 5, 20)  # Amounts

        # Write headers
        row = 0
        sheet.write(row, 0, 'Name', bold)
        col = 1
        if options.get('debit_credit'):
            sheet.write(row, col, 'Debit', bold)
            sheet.write(row, col + 1, 'Credit', bold)
            col += 2
        sheet.write(row, col, 'Balance', bold)
        if options.get('enable_filter'):
            sheet.write(row, col + 1, 'Previous Period', bold)

        # Write data rows
        row = 1
        for line in lines:
            # Indentation for hierarchy
            indent = '    ' * line.get('level', 0) if line.get('unfoldable', False) else ''
            name = indent + line.get('name', '')
            sheet.write(row, 0, name)

            # Write amounts
            col = 1
            for column in line.get('columns', []):
                value = column.get('no_format', 0.0)
                if isinstance(value, (int, float)):
                    sheet.write(row, col, value, money_format)
                else:
                    sheet.write(row, col, value)
                col += 1
            row += 1

        # Write totals
        sheet.write(row, 0, 'Total', bold)
        total_col = 1 if options.get('debit_credit') else 3
        total = sum(line.get('columns')[-1].get('no_format', 0.0)
                   for line in lines if not line.get('unfoldable', False))
        sheet.write(row, total_col, total, money_format)
