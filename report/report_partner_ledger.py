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
        
        # Préparation des paramètres pour la requête SQL
        move_state = tuple(data['computed']['move_state'])
        account_ids = tuple(data['computed']['account_ids'])
        
        # Construction de la requête SQL pour trouver les lignes de compte
        query = """
            SELECT "account_move_line".id, "account_move_line".date, j.code, acc.code as a_code, acc.name as a_name, "account_move_line".ref, m.name as move_name, "account_move_line".name, "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency,"account_move_line".currency_id, c.symbol AS currency_code
            FROM account_move_line, account_journal j, account_account acc, account_move m, res_currency c
            WHERE "account_move_line".partner_id = %s
                AND "account_move_line".journal_id = j.id
                AND "account_move_line".account_id = acc.id
                AND m.id = "account_move_line".move_id
                AND "account_move_line".currency_id = c.id
                AND m.state IN %s
                AND "account_move_line".account_id IN %s"""
                
        # Ajout des conditions de filtrage supplémentaires
        params = [partner.id, move_state, account_ids]
        
        # Ajout des conditions de journal, date et état si présentes
        if data['form'].get('journal_ids', []):
            query += " AND \"account_move_line\".journal_id in %s"
            params.append(tuple(data['form']['journal_ids']))
            
        if data['form'].get('target_move') == 'posted':
            query += " AND \"account_move_line\".parent_state = %s"
            params.append('posted')
            
        if data['form'].get('date_from'):
            query += " AND \"account_move_line\".date >= %s"
            params.append(data['form']['date_from'])
            
        if data['form'].get('date_to'):
            query += " AND \"account_move_line\".date <= %s"
            params.append(data['form']['date_to'])
            
        # Clause de réconciliation
        if not data['form']['reconciled']:
            query += " AND \"account_move_line\".full_reconcile_id IS NULL"
            
        query += " ORDER BY \"account_move_line\".date"
        
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
        
        # Préparation des paramètres pour la requête SQL
        move_state = tuple(data['computed']['move_state'])
        account_ids = tuple(data['computed']['account_ids'])
        
        # Construction de la requête SQL pour trouver les sommes
        query = """
            SELECT sum(""" + field + """)
            FROM account_move_line, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id = %s
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s"""
                
        # Ajout des conditions de filtrage supplémentaires
        params = [partner.id, move_state, account_ids]
        
        # Ajout des conditions de journal, date et état si présentes
        if data['form'].get('journal_ids', []):
            query += " AND \"account_move_line\".journal_id in %s"
            params.append(tuple(data['form']['journal_ids']))
            
        if data['form'].get('target_move') == 'posted':
            query += " AND \"account_move_line\".parent_state = %s"
            params.append('posted')
            
        if data['form'].get('date_from'):
            query += " AND \"account_move_line\".date >= %s"
            params.append(data['form']['date_from'])
            
        if data['form'].get('date_to'):
            query += " AND \"account_move_line\".date <= %s"
            params.append(data['form']['date_to'])
            
        # Clause de réconciliation
        if not data['form']['reconciled']:
            query += " AND \"account_move_line\".full_reconcile_id IS NULL"
            
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
        
        # Initialisation des états de mouvement
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move') == 'posted':
            data['computed']['move_state'] = ['posted']
            
        # Préparation des paramètres pour la requête SQL
        move_state = tuple(data['computed']['move_state'])
        
        # Détermination des comptes en fonction de la sélection
        result_selection = data['form'].get('result_selection')
        if result_selection == 'customer':
            self.env.cr.execute("""
                SELECT a.id
                FROM account_account a
                WHERE a.account_type = 'asset_receivable'
                AND NOT a.deprecated""")
            data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        elif result_selection == 'supplier':
            self.env.cr.execute("""
                SELECT a.id
                FROM account_account a
                WHERE a.account_type = 'liability_payable'
                AND NOT a.deprecated""")
            data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        else:
            self.env.cr.execute("""
                SELECT a.id
                FROM account_account a
                WHERE a.account_type IN ('asset_receivable', 'liability_payable')
                AND NOT a.deprecated""")
            data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
            
        # S'assurer que account_ids n'est pas vide
        if not data['computed']['account_ids']:
            return {
                'doc_ids': [],
                'doc_model': self.env['res.partner'],
                'data': data,
                'docs': [],
                'time': time,
                'lines': self._lines,
                'sum_partner': self._sum_partner,
            }
            
        account_ids = tuple(data['computed']['account_ids'])
        
        # Construction de la requête SQL pour trouver les partenaires
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM account_move_line, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated"""
                
        # Ajout des conditions de filtrage supplémentaires
        params = [move_state, account_ids]
        
        # Ajout des conditions de journal, date et état si présentes
        if data['form'].get('journal_ids', []):
            query += " AND \"account_move_line\".journal_id in %s"
            params.append(tuple(data['form']['journal_ids']))
            
        if data['form'].get('target_move') == 'posted':
            query += " AND \"account_move_line\".parent_state = %s"
            params.append('posted')
            
        if data['form'].get('date_from'):
            query += " AND \"account_move_line\".date >= %s"
            params.append(data['form']['date_from'])
            
        if data['form'].get('date_to'):
            query += " AND \"account_move_line\".date <= %s"
            params.append(data['form']['date_to'])
            
        # Clause de réconciliation
        if not data['form'].get('reconciled', False):
            query += " AND \"account_move_line\".full_reconcile_id IS NULL"
            
        self.env.cr.execute(query, params)
        partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
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
