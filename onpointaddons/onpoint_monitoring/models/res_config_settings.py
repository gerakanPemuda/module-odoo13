# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_host = fields.Char(default='www.wtccloud.net', default_model='onpoint.seba.ftp', required=True)
    default_username = fields.Char(default='loggersD3', default_model='onpoint.seba.ftp', required=True)
    default_password = fields.Char(default='loggersD3', default_model='onpoint.seba.ftp', required=True)
