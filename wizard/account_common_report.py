# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountCommonReport(models.TransientModel):
    _name = "account.common.report"
    _description = "Account Common Report"

    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                  default=lambda self: self.env['account.journal'].search([]))
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    
    # Ajout des champs de comparaison dans le modèle parent
    date_from_cmp = fields.Date(string='Comparison Start Date')
    date_to_cmp = fields.Date(string='Comparison End Date')
    filter_cmp = fields.Selection([('filter_no', 'No Filters'),
                                ('filter_date', 'Date')], string='Filter by',
                                required=False, default='filter_no')
    enable_filter = fields.Boolean(string='Enable Comparison')
    label_filter = fields.Char(string='Column Label',
                            help="This label will be displayed on report to show the balance computed for the given comparison filter.")

    def check_report(self):
        """
        To be implemented by each report
        :return: Action dictionary
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.common.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }
