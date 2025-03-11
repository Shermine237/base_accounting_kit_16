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


class FinancialReport(models.TransientModel):
    _name = "financial.report"
    _inherit = "account.common.report"
    _description = "Financial Reports"

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        readonly=True,
        default=lambda self: self.env.company
    )
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', required=True, default='posted')
    enable_filter = fields.Boolean(string='Enable Comparison')
    account_report_id = fields.Many2one(
        'account.report',
        string='Account Report',
        required=True
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

    @api.model
    def _get_account_report(self):
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(self._context.get('active_id')).name
            reports = self.env['account.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    def _build_comparison_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        if data['form']['filter_cmp'] == 'filter_date':
            result['date_from'] = data['form']['date_from_cmp']
            result['date_to'] = data['form']['date_to_cmp']
            result['strict_range'] = True
        return result

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self.with_context(discard_logo_check=True).print_report(data)

    def print_report(self, data):
        report_action = self.account_report_id._get_report_default_action()
        if not report_action:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No report action defined for this report.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        action = report_action.copy()
        action.update({
            'context': {
                'model': 'account.report',
                'active_id': self.account_report_id.id,
                'active_ids': [self.account_report_id.id],
                'report_type': 'pdf',
                'date_from': self.date_from,
                'date_to': self.date_to,
                'target_move': self.target_move,
                'enable_filter': self.enable_filter,
                'debit_credit': self.debit_credit,
                'view_format': self.view_format,
                'company_id': self.company_id.id,
            }
        })
        return action


class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Report'
    _inherit = 'account.report'

    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise ValueError('Form content is missing.')

        report = self.env['account.report'].browse(data['form']['account_report_id'])
        if not report:
            raise ValueError('Report not found.')

        lines = report._get_lines({
            'date': {
                'date_from': data['form'].get('date_from'),
                'date_to': data['form'].get('date_to'),
                'filter': 'custom',
            },
            'target_move': data['form'].get('target_move', 'posted'),
            'company_id': data['form'].get('company_id', self.env.company.id),
        })

        return {
            'doc_ids': docids,
            'doc_model': 'account.report',
            'data': data['form'],
            'docs': report,
            'lines': lines,
        }
