# -*- coding: utf-8 -*-
{
    'name': "Point Of Sale  Bank Payments ",
    'summary': "Point Of Sale  Bank Payments ",
    'author': "Eco-Tech, Omar Amr",
    'website': "https://ecotech.com",

    'category': 'Products',
    'version': '17.0.1.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    'data':[
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets': {
        # 'point_of_sale.assets_prod': [
        # ],
        'point_of_sale._assets_pos': [
            # "eco_bank_payments_pos/src/js/closeSessionPopup.js"
            "eco_bank_payments_pos/static/src/js/closeSessionPopup.js",
        ],
    },
}

