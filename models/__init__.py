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

# Modèles de base Odoo
from . import account_account
from . import account_journal
from . import account_move
from . import account_payment
from . import product_template
from . import res_config_settings
from . import res_partner

# Modèles de gestion des immobilisations
from . import account_asset

# Modèles de rapports (ordre important)
from . import account_report  # Modèle abstrait de base
from . import report_financial  # Implémentation concrète

# Modèles spécifiques
from . import account_dashboard
from . import credit_limit
from . import multiple_invoice
from . import multiple_invoice_layout
from . import payment_matching
from . import recurring_payments

# Modèles désactivés
# from . import account_followup
