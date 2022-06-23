from odoo import api, fields, models


class OnpointTelegramGroup(models.Model):
    _name = 'onpoint.telegram.group'

    name = fields.Char(string='Group Name', required=True)
    chat_id = fields.Char(string='Chat Group ID', required=True)
