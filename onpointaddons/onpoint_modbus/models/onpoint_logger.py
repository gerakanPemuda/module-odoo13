from odoo import models, fields, api, _
from datetime import datetime, timezone, timedelta
from ftplib import FTP
import csv
import pandas as pd
import chardet
import math
import io
import logging

_logger = logging.getLogger(__name__)


class OnpointLogger(models.Model):
    _name = 'onpoint.logger'
    _inherit = ['onpoint.logger', 'onpoint.pointorange']

    mmim_line_ids = fields.One2many('onpoint.mmim.line', 'logger_id')

    def read_ftp_pointorange(self):
        record = super(OnpointLogger, self).read_ftp_pointorange()
        _logger.debug("Inherit Point Orange")

        # if self.mmim_line_ids:
        #     for channel in self.channel_ids:
        #         if channel.mmim_line_ids:
        #             for mmim_line in channel.mmim_line_ids:
        #                 mmim_line.write({
        #                     'data_write': channel.last_value
        #                 })
        #                 mmim_line.write_data()


class OnpointLoggerChannel(models.Model):
    _name = 'onpoint.logger.channel'
    _inherit = ['onpoint.logger.channel', 'onpoint.pointorange']

    mmim_line_ids = fields.One2many('onpoint.mmim.line', 'logger_channel_id')


