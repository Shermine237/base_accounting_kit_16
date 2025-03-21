# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
import io
import json
import xlsxwriter
from datetime import datetime


class AccountFinancialReport(models.Model):
    _name = 'account.financial.report'
    _description = 'Financial Report'
    _order = 'sequence, id'
    _parent_store = True
    _parent_name = "parent_id"
    _rec_name = 'name'

    name = fields.Char('Report Name', required=True, translate=True)
    parent_id = fields.Many2one('account.financial.report', 'Parent', ondelete='cascade', index=True)
    parent_path = fields.Char(index=True, unaccent=False)
    children_ids = fields.One2many('account.financial.report', 'parent_id', 'Children')
    sequence = fields.Integer('Sequence')
    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        recursive=True,
        store=True,
        compute_sudo=True,
        depends=['parent_id']
    )
    
    # Type de rapport selon les standards Odoo 16
    type = fields.Selection([
        ('sum', 'Summary'),  # Pour les états financiers
        ('accounts', 'Accounts'),  # Pour les grands livres
        ('bs', 'Balance Sheet'),
        ('pl', 'Profit and Loss'),
        ('cf', 'Cash Flow Statement'),
        ('gl', 'General Ledger'),
        ('ptl', 'Partner Ledger'),
        ('tb', 'Trial Balance'),
        ('ar', 'Aged Receivable'),
        ('ap', 'Aged Payable'),
    ], 'Report Type', default='sum')
    
    # Relations avec les comptes
    account_ids = fields.Many2many(
        'account.account',
        'account_account_financial_report',
        'report_line_id',
        'account_id',
        string='Accounts'
    )
    account_report_id = fields.Many2one(
        'account.financial.report',
        string='Report Value',
        help="Used for 'Report Value' type reports"
    )
    
    # Configuration d'affichage selon les standards Odoo 16
    sign = fields.Selection([
        ('-1', 'Reverse balance sign'),
        ('1', 'Preserve balance sign')
    ], 'Sign on Reports', required=True, default='1')
    
    display_detail = fields.Selection([
        ('no_detail', 'No detail'),
        ('detail_flat', 'Display children flat'),
        ('detail_with_hierarchy', 'Display children with hierarchy')
    ], 'Display details', default='detail_with_hierarchy')
    
    style_overwrite = fields.Selection([
        ('0', 'Automatic formatting'),
        ('1', 'Main Title 1 (bold, underlined)'),
        ('2', 'Title 2 (bold)'),
        ('3', 'Title 3 (bold, smaller)'),
        ('4', 'Normal Text'),
        ('5', 'Italic Text (smaller)'),
        ('6', 'Smallest Text'),
    ], 'Financial Report Style', default='4')
    
    # Options de base pour les rapports
    show_debit_credit = fields.Boolean('Show Debit/Credit Columns')
    show_balance = fields.Boolean('Show Balance', default=True)
    enable_filter = fields.Boolean('Enable Comparison')
    show_hierarchy = fields.Boolean('Show Hierarchy', default=True)
    show_journal = fields.Boolean('Show Journal Filter')
    show_partner = fields.Boolean('Show Partner Filter')
    show_analytic = fields.Boolean('Show Analytic Filter')
    
    @api.depends('parent_id')
    def _compute_level(self):
        """Calcule le niveau hiérarchique de manière récursive"""
        for report in self:
            level = 0
            parent = report.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            report.level = level
            
    def _get_children_by_order(self):
        """Retourne les enfants triés par séquence"""
        return self.search([('id', 'child_of', self.ids)], order='sequence, name')
        
    @api.onchange('type')
    def _onchange_type(self):
        """Met à jour les filtres et le style en fonction du type de rapport"""
        if self.type in ['bs', 'pl', 'cf']:
            self.display_detail = 'detail_with_hierarchy'
            self.style_overwrite = '1'
            self.analytic_groupby = self.type == 'pl'
        elif self.type in ['gl', 'tb']:
            self.display_detail = 'detail_flat'
            self.style_overwrite = '4'
            self.account_type = True
            self.comparison = True
        elif self.type in ['ptl', 'ar', 'ap']:
            self.display_detail = 'detail_flat'
            self.style_overwrite = '4'
            self.partner = True

    def get_xlsx(self, options, response=None):
        """Génère le rapport Excel selon les standards Odoo 16"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.name[:31])

        # Styles
        title_style = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
        })
        header_style = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
            'bg_color': '#D3D3D3',
        })
        cell_style = workbook.add_format({
            'align': 'left',
            'border': 1,
        })
        number_style = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00',
        })

        # En-tête
        sheet.merge_range('A1:E1', self.name, title_style)
        headers = ['Code', 'Account', 'Debit', 'Credit', 'Balance']
        for col, header in enumerate(headers):
            sheet.write(1, col, header, header_style)

        # Données
        lines = self._get_report_lines(options)
        row = 2
        for line in lines:
            sheet.write(row, 0, line.get('code', ''), cell_style)
            sheet.write(row, 1, line.get('name', ''), cell_style)
            sheet.write(row, 2, line.get('debit', 0.0), number_style)
            sheet.write(row, 3, line.get('credit', 0.0), number_style)
            sheet.write(row, 4, line.get('balance', 0.0), number_style)
            row += 1

        # Ajustement des colonnes
        for col in range(5):
            sheet.set_column(col, col, 15)

        workbook.close()
        output.seek(0)
        return output.read()

    def _get_report_lines(self, options):
        """Génère les lignes du rapport selon le type"""
        self.ensure_one()
        lines = []
        
        if self.type in ['bs', 'pl', 'cf']:
            lines = self._get_financial_lines(options)
        elif self.type in ['gl', 'tb']:
            lines = self._get_ledger_lines(options)
        elif self.type in ['ptl', 'ar', 'ap']:
            lines = self._get_partner_lines(options)
            
        return lines

    def _get_financial_lines(self, options):
        """Génère les lignes pour les états financiers"""
        self.ensure_one()
        lines = []
        
        # Construction du domaine de base
        domain = self._get_domain(options)
        
        if self.account_ids:
            # Si des comptes sont directement liés
            accounts = self.account_ids
        else:
            # Sinon, utiliser les comptes selon le type
            account_types = {
                'bs': ['asset', 'liability', 'equity'],
                'pl': ['income', 'expense'],
                'cf': ['asset', 'liability', 'income', 'expense'],
            }
            domain += [('account_type', 'in', account_types.get(self.type, []))]
            accounts = self.env['account.account'].search(domain)
            
        # Calcul des soldes
        for account in accounts:
            balance = sum(account.mapped('balance'))
            if float_is_zero(balance, precision_digits=2) and not options.get('show_zero_balance'):
                continue
                
            lines.append({
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'level': self.level,
                'debit': sum(account.mapped('debit')),
                'credit': sum(account.mapped('credit')),
                'balance': balance * (int(self.sign) or 1),
            })
            
        return lines

    def _get_ledger_lines(self, options):
        """Génère les lignes pour les grands livres"""
        self.ensure_one()
        lines = []
        
        # Construction du domaine
        domain = self._get_domain(options)
        if self.type == 'gl':
            # Pour le grand livre général
            if options.get('account_type'):
                domain += [('account_id.account_type', 'in', options['account_type'])]
        elif self.type == 'tb':
            # Pour la balance
            if options.get('account_type'):
                domain += [('account_id.account_type', 'in', options['account_type'])]
                
        # Récupération des écritures
        move_lines = self.env['account.move.line'].search(domain)
        
        # Regroupement par compte
        accounts = {}
        for line in move_lines:
            if line.account_id not in accounts:
                accounts[line.account_id] = {
                    'debit': 0.0,
                    'credit': 0.0,
                    'balance': 0.0,
                }
            accounts[line.account_id]['debit'] += line.debit
            accounts[line.account_id]['credit'] += line.credit
            accounts[line.account_id]['balance'] += line.balance
            
        # Génération des lignes
        for account, values in accounts.items():
            if float_is_zero(values['balance'], precision_digits=2) and not options.get('show_zero_balance'):
                continue
                
            lines.append({
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'level': self.level,
                'debit': values['debit'],
                'credit': values['credit'],
                'balance': values['balance'] * (int(self.sign) or 1),
            })
            
        return lines

    def _get_partner_lines(self, options):
        """Génère les lignes pour les rapports partenaires"""
        self.ensure_one()
        lines = []
        
        # Construction du domaine
        domain = self._get_domain(options)
        if self.type in ['ar', 'ap']:
            # Pour les balances âgées
            account_types = ['asset_receivable'] if self.type == 'ar' else ['liability_payable']
            domain += [('account_id.account_type', 'in', account_types)]
            
        # Filtre sur les partenaires
        if options.get('partner_ids'):
            domain += [('partner_id', 'in', options['partner_ids'])]
            
        # Récupération des écritures
        move_lines = self.env['account.move.line'].search(domain)
        
        # Regroupement par partenaire
        partners = {}
        for line in move_lines:
            if not line.partner_id:
                continue
                
            if line.partner_id not in partners:
                partners[line.partner_id] = {
                    'debit': 0.0,
                    'credit': 0.0,
                    'balance': 0.0,
                }
            partners[line.partner_id]['debit'] += line.debit
            partners[line.partner_id]['credit'] += line.credit
            partners[line.partner_id]['balance'] += line.balance
            
        # Génération des lignes
        for partner, values in partners.items():
            if float_is_zero(values['balance'], precision_digits=2) and not options.get('show_zero_balance'):
                continue
                
            lines.append({
                'id': partner.id,
                'code': partner.ref or '',
                'name': partner.name,
                'level': self.level,
                'debit': values['debit'],
                'credit': values['credit'],
                'balance': values['balance'] * (int(self.sign) or 1),
            })
            
        return lines

    def _get_domain(self, options):
        """Construit le domaine de recherche selon les options"""
        self.ensure_one()
        domain = []
        
        # Filtre de date
        if options.get('date'):
            domain += [
                ('date', '>=', options['date']['date_from']),
                ('date', '<=', options['date']['date_to']),
            ]
            
        # Filtre des journaux
        if options.get('journals'):
            domain += [('journal_id', 'in', options['journals'])]
            
        # Filtre multi-société
        if not options.get('multi_company'):
            domain += [('company_id', '=', self.env.company.id)]
            
        return domain


class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Reports'

    def _get_report_values(self, docids, data=None):
        """Génère les valeurs pour le rapport PDF"""
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        report = self.env['account.financial.report'].browse(data['form']['account_report_id'])
        return {
            'doc_ids': docids,
            'doc_model': 'account.financial.report',
            'data': data['form'],
            'docs': report,
            'get_account_lines': self._get_account_lines,
        }
