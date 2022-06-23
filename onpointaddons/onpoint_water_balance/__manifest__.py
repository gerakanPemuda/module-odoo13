{
    'name': 'Onpoint Water Balance',
    'version': '13.0.1.0',
    'summary': 'Water Balance Calculator',
    'description': """
    This module provide functionality to calculate water balance for OnPoint.
    """,
    'category': 'Water',
    'sequence': 10,
    'author': 'Paulus Satya Pamungkas',
    'website': '',
    'license': 'LGPL-3',
    'external_dependencies': {'python': ['numpy']},
    'depends': ['base', 'onpoint_base', 'onpoint_pointorange'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/system_input_wizard.xml',
        'wizards/billed_consumption_wizard.xml',
        'views/onpoint_wb_views.xml',
        'views/onpoint_wb_system_input_views.xml',
        'views/onpoint_wb_billed_views.xml',
        'views/onpoint_wb_unauthorized_views.xml',
        'views/onpoint_wb_meter_views.xml',
        'views/onpoint_wb_network_views.xml',
        'views/onpoint_wb_pressure_views.xml',
        'views/onpoint_wb_intermittent_views.xml',
        'views/onpoint_wb_financial_views.xml',
        'views/onpoint_wb_dash_daily_views.xml',
        'views/onpoint_wb_dash_period_views.xml',
        'views/onpoint_wb_dash_yearly_views.xml',
        'views/onpoint_wb_config.xml',
        'views/onpoint_wb_menu.xml'
    ],
    'demo': ['Demo'],
    'application': True,
    'installable': True,
    'auto_install': False
}
