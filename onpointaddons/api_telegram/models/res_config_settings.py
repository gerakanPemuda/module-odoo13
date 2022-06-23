# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    telegram_token = fields.Char(sting='Userkey', config_parameter='api.telegram_token')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res['telegram_token'] = self.env['ir.config_parameter'].sudo().get_param('api_telegram.telegram_token',
                                                                                 default="")
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('api_telegram.telegram_token', self.telegram_token)

        super(ResConfigSettings, self).set_values()
