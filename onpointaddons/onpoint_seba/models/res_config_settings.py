# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ftp_seba_host = fields.Char(sting='Host', config_parameter='onpoint_seba.ftp_seba_host')
    ftp_seba_port = fields.Integer(string='Port', default="21", config_parameter='onpoint_seba.ftp_seba_port')
    ftp_seba_username = fields.Char(string='Username', config_parameter='onpoint_seba.ftp_seba_username')
    ftp_seba_password = fields.Char(string='Password', config_parameter='onpoint_seba.ftp_seba_password')
    ftp_seba_folder = fields.Char(string='Folder', config_parameter='onpoint_seba.ftp_seba_folder', default="logD3")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res['ftp_seba_host'] = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_host', default="")
        res['ftp_seba_port'] = int(self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_port', default=21))
        res['ftp_seba_username'] = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_username', default="")
        res['ftp_seba_password'] = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_password', default="")
        res['ftp_seba_folder'] = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_folder', default="logD3")

        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('onpoint_seba.ftp_seba_host', self.ftp_seba_host)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_seba.ftp_seba_port', self.ftp_seba_port)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_seba.ftp_seba_username', self.ftp_seba_username)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_seba.ftp_seba_password', self.ftp_seba_password)
        self.env['ir.config_parameter'].sudo().set_param('onpoint_seba.ftp_seba_folder', self.ftp_seba_folder)

        super(ResConfigSettings, self).set_values()
