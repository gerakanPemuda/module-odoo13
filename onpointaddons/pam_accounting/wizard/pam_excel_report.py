from odoo import models, fields, api, _

class PamExcelReport(models.TransientModel):
    _name = 'pam.excel.report'

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
