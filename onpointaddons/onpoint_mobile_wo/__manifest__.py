{
    'name': 'OnPoint Mobile - Work Order',
    'version': '1.0',
    'summary': 'OnPoint Mobile Work Order',
    'description': """

OnPoint Mobile Work Order 1.0
==============================

OnPoint Mobile Work Order System
copyright 2020

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'onpoint_wo',
        ],
    'demo': [],
    'data': [
        # 'views/onpoint_mobile_module_views.xml',
        # 'views/onpoint_mobile_module_menu.xml',
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'views/main_templates.xml',
        'views/wo_templates.xml',
    ],
    'qweb': [],
    'application': True,
}