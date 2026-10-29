# -*- encoding: utf-8 -*-

{
    'name' : 'Kardex',
    'version' : '13.0.1.1.1',
    'category': 'Operations/Inventory',
    'description': """Modulo para reporte de kardex""",
    'author': 'aquíH',
    'website': 'http://aquih.com/',
    'depends' : [ 'stock_account' ],
    'data' : [
        'views/res_company_views.xml',
        'views/report.xml',
        'views/reporte_kardex.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
