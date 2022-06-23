from odoo import api, fields, models

class Company(models.Model):
    _inherit = 'res.company'

    api_login = fields.Char(string='API Login')
    api_password = fields.Char(string='API Password')