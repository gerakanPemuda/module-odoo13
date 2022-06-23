# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api

class sh_theme_preview_wizard(models.TransientModel):
    _name = "sh.theme.preview.wizard"
    _description = 'Theme Preview Wizard'    
    
    img_src = fields.Char(string = "Image Src")
    
    