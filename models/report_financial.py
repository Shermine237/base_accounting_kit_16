# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountReport(models.Model):
    _inherit = 'account.report'

    @api.model
    def _get_financial_report_pdf_lines(self, options):
        """Génère les lignes pour le rapport PDF"""
        self.ensure_one()
        lines = []
        
        # Contexte pour les dates et filtres
        context = options.get('context', {})
        comparison_context = options.get('comparison_context', {})
        
        # Récupération des lignes via les méthodes standard
        lines = self._get_financial_report_lines(options)
        
        # Ajout des données de comparaison si activé
        if comparison_context:
            for line in lines:
                line['comparison'] = self._get_balance_columns(
                    line.get('account_type'),
                    comparison_context
                )
                
        return lines

    def _get_financial_report_lines(self, options):
        """Méthode standard pour générer les lignes du rapport"""
        self.ensure_one()
        lines = []
        
        # Logique pour générer les lignes selon le type de rapport
        if self.name == 'Balance Sheet':
            lines.extend(self._get_balance_sheet_lines(options))
        elif self.name == 'Profit and Loss':
            lines.extend(self._get_profit_loss_lines(options))
        elif self.name == 'Cash Flow Statement':
            lines.extend(self._get_cash_flow_lines(options))
        
        return lines

    def _get_balance_sheet_lines(self, options):
        """Génère les lignes pour le bilan"""
        lines = []
        # Actifs
        assets = {
            'name': 'Assets',
            'level': 1,
            'columns': self._get_balance_columns('asset', options),
        }
        lines.append(assets)
        
        # Passifs
        liabilities = {
            'name': 'Liabilities',
            'level': 1,
            'columns': self._get_balance_columns('liability', options),
        }
        lines.append(liabilities)
        
        return lines

    def _get_profit_loss_lines(self, options):
        """Génère les lignes pour le compte de résultat"""
        lines = []
        # Revenus
        income = {
            'name': 'Income',
            'level': 1,
            'columns': self._get_balance_columns('income', options),
        }
        lines.append(income)
        
        # Dépenses
        expense = {
            'name': 'Expenses',
            'level': 1,
            'columns': self._get_balance_columns('expense', options),
        }
        lines.append(expense)
        
        return lines

    def _get_cash_flow_lines(self, options):
        """Génère les lignes pour le tableau des flux de trésorerie"""
        lines = []
        # Flux opérationnels
        operating = {
            'name': 'Operating Activities',
            'level': 1,
            'columns': self._get_cash_flow_columns('operating', options),
        }
        lines.append(operating)
        
        # Flux d'investissement
        investing = {
            'name': 'Investing Activities',
            'level': 1,
            'columns': self._get_cash_flow_columns('investing', options),
        }
        lines.append(investing)
        
        # Flux de financement
        financing = {
            'name': 'Financing Activities',
            'level': 1,
            'columns': self._get_cash_flow_columns('financing', options),
        }
        lines.append(financing)
        
        return lines

    def _get_balance_columns(self, account_type, options):
        """Calcule les colonnes de solde pour un type de compte donné"""
        self.ensure_one()
        columns = []
        
        # Colonnes de débit/crédit si activées
        if options.get('debit_credit'):
            debit, credit = self._compute_account_balance(account_type, options)
            columns.extend([
                {'name': debit, 'no_format': debit, 'class': 'number'},
                {'name': credit, 'no_format': credit, 'class': 'number'},
            ])
        
        # Solde de la période courante
        balance = self._compute_account_balance(account_type, options, balance_only=True)
        columns.append({
            'name': balance,
            'no_format': balance,
            'class': 'number',
        })
        
        return columns

    def _get_cash_flow_columns(self, activity_type, options):
        """Calcule les colonnes pour le tableau des flux de trésorerie"""
        self.ensure_one()
        columns = []
        
        # Montant de la période courante
        amount = self._compute_cash_flow(activity_type, options)
        columns.append({
            'name': amount,
            'no_format': amount,
            'class': 'number',
        })
        
        return columns

    def _compute_account_balance(self, account_type, options, balance_only=False):
        """Calcule le solde pour un type de compte et une période donnés"""
        domain = [
            ('account_id.internal_type', '=', account_type),
        ]
        
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
            
        if options.get('journal_ids'):
            domain.append(('journal_id', 'in', options['journal_ids']))
            
        if options.get('state') == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
            
        aml = self.env['account.move.line'].search(domain)
        
        if balance_only:
            return sum(aml.mapped('balance'))
        else:
            return sum(aml.mapped('debit')), sum(aml.mapped('credit'))

    def _compute_cash_flow(self, activity_type, options):
        """Calcule le montant des flux de trésorerie pour un type d'activité et une période donnés"""
        domain = []
        
        if activity_type == 'operating':
            domain.append(('account_id.internal_type', 'in', ['receivable', 'payable']))
        elif activity_type == 'investing':
            domain.append(('account_id.internal_type', '=', 'other'))
        elif activity_type == 'financing':
            domain.append(('account_id.internal_type', '=', 'other'))
            
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
            
        if options.get('state') == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
            
        amount = sum(self.env['account.move.line'].search(domain).mapped('balance'))
        return amount


class ReportFinancial(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_financial'
    _description = 'Financial Reports'
    _inherit = 'report.report_xlsx.abstract'

    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account):
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial balances
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'),
                date_to=False,
                initial_bal=True
            )._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            
            sql = ("""
                SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 
                       NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, 
                       COALESCE(SUM(l.debit),0.0) AS debit, 
                       COALESCE(SUM(l.credit),0.0) AS credit, 
                       COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, 
                       '' AS lpartner_id,
                       '' AS move_name, '' AS mmove_id, '' AS currency_code,
                       NULL AS currency_id,
                       '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,
                       '' AS partner_name
                FROM account_move_line l
                LEFT JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN account_move i ON (m.id =i.id)
                WHERE l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = {'date': 'l.date, l.move_id', 'journal_partner': 'j.code, p.name, l.move_id'}
        sql_sort_by = sql_sort.get(sortby) or sql_sort['date']
        sql = ("""
            SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode,
                   l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname,
                   COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit,
                   COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,
                   m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name
            FROM account_move_line l
            JOIN account_move m ON (l.move_id=m.id)
            LEFT JOIN res_currency c ON (l.currency_id=c.id)
            LEFT JOIN res_partner p ON (l.partner_id=p.id)
            JOIN account_journal j ON (l.journal_id=j.id)
            JOIN account_account acc ON (l.account_id = acc.id)
            WHERE l.account_id IN %s """ + self.env.context.get('compute_sql_where', '') + """
            GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name,
                     c.symbol, p.name ORDER BY """ + sql_sort_by)
        params = (tuple(accounts.ids),) + tuple(self.env.context.get('compute_params', []))
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = {'code': account.code, 'name': account.name, 'debit': 0.0, 'credit': 0.0, 'balance': 0.0,
                   'type': account.internal_type, 'level': account.level, 'currency_id': currency.id}
            for line in move_lines.get(account.id):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        account_res = self.with_context(data['form'].get('used_context'))._get_account_move_entry(accounts, True, 'date', display_account)

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': datetime,
            'Accounts': account_res,
        }

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True,
                                     'align': 'center', 'bold': True, 'bg_color': '#E0E0E0'})
        format2 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        format3 = workbook.add_format({'font_size': 12, 'align': 'right', 'bold': True})
        format4 = workbook.add_format({'font_size': 10, 'align': 'left'})
        format5 = workbook.add_format({'font_size': 10, 'align': 'right'})
        format6 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format7 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format8 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True})

        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 40)
        sheet.set_column('C:E', 15)

        year = data['form']['date_from'].year
        sheet.merge_range('A1:E1', f'Financial Report {year}', format1)

        y_offset = 2
        if data['form']['enable_filter']:
            y_offset = 3
            sheet.write(y_offset, 0, '', format2)
            sheet.write(y_offset, 1, 'Balance', format2)
            sheet.write(y_offset, 2, data['form']['label_filter'], format2)

        # Report headers
        sheet.write(y_offset + 1, 0, _('Code'), format2)
        sheet.write(y_offset + 1, 1, _('Account'), format2)
        sheet.write(y_offset + 1, 2, _('Debit'), format3)
        sheet.write(y_offset + 1, 3, _('Credit'), format3)
        sheet.write(y_offset + 1, 4, _('Balance'), format3)

        accounts = self.env['account.account'].search([])
        account_res = self.with_context(data['form'].get('used_context'))._get_account_move_entry(
            accounts, True, 'date', data['form']['display_account'])

        if account_res:
            for account in account_res:
                y_offset += 1
                sheet.write(y_offset, 0, account['code'], format4)
                sheet.write(y_offset, 1, account['name'], format4)
                sheet.write(y_offset, 2, account['debit'], format5)
                sheet.write(y_offset, 3, account['credit'], format5)
                sheet.write(y_offset, 4, account['balance'], format5)
