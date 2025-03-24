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

from odoo import models, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def action_open_reconcile(self):
        if self.type in ['bank', 'cash']:
            # Open reconciliation view for bank statements belonging to this journal
            bank_stmt = self.env['account.bank.statement'].search([('journal_id', 'in', self.ids)]).mapped('line_ids')
            return {
                'type': 'ir.actions.client',
                'tag': 'bank_statement_reconciliation_view',
                'context': {'statement_line_ids': bank_stmt.ids, 'company_ids': self.mapped('company_id').ids},
            }
        else:
            # Open reconciliation view for customers/suppliers
            action_context = {'show_mode_selector': False, 'company_ids': self.mapped('company_id').ids}
            if self.type == 'sale':
                action_context.update({'mode': 'customers'})
            elif self.type == 'purchase':
                action_context.update({'mode': 'suppliers'})
            return {
                'type': 'ir.actions.client',
                'tag': 'manual_reconciliation_view',
                'context': action_context,
            }

    @api.depends('outbound_payment_method_ids')
    def _compute_check_printing_payment_method_selected(self):
        for journal in self:
            journal.check_printing_payment_method_selected = any(
                pm.code == 'check_printing' for pm in journal.outbound_payment_method_ids)

    @api.model
    def check_dashboard_journals(self):
        """
        Vérifie l'existence des journaux nécessaires pour le tableau de bord
        et les crée si nécessaire
        """
        company_id = self.env.company.id
        journals = self.search([
            ('company_id', '=', company_id),
            ('type', '=', 'general')
        ])
        
        if not journals:
            # Aucun journal de type général trouvé, créer un journal par défaut
            try:
                default_account = self.env['account.account'].search([
                    ('company_id', '=', company_id),
                    ('account_type', '=', 'asset_current')
                ], limit=1)
                
                if not default_account:
                    return {'error': 'Aucun compte comptable trouvé pour créer un journal général'}
                
                self.create({
                    'name': 'Journal des opérations diverses',
                    'code': 'MISC',
                    'type': 'general',
                    'company_id': company_id,
                    'default_account_id': default_account.id,
                })
                return {'success': 'Journal général créé avec succès'}
            except Exception as e:
                return {'error': f'Erreur lors de la création du journal: {str(e)}'}
        
        return {'success': 'Journaux existants'}

    @api.model
    def _enable_pdc_on_bank_journals(self):
        """ Enables check printing payment method and add a check
        sequence on bank journals. Called upon module installation 
        via data file.
        """
        pdcin = self.env.ref('base_accounting_kit_16.account_payment_method_pdc_in')
        pdcout = self.env.ref('base_accounting_kit_16.account_payment_method_pdc_out')
        bank_journals = self.search([('type', '=', 'bank')])
        for bank_journal in bank_journals:
            bank_journal._create_check_sequence()
            bank_journal.write({
                'inbound_payment_method_ids': [(4, pdcin.id, None)],
                'outbound_payment_method_ids': [(4, pdcout.id, None)],
            })
