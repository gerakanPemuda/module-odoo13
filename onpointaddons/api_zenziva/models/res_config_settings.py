# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    zenziva_userkey = fields.Char(sting='Userkey', config_parameter='api.zenziva_userkey')
    zenziva_passkey = fields.Char(string='Passkey', config_parameter='api.zenziva_passkey')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res['zenziva_userkey'] = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_userkey',
                                                                                  default="")
        res['zenziva_passkey'] = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_passkey',
                                                                                 default="")
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('api.zenziva_userkey', self.zenziva_userkey)
        self.env['ir.config_parameter'].sudo().set_param('api.zenziva_passkey', self.zenziva_passkey)

        super(ResConfigSettings, self).set_values()
