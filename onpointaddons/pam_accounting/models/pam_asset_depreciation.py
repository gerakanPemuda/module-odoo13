from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PamAssetDepreciation(models.Model):
    _name = 'pam.asset.depreciation'


    name = fields.Float(string='Tarif', required=True)
    use_max = fields.Integer(string='Masa Manfaat Max', required=True)