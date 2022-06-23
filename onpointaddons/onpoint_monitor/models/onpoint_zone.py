from odoo import models, fields, api


class OnpointZone(models.Model):
    _name = 'onpoint.zone'

    name = fields.Char(required=True)
    wtp_id = fields.Many2one('onpoint.wtp', index=True)
    remarks = fields.Text()