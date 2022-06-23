from odoo import models, fields, api


class OnpointDocumentCategory(models.Model):
    _name = 'onpoint.document.category'
    _order = 'name asc'

    name = fields.Char(required=True)
