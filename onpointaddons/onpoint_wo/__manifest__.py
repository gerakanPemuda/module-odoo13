{
    'name': 'OnPoint - Work Order System',
    'version': '1.0',
    'summary': 'OnPoint Work Order',
    'description': """

OnPoint Work Order System 3.0
==============================

OnPoint Work Order System
copyright 2019

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'onpoint_base',
        'base_geolocalize',
        'web_google_maps',
        'highcharts_base',
        ],
    'demo': [],
    'data': [
        'views/onpoint_work_order_views.xml',
        'views/onpoint_work_order_line_views.xml',
        'views/onpoint_work_order_wizard_views.xml',
        'views/onpoint_work_order_comment_wizard_views.xml',
        'views/onpoint_wo_sequence.xml',
        'views/onpoint_wo_type_views.xml',
        'views/onpoint_wo_menu.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
    ],
    'application': True,
}