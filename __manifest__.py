# -*- encoding: utf-8 -*-

{
    'name' : 'Kardex',
    'version' : '1.2',
    'category': 'Inventory/Inventory',
    'description': """Modulo para reporte de kardex""",
    'author': 'aquíH',
    'website': 'http://aquih.com/',
    'depends' : [ 'stock_account' ],
    'data' : [
        'views/report.xml',
        'views/reporte_kardex.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
