from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamDepreciation(models.Model):
    _name = 'pam.depreciation'

    months = fields.Selection([
    	('1', 'Januari'),
    	('2', 'Februari'),
    	('3', 'Maret'),
    	('4', 'April'),
    	('5', 'Mei'),
    	('6', 'Juni'),
    	('7', 'Juli'),
    	('8', 'Agustus'),
    	('9', 'September'),
    	('10', 'Oktober'),
    	('11', 'November'),
    	('12', 'Desember'),
        ], string='Bulan')
    years = fields.Char(string='Tahun')
