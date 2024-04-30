# -*- coding: utf-8 -*-
{
    'name': "Point Of Sale Mircato Enhancement",

    'summary': "POS Enhancements for mircato",
    'author': "Eco-Tech, Omar Amr",
    'website': "https://ecotech.com",

    'category': 'Products',
    'version': '17.0.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'point_of_sale','pos_hr'
    ],

    'data':[
        'views/employee.xml'
    ],
    'assets': {
        # 'point_of_sale.assets_prod': [
        # ],
        'point_of_sale._assets_pos': [
            'pos_mircato_enhancements/static/src/xml/partner_editor.xml',
            'pos_mircato_enhancements/static/src/js/partner_editor.js',
            'pos_mircato_enhancements/static/src/js/pos_store.js',
            'pos_mircato_enhancements/static/src/js/order_reciept.js',
            'pos_mircato_enhancements/static/src/js/refundButton.js',
            'pos_mircato_enhancements/static/src/js/closeSessionPopup.js',
            'pos_mircato_enhancements/static/src/js/TicketScreen.js',            
            'pos_mircato_enhancements/static/src/xml/orderReciept.xml',
            'pos_mircato_enhancements/static/src/xml/Closepopup.xml'

        ],
    },
}

