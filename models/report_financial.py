# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, osv
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.osv import expression
import io
import json
import xlsxwriter
from datetime import datetime


class AccountFinancialReport(models.Model):
    _name = "account.financial.report"
    _description = "Account Report"

    name = fields.Char('Report Name', required=True, translate=True)
    parent_id = fields.Many2one('account.financial.report', 'Parent')
    children_ids = fields.One2many('account.financial.report', 'parent_id', 'Account Report')
    sequence = fields.Integer('Sequence')
    level = fields.Integer(compute='_compute_level', string='Level', store=True, recursive=True)
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
    show_journal = fields.Boolean('Show Journal', default=False)
    show_balance = fields.Boolean('Show Balance', default=True)
    show_debit_credit = fields.Boolean('Show Debit/Credit', default=False)
    show_hierarchy = fields.Boolean('Show Hierarchy', default=False)
    show_partner = fields.Boolean('Show Partner Details', default=False)
    show_analytic = fields.Boolean('Show Analytic', default=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    account_type = fields.Selection([
        ('asset_receivable', 'Receivable'),
        ('asset_cash', 'Bank and Cash'),
        ('asset_current', 'Current Assets'),
        ('asset_non_current', 'Non-current Assets'),
        ('asset_prepayments', 'Prepayments'),
        ('asset_fixed', 'Fixed Assets'),
        ('liability_payable', 'Payable'),
        ('liability_credit_card', 'Credit Card'),
        ('liability_current', 'Current Liabilities'),
        ('liability_non_current', 'Non-current Liabilities'),
        ('equity', 'Equity'),
        ('equity_unaffected', 'Current Year Earnings'),
        ('income', 'Income'),
        ('income_other', 'Other Income'),
        ('expense', 'Expenses'),
        ('expense_depreciation', 'Depreciation'),
        ('expense_direct_cost', 'Cost of Revenue'),
        ('off_balance', 'Off-Balance Sheet')
    ], string='Account Type')
    # Nous n'utilisons pas company_id ici pour éviter les conflits

    def _get_children_by_order(self):
        """Return a recordset of all the children computed recursively in a certain order"""
        res = self
        children = self.search([('parent_id', 'in', self.ids)], order='sequence ASC')
        if children:
            for child in children:
                res += child._get_children_by_order()
        return res

    # Suppression de toutes les méthodes liées à la multi-société pour éviter les conflits

    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        """Compute the level of each report"""
        for report in self:
            level = 0
            parent = report.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            report.level = level

    def _get_account_domain(self):
        """Get the domain for account move lines"""
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id)]
        # Nous n'utilisons pas company_id dans le domaine
        return domain

    def _compute_account_balance(self, accounts):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            domain = self._get_account_domain()
            tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=domain)
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                     " FROM " + tables + \
                     " WHERE account_id IN %s " \
                     + filters + \
                     " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _get_options(self, previous_options=None):
        """Get the options for the report"""
        self.ensure_one()
        options = previous_options or {}
        # Ne pas forcer multi_company à True
        return options

    def _get_domain(self, options):
        """Get the domain for the report"""
        return []

    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}
        obj_report = self.env['account.financial.report'].browse(data['form']['account_report_id'][0])
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        result = self.with_context(data['form']['used_context'])._compute_report_balance(obj_report)
        data['computed']['result'] = result

        return {
            'doc_ids': self.ids,
            'doc_model': 'account.financial.report',
            'docs': obj_report,
            'data': data,
        }

    def _build_contexts(self, data):
        result = {}
        result['date_from'] = data['form'].get('date_from', False)
        result['date_to'] = data['form'].get('date_to', False)
        result['strict_range'] = True if result.get('date_from', False) else False
        return result

    def _compute_report_balance(self, reports):
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id] = self._compute_account_balance(report.account_ids)
                for value in res[report.id].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0)
            elif report.type == 'account_type':
                # it's the sum the account types
                accounts = self.env['account.account'].search([('account_type', 'in', ['asset', 'liability', 'equity', 'income', 'expense'])])
                res[report.id] = self._compute_account_balance(accounts)
                for value in res[report.id].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def _get_report_name(self):
        """Get the report name based on the type"""
        self.ensure_one()
        if self.type == 'sum':
            return _('Financial Report')
        elif self.type == 'accounts':
            return _('Account Balance Report')
        elif self.type == 'account_type':
            return _('Account Type Report')
        else:
            return _('Report Value')

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

    def get_report_values(self, data):
        """Récupère les valeurs pour le rapport"""
        form = data.get('form', {})
        debit_credit = form.get('show_debit_credit', False)
        show_balance = form.get('show_balance', True)
        show_hierarchy = form.get('show_hierarchy', False)
        show_partner = form.get('show_partner', False)
        show_analytic = form.get('show_analytic', False)
        show_journal = form.get('show_journal', False)
        enable_filter = form.get('enable_filter', False)
        comparison_context = form.get('comparison_context', {})
        
        lines = []
        # Logique de génération des lignes du rapport
        if show_hierarchy:
            lines = self._get_hierarchical_lines(data)
        else:
            lines = self._get_flat_lines(data)
            
        if show_partner and self.type in ['ptl', 'ar', 'ap']:
            lines = self._add_partner_details(lines, data)
            
        if show_analytic and self.type in ['pl']:
            lines = self._add_analytic_details(lines, data)
            
        if show_journal:
            lines = self._add_journal_details(lines, data)
            
        return {
            'doc_ids': data.get('ids', []),
            'doc_model': data.get('model', 'account.financial.report'),
            'data': data,
            'docs': self,
            'lines': lines,
            'debit_credit': debit_credit,
            'show_balance': show_balance,
            'show_hierarchy': show_hierarchy,
            'show_partner': show_partner,
            'show_analytic': show_analytic,
            'show_journal': show_journal,
            'enable_filter': enable_filter,
            'comparison_context': comparison_context,
        }
        
    def _get_hierarchical_lines(self, data):
        """Génère les lignes de rapport en mode hiérarchique"""
        lines = []
        form = data.get('form', {})
        comparison_context = form.get('comparison_context', {})
        
        def _get_children_by_order():
            return self.search([('parent_id', '=', self.id)], order='sequence ASC')
            
        def _process_report(report, parent_id=False, level=1):
            currency_table = self.env['res.currency']._get_query_currency_table(self.env.companies.ids)
            MoveLine = self.env['account.move.line']
            domain = self._get_move_line_domain(form)
            
            if report.type == 'accounts':
                # Pour les lignes de type 'accounts', on récupère les écritures comptables
                if report.account_ids:
                    domain.append(('account_id', 'in', report.account_ids.ids))
                query = MoveLine._where_calc(domain)
                tables, where_clause, where_params = query.get_sql()
                
                select = """
                    SELECT 
                        account_move_line.account_id as account_id,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)) as debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)) as credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) as balance
                """
                
                if form.get('show_partner', False):
                    select += """,
                        account_move_line.partner_id as partner_id
                    """
                    
                if form.get('show_analytic', False):
                    select += """,
                        account_move_line.analytic_account_id as analytic_account_id
                    """
                    
                if form.get('show_journal', False):
                    select += """,
                        account_move_line.journal_id as journal_id
                    """
                
                sql = f"""
                    {select}
                    FROM {tables}
                    LEFT JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                    WHERE {where_clause}
                """
                
                group_by = """
                    GROUP BY account_move_line.account_id
                """
                
                if form.get('show_partner', False):
                    group_by += ", account_move_line.partner_id"
                if form.get('show_analytic', False):
                    group_by += ", account_move_line.analytic_account_id"
                if form.get('show_journal', False):
                    group_by += ", account_move_line.journal_id"
                    
                sql += group_by
                
                self.env.cr.execute(sql, where_params)
                results = self.env.cr.dictfetchall()
                
                accounts = self.env['account.account'].browse([x['account_id'] for x in results])
                accounts_by_id = {account.id: account for account in accounts}
                
                for values in results:
                    account = accounts_by_id[values['account_id']]
                    
                    line = {
                        'id': report.id,
                        'name': account.name,
                        'level': level,
                        'parent_id': parent_id,
                        'type': 'account',
                        'account_type': account.account_type,
                        'debit': values['debit'],
                        'credit': values['credit'],
                        'balance': values['balance'],
                        'account_id': account.id,
                        'show_hierarchy': form.get('show_hierarchy', False)
                    }
                    
                    if form.get('show_partner', False) and values.get('partner_id'):
                        partner = self.env['res.partner'].browse(values['partner_id'])
                        line.update({
                            'partner_id': partner.id,
                            'partner_name': partner.name
                        })
                        
                    if form.get('show_analytic', False) and values.get('analytic_account_id'):
                        analytic = self.env['account.analytic.account'].browse(values['analytic_account_id'])
                        line.update({
                            'analytic_id': analytic.id,
                            'analytic_name': analytic.name
                        })
                        
                    if form.get('show_journal', False) and values.get('journal_id'):
                        journal = self.env['account.journal'].browse(values['journal_id'])
                        line.update({
                            'journal_id': journal.id,
                            'journal_name': journal.name
                        })
                        
                    lines.append(line)
                    
            elif report.type == 'account_type':
                # Pour les lignes de type 'account_type', on regroupe par type de compte
                domain.append(('account_id.account_type', '=', report.account_type))
                query = MoveLine._where_calc(domain)
                tables, where_clause, where_params = query.get_sql()
                
                sql = f"""
                    SELECT 
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)) as debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)) as credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) as balance
                    FROM {tables}
                    LEFT JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                    WHERE {where_clause}
                """
                
                self.env.cr.execute(sql, where_params)
                result = self.env.cr.dictfetchone()
                
                if result:
                    lines.append({
                        'id': report.id,
                        'name': report.name,
                        'level': level,
                        'parent_id': parent_id,
                        'type': 'account_type',
                        'account_type': report.account_type,
                        'debit': result['debit'] or 0.0,
                        'credit': result['credit'] or 0.0,
                        'balance': result['balance'] or 0.0,
                        'show_hierarchy': form.get('show_hierarchy', False)
                    })
                    
            elif report.type == 'account_report' and report.account_report_id:
                # Pour les lignes de type 'account_report', on récupère les valeurs du rapport lié
                lines.extend(_process_report(report.account_report_id, report.id, level + 1))
                
            elif report.type == 'sum':
                # Pour les lignes de type 'sum', on calcule la somme des enfants
                lines.append({
                    'id': report.id,
                    'name': report.name,
                    'level': level,
                    'parent_id': parent_id,
                    'type': 'sum',
                    'debit': 0.0,
                    'credit': 0.0,
                    'balance': 0.0,
                    'show_hierarchy': form.get('show_hierarchy', False)
                })
                
                for child in _get_children_by_order():
                    child_lines = _process_report(child, report.id, level + 1)
                    for child_line in child_lines:
                        lines[-1]['debit'] += child_line['debit']
                        lines[-1]['credit'] += child_line['credit']
                        lines[-1]['balance'] += child_line['balance']
                    lines.extend(child_lines)
                    
            return lines
            
        # Début du traitement
        return _process_report(self)

    def _get_flat_lines(self, data):
        """Génère les lignes de rapport en mode plat"""
        lines = self._get_hierarchical_lines(data)
        # En mode plat, on ne garde que les lignes de type 'account'
        return [line for line in lines if line['type'] == 'account']

    def _add_partner_details(self, lines, data):
        """Ajoute les détails des partenaires aux lignes"""
        if not data.get('form', {}).get('show_partner', False):
            return lines
            
        result = []
        MoveLine = self.env['account.move.line']
        Partner = self.env['res.partner']
        
        for line in lines:
            if line.get('account_id'):
                domain = self._get_move_line_domain(data.get('form', {}))
                domain.append(('account_id', '=', line['account_id']))
                
                query = MoveLine._where_calc(domain)
                tables, where_clause, where_params = query.get_sql()
                
                sql = """
                    SELECT DISTINCT partner_id
                    FROM """ + tables + """
                    WHERE """ + where_clause + """
                    AND partner_id IS NOT NULL
                """
                
                self.env.cr.execute(sql, where_params)
                partner_ids = [x[0] for x in self.env.cr.fetchall()]
                partners = Partner.browse(partner_ids)
                
                for partner in partners:
                    domain.append(('partner_id', '=', partner.id))
                    query = MoveLine._where_calc(domain)
                    tables, where_clause, where_params = query.get_sql()
                    
                    sql = """
                        SELECT 
                            SUM(debit) as debit,
                            SUM(credit) as credit,
                            SUM(balance) as balance
                        FROM """ + tables + """
                        WHERE """ + where_clause
                        
                    self.env.cr.execute(sql, where_params)
                    values = self.env.cr.dictfetchone()
                    
                    if values and not float_is_zero(values['balance'], precision_digits=2):
                        result.append({
                            'id': line['id'],
                            'name': partner.name,
                            'level': line['level'] + 1,
                            'parent_id': line['id'],
                            'type': 'partner',
                            'debit': values['debit'],
                            'credit': values['credit'],
                            'balance': values['balance'],
                            'partner_id': partner.id
                        })
                        
            result.append(line)
            
        return result
        
    def _add_analytic_details(self, lines, data):
        """Ajoute les détails analytiques aux lignes"""
        if not data.get('form', {}).get('show_analytic', False):
            return lines
            
        result = []
        MoveLine = self.env['account.move.line']
        AnalyticAccount = self.env['account.analytic.account']
        
        for line in lines:
            if line.get('account_id'):
                domain = self._get_move_line_domain(data.get('form', {}))
                domain.append(('account_id', '=', line['account_id']))
                
                query = MoveLine._where_calc(domain)
                tables, where_clause, where_params = query.get_sql()
                
                sql = """
                    SELECT DISTINCT analytic_account_id
                    FROM """ + tables + """
                    WHERE """ + where_clause + """
                    AND analytic_account_id IS NOT NULL
                """
                
                self.env.cr.execute(sql, where_params)
                analytic_ids = [x[0] for x in self.env.cr.fetchall()]
                analytics = AnalyticAccount.browse(analytic_ids)
                
                for analytic in analytics:
                    domain.append(('analytic_account_id', '=', analytic.id))
                    query = MoveLine._where_calc(domain)
                    tables, where_clause, where_params = query.get_sql()
                    
                    sql = """
                        SELECT 
                            SUM(debit) as debit,
                            SUM(credit) as credit,
                            SUM(balance) as balance
                        FROM """ + tables + """
                        WHERE """ + where_clause
                        
                    self.env.cr.execute(sql, where_params)
                    values = self.env.cr.dictfetchone()
                    
                    if values and not float_is_zero(values['balance'], precision_digits=2):
                        result.append({
                            'id': line['id'],
                            'name': analytic.name,
                            'level': line['level'] + 1,
                            'parent_id': line['id'],
                            'type': 'analytic',
                            'debit': values['debit'],
                            'credit': values['credit'],
                            'balance': values['balance'],
                            'analytic_id': analytic.id
                        })
                        
            result.append(line)
            
        return result
        
    def _add_journal_details(self, lines, data):
        """Ajoute les détails des journaux aux lignes"""
        if not data.get('form', {}).get('show_journal', False):
            return lines
            
        result = []
        MoveLine = self.env['account.move.line']
        Journal = self.env['account.journal']
        
        for line in lines:
            if line.get('account_id'):
                domain = self._get_move_line_domain(data.get('form', {}))
                domain.append(('account_id', '=', line['account_id']))
                
                query = MoveLine._where_calc(domain)
                tables, where_clause, where_params = query.get_sql()
                
                sql = """
                    SELECT DISTINCT journal_id
                    FROM """ + tables + """
                    WHERE """ + where_clause
                    
                self.env.cr.execute(sql, where_params)
                journal_ids = [x[0] for x in self.env.cr.fetchall()]
                journals = Journal.browse(journal_ids)
                
                for journal in journals:
                    domain.append(('journal_id', '=', journal.id))
                    query = MoveLine._where_calc(domain)
                    tables, where_clause, where_params = query.get_sql()
                    
                    sql = """
                        SELECT 
                            SUM(debit) as debit,
                            SUM(credit) as credit,
                            SUM(balance) as balance
                        FROM """ + tables + """
                        WHERE """ + where_clause
                        
                    self.env.cr.execute(sql, where_params)
                    values = self.env.cr.dictfetchone()
                    
                    if values and not float_is_zero(values['balance'], precision_digits=2):
                        result.append({
                            'id': line['id'],
                            'name': journal.name,
                            'level': line['level'] + 1,
                            'parent_id': line['id'],
                            'type': 'journal',
                            'debit': values['debit'],
                            'credit': values['credit'],
                            'balance': values['balance'],
                            'journal_id': journal.id
                        })
                        
            result.append(line)
            
        return result

    def _get_move_line_domain(self, options):
        domain = [('company_id', '=', self.company_id.id)]
        if options.get('date'):
            domain += [
                ('date', '>=', options['date']['date_from']),
                ('date', '<=', options['date']['date_to']),
            ]
        if options.get('journals'):
            domain += [('journal_id', 'in', options['journals'])]
        return domain

    @api.model
    def _get_default_company(self):
        """Get the default company for the report"""
        return self.env.company

    @api.model
    def _get_allowed_company_ids(self):
        """Get the allowed companies for the report"""
        return self.env.companies.ids

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """Override _search to handle company_id domain"""
        return super(AccountFinancialReport, self)._search(args, offset=offset, limit=limit, order=order,
                                                         count=count, access_rights_uid=access_rights_uid)

class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Reports'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        """Génère les valeurs pour le rapport PDF"""
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
            
        report = self.env['account.financial.report'].browse(docids)
        return report.get_report_values(data)
