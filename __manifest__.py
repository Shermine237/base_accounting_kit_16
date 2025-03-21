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
    'depends': ['base', 'web', 'account', 'account_check_printing', 'report_xlsx', 'sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/account_financial_report_data.xml',
        'data/cash_flow_data.xml',
        # 'data/account_asset_data.xml',  # Commenté car les modèles d'actifs ne sont pas compatibles avec Odoo 16
        'data/account_pdc_data.xml',
        # 'data/followup_levels.xml',  # Commenté car le modèle followup.line n'existe plus dans Odoo 16
        'data/multiple_invoice_data.xml',
        'data/recurring_entry_cron.xml',
        
        # Views
        'views/account_report_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_view.xml',
        'views/accounting_menu.xml',
        'views/dashboard_views.xml',
        'views/reports_config_view.xml',
        'views/res_config_view.xml',
        # 'views/account_asset_views.xml',  # Commenté car les modèles d'actifs ne sont pas compatibles avec Odoo 16
        # 'views/account_asset_templates.xml',  # Commenté car les modèles d'actifs ne sont pas compatibles avec Odoo 16
        'views/account_configuration.xml',
        # 'views/account_followup.xml',  # Commenté car le modèle followup.line n'existe plus dans Odoo 16
        'views/account_group.xml',
        'views/credit_limit_view.xml',
        # 'views/followup_report.xml',  # Commenté car le modèle followup.line n'existe plus dans Odoo 16
        'views/multiple_invoice_form.xml',
        'views/multiple_invoice_layout_view.xml',
        'views/payment_matching.xml',
        'views/product_template_views.xml',
        'views/product_views.xml',
        'views/recurring_payments_view.xml',
        
        # Wizards
        'wizard/trial_balance.xml',
        'wizard/account_bank_book_wizard_view.xml',
        'wizard/account_cash_book_wizard_view.xml',
        'wizard/account_day_book_wizard_view.xml',
        'wizard/financial_report.xml',
        'wizard/cash_flow_report.xml',
        'wizard/general_ledger.xml',
        'wizard/partner_ledger.xml',
        'wizard/tax_report.xml',
        'wizard/aged_partner.xml',
        # 'wizard/asset_depreciation_confirmation_wizard_views.xml',  # Commenté car les modèles d'actifs ne sont pas compatibles avec Odoo 16
        # 'wizard/asset_modify_views.xml',  # Commenté car les modèles d'actifs ne sont pas compatibles avec Odoo 16
        'wizard/account_lock_date.xml',
        'wizard/journal_audit.xml',
        
        # Reports
        'report/report.xml',
        'report/financial_report_actions.xml',
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
        # 'report/account_asset_report_views.xml',  # Commenté car les modèles d'actifs ne sont pas compatibles avec Odoo 16
        'report/multiple_invoice_layouts.xml',
        'report/multiple_invoice_report.xml',
        'report/report_financial_xlsx.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Fonts
            ('https://fonts.googleapis.com', 'preconnect'),
            ('https://fonts.gstatic.com', 'preconnect'),
            'https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap',
            
            # Styles
            '/base_accounting_kit_16/static/src/scss/style.scss',
            '/base_accounting_kit_16/static/src/scss/account_dashboard.scss',
            '/base_accounting_kit_16/static/lib/bootstrap-toggle/css/bootstrap-toggle.min.css',
            
            # Core Scripts
            '/base_accounting_kit_16/static/src/js/account_dashboard.js',
            '/base_accounting_kit_16/static/src/js/account_reports.js',
            
            # Payment Scripts
            '/base_accounting_kit_16/static/src/js/payment/payment_model.js',
            '/base_accounting_kit_16/static/src/js/payment/payment_render.js',
            '/base_accounting_kit_16/static/src/js/payment/payment_matching.js',
            '/base_accounting_kit_16/static/src/js/payment/payment_widget.js',
            
            # Chart Scripts
            '/base_accounting_kit_16/static/lib/chart.js/chart.min.js',
            
            # Toggle Scripts
            '/base_accounting_kit_16/static/lib/bootstrap-toggle/js/bootstrap-toggle.min.js',
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
