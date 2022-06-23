from odoo import models, fields, api, tools
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
import logging
import math

_logger = logging.getLogger(__name__)


class OnpointScadaParameter(models.Model):
    _name = 'onpoint.scada.parameter'

    name = fields.Char(required=True)
    line_ids = fields.One2many('onpoint.scada.sensor.parameter', 'parameter_id')


class OnpointScadaSensorParameter(models.Model):
    _name = 'onpoint.scada.sensor.parameter'

    parameter_id = fields.Many2one('onpoint.scada.parameter', required=True, string='Parameter', ondelete='cascade', index=True)
    unit_line_id = fields.Many2one('onpoint.scada.unit.line', required=True, string='Sensor', ondelete='cascade', index=True)
    parameter_value = fields.Float(default=0, required=True, string='Value')


