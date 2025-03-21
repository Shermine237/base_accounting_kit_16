# -*- coding: utf-8 -*-
{
    'name': 'Odoo 16 Accounting',
    'version': '16.0.1.1',
    'category': 'Accounting',
    'summary': 'Accounting Reports, Asset Management and Account Budget, Cost Accounting',
    'description': """
        Accounting Reports, Asset Management and Account Budget, Cost Accounting.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'account', 'account_check_printing', 'report_xlsx', 'sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/account_financial_report_data.xml',
        'data/cash_flow_data.xml',
        
        # Views
        'views/account_report_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_view.xml',
        'views/accounting_menu.xml',
        'views/assets.xml',
        'views/dashboard_views.xml',
        'views/reports_config_view.xml',
        'views/res_config_view.xml',
        
        # Wizards
        'wizard/account_report_common_view.xml',
        'wizard/trial_balance_view.xml',
        'wizard/bank_book_view.xml',
        'wizard/cash_book_view.xml',
        'wizard/day_book_view.xml',
        'wizard/financial_report.xml',
        'wizard/cash_flow_report.xml',
        
        # Reports
        'report/report.xml',
        'report/financial_report_actions.xml',
        'report/report_financial.xml',
        'report/report_trial_balance.xml',
        'report/general_ledger_report.xml',
        'report/report_journal_audit.xml',
        'report/report_tax.xml',
        'report/report_aged_partner.xml',
        'report/report_partner_ledger.xml',
        'report/account_bank_book_view.xml',
        'report/account_cash_book_view.xml',
        'report/account_day_book_view.xml',
        'report/cash_flow_report.xml',
        
        # Report Templates
        'report/account_day_book_templates.xml',
        'report/account_bank_book_templates.xml',
        'report/account_cash_book_templates.xml',
        'report/account_financial_report_templates.xml',
        'report/trial_balance_templates.xml',
        'report/cash_flow_report_templates.xml',
        'report/report_financial_xlsx.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_accounting_kit_16/static/src/css/account_report.css',
            'base_accounting_kit_16/static/src/js/account_report.js',
            'base_accounting_kit_16/static/src/xml/template.xml',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
