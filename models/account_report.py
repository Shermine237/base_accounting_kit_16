# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import io
import xlsxwriter

class AccountReport(models.Model):
    _inherit = 'account.report'
    _description = 'Financial Reports'

    # Types de rapports disponibles
    report_type = fields.Selection([
        ('bs', 'Balance Sheet'),
        ('pl', 'Profit and Loss'),
        ('cf', 'Cash Flow Statement'),
        ('gl', 'General Ledger'),
        ('ptl', 'Partner Ledger'),
        ('tb', 'Trial Balance'),
        ('ar', 'Aged Receivable'),
        ('ap', 'Aged Payable')
    ], string='Report Type', required=True)

    # Filtres communs
    filter_date_range = fields.Boolean('Date Range Filter', default=True)
    filter_unfold_all = fields.Boolean('Unfold All', default=True)
    filter_journals = fields.Boolean('Journals Filter', default=True)
    filter_multi_company = fields.Selection([
        ('disabled', 'Disabled'),
        ('companies', 'Companies'),
        ('tax_units', 'Tax Units')
    ], string='Multi-company Filter', default='companies')

    # Filtres spécifiques
    filter_analytic_groupby = fields.Boolean('Analytic Groupby', default=False)
    filter_partner = fields.Boolean('Partner Filter', default=False)
    filter_account_type = fields.Boolean('Account Type Filter', default=False)
    filter_comparison = fields.Boolean('Comparison Filter', default=False)

    @api.onchange('report_type')
    def _onchange_report_type(self):
        """Active les filtres spécifiques selon le type de rapport"""
        self.filter_analytic_groupby = self.report_type == 'pl'
        self.filter_partner = self.report_type in ['ptl', 'ar', 'ap']
        self.filter_account_type = self.report_type in ['pl', 'gl', 'tb']
        self.filter_comparison = self.report_type in ['gl', 'tb']

    def get_xlsx(self, options, response=None):
        """Export Excel utilisant les fonctionnalités standard d'Odoo"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.name)

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

        # En-tête du rapport
        sheet.merge_range('A1:D1', self.name, title_style)
        company = self.env.company
        sheet.write('A2', _('Company:'), header_style)
        sheet.write('B2', company.name, cell_style)
        sheet.write('C2', _('Date:'), header_style)
        sheet.write('D2', fields.Date.today().strftime('%Y-%m-%d'), cell_style)

        # En-tête des colonnes
        headers = ['Code', 'Account', 'Debit', 'Credit', 'Balance']
        for col, header in enumerate(headers):
            sheet.write(3, col, header, header_style)

        # Données du rapport
        lines = self._get_lines(options)
        row = 4
        for line in lines:
            sheet.write(row, 0, line.get('code', ''), cell_style)
            sheet.write(row, 1, line.get('name', ''), cell_style)
            sheet.write(row, 2, line.get('debit', 0.0), number_style)
            sheet.write(row, 3, line.get('credit', 0.0), number_style)
            sheet.write(row, 4, line.get('balance', 0.0), number_style)
            row += 1

        # Ajustement des colonnes
        for col in range(len(headers)):
            sheet.set_column(col, col, 15)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response

    def _get_lines(self, options):
        """Récupère les lignes du rapport selon le type"""
        self.ensure_one()
        
        if self.report_type == 'bs':
            return self._get_balance_sheet_lines(options)
        elif self.report_type == 'pl':
            return self._get_profit_loss_lines(options)
        elif self.report_type == 'cf':
            return self._get_cash_flow_lines(options)
        elif self.report_type == 'gl':
            return self._get_general_ledger_lines(options)
        elif self.report_type == 'ptl':
            return self._get_partner_ledger_lines(options)
        elif self.report_type == 'tb':
            return self._get_trial_balance_lines(options)
        elif self.report_type == 'ar':
            return self._get_aged_receivable_lines(options)
        elif self.report_type == 'ap':
            return self._get_aged_payable_lines(options)
        else:
            raise UserError(_('Report type %s not supported') % self.report_type)

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
            move_lines = self.env['account.move.line'].search(domain)
            debit = sum(move_lines.mapped('debit'))
            credit = sum(move_lines.mapped('credit'))
            balance = debit - credit
            
            # Création de la ligne
            lines.append({
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'debit': debit,
                'credit': credit,
                'balance': balance,
                'level': 1,
                'unfoldable': False,
                'unfolded': True,
            })
            
        return lines
