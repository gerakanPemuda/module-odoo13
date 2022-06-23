from odoo import models, fields, api
from odoo.osv import expression
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamWaterAccount(models.Model):
    _name = 'pam.water.account'
    _order = "years, months"
    
    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = int(current_year) - 3
        results = []
        for year in range(min_year, current_year):
            results.append((str(year), str(year)))
        return results

    name = fields.Char(compute='compute_name')
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
    ], string='Bulan', default='01', required=True)
    years = fields.Selection(_get_years, string='Tahun Arus Kas', default=_default_year, required=True)
    start_date = fields.Date(compute='set_period_date')
    end_date = fields.Date(compute='set_period_date')

    this_month_water_bill = fields.Float(compute='get_this_month_water_bill', string='Penjualan Air Bln Lalu')
    this_month_administration_fee = fields.Float(compute='get_this_month_administration_fee', string='Beban Tetap Bln Lalu')
    payment_receive = fields.Float(string='Bulan Ini', required=True, default=0)
    payment_receive_until_this_month = fields.Float(string='Sampai Bulan Ini', required=True, default=0)
    water_productivity = fields.Float(string='Air yang diproduksi', required=True, default=0)
    water_distribution = fields.Float(string='Distribusi Air', required=True, default=0)
    water_accounted = fields.Float(string='Dipertanggungjawabkan', required=True, default=0)
    # non_revenue_water = fields.Float(string='Kehilangan Air', compute='calculate_nrw')
    recorded_account = fields.Float(string='Tercatat', required=True, default=0)
    number_of_customers = fields.Float(string='Jumlah Pelanggan', required=True, default=0)
    number_of_employee = fields.Float(string='Jumlah Pegawai', required=True, default=0) 

    def set_period_date(self):
        self.start_date = self.years + '-' + self.months + '-01'
        self.end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

    def compute_name(self):
        self.name = dict(self._fields['months'].selection).get(self.months) + " " + self.years

    @api.depends('months', 'years')
    def get_this_month_water_bill(self):
        water_bill = 0
        if self.start_date:
            sql = """
                select coalesce(sum(credit-debit), 0) as water_bill 
                from pam_journal_entry a
                inner join pam_journal_entry_line b on a.id = b.journal_entry_id
                inner join pam_coa c on c.id = b.coa_id
                where c.code = '31111110' and a.entry_date between %s and %s
                """

            self._cr.execute(sql, (self.start_date, self.end_date))
            result = self._cr.fetchone()

            if result:
                water_bill = result[0]

        self.this_month_water_bill = water_bill
    
    @api.depends('months', 'years')
    def get_this_month_administration_fee(self):
        administration_fee = 0
        if self.start_date:
            sql = """
                select coalesce(sum(credit-debit), 0) as administration_fee
                from pam_journal_entry a
                inner join pam_journal_entry_line b on a.id = b.journal_entry_id
                inner join pam_coa c on c.id = b.coa_id
                where c.code IN ('31111120', '31111130', '31111140', '31111150', '31111160')
                and a.entry_date between %s and %s
                """

            self._cr.execute(sql, (self.start_date, self.end_date))
            result = self._cr.fetchone()

            if result:
                administration_fee = result[0]
        
        self.this_month_administration_fee = administration_fee
