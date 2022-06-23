{
    'name': 'Onpoint - SCADA',
    'version': '2021',
    'summary': 'Onpoint - SCADA',
    'description': """

Onpoint - SCADA 2021
=======================================================
copyright 2021

    """,
    'author': 'TGS',
    'website': 'http://',
    'category': 'Community',
    'sequence': 0,
    'depends': [
        'onpoint_base',
    ],
    'demo': [],
    'data': [
        'views/onpoint_scada_assets_backend.xml',
        'views/onpoint_scada_sensor_type_views.xml',
        'views/onpoint_scada_location_views.xml',
        'views/onpoint_scada_parameter_views.xml',
        'views/onpoint_scada_sensor_parameter_views.xml',
        'views/onpoint_scada_unit_detail_views.xml',
        'views/onpoint_scada_alarm_views.xml',
        'views/onpoint_location_templates.xml',
        'views/onpoint_unit_templates.xml',
        'reports/onpoint_gunung_ulin_report_templates.xml',
        'reports/onpoint_gunung_ulin_report_views.xml',
        'reports/onpoint_gunung_rely_report_templates.xml',
        'reports/onpoint_gunung_rely_report_views.xml',
        'reports/onpoint_spam_ikk_report_templates.xml',
        'reports/onpoint_spam_ikk_report_views.xml',
        'views/onpoint_scada_menu.xml',
        'schedulers/onpoint_scheduler_scada.xml',
        'reports/onpoint_scada_unit_report_templates.xml',
        'reports/onpoint_scada_unit_report_views.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/onpoint_unit_chart_templates.xml',
    ],
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
