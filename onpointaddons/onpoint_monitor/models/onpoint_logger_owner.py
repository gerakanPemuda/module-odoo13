from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
import logging
_logger = logging.getLogger(__name__)


class OnpointLoggerOwner(models.Model):
    _name = 'onpoint.logger.owner'

    owner = fields.Selection([
        ('general', 'General'),
    ], default='general', string='Owner', required=True)