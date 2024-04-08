# -*- encoding: utf-8 -*-
{
    'name': "SGEEDE Internal Transfer",
    'version': '1.1',
    'category': 'Tools',
    'summary': """Odoo's enchanced advance stock internal transfer module""",
    'description': """Odoo's enchanced advance stock internal transfer module""",
    'author': 'SGEEDE',
    'website': 'http://www.sgeede.com',
    'depends': ['base', 'account', 'stock', 'product'],
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/stock_internal_transfer_view.xml',
        'views/stock_view.xml',
        'views/res_config_view.xml',
        'views/res_company_inh_view.xml',
        'wizard/wizard_stock_internal_transfer_view.xml',
    ],
    'installable': True,
    'active': False,
    'images': [
        'images/main_screenshot.png',
        'images/sgeede.png'
    ],
}
