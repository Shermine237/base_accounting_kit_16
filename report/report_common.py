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

from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountCommonReport(models.TransientModel):
    _name = "account.common.report"
    _description = "Account Common Report"

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    journal_ids = fields.Many2many('account.journal', string='Journals',
                                 required=True,
                                 default=lambda self: self.env['account.journal'].search([]))
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                  ('all', 'All Entries')],
                                 string='Target Moves', required=True,
                                 default='posted')
    display_account = fields.Selection([
        ('all', 'All'),
        ('movement', 'With movements'),
        ('not_zero', 'With balance not equal to 0')],
        string='Display Accounts', required=True, default='movement')

    def _build_contexts(self, data):
        """Construit le contexte pour le rapport"""
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['company_id'] = data['form']['company_id'][0] if data['form'].get('company_id') else False
        return result

    def check_report(self):
        """Point d'entrée pour la génération du rapport"""
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move',
                                'display_account', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                          lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)

    def pre_print_report(self, data):
        """Préparation des données avant impression"""
        data['form'].update(self.read(['display_account'])[0])
        return data

    def _get_report_values(self, docids, data=None):
        """Méthode standard pour obtenir les valeurs du rapport"""
        if not data.get('form'):
            raise UserError(_('Form content is missing, this report cannot be printed.'))

        return {
            'doc_ids': docids,
            'doc_model': self._name,
            'data': data,
            'docs': self.env[data['model']].browse(data.get('ids', [])),
            'lines': self._get_lines(data.get('form', {})),
        }

    def _get_lines(self, options):
        """Méthode à surcharger dans les classes filles"""
        return []

    def _print_report(self, data):
        """Méthode à surcharger dans les classes filles"""
        raise UserError(_('_print_report method not implemented'))
