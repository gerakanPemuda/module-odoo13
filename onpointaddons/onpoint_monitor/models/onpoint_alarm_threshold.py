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


class OnpointAlarmThreshold(models.Model):
    _name = 'onpoint.alarm.threshold'
    _rec_name = 'alarm_type'

    alarm_type = fields.Selection([
        ('temperature', 'Temperature'),
        ('battery', 'Battery Voltage'),
        ('signal', 'Signal Strength'),
        ('submerged', 'Submerged')
    ])
    normal_min = fields.Float(string='Normal')
    normal_max = fields.Float(string='Normal')
    medium_min = fields.Float(string='Medium')
    medium_max = fields.Float(string='Medium')
    danger_min = fields.Float(string='Danger')
    danger_max = fields.Float(string='Danger')
    normal_submerged = fields.Integer(string='Submersion Days', default='0')
    medium_submerged = fields.Integer(string='Submersion Days', default='1')
    danger_submerged = fields.Integer(string='Submersion Days', default='2')
