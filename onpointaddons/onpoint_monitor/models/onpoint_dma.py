from odoo import models, fields, api
from datetime import datetime, timedelta


class OnpointDma(models.Model):
    _name = 'onpoint.dma'

    name = fields.Char(required=True)
    zone_id = fields.Many2one('onpoint.zone', index=True)
    remarks = fields.Text()
    logger_ids = fields.One2many('onpoint.logger', 'dma_id')
