{
    'name': 'OnPointLite - Base System',
    'version': '1.0',
    'summary': 'OnPointLite Base',
    'description': """

OnPointLite Base System 1.0
==============================

OnPointLite Base System
copyright 2022

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        # 'mail',
        'base',
        'hr',
        'web_fontawesome',
        'highcharts_base',
        # 'onpoint_monitor',
        ],
    'demo': [],
    'data': [
        'views/res_company_views.xml',
        'views/main_templates.xml',
        'views/dashboard_templates.xml',
        'views/logger_detail_templates.xml',
        'views/logger_channel_consumption_templates.xml',
        'views/logger_form_templates.xml',
        # 'views/mobile_login_templates.xml',
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        # 'views/onpoint_logger_realtime_dashboard_views.xml',
        # 'views/onpoint_logger_views.xml',
        # 'views/onpointlite_database_configuration_views.xml',
        # 'views/onpointlite_base_menu.xml',
        # 'views/res_config_settings_views.xml',
        # 'schedulers/onpoint_scheduler_seba.xml',
        # 'data/onpoint.seba.spec.csv',
        # 'data/onpoint_logger_brand.xml',
        # 'data/onpoint_logger_point.xml',
    ],
    'qweb': [
        # "static/src/xml/onpoint_logger_realtime_dashboard.xml",
    ],
    'application': True,
}