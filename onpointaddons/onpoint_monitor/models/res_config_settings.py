# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    time_zone = fields.Selection([
        ('7', 'Waktu Indonesia bagian Barat (WIB)'),
        ('8', 'Waktu Indonesia bagian Tengah (WITA)'),
        ('9', 'Waktu Indonesia bagian Timur (WIT)'),
    ], default='7', string='Timezone', required=True)
    inactive_days = fields.Integer(string='Inactive Days Warning', default=2)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res['time_zone'] = self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.time_zone', default="7")
        res['inactive_days'] = int(self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.inactive_days', default=2))

        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('onpoint_monitor.time_zone', self.time_zone)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_monitor.inactive_days', int(self.inactive_days))

        super(ResConfigSettings, self).set_values()
