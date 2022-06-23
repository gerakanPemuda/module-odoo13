from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

BALANCE_STATE_SELECTION = [
    ('active', 'Active'),
    ('inactive', 'Inactive')
]

class PamBalance(models.Model):
    _name = 'pam.balance'

    def _default_date(self):
        return (datetime.now() + relativedelta(hours=7)).date()

    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = current_year - 3
        results = []
        for year in range(min_year, current_year):
            str_year = str(year)
            results.append((str_year, str_year))
        return results


    name = fields.Char(index=True)
    period_month = fields.Selection([
        ('01', 'Januari'),
        ('02', 'Februari'),
        ('03', 'Maret'),
        ('04', 'April'),
        ('05', 'Mei'),
        ('06', 'Juni'),
        ('07', 'Juli'),
        ('08', 'Agustus'),
        ('09', 'September'),
        ('10', 'Oktober'),
        ('11', 'November'),
        ('12', 'Desember'),
    ], default='01', string='Bulan')
    period_year = fields.Selection(_get_years, string='Tahun', default=_default_year)
    state = fields.Selection(BALANCE_STATE_SELECTION, default='active')
    profit_after_tax = fields.Float(default=0)   
    line_ids = fields.One2many('pam.balance.line', 'balance_id')

    @api.model
    def create(self, vals):
        name = str(vals['period_year']) + str(vals['period_month'])

        vals.update({
            'name': name
        })
        res = super(PamBalance, self).create(vals)
        return res


class PamBalanceLine(models.Model):
    _name = 'pam.balance.line'

    balance_id = fields.Many2one('pam.balance', index=True, ondelete='cascade')
    balance_name = fields.Char('pam.balance', related='balance_id.name')
    balance_state = fields.Selection(BALANCE_STATE_SELECTION, 'pam.balance', related='balance_id.state')
    coa_id = fields.Many2one('pam.coa', string='Kode Akun', index=True)
    coa_id_name = fields.Char(string='Nama Akun', index=True)
    beginning_balance = fields.Float(string='Saldo Awal', required=True, default = 0)
    current_balance = fields.Float(string='Saldo Bulan Ini', required=True, default = 0)
    ending_balance = fields.Float(string='Saldo Akhir', required=True, default = 0)

    @api.onchange('coa_id')
    def onchange_coa_id_name(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name