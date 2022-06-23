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


class OnpointSchedulerMmim(models.Model):
    _name = 'onpoint.scheduler.mmim'

    @api.model
    def read_mmim_data(self):
        mmims = self.env['onpoint.mmim'].search([])

        for mmim in mmims:
            for line in mmim.line_ids:
                line.write_data()
                line.read_data()


