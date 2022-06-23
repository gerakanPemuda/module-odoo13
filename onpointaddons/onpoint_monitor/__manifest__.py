{
    'name': 'OnPoint - Monitor System',
    'version': '1.0',
    'summary': 'OnPoint Monitor',
    'description': """

OnPoint Monitor System 3.0
==============================

OnPoint Monitor System
copyright 2019

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'onpoint_base',
        # 'gws_google_maps',
        'highcharts_base',
        ],
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/onpoint_monitor_assets_backend.xml',
        'views/onpoint_alarm_threshold_views.xml',
        'views/onpoint_wtp_views.xml',
        'views/onpoint_zone_views.xml',
        'views/onpoint_dma_views.xml',
        'views/onpoint_meter_type_views.xml',
        'views/onpoint_meter_brand_views.xml',
        'views/onpoint_meter_size_views.xml',
        'views/onpoint_pipe_material_views.xml',
        'views/onpoint_valve_control_views.xml',
        'views/onpoint_logger_brand_views.xml',
        'views/onpoint_logger_point_views.xml',
        'views/onpoint_logger_owner_views.xml',
        'views/onpoint_logger_views.xml',
        'views/onpoint_logger_value_views.xml',
        'views/onpoint_logger_type_views.xml',
        'views/onpoint_value_type_views.xml',
        'views/onpoint_value_unit_views.xml',
        'views/onpoint_logger_compare_views.xml',
        'views/onpoint_monitor_menu.xml',
        'views/res_config_settings_views.xml',
        'reports/report_style_templates.xml',
        'reports/onpoint_logger_report_views.xml',
        'reports/onpoint_logger_report_templates.xml',
        'reports/onpoint_logger_compare_report_views.xml',
        'reports/onpoint_logger_compare_report_templates.xml',
        'data/onpoint.logger.brand.csv',
        'data/onpoint.logger.type.csv',
        'data/onpoint.value.type.csv',
        'data/onpoint.value.unit.csv',
    ],
    'qweb': [
        'static/src/xml/onpoint_logger_chart_templates.xml',
        'static/src/xml/onpoint_logger_compare_templates.xml',
        'static/src/xml/onpoint_monitor_dashboard_templates.xml',
    ],
    'application': True,
}