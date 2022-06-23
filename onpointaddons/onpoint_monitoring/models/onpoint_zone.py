from odoo import models, fields, api

class OnpointZone(models.Model):
    _name = 'onpoint.zone'
    
    name = fields.Char(required=True)
    remarks = fields.Text()