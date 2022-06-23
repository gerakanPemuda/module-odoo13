from odoo import models, fields, api


class OnpointValueUnit(models.Model):
    _name = 'onpoint.value.unit'
    
    name = fields.Char()
    value_type_id = fields.Many2one('onpoint.value.type', required=True, index=True)
