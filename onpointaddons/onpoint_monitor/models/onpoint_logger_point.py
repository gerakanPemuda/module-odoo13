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
    _inherits = {
        'onpoint.logger.owner': 'owner_id'
    }

    name = fields.Char(string='Point', default='General', required=True)
    code = fields.Char(string='Code', required=True, index=True)
    code_alt = fields.Char(string='Code in Trending File', compute='_compute_code_trending')
    code_source = fields.Char(string='Code Source', index=True)
    code_source_alt = fields.Char(string='Code  Source in Trending File', compute='_compute_code_trending')
    is_sensor = fields.Boolean(string='Sensor', default=False)
    is_alarm = fields.Boolean(string='Alarm', default=False)
    need_totalizer = fields.Boolean(string='Need Totalizer', default=False)
    function_name = fields.Char(string='Function Name')
    function_name_display = fields.Char(string='Function Display')
    owner_id = fields.Many2one('onpoint.logger.owner', ondedelete='cascade', required=True, index=True)
    alarm_type = fields.Selection([
        ('temperature', 'Temperature'),
        ('battery', 'Battery Voltage'),
        ('external', 'External Power'),
        ('signal', 'Signal Strength'),
        ('submerged', 'Submerged')
    ])

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        coa_ref = self.search(domain + args, limit=limit)
        return coa_ref.name_get()

    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            if record.code:
                name = record.code + ' - ' + record.name
            else:
                name = record.name

            result.append((record.id, name))
        return result

    def _compute_code_trending(self):
        for record in self:
            if record.code:
                point = record.code[0:2]
                point_index = record.code[2:4]
                record.code_alt = point + point_index.zfill(2)
            else:
                record.code_alt = ''

            if record.code_source:
                point_source = record.code_source[0:2]
                point_source_index = record.code_source[2:4]
                record.code_source_alt = point_source + point_source_index.zfill(2)
            else:
                record.code_source_alt = ''


