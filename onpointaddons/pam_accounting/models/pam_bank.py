from odoo import models, fields, api

class PamBank(models.Model):
    _name = 'pam.bank'

    name = fields.Char(string='Nama', required=True)
    coa_id = fields.Many2one('pam.coa', string='Kode Akun', index=True)

