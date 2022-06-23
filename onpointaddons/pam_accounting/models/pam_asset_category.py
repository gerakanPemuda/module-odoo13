from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PamAssetCategory(models.Model):
    _name = 'pam.asset.category'

    # name = fields.Selection([
    # 	('land', 'Tanah dan Hak Atas Tanah'),
    # 	('fount', 'Sumber Air'),
    # 	('pump', 'Instalasi Perpompaan'),
    # 	('ipa', 'Instalasi Pengolahan Air'),
    # 	('transdis', 'Instalasi Transmisi dan Distribusi'),
    # 	('building', 'Bangunan dan Gedung'),
    # 	('nonwater', 'Instalasi Non Pabrik Air'),
    # 	('transportation', 'Alat Pengangkut-Kendaraan'),
    # 	('furniture', 'Perabotan dan Inventaris Kantor')
    # 	], default='land', required=True)
    name = fields.Char(string='Kategori Asset', required=True, index=True)
    sequence = fields.Integer(string='Urutan')
    coa_id_debit = fields.Many2one('pam.coa', string='Kode Akun Debit', required=True, index=True)
    coa_id_d_name = fields.Char(related='coa_id_debit.name')
    coa_id_credit = fields.Many2one('pam.coa', string='Kode Akun Credit', required=True, index=True)
    coa_id_c_name = fields.Char(related='coa_id_credit.name')
    group_pay = fields.Many2one('pam.asset.group.pay', string='Kelompok Biaya', required=True, index=True)
    reduction_ids = fields.One2many('pam.asset.reduction', 'category_id')