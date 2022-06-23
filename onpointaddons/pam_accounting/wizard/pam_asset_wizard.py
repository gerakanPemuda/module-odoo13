from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamAssetWizard(models.TransientModel):
    _name = 'pam.asset.wizard'

    name = fields.Char()
    journal_entry_id  = fields.Many2one('pam.journal.entry', required=True, index=True, ondelete='cascade')
    line_ids = fields.One2many('pam.asset.line.wizard', 'asset_id')

    def create_asset(self):
        for line in self.line_ids:
            asset_reduction = self.env['pam.asset.reduction'].search([('coa_id','=',line.coa_id.id)])
            # raise ValidationError(_("%s")%(line.coa_id.id))
            if asset_reduction:
                # raise ValidationError(_("%s")%(asset_reduction))
                create_asset = self.env['pam.asset'].create({
                    'name' : self.journal_entry_id.remark,
                    'journal_id': self.journal_entry_id.id,
                    'category_id' : asset_reduction.category_id.id,
                    'coa_id' : line.coa_id.id,
                    'qty' : line.qty,
                    'uom_id' : line.uom_id.id,
                    'get_month' : ((datetime.strptime(self.journal_entry_id.entry_date, "%Y-%m-%d")).strftime("%m")),
                    'years' : (datetime.strptime(self.journal_entry_id.entry_date, "%Y-%m-%d")).strftime("%Y"),
                    'depreciation_id' : asset_reduction.depreciation_id.id,
                    'use_max' : asset_reduction.depreciation_use_max,
                    'price' : line.price
                    })
                if asset_reduction.is_depreciation == True:
                    create_asset.set_depreciation()

                if self.journal_entry_id.state == 'draft':
                    sequence = self.journal_entry_id.code_number + '/' + self.journal_entry_id.code_journal_type + '/' + self.journal_entry_id.code_month + '/' + self.journal_entry_id.code_year
                    self.journal_entry_id.write({'name' : sequence, 'state' : 'submit'})
                    self.journal_entry_id.message_post(body="Journal Submitted")
                else:
                    if self.journal_entry_id.state == 'paid':
                        self.journal_entry_id.payment_submit()

                    self.journal_entry_id.write({'state' : 'submit'})
                    self.journal_entry_id.message_post(body="Journal Submitted")


class PamAssetLineWizard(models.TransientModel):
    _name = 'pam.asset.line.wizard'

    asset_id = fields.Many2one('pam.asset.wizard')
    coa_id = fields.Many2one('pam.coa', string='Kode Perkiraan', required=True, index=True, domain="([('transactional', '=', True)])")
    price = fields.Float(string='Harga Jual', required=True)
    qty = fields.Float(string='Qty')
    uom_id = fields.Many2one('pam.uom', string='Unit')