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

# Wizards de rapports financiers
from . import financial_report
from . import general_ledger
from . import partner_ledger
from . import tax_report

# Wizards de rapports comptables
from . import aged_partner
from . import journal_audit
from . import cash_flow_report
from . import account_balance_report

# Wizards de livres comptables
from . import account_bank_book_wizard
from . import account_cash_book_wizard
from . import account_day_book_wizard

# Wizards pour les immobilisations
from . import asset_modify
from . import asset_depreciation_confirmation_wizard

# Autres wizards
from . import account_report_common_partner
from . import account_lock_date
