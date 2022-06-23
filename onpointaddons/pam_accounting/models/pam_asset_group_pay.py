from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PamAssetGroupPay(models.Model):
    _name = 'pam.asset.group.pay'

    name = fields.Char(string='Kelompok Biaya', required=True)