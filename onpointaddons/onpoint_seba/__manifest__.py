{
    'name': 'OnPoint - Seba System',
    'version': '1.0',
    'summary': 'OnPoint Seba',
    'description': """

OnPoint Seba System 3.0
==============================

OnPoint Seba System
copyright 2019

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'onpoint_monitor',
    ],
    'demo': [],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/onpoint_logger_realtime_dashboard_views.xml',
        'views/onpoint_logger_views.xml',
        'views/onpoint_seba_spec_views.xml',
        'views/onpoint_seba_menu.xml',
        'views/res_config_settings_views.xml',
        'schedulers/onpoint_scheduler_seba.xml',
        'data/onpoint.seba.spec.csv',
        'data/onpoint_logger_brand.xml',
        'data/onpoint_logger_point.xml',
    ],
    'qweb': [
        "static/src/xml/onpoint_logger_realtime_dashboard.xml",
    ],
    'application': True,
}