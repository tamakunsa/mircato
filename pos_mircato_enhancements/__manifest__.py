# -*- coding: utf-8 -*-
{
    'name': "Point Of Sale Mircato Enhancement",

    'summary': "Enhancements for mircato",
    'author': "Eco-Tech, Omar Amr",
    'website': "https://ecotech.com",

    'category': 'Products',
    'version': '17.0.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'point_of_sale',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_mircato_enhancements/static/src/xml/partner_editor.xml',
            'pos_mircato_enhancements/static/src/js/partner_editor.js',
        ],
    },
}

