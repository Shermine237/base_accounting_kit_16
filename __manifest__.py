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
    'depends': ['base', 'web', 'account', 'account_check_printing', 'report_xlsx', 'sale', 'base_account_budget_16', 'l10n_syscohada'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Python files
        'wizard/account_profit_loss.py',
        
        # Data
        'data/account_financial_report_data.xml',
        'data/cash_flow_data.xml',
        'data/account_pdc_data.xml',
        'data/multiple_invoice_data.xml',
        'data/multiple_invoice_layout_action.xml',
        'data/recurring_entry_cron.xml',
        
        # Views
        'views/account_report_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_view.xml',
        'views/accounting_menu.xml',
        'views/dashboard_views.xml',
        'views/reports_config_view.xml',
        'views/res_config_view.xml',
        'views/account_configuration.xml',
        'views/account_group.xml',
        'views/credit_limit_view.xml',
        'views/multiple_invoice_form.xml',
        'views/multiple_invoice_layout_view.xml',
        'views/payment_matching.xml',
        'views/product_template_views.xml',
        'views/product_views.xml',
        'views/recurring_payments_view.xml',
        
        # Wizards
        'wizard/account_common_report_view.xml',
        'wizard/account_report_common_partner_view.xml',
        'wizard/trial_balance.xml',
        'wizard/account_bank_book_wizard_view.xml',
        'wizard/account_cash_book_wizard_view.xml',
        'wizard/account_day_book_wizard_view.xml',
        'wizard/account_balance_view.xml',
        'wizard/account_profit_loss_view.xml',
        'wizard/financial_report.xml',
        'wizard/cash_flow_report.xml',
        'wizard/general_ledger.xml',
        'wizard/partner_ledger.xml',
        'wizard/tax_report.xml',
        'wizard/aged_partner.xml',
        'wizard/account_lock_date.xml',
        'wizard/journal_audit.xml',
        
        # Reports
        'report/report.xml',
        'report/report_financial.xml',
        'report/report_trial_balance.xml',
        'report/report_general_ledger.xml',
        'report/report_journal_audit.xml',
        'report/report_tax.xml',
        'report/report_aged_partner.xml',
        'report/report_partner_ledger.xml',
        'report/account_bank_book_view.xml',
        'report/account_cash_book_view.xml',
        'report/account_day_book_view.xml',
        'report/cash_flow_report.xml',
        'report/multiple_invoice_layouts.xml',
        'report/multiple_invoice_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Fonts
            'https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap',
            
            # Styles
            '/base_accounting_kit_16/static/src/scss/style.scss',
            '/base_accounting_kit_16/static/src/scss/account_asset.scss',
            '/base_accounting_kit_16/static/lib/bootstrap-toggle-master/css/bootstrap-toggle.min.css',
            
            # Chart.js Library (load before other scripts)
            '/base_accounting_kit_16/static/lib/chart.js/chart.min.js',
            
            # Core Scripts
            '/base_accounting_kit_16/static/src/js/account_dashboard.js',
            '/base_accounting_kit_16/static/src/js/account_reports.js',
            
            # Payment Scripts
            '/base_accounting_kit_16/static/src/js/payment/payment_model.js',
            '/base_accounting_kit_16/static/src/js/payment/payment_render.js',
            '/base_accounting_kit_16/static/src/js/payment/payment_matching.js',
            '/base_accounting_kit_16/static/src/js/payment/payment_widget.js',
            
            # Toggle Scripts
            '/base_accounting_kit_16/static/lib/bootstrap-toggle-master/js/bootstrap-toggle.min.js',
            
            # XML Templates
            '/base_accounting_kit_16/static/src/xml/template.xml',
        ],
        'web.assets_qweb': [
            '/base_accounting_kit_16/static/src/xml/template.xml',
        ],
        'web.qunit_suite_tests': [
            '/base_accounting_kit_16/static/tests/account_dashboard_tests.js',
            '/base_accounting_kit_16/static/tests/payment_tests.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
