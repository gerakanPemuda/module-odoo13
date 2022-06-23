from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
import logging
_logger = logging.getLogger(__name__)


class OnpointLoggerBrand(models.Model):
    _name = 'onpoint.logger.brand'
    _inherit = ['image.mixin']
    _inherits = {
        'onpoint.logger.owner': 'owner_id'
    }

    name = fields.Char(required=True)
    owner_id = fields.Many2one('onpoint.logger.owner', required=True, ondelete='cascade')
    convert_time = fields.Boolean(default=False)
