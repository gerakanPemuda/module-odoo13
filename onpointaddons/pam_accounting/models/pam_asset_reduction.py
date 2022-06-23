from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamAssetReduction(models.Model):
    _name = 'pam.asset.reduction'

    category_id = fields.Many2one('pam.asset.category')
    coa_id = fields.Many2one('pam.coa', string='Kode Akun', required=True, index=True)
    coa_id_name = fields.Char(string='Nama Akun')
    depreciation_id = fields.Many2one('pam.asset.depreciation', string='Tarif', required=True)
    depreciation_use_max = fields.Integer(related='depreciation_id.use_max' , string='Masa Manfaat Max')
    is_depreciation = fields.Boolean(string='Menyusut', default=True)

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name