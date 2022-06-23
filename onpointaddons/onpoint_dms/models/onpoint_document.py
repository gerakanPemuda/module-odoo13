from odoo import models, fields, api


class OnpointDocument(models.Model):
    _name = 'onpoint.document'
    _order = 'name asc'
    _inherit = ['image.mixin']

    name = fields.Char(required=True)
    document_category_id = fields.Many2one('onpoint.document.category', string='Category', required=True, index=True)
    document_file = fields.Binary(string='Document')
    file_name = fields.Char(string='File Name')
