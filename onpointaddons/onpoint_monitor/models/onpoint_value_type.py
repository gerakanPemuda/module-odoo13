from odoo import models, fields, api


class OnpointValueType(models.Model):
    _name = 'onpoint.value.type'

    name = fields.Char()
    need_totalizer = fields.Boolean(string='Need Totalizer', default=False)
