{
    'name': 'OnPoint - Point Orange System',
    'version': '1.0',
    'summary': 'OnPoint Point Orange',
    'description': """

OnPoint Point Orange System 3.0
==============================

OnPoint Point Orange System
copyright 2020

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'onpoint_monitor',
        'onpoint_message'
    ],
    'demo': [],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/onpoint_logger_alarm_views.xml',
        'views/onpoint_logger_views.xml',
        'views/res_config_settings_views.xml',
        'schedulers/onpoint_scheduler_pointorange.xml',
        'data/onpoint_logger_brand.xml',
        'data/onpoint.logger.point.csv',
    ],
    'qweb': [
    ],
    'application': True,
}