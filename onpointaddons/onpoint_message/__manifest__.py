{
    'name': 'Onpoint - Message and Notification System',
    'version': '2020',
    'summary': 'Onpoint - Message and Notification System',
    'description': """

Onpoint - Message and Notification System 2020
==============================================
copyright 2020

    """,
    'author': 'TGS',
    'website': 'http://',
    'category': 'Community',
    'sequence': 0,
    'depends': [
            'onpoint_monitor',
            'api_zenziva',
    ],
    'demo': [],
    'data': [
        'views/onpoint_logger_views.xml',
        'views/onpoint_logger_outbox_views.xml',
        'schedulers/onpoint_scheduler_message.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
