# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ftp_pointorange_host = fields.Char(sting='Host', config_parameter='onpoint_pointorange.ftp_pointorange_host')
    ftp_pointorange_port = fields.Integer(string='Port', default="21",
                                          config_parameter='onpoint_pointorange.ftp_pointorange_port')
    ftp_pointorange_username = fields.Char(string='Username',
                                           config_parameter='onpoint_pointorange.ftp_pointorange_username')
    ftp_pointorange_password = fields.Char(string='Password',
                                           config_parameter='onpoint_pointorange.ftp_pointorange_password')
    ftp_pointorange_folder = fields.Char(string='Folder', config_parameter='onpoint_pointorange.ftp_pointorange_folder',
                                         default="logD3")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res['ftp_pointorange_host'] = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_host', default="")
        res['ftp_pointorange_port'] = int(
            self.env['ir.config_parameter'].sudo().get_param('onpoint_pointorange.ftp_pointorange_port', default=21))
        res['ftp_pointorange_username'] = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_username', default="")
        res['ftp_pointorange_password'] = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_password', default="")
        res['ftp_pointorange_folder'] = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_folder', default="logD3")

        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('onpoint_pointorange.ftp_pointorange_host',
                                                         self.ftp_pointorange_host)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_pointorange.ftp_pointorange_port',
                                                         self.ftp_pointorange_port)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_pointorange.ftp_pointorange_username',
                                                         self.ftp_pointorange_username)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_pointorange.ftp_pointorange_password',
                                                         self.ftp_pointorange_password)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_pointorange.ftp_pointorange_folder',
                                                         self.ftp_pointorange_folder)

        super(ResConfigSettings, self).set_values()

    def act_testing_connection(self):
        result = self.env['onpoint.logger'].testing_ftp_connection()
        return True

