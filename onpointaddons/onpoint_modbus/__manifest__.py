{
    'name': 'OnPoint - Modbus',
    'version': '1.0',
    'summary': 'OnPoint Modbus Communication',
    'description': """

OnPoint Modbus 1.0
==============================

OnPoint Modbus System
copyright 2020

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'onpoint_monitor',
        'onpoint_pointorange',
        ],
    'demo': [],
    'data': [
        'views/onpoint_modbus_comm_views.xml',
        'views/onpoint_mmim_views.xml',
        'views/onpoint_mmim_value_views.xml',
        'views/onpoint_modbus_menu.xml',
        'schedulers/onpoint_scheduler_mmim.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    'application': True,
}