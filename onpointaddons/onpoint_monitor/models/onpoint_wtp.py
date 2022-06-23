from odoo import models, fields, api


class OnpointWtp(models.Model):
    _name = 'onpoint.wtp'

    name = fields.Char(required=True)
    remarks = fields.Text()