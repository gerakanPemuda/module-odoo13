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
        loggers = self.env['onpoint.logger'].search([('brand_owner', '=', 'seba')])

        for logger in loggers:
            logger.read_ftp_seba()

    @api.model
    def read_realtime_data(self):
        loggers = self.env['onpoint.logger'].search([('brand_owner', '=', 'seba'),
                                                     ('is_realtime', '=', True),
                                                     ('state', '=', 'enabled')])

        for logger in loggers:
            try:
                _logger.info('Logger %s', logger.name)
                logger.act_read_realtime()
            except Exception as e:
                _logger.error('Error Logger %s', logger.name)
                pass

