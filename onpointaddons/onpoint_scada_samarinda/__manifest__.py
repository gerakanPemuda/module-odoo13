{
    'name': 'Onpoint - SCADA',
    'version': '2022',
    'summary': 'Onpoint - SCADA',
    'description': """

Onpoint - SCADA 2022
=======================================================
copyright 2022

    """,
    'author': 'TGS',
    'website': 'http://',
    'category': 'Community',
    'sequence': 0,
    'depends': [
        'onpoint_base',
        'onpoint_modbus'
    ],
    'demo': [],
    'data': [
        'views/onpoint_scada_dashboard_views.xml',
        'views/onpoint_scada_menu.xml',
        'templates/main_templates.xml',
        'templates/home_templates.xml',
    ],
    'qweb': [
    ],
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
