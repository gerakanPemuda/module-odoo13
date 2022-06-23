from odoo import models, fields, api, tools
from datetime import datetime, timezone, timedelta
import xlsxwriter
import base64
from io import StringIO, BytesIO
from odoo.exceptions import ValidationError
import logging
import math

_logger = logging.getLogger(__name__)


class OnpointMmimLine(models.Model):
    _name = 'onpoint.mmim.line'
    _inherit = 'onpoint.mmim.line'

    def get_last_data(self, line_id):
        last_value = self.env['onpoint.mmim.line'].search([('id', '=', line_id)])
        return last_value
