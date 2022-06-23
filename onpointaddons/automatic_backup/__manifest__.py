# -*- coding: utf-8 -*-
{
    'name': 'Automatic Backup (Dropbox, Google Drive, Amazon S3, SFTP, Local)',
    'version': '1.7.5',
    'summary': 'Automatic Backup',
    'author': 'Grzegorz Krukar (support@gksoftware.pl)',
    'description': """
    Automatic Backup
    """,
    'data': [
        'data/data.xml',
        'views/automatic_backup.xml',
        'security/security.xml'
    ],
    'depends': [
        'mail',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'price': 30.00,
    'currency': 'EUR',
}
