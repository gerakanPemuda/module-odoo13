from odoo import models, fields, api
from odoo.osv import expression
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
import logging
_logger = logging.getLogger(__name__)


class OnpointLoggerPoint(models.Model):
    _name = 'onpoint.logger.point'
    _inherit = 'onpoint.logger.point'

    def get_all(self, owner):
        points = self.search([('owner', '=', owner)])
        return points
