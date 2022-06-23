from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamAssetSubtraction(models.Model):
    _name = 'pam.asset.subtraction'

    name = fields.Char(string='No. Pengurangan Asset')
    date = fields.Date(string='Tanggal Asset', required=True)
    state = fields.Selection([
        ('draft', 'Draf'),
        ('confirm', 'Konfirmasi')], string='Status', default='draft')
    line_ids = fields.One2many('pam.asset.subtraction.line', 'subtraction_id')

    def to_confirm(self):
        asset_item_id = self.env['pam.asset.item.detail'].search([('name', '=', self.line_ids.code_id.name)])
        asset_item_id.update({
            'is_activ': False
        })

        self.write({
            'name': self.env['ir.sequence'].next_by_code('pam.asset.subtraction.sequence') or '',
            'state': 'confirm'
        })


class PamAssetSubtractionLine(models.Model):
    _name = 'pam.asset.subtraction.line'

    subtraction_id = fields.Many2one('pam.asset.subtraction')
    code_id = fields.Many2one('pam.asset.item.detail', string='Kode Barang', required=True)
    remark_id = fields.Text(string='Detail Barang')
    department_id = fields.Char(string='Departemen')
    remark = fields.Text(string='Keterangan', required=True)

    @api.onchange('code_id')
    def onchange_code_id(self):
        if self.code_id:
            self.remark_id = self.code_id.remark
        if self.code_id:
            self.department_id = self.code_id.department_id.name
