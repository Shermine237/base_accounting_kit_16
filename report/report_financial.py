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
from odoo import api, fields, models


# ---------------------------------------------------------
# Account Financial Report Extension
# ---------------------------------------------------------


class AccountFinancialReportExtension(models.Model):
    _inherit = "account.financial.report"
    
    # Cette méthode est déjà définie dans models/report_financial.py
    # avec le nom _compute_level. Nous la laissons commentée ici
    # pour référence, mais elle n'est pas utilisée.
    """
    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level
    """
    
    # Cette méthode peut être utile et n'est pas présente dans l'autre fichier
    def _get_children_by_order(self):
        """returns a recordset of all the children computed recursively,
         and sorted by sequence. Ready for the printing"""
        res = self
        children = self.search([('parent_id', 'in', self.ids)],
                               order='sequence ASC')
        if children:
            for child in children:
                res += child._get_children_by_order()
        return res
