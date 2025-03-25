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

import time

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_partnerledger'
    _description = 'Partner Ledger Report'

    def _lines(self, data, partner):
        full_account = []
        currency = self.env['res.currency']
        
        # Adaptation pour Odoo 16 qui n'utilise plus _query_get
        domain = []
        context = data['form'].get('used_context', {})
        
        if context.get('date_from'):
            domain.append(('date', '>=', context['date_from']))
        if context.get('date_to'):
            domain.append(('date', '<=', context['date_to']))
        if context.get('journal_ids'):
            domain.append(('journal_id', 'in', context['journal_ids']))
        if context.get('company_id'):
            domain.append(('company_id', '=', context['company_id']))
        if context.get('state') == 'posted':
            domain.append(('parent_state', '=', 'posted'))
        
        # Construction de la requête SQL
        query = self.env['account.move.line']._where_calc(domain)
        tables, where_clause, where_params = query.get_sql()
        
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        params = [partner.id, tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + where_params
        query = """
            SELECT "account_move_line".id, "account_move_line".date, j.code, acc.code as a_code, acc.name as a_name, "account_move_line".ref, m.name as move_name, "account_move_line".name, "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency,"account_move_line".currency_id, c.symbol AS currency_code
            FROM """ + tables + """
            LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
            LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
            LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
            LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
            WHERE "account_move_line".partner_id = %s
                AND m.state IN %s
                AND "account_move_line".account_id IN %s AND """ + where_clause + reconcile_clause + """
                ORDER BY "account_move_line".date"""
        self.env.cr.execute(query, params)
        res = self.env.cr.dictfetchall()
        sum = 0.0
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        for r in res:
            r['date'] = r['date']
            r['displayed_name'] = r['move_name']
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            r['currency_id'] = currency.browse(r.get('currency_id'))
            full_account.append(r)
        return full_account

    def _sum_partner(self, data, partner, field):
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        result = 0.0
        
        # Adaptation pour Odoo 16 qui n'utilise plus _query_get
        domain = []
        context = data['form'].get('used_context', {})
        
        if context.get('date_from'):
            domain.append(('date', '>=', context['date_from']))
        if context.get('date_to'):
            domain.append(('date', '<=', context['date_to']))
        if context.get('journal_ids'):
            domain.append(('journal_id', 'in', context['journal_ids']))
        if context.get('company_id'):
            domain.append(('company_id', '=', context['company_id']))
        if context.get('state') == 'posted':
            domain.append(('parent_state', '=', 'posted'))
        
        # Construction de la requête SQL
        query = self.env['account.move.line']._where_calc(domain)
        tables, where_clause, where_params = query.get_sql()
        
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '

        params = [partner.id, tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + where_params
        query = """SELECT sum(""" + field + """)
                FROM """ + tables + """
                LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
                WHERE "account_move_line".partner_id = %s
                    AND m.state IN %s
                    AND "account_move_line".account_id IN %s
                    AND """ + where_clause + reconcile_clause
        self.env.cr.execute(query, params)
        res = self.env.cr.fetchone()
        if res and res[0]:
            result = res[0]
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        data['computed'] = {}

        obj_partner = self.env['res.partner']
        query_get_data = self._get_query_data(data['form'])
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection')
        if result_selection == 'customer':
            data['computed']['account_ids'] = query_get_data[1]
        elif result_selection == 'supplier':
            data['computed']['account_ids'] = query_get_data[2]
        else:
            data['computed']['account_ids'] = query_get_data[0]

        self.env.cr.execute(
            """SELECT a.id
               FROM account_account a
               WHERE a.account_type IN ('asset_receivable', 'liability_payable')
               AND NOT a.deprecated""")
        data['computed']['account_ids'] = [a for (a,) in
                                           self.env.cr.fetchall()]
        params = [tuple(data['computed']['account_ids'])] + query_get_data[3]
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '

        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM account_move_line, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[4] + reconcile_clause
        self.env.cr.execute(query, params)
        partner_ids = [res['partner_id'] for res in
                       self.env.cr.dictfetchall()]
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: x.name)

        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
        }
        
    def _get_query_data(self, form):
        """
        Méthode auxiliaire pour construire les requêtes SQL
        """
        # Adaptation pour Odoo 16 qui n'utilise plus _query_get
        domain = []
        context = form.get('used_context', {})
        
        if context.get('date_from'):
            domain.append(('date', '>=', context['date_from']))
        if context.get('date_to'):
            domain.append(('date', '<=', context['date_to']))
        if context.get('journal_ids'):
            domain.append(('journal_id', 'in', context['journal_ids']))
        if context.get('company_id'):
            domain.append(('company_id', '=', context['company_id']))
        if context.get('state') == 'posted':
            domain.append(('parent_state', '=', 'posted'))
        
        # Construction de la requête SQL
        query = self.env['account.move.line']._where_calc(domain)
        tables, where_clause, where_params = query.get_sql()
        
        # Comptes clients (receivable) - Dans Odoo 16, account_type remplace internal_type
        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.account_type = 'asset_receivable'
            AND NOT a.deprecated""")
        customer_accounts = [a for (a,) in self.env.cr.fetchall()]
        
        # Comptes fournisseurs (payable) - Dans Odoo 16, account_type remplace internal_type
        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.account_type = 'liability_payable'
            AND NOT a.deprecated""")
        supplier_accounts = [a for (a,) in self.env.cr.fetchall()]
        
        # Tous les comptes (receivable + payable)
        all_accounts = customer_accounts + supplier_accounts
        
        return tables, customer_accounts, supplier_accounts, where_params, where_clause
