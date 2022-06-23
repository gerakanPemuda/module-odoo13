from odoo import models, fields, api

class OnpointValueUnit(models.Model):
    _name = 'onpoint.value.unit'
    
    name = fields.Char()