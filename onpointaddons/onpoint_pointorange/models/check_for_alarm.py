import sys
from ftplib import FTP
import xmlrpc.client


# import csv
# import pandas as pd

def check(db):
    url = 'https://' + db + '.opwater.id'
    # db = sys.argv[1]
    username = 'admin'
    password = 'pegasus#123'

    ftp = FTP()
    ftp.connect('www.wtccloud.net', 21)
    ftp.login('pointorange', 'pointorange')
    ftp.cwd('onpoint')

    files = ftp.nlst()

    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    print('Odoo Version : ', common.version())

    uid = common.authenticate(db, username, password, {})
    print('UID : ', uid)

    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    for file_name in files:
        if '_A_' in file_name:
            names = file_name.split('_A_')
            print(names[0], ' ', names[1])

            logger = models.execute_kw(db, uid, password,
                                       'onpoint.logger',
                                       'search_read',
                                       [[['identifier', '=', names[0]]]])
            if logger:
                print(logger[0]['name'])
            else:
                print('none')

    #
    # x = models.execute_kw(db, uid, password,
    #                       'onpoint.logger', 'search', [()])
    # print(x)


a = sys.argv[1]
check(a)
