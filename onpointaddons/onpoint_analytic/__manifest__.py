{
    'name': 'OnPoint - Analytic System',
    'version': '1.0',
    'summary': 'OnPoint Analytic',
    'description': """

OnPoint Analytic System 3.0
==============================

OnPoint Analytic System
copyright 2019

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'onpoint_base',
        'onpoint_monitor',
        ],
    'demo': [],
    'data': [
        'views/onpoint_analytic_assets_backend.xml',
        'views/onpoint_cp_recap_views.xml',
        'views/onpoint_dma_billing_views.xml',
        'views/onpoint_water_balance_views.xml',
        'views/onpoint_night_flow_views.xml',
        'views/onpoint_analytic_menu.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/onpoint_night_flow_templates.xml',
    ],
    'application': True,
}