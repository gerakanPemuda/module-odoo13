{
    'name': 'Onpoint - Telegram Message and Notification System',
    'version': '2020',
    'summary': 'Onpoint - Telegram Message and Notification System',
    'description': """

Onpoint - Telegram Message and Notification System 2021
=======================================================
copyright 2021

    """,
    'author': 'TGS',
    'website': 'http://',
    'category': 'Community',
    'sequence': 0,
    'depends': [
        'onpoint_pointorange',
        'api_telegram',
    ],
    'demo': [],
    'data': [
        'views/onpoint_telegram_group_views.xml',
        'views/onpoint_logger_views.xml',
        'views/onpoint_telegram_menu.xml',
        'schedulers/onpoint_scheduler_telegram.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
