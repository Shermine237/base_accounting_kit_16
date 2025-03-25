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

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportJournalAudit(models.AbstractModel):
    _name = 'report.base_accounting_kit_16.report_journal_audit'
    _description = 'Journal Audit Report'

    def lines(self, target_move, journal_ids, sort_selection, data):
        if isinstance(journal_ids, int):
            journal_ids = [journal_ids]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']

        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_ids)] + query_get_clause[1]
        query = 'SELECT "account_move_line".id FROM ' + query_get_clause[0] + \
                ', account_move am, account_account acc ' \
                'WHERE "account_move_line".account_id = acc.id ' \
                'AND "account_move_line".move_id=am.id ' \
                'AND am.state IN %s ' \
                'AND "account_move_line".journal_id IN %s ' \
                'AND ' + query_get_clause[2] + ' ' \
                'ORDER BY '
        if sort_selection == 'date':
            query += '"account_move_line".date'
        else:
            query += 'am.name'
        query += ', "account_move_line".move_id, acc.code'

        self.env.cr.execute(query, params)
        ids = (x[0] for x in self.env.cr.fetchall())
        return self.env['account.move.line'].browse(ids)

    def _sum_debit(self, data, journal_id):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted']

        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_id)] + query_get_clause[1]
        query = 'SELECT SUM(debit) FROM ' + query_get_clause[0] + \
                ', account_move am ' \
                'WHERE "account_move_line".move_id=am.id AND am.state IN %s ' \
                'AND "account_move_line".journal_id IN %s AND ' + \
                query_get_clause[2] + ' '

        self.env.cr.execute(query, params)
        return self.env.cr.fetchone()[0] or 0.0

    def _sum_credit(self, data, journal_id):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted']

        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_id)] + query_get_clause[1]
        query = 'SELECT SUM(credit) FROM ' + query_get_clause[0] + \
                ', account_move am ' \
                'WHERE "account_move_line".move_id=am.id AND am.state IN %s ' \
                'AND "account_move_line".journal_id IN %s AND ' + \
                query_get_clause[2] + ' '

        self.env.cr.execute(query, params)
        return self.env.cr.fetchone()[0] or 0.0

    def _get_taxes(self, data, journal_id):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted']

        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_id)] + query_get_clause[1]
        query = 'SELECT COALESCE(SUM("account_move_line".debit-' \
                '"account_move_line".credit), 0) as balance, ' \
                'COALESCE(SUM(debit),0) as debit, ' \
                'COALESCE(SUM(credit), 0) as credit, tax.id ' \
                'FROM ' + query_get_clause[0] + \
                ', account_move am, ' \
                'account_tax tax, account_tax_account_tag tag ' \
                'WHERE "account_move_line".move_id=am.id ' \
                'AND am.state IN %s ' \
                'AND "account_move_line".journal_id IN %s ' \
                'AND ' + query_get_clause[2] + ' ' \
                'AND tax.id = tag.account_tax_id ' \
                'AND tag.account_account_tag_id IN ' \
                '("account_move_line".tax_tag_ids) ' \
                'GROUP BY tax.id'

        self.env.cr.execute(query, params)
        ids = {}
        for row in self.env.cr.dictfetchall():
            ids[row['id']] = {
                'id': row['id'],
                'balance': row['balance'],
                'debit': row['debit'],
                'credit': row['credit'],
            }
        return ids

    def _get_tax_amount(self, journal_id, data, tax_id):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted']
        res = {}
        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_id), tax_id] + \
                 query_get_clause[1]
        query = 'SELECT COALESCE(SUM("account_move_line".debit-' \
                '"account_move_line".credit), 0) as balance, ' \
                'COALESCE(SUM(debit),0) as debit, ' \
                'COALESCE(SUM(credit), 0) as credit ' \
                'FROM ' + query_get_clause[0] + \
                ', account_move am, ' \
                'account_tax tax, account_tax_account_tag tag ' \
                'WHERE "account_move_line".move_id=am.id ' \
                'AND am.state IN %s ' \
                'AND "account_move_line".journal_id IN %s ' \
                'AND tax.id = %s ' \
                'AND ' + query_get_clause[2] + ' ' \
                'AND tag.account_tax_id = tax.id ' \
                'AND tag.account_account_tag_id IN ' \
                '("account_move_line".tax_tag_ids) '

        self.env.cr.execute(query, params)
        res = self.env.cr.fetchone()
        if res:
            if journal_id.type == 'sale':
                # sales operation are credits
                res = res[0] * -1, res[1] * -1, res[2] * -1
            return res
        return 0.0, 0.0, 0.0

    def _get_tax_base_amount(self, journal_id, data, tax_id):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted']
        query_get_clause = self._get_query_get_clause(data)
        params = [tuple(move_state), tuple(journal_id), tax_id] + \
                 query_get_clause[1]
        query = 'SELECT COALESCE(SUM("account_move_line".debit-' \
                '"account_move_line".credit), 0) as balance, ' \
                'COALESCE(SUM(debit),0) as debit, ' \
                'COALESCE(SUM(credit), 0) as credit ' \
                'FROM ' + query_get_clause[0] + \
                ', account_move am, ' \
                'account_tax tax, account_tax_repartition_line arl ' \
                'WHERE "account_move_line".move_id=am.id ' \
                'AND am.state IN %s ' \
                'AND "account_move_line".journal_id IN %s ' \
                'AND tax.id = %s ' \
                'AND ' + query_get_clause[2] + ' ' \
                'AND arl.account_tax_id = tax.id ' \
                'AND arl.repartition_type = \'base\' ' \
                'AND "account_move_line".tax_repartition_line_id = arl.id ' \

        self.env.cr.execute(query, params)
        res = self.env.cr.fetchone()
        if res:
            if journal_id.type == 'sale':
                # sales operation are credits
                res = res[0] * -1, res[1] * -1, res[2] * -1
            return res
        return 0.0, 0.0, 0.0

    def _get_query_get_clause(self, data):
        """
        Adaptation pour Odoo 16 qui n'utilise plus _query_get
        """
        # Récupération des filtres du contexte
        context = data['form'].get('used_context', {})
        domain = []
        
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
        
        return tables, where_params, where_clause

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        target_move = data['form'].get('target_move', 'all')
        sort_selection = data['form'].get('sort_selection', 'date')

        res = {}
        for journal in data['form']['journal_ids']:
            res[journal] = self.with_context(
                data['form'].get('used_context', {})).lines(
                target_move, journal, sort_selection, data)
        return {
            'doc_ids': data['form']['journal_ids'],
            'doc_model': self.env['account.journal'],
            'data': data,
            'docs': self.env['account.journal'].browse(
                data['form']['journal_ids']),
            'time': self._get_tax_amount,
            'base_amount': self._get_tax_base_amount,
            'lines': res,
            'sum_credit': self._sum_credit,
            'sum_debit': self._sum_debit,
            'get_taxes': self._get_taxes,
            'company_id': self.env.company,
        }
