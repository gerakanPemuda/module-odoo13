from odoo import models, fields, api

class OnpointDma(models.Model):
    _name = 'onpoint.dma'
    
    name = fields.Char(required=True)
    zone_id = fields.Many2one('onpoint.zone', required=True, index=True)
    remarks = fields.Text()