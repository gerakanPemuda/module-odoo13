from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone
from time import mktime
from ftplib import FTP
import csv
import pandas as pd
import io

# from pymodbus.client.sync import ModbusTcpClient
# from pymodbus.client.async import ModbusTcpClient as ModbusClient

import logging

_logger = logging.getLogger(__name__)


class OnpointSchedulerPointorange(models.Model):
    _name = 'onpoint.scheduler.pointorange'
    _inherit = ['onpoint.pointorange']

    @api.model
    def read_data(self):
        loggers = self.env['onpoint.logger'].search([('brand_owner', '=', 'pointorange'),
                                                     ('state', '=', 'enabled')])

        for logger in loggers:
            try:
                _logger.info('Logger %s', logger.name)
                logger.read_ftp_pointorange()
                _logger.info('Logger complete')
            except Exception as e:
                _logger.info('Logger incomplete')
                pass

    @api.model
    def read_data_alarm(self):
        loggers = self.env['onpoint.logger'].search([('brand_owner', '=', 'pointorange'),
                                                     ('state', '=', 'enabled')])

        for logger in loggers:
            logger.read_ftp_pointorange_alarm()

        active_alarms = self.env['onpoint.logger.alarm'].search([('is_active', '=', True)])

        for active_alarm in active_alarms:
            logger = self.env['onpoint.logger'].search([('id', '=', active_alarm.logger_id.id)])
            logger.read_ftp_pointorange()

        self.env['onpoint.vw.logger.threshold'].search([]).send_alarm()


