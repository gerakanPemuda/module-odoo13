{
    'name': 'OnPoint - Monitoring System',
    'version': '1.0',
    'summary': 'OnPoint Monitoring',
    'description': """

OnPoint Monitoring System 3.0
==============================

OnPoint Monitoring System
copyright 2019

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'base',
        'hr',
        'dash_board',
        'web_fontawesome',
        'web_widget_color'
    ],
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/onpoint_zone_views.xml',
        'views/onpoint_dma_views.xml',
        'views/onpoint_dashboard_views.xml',
        'views/onpoint_logger_dashboard_views.xml',
        'views/onpoint_logger_realtime_dashboard_views.xml',
        'views/onpoint_comparison_dashboard_views.xml',
        'views/onpoint_mimic_diagram_views.xml',
        'views/onpoint_logger_type_views.xml',
        'views/onpoint_value_type_views.xml',
        'views/onpoint_value_unit_views.xml',
        'views/onpoint_logger_views.xml',
        'views/onpoint_logger_value_views.xml',
        'views/onpoint_seba_spec_views.xml',
        'views/onpoint_comparison_views.xml',
        'views/onpoint_mimic_views.xml',
        'views/onpoint_water_balance_views.xml',
        # 'views/res_config_settings_views.xml'
        'views/onpoint_monitoring_menu.xml', 
        'schedulers/onpoint_scheduler_seba.xml', 
        'data/onpoint.logger.type.csv',
        'data/onpoint.value.type.csv',
        'data/onpoint.value.unit.csv',
    ],
    'qweb': [
        "static/src/xml/onpoint_dashboard.xml",
        "static/src/xml/onpoint_logger_dashboard.xml",
        "static/src/xml/onpoint_logger_realtime_dashboard.xml",
        "static/src/xml/onpoint_comparison_dashboard.xml",
        "static/src/xml/onpoint_mimic_diagram.xml",
    ],    
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
