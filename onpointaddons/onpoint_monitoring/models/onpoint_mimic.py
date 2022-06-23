from odoo import models, fields, api
from odoo.http import request
from datetime import datetime
from time import mktime

import logging
_logger = logging.getLogger(__name__)


class OnpointMimic(models.Model):
    _name = 'onpoint.mimic'
    
    name = fields.Char(required=True)
    mimic_diagram = fields.Char(required=True)
    line_ids = fields.One2many('onpoint.mimic.line', 'mimic_id')


    @api.model
    def get_data(self):
        mimic_diagram = self.env['onpoint.mimic'].sudo().search_read([('id', '=', 1)], limit=1)

        return mimic_diagram


class OnpointMimicLine(models.Model):
    _name = 'onpoint.mimic.line'
    
    mimic_id = fields.Many2one('onpoint.mimic', string='Mimic Diagram', required=True, index=True, ondelete='cascade')
    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger')



