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

# Classes de base pour les rapports
from . import report_common
from . import report_common_account
from . import report_common_partner

# Rapports financiers
from . import report_financial
from . import report_financial_xlsx
from . import report_general_ledger
from . import report_partner_ledger
from . import report_trial_balance
from . import report_tax
from . import report_asset
from . import report_multiple_invoice

# Rapports comptables
from . import report_aged_partner
from . import report_journal
from . import report_journal_audit
from . import cash_flow_report

# Rapports de livres
from . import report_bank_book
from . import report_cash_book
from . import report_day_book
