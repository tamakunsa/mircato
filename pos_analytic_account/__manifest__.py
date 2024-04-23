{
    'name': "POS Analytic Account",
    'summary': """
       Use analytic account defined on POS configuration for POS orders and in Journal Entry""",

    'description': """
        Use analytic account defined on POS configuration for POS orders and in Journal Entry
    """,
    'author': 'Abdallah Mohamed',
    'license': 'OPL-1',
    'category': 'Sales/Point of Sale',
    'website': 'https://www.abdalla.work/r/Ohk',
    'support': 'https://www.abdalla.work/r/Ohk',
    'version': '16.0.1',
    'depends': [
        'point_of_sale',
        'account',
        'analytic'
    ],
    'data': [
        'views/pos_config.xml',
        'views/pos_order.xml',
        'views/account_move_inh_view.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/module_screenshot.png',
    ],
    'installable': True,
}
