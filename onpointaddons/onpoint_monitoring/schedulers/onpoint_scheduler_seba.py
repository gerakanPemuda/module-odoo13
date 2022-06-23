from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone
from time import mktime
from ftplib import FTP
import csv
import io


# from pymodbus.client.sync import ModbusTcpClient
# from pymodbus.client.async import ModbusTcpClient as ModbusClient

import logging
_logger = logging.getLogger(__name__)


class OnpointSchedulerSeba(models.Model):
    _name = 'onpoint.scheduler.seba'
    _inherit = ['onpoint.seba']


    @api.model
    def read_data(self):

        ftp = FTP('www.wtccloud.net')
        ftp.login('loggersD3', 'loggersD3')
        data = []

        seba = self.env['onpoint.logger.brand'].search([('name', '=', 'Seba')])
        loggers = self.env['onpoint.logger'].search([('brand_id', '=', seba.id)])

        for logger in loggers:
            
            _logger.debug('Logger %s', logger)

            ftp.cwd('/logd3/')

            folder_name = str(logger.identifier).zfill(8)

            ftp.cwd(folder_name)

            files = ftp.nlst()
            value_ids = []

            for file_name in files:
                check_file_name = 'measdata_' in file_name
                if check_file_name:
                    _logger.debug('file : %s', file_name)

                    temp_file = io.BytesIO()

                    ftp.retrbinary('RETR ' + file_name, temp_file.write)
                    temp_file.seek(0)

                    stream_data = temp_file.read()

                    # _logger.debug('stream %s', stream_data)


                    buffer = temp_file.getbuffer()

                    data = self._process_block1(buffer)

                    channel_values = self._process_block7(buffer, data)

                    for channel in logger.channel_ids:
                        # _logger.debug('Points : %s', channel.points)
                        
                        idx = 0
                        for channel_value in channel_values:
                            # _logger.debug('%s --> dates : %s = %s', channel.points, channel_value['dates'], channel_value[channel.points])

                            value_date = datetime.strptime(channel_value['dates'], '%Y-%m-%d %H:%M:%S')
                            value_vals = {
                                'channel_id' : channel.id,
                                'dates' : value_date,
                                'channel_value' : channel_value[channel.points]
                            }

                            row_value = (0, 0, value_vals)
                            value_ids.append(row_value)

                    ftp.rename(file_name, 'archives/' + file_name)

                    logger.sudo().update({
                        'value_ids' : value_ids
                    })

        ftp.quit
        

