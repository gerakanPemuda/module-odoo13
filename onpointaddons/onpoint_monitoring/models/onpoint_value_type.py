from odoo import models, fields, api

class OnpointValueType(models.Model):
    _name = 'onpoint.value.type'
    
    name = fields.Char()