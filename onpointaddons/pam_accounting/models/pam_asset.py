from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PamUom(models.Model):
    _name = 'pam.uom'

    name = fields.Char(string='Nama', required=True)

class PamAsset(models.Model):
    _name = 'pam.asset'
    _inherit = ['mail.thread']

    def _get_code_year(self, entry_date):
        if entry_date:
            return datetime.strptime(entry_date, "%Y-%m-%d").strftime("%Y")
        else:
            return '2019'

    def _default_code_year(self):
        return self._get_code_year(datetime.now().strftime("%Y-%m-%d"))

    name = fields.Char(string='Nama', required=True)
    category_id = fields.Many2one('pam.asset.category', string='Kelompok Aset', index=True)
    coa_id = fields.Many2one('pam.coa', string='Kode Akun', required=True, index=True)
    # coa_id_name = fields.Char(string='Nama Akun', compute='compute_coa_id' ,index=True)
    item_id = fields.Many2one('pam.asset.item', string='Jenis Barang')
    qty = fields.Float(string='Qty')
    uom_id = fields.Many2one('pam.uom', string='Unit')
    journal_id = fields.Many2one('pam.journal.entry', string='No Bukti Voucher')
    vendor_id = fields.Many2one('pam.vendor', string='Vendor', index=True)
    spk = fields.Text(string='No. Bukti SPK/Kontrak Kerja')
    months = fields.Selection([
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
    years = fields.Char(string='Tahun', default=_default_code_year)
    depreciation_id = fields.Many2one('pam.asset.depreciation', string='Tarif')
    use_max = fields.Integer(string='Masa Manfaat Max')
    price = fields.Float(string='Perolehan Awal', default=0, required=True)
    price_add = fields.Float(string='Penambahan', default=0)
    price_subtract = fields.Float(string='Pengurangan', default=0)
    price_nett = fields.Float(string='Perolehan Akhir', compute='_compute_price_nett')
    remark = fields.Char(string='Keterangan')

    start_months = fields.Selection([
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
    ], string='Bulan')
    start_years = fields.Char(string='Tahun')

    line_ids = fields.One2many('pam.asset.line', 'asset_id')
    item_detail_ids = fields.One2many('pam.asset.item.detail', 'asset_id')

    @api.depends('coa_id')
    def compute_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name

    @api.depends('price', 'price_add', 'price_subtract')
    def _compute_price_nett(self):
        self.price_nett = (self.price + self.price_add) - self.price_subtract

    @api.onchange('depreciation_id')
    def set_use_max(self):
        if self.depreciation_id:
            # tariff = float(self.tariff)

            self.use_max = self.depreciation_id.use_max
        else:
            self.use_max = 0

    def set_depreciation(self):

        self.env['pam.asset.line'].search([('asset_id','=', self.id)]).unlink()

        depreciation_year = int(self.years)
        end_year = depreciation_year + self.use_max

        annual_depreciation = self.price / self.use_max
        monthly_depreciation = annual_depreciation / 12

        if self.start_months != False:
            change_year = int(self.start_years)
            change_month = int(self.start_months)


        annual_depreciation_change = self.price_nett / self.use_max
        monthly_depreciation_change = annual_depreciation_change / 12

        line_ids = []
        while depreciation_year <= end_year:

            detail_ids = []
            month_idx = 1

            annual_depreciation_price = 0

            while month_idx <= 12:

                monthly_depreciation_price = monthly_depreciation

                if self.start_months != False:
                    if depreciation_year >= change_year:
                        if depreciation_year == change_year:
                            if month_idx >= change_month:
                                monthly_depreciation_price = monthly_depreciation_change
                        else:
                            monthly_depreciation_price = monthly_depreciation_change


                if depreciation_year == int(self.years):
                    if month_idx < int(self.months):
                        monthly_depreciation_price = 0
                else:
                    if depreciation_year == int(end_year):
                        if month_idx > int(self.months) - 1:
                            monthly_depreciation_price = 0
    
                detail_vals = {
                    'months' : (str(month_idx)).zfill(2),
                    'years' : str(depreciation_year),
                    'price' : monthly_depreciation_price
                }

                row_detail = (0, 0, detail_vals)
                detail_ids.append(row_detail)
            
                annual_depreciation_price = annual_depreciation_price + monthly_depreciation_price
                month_idx = month_idx + 1
            

            line_vals = {
                'years' : str(depreciation_year),
                'price' : annual_depreciation_price,
                'detail_ids' : detail_ids
            }

            row_line = (0, 0, line_vals)
            line_ids.append(row_line)

            depreciation_year = depreciation_year + 1

        asset_data = self.env['pam.asset'].search([('id', '=', self.id)])

        asset_data.sudo().update({
            'line_ids' : line_ids
        })


class PamAssetLine(models.Model):
    _name = 'pam.asset.line'

    asset_id  = fields.Many2one('pam.asset', required=True, index=True, ondelete='cascade')
    years = fields.Char(string='Tahun', index=True)
    price = fields.Float(string='Biaya Penyusutan', default=0, required=True)
    detail_ids = fields.One2many('pam.asset.detail', 'asset_line_id')
    # required years yg di .py ini di pindah ke views karna errors reference

class PamAssetDetail(models.Model):
    _name = 'pam.asset.detail'

    asset_line_id  = fields.Many2one('pam.asset.line', required=True, index=True, ondelete='cascade')
    months = fields.Selection([
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
    ], default='01', index=True, string='Bulan', required=True)
    years = fields.Char(string='Tahun', index=True, required=True)
    price = fields.Float(string='Biaya Penyusutan', default=0, required=True)

class PamAssetItemDetail(models.Model):
    _name = 'pam.asset.item.detail'

    asset_id  = fields.Many2one('pam.asset')
    name = fields.Char(string='Kode', required=True)
    remark = fields.Text(string='Keterangan', required=True)
    department_id = fields.Many2one('hr.department', required=True, string='Departemen')
    is_activ = fields.Boolean(default=True, string='Aktiv')
