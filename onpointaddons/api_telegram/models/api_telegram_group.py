from odoo import api, fields, models


class ApiTelegramGroup(models.Model):
    _name = 'api.telegram.group'

    name = fields.Char(string='Group Name', required=True)
    chat_id = fields.Char(string='Chat Group ID', required=True)
