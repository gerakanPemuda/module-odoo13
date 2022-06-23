from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
import logging
_logger = logging.getLogger(__name__)


class OnpointLoggerThreshold(models.Model):
    _name = 'onpoint.logger.threshold'

    # Threshold
    overrange_enabled = fields.Boolean(default=False)
    overrange_threshold = fields.Float(string='Overrange', default='0')

    hi_hi_enabled = fields.Boolean(default=False)
    hi_hi_threshold = fields.Float(string='Hi Hi', default='0')

    hi_enabled = fields.Boolean(default=False)
    hi_threshold = fields.Float(string='Hi', default='0')

    lo_enabled = fields.Boolean(default=False)
    lo_threshold = fields.Float(string='Lo', default='0')

    lo_lo_enabled = fields.Boolean(default=False)
    lo_lo_threshold = fields.Float(string='Lo Lo', default='0')

    underrange_enabled = fields.Boolean(default=False)
    underrange_threshold = fields.Float(string='Underrange', default='0')
