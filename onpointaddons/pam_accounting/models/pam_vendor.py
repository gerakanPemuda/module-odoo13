from odoo import models, fields, api


class PamVendor(models.Model):
    _name = 'pam.vendor'

    name = fields.Char(string='Nama', required=True)
    address = fields.Char(string='Alamat')
    phone = fields.Char(string='Telp/HP')
    notes = fields.Text(string='Catatan')

