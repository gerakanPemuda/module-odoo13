from odoo import models, fields, api, exceptions, _
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PamAssetItem(models.Model):
    _name = 'pam.asset.item'

    name = fields.Char(string='Nama Barang')