{
    'name': 'OnPoint - Base System',
    'version': '1.0',
    'summary': 'OnPoint Base',
    'description': """

OnPoint Base System 3.0
==============================

OnPoint Base System
copyright 2019

    """,
    'author': '',
    'website': 'http://',
    'category': '',
    'sequence': 0,
    'depends': [
        'mail',
        'base',
        'hr',
        'web_fontawesome',
    ],
    'demo': [],
    'data': [
        'views/onpoint_base_assets_backend.xml',
        'views/onpoint_base_menu.xml',
    ],
    'qweb': [
        'static/src/xml/onpoint_copyright_dashboard_templates.xml',
    ],
    'application': True,
}
