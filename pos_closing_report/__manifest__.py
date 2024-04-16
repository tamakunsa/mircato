{
    'name': "Sale Details Report",
    'summary': """""",
    'description': """""",
    'author': '',
    'category': 'Products',
    'version': '17.0.1.1',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'reports/report_sale_details.xml',
        'views/session_report_view.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_closing_report/static/src/js/SalesDetailsReport.js',
            'pos_closing_report/static/src/xml/SaleDetailsReport.xml',
        ],
    },

    'installable': True,
}
