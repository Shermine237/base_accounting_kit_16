# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import io
import xlsxwriter


class AccountFinancialReport(models.Model):
    _name = 'account.financial.report'
    _description = 'Financial Report'
    _order = 'sequence, id'

    name = fields.Char('Report Name', required=True, translate=True)
    parent_id = fields.Many2one('account.financial.report', 'Parent')
    children_ids = fields.One2many('account.financial.report', 'parent_id', 'Children')
    sequence = fields.Integer('Sequence')
    level = fields.Integer('Level', compute='_compute_level', recursive=True, store=True)
    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
    ], 'Type', default='sum')
    account_ids = fields.Many2many('account.account', 'account_account_financial_report', 'report_line_id', 'account_id', 'Accounts')
    account_report_id = fields.Many2one('account.financial.report', 'Report Value')
    sign = fields.Selection([('-1', 'Reverse balance sign'), ('1', 'Preserve balance sign')], 'Sign on Reports', required=True, default='1')
    display_detail = fields.Selection([
        ('no_detail', 'No detail'),
        ('detail_flat', 'Display children flat'),
        ('detail_with_hierarchy', 'Display children with hierarchy')
    ], 'Display details', default='detail_flat')
    style_overwrite = fields.Selection([
        ('0', 'Automatic formatting'),
        ('1', 'Main Title 1 (bold, underlined)'),
        ('2', 'Title 2 (bold)'),
        ('3', 'Title 3 (bold, smaller)'),
        ('4', 'Normal Text'),
        ('5', 'Italic Text (smaller)'),
        ('6', 'Smallest Text'),
    ], 'Financial Report Style', default='0')
    
    # Options de filtrage
    filter_date_range = fields.Boolean('Date Range Filter', default=True)
    filter_unfold_all = fields.Boolean('Unfold All Filter', default=True)
    filter_journals = fields.Boolean('Journals Filter', default=True)
    filter_multi_company = fields.Boolean('Multi-company Filter', default=True)
    filter_analytic_groupby = fields.Boolean('Analytic Groupby Filter')
    filter_partner = fields.Boolean('Partner Filter')
    filter_account_type = fields.Boolean('Account Type Filter')
    filter_comparison = fields.Boolean('Comparison Filter')

    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        """Calcule le niveau hiérarchique de chaque ligne de rapport"""
        for report in self:
            level = 0
            parent = report.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            report.level = level


class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Reports'
    _inherit = 'account.report'

    def _get_report_values(self, docids, data=None):
        """Génère les valeurs pour le rapport PDF"""
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}
        obj_account = self.env['account.financial.report'].browse(data['form']['account_report_id'][0])
        
        # Récupération des lignes du rapport
        lines = self._get_financial_report_pdf_lines(data.get('form', {}))
        
        return {
            'doc_ids': docids,
            'doc_model': 'account.financial.report',
            'data': data['form'],
            'docs': obj_account,
            'lines': lines,
        }

    def _get_financial_report_pdf_lines(self, options):
        """Génère les lignes pour le rapport PDF"""
        lines = []
        report_type = options.get('report_type', 'bs')
        
        # Récupération des données selon le type de rapport
        if report_type == 'bs':
            lines = self._get_balance_sheet_lines(options)
        elif report_type == 'pl':
            lines = self._get_profit_loss_lines(options)
        elif report_type == 'cf':
            lines = self._get_cash_flow_lines(options)
        elif report_type == 'gl':
            lines = self._get_general_ledger_lines(options)
        elif report_type == 'ptl':
            lines = self._get_partner_ledger_lines(options)
        elif report_type == 'tb':
            lines = self._get_trial_balance_lines(options)
        elif report_type == 'ar':
            lines = self._get_aged_receivable_lines(options)
        elif report_type == 'ap':
            lines = self._get_aged_payable_lines(options)
        
        return lines

    def _get_balance_sheet_lines(self, options):
        """Génère les lignes du bilan"""
        lines = []
        accounts = self.env['account.account'].search([
            ('company_id', 'in', self.env.companies.ids),
            ('internal_type', 'in', ['asset', 'liability', 'equity'])
        ])
        
        for account in accounts:
            # Calcul des soldes
            domain = self._get_domain(account, options)
            balance = sum(self.env['account.move.line'].search(domain).mapped('balance'))
            
            # Création de la ligne
            lines.append({
                'id': account.id,
                'name': account.name,
                'code': account.code,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
                'columns': [
                    {'name': balance, 'class': 'number'},
                ],
            })
            
        return lines

    def _get_domain(self, account, options):
        """Construit le domaine de recherche selon les options"""
        domain = [
            ('account_id', '=', account.id),
            ('company_id', 'in', self.env.companies.ids),
        ]
        
        # Filtre de date
        if options.get('date'):
            domain += [
                ('date', '>=', options['date'].get('date_from')),
                ('date', '<=', options['date'].get('date_to')),
            ]
            
        # Filtre des journaux
        if options.get('journals'):
            domain += [('journal_id', 'in', options['journals'])]
            
        return domain

    def get_xlsx(self, options, response=None):
        """Export Excel utilisant les fonctionnalités standard d'Odoo"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._description)

        # Styles
        title_style = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'border': 1,
            'bg_color': '#F2F2F2'
        })
        header_style = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
            'bg_color': '#D9D9D9'
        })
        cell_style = workbook.add_format({
            'align': 'left',
            'border': 1
        })
        number_style = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00'
        })

        # En-tête
        sheet.merge_range('A1:D1', self._description, title_style)
        headers = ['Code', 'Account', 'Debit', 'Credit', 'Balance']
        for col, header in enumerate(headers):
            sheet.write(1, col, header, header_style)

        # Données
        lines = self._get_financial_report_pdf_lines(options)
        row = 2
        for line in lines:
            sheet.write(row, 0, line.get('code', ''), cell_style)
            sheet.write(row, 1, line.get('name', ''), cell_style)
            for col, column in enumerate(line.get('columns', [])):
                sheet.write(row, col + 2, column.get('name', 0), number_style)
            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response
