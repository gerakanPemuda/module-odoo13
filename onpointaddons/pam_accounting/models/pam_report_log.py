from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamReportLog(models.Model):
    _name = 'pam.report.log'

    name = fields.Char(string='Nama')
    report_type = fields.Char(string='Tipe Laporan')
    report_format = fields.Char(string='Format Laporan')