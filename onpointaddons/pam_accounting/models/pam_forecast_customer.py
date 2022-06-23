from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta
from calendar import monthrange

import logging
_logger = logging.getLogger(__name__)

class PamCustomerClasification(models.Model):
    _name = 'pam.customer.classification'

    name = fields.Char(string='Klasifikasi', required=True)
    subscription_fee = fields.Float(string='Biaya Abonemen', required=True, default=0)
    installation_fee = fields.Float(string='Biaya Pemasangan', required=True, default=0)


class PamForecastCustomer(models.Model):
    _name = 'pam.forecast.customer'
    _rec_name = 'years'
    _description = 'Rencana Pelanggan'
    _inherit = ['mail.thread']

    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = current_year - 2
        results = []
        for year in range(min_year, current_year):
            str_year = str(year)
            results.append((str_year, str_year))
        return results

    years = fields.Selection(_get_years, string='Tahun Anggaran', default=_default_year)

    water_usage = fields.Float(string='Elastisitas Pemakaian Air', required=True)
    rate_increase = fields.Float(string='Kenaikan Tarif', required=True)
    rate_increase_month =  fields.Selection([
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
    ], default='01', required=True, string='Kenaikan pada Bulan')

    new_customer_ids= fields.One2many('pam.forecast.customer.line', 'forecast_customer_id')
    lost_customer_ids= fields.One2many('pam.forecast.customer.line', 'forecast_customer_id')
    total_customer_ids= fields.One2many('pam.forecast.customer.line', 'forecast_customer_id')
    installment_customer_new_ids= fields.One2many('pam.forecast.customer.line', 'forecast_customer_id')
    subscription_customer_new_ids= fields.One2many('pam.forecast.customer.line', 'forecast_customer_id')
    subscription_customer_total_ids= fields.One2many('pam.forecast.customer.line', 'forecast_customer_id')
    amount_ids= fields.One2many('pam.forecast.customer.line', 'forecast_customer_id')
    sales_ids= fields.One2many('pam.forecast.customer.line', 'forecast_customer_id')

    def get_classifications(self):
        classifications = self.env['pam.customer.classification'].search([])

        data = []
        for classification in classifications:
            vals = {
                'forecast_customer_id' : self.id,
                'customer_classification_id' : classification.id,
                'subscription_fee_amount' : classification.subscription_fee / 1000,
                'installment_fee_amount' : classification.installation_fee / 1000
            }

            row = (0, 0, vals)
            data.append(row)
        
        self.env['pam.forecast.customer.line'].search([('forecast_customer_id','=', self.id)]).unlink()

        customer = self.env['pam.forecast.customer'].search([('id', '=', self.id)])

        customer.update({
            'new_customer_ids': data
        })


class PamForecastCustomerLine(models.Model):
    _name = 'pam.forecast.customer.line'

    forecast_customer_id  = fields.Many2one('pam.forecast.customer', required=True, index=True, ondelete='cascade')
    rate_increase = fields.Float('pam.forecast.customer', related='forecast_customer_id.rate_increase')    
    rate_increase_month = fields.Selection('pam.forecast.customer', related='forecast_customer_id.rate_increase_month')    
    customer_classification_id = fields.Many2one('pam.customer.classification', required=True, index=True)

    month_1_new       = fields.Integer(string='I', default=0, required=True)
    month_2_new       = fields.Integer(string='II', default=0, required=True)
    month_3_new       = fields.Integer(string='III', default=0, required=True)
    month_4_new       = fields.Integer(string='IV',default=0, required=True)
    month_5_new       = fields.Integer(string='V',default=0, required=True)
    month_6_new       = fields.Integer(string='VI',default=0, required=True)
    month_7_new       = fields.Integer(string='VII',default=0, required=True)
    month_8_new       = fields.Integer(string='VIII',default=0, required=True)
    month_9_new       = fields.Integer(string='IX',default=0, required=True)
    month_10_new      = fields.Integer(string='X',default=0, required=True)
    month_11_new      = fields.Integer(string='XI',default=0, required=True)
    month_12_new      = fields.Integer(string='XII',default=0, required=True)
    sub_total_new     = fields.Integer(string='Total',default=0, compute='_compute_sub_total', store=True)

    month_1_lost       = fields.Integer(string='I', default=0, required=True)
    month_2_lost       = fields.Integer(string='II', default=0, required=True)
    month_3_lost       = fields.Integer(string='III', default=0, required=True)
    month_4_lost       = fields.Integer(string='IV',default=0, required=True)
    month_5_lost       = fields.Integer(string='V',default=0, required=True)
    month_6_lost       = fields.Integer(string='VI',default=0, required=True)
    month_7_lost       = fields.Integer(string='VII',default=0, required=True)
    month_8_lost       = fields.Integer(string='VIII',default=0, required=True)
    month_9_lost       = fields.Integer(string='IX',default=0, required=True)
    month_10_lost      = fields.Integer(string='X',default=0, required=True)
    month_11_lost      = fields.Integer(string='XI',default=0, required=True)
    month_12_lost      = fields.Integer(string='XII',default=0, required=True)
    sub_total_lost     = fields.Integer(string='Total',default=0, compute='_compute_sub_total_lost', store=True)

    total_last_year       = fields.Integer(string='Jumlah Sambungan Tahun Sebelumnya', default=0, required=True)
    month_1_total       = fields.Integer(string='I', compute='_compute_total', default=0, store=True)
    month_2_total       = fields.Integer(string='II', compute='_compute_total', default=0, store=True)
    month_3_total       = fields.Integer(string='III', compute='_compute_total', default=0, store=True)
    month_4_total       = fields.Integer(string='IV', compute='_compute_total', default=0, store=True)
    month_5_total       = fields.Integer(string='V', compute='_compute_total', default=0, store=True)
    month_6_total       = fields.Integer(string='VI', compute='_compute_total', default=0, store=True)
    month_7_total       = fields.Integer(string='VII', compute='_compute_total', default=0, store=True)
    month_8_total       = fields.Integer(string='VIII', compute='_compute_total', default=0, store=True)
    month_9_total       = fields.Integer(string='IX', compute='_compute_total', default=0, store=True)
    month_10_total      = fields.Integer(string='X', compute='_compute_total', default=0, store=True)
    month_11_total      = fields.Integer(string='XI', compute='_compute_total', default=0, store=True)
    month_12_total      = fields.Integer(string='XII', compute='_compute_total', default=0, store=True)

    subscription_fee = fields.Float(string='Biaya Abonemen Pelanggan', default=0, compute='_compute_subscription')  #Real
    subscription_fee_amount = fields.Float(string='Biaya Abonemen Pelanggan', required=True, default=0)             #Divide by 1000

    month_1_subscription_new       = fields.Float(string='I', compute='_compute_subscription', default=0)
    month_2_subscription_new       = fields.Float(string='II', compute='_compute_subscription', default=0)
    month_3_subscription_new       = fields.Float(string='III', compute='_compute_subscription', default=0)
    month_4_subscription_new       = fields.Float(string='IV', compute='_compute_subscription', default=0)
    month_5_subscription_new       = fields.Float(string='V', compute='_compute_subscription', default=0)
    month_6_subscription_new       = fields.Float(string='VI', compute='_compute_subscription', default=0)
    month_7_subscription_new       = fields.Float(string='VII', compute='_compute_subscription', default=0)
    month_8_subscription_new       = fields.Float(string='VIII', compute='_compute_subscription', default=0)
    month_9_subscription_new       = fields.Float(string='IX', compute='_compute_subscription', default=0)
    month_10_subscription_new      = fields.Float(string='X', compute='_compute_subscription', default=0)
    month_11_subscription_new      = fields.Float(string='XI', compute='_compute_subscription', default=0)
    month_12_subscription_new      = fields.Float(string='XII', compute='_compute_subscription', default=0)
    sub_total_subscription_new     = fields.Float(string='Total', compute='_compute_subscription', default=0, store=True)

    month_1_subscription_amount_new       = fields.Float(string='I', compute='_compute_subscription', default=0)
    month_2_subscription_amount_new       = fields.Float(string='II', compute='_compute_subscription', default=0)
    month_3_subscription_amount_new       = fields.Float(string='III', compute='_compute_subscription', default=0)
    month_4_subscription_amount_new       = fields.Float(string='IV', compute='_compute_subscription', default=0)
    month_5_subscription_amount_new       = fields.Float(string='V', compute='_compute_subscription', default=0)
    month_6_subscription_amount_new       = fields.Float(string='VI', compute='_compute_subscription', default=0)
    month_7_subscription_amount_new       = fields.Float(string='VII', compute='_compute_subscription', default=0)
    month_8_subscription_amount_new       = fields.Float(string='VIII', compute='_compute_subscription', default=0)
    month_9_subscription_amount_new       = fields.Float(string='IX', compute='_compute_subscription', default=0)
    month_10_subscription_amount_new      = fields.Float(string='X', compute='_compute_subscription', default=0)
    month_11_subscription_amount_new      = fields.Float(string='XI', compute='_compute_subscription', default=0)
    month_12_subscription_amount_new      = fields.Float(string='XII', compute='_compute_subscription', default=0)
    sub_total_subscription_amount_new     = fields.Float(string='Total', compute='_compute_subscription', default=0, store=True)

    month_1_subscription_total       = fields.Float(string='I', compute='_compute_subscription', default=0)
    month_2_subscription_total       = fields.Float(string='II', compute='_compute_subscription', default=0)
    month_3_subscription_total       = fields.Float(string='III', compute='_compute_subscription', default=0)
    month_4_subscription_total       = fields.Float(string='IV', compute='_compute_subscription', default=0)
    month_5_subscription_total       = fields.Float(string='V', compute='_compute_subscription', default=0)
    month_6_subscription_total       = fields.Float(string='VI', compute='_compute_subscription', default=0)
    month_7_subscription_total       = fields.Float(string='VII', compute='_compute_subscription', default=0)
    month_8_subscription_total       = fields.Float(string='VIII', compute='_compute_subscription', default=0)
    month_9_subscription_total       = fields.Float(string='IX', compute='_compute_subscription', default=0)
    month_10_subscription_total      = fields.Float(string='X', compute='_compute_subscription', default=0)
    month_11_subscription_total      = fields.Float(string='XI', compute='_compute_subscription', default=0)
    month_12_subscription_total      = fields.Float(string='XII', compute='_compute_subscription', default=0)
    sub_total_subscription_total     = fields.Float(string='Total', compute='_compute_subscription', default=0, store=True)

    month_1_subscription_amount_total       = fields.Float(string='I', compute='_compute_subscription', default=0)
    month_2_subscription_amount_total       = fields.Float(string='II', compute='_compute_subscription', default=0)
    month_3_subscription_amount_total       = fields.Float(string='III', compute='_compute_subscription', default=0)
    month_4_subscription_amount_total       = fields.Float(string='IV', compute='_compute_subscription', default=0)
    month_5_subscription_amount_total       = fields.Float(string='V', compute='_compute_subscription', default=0)
    month_6_subscription_amount_total       = fields.Float(string='VI', compute='_compute_subscription', default=0)
    month_7_subscription_amount_total       = fields.Float(string='VII', compute='_compute_subscription', default=0)
    month_8_subscription_amount_total       = fields.Float(string='VIII', compute='_compute_subscription', default=0)
    month_9_subscription_amount_total       = fields.Float(string='IX', compute='_compute_subscription', default=0)
    month_10_subscription_amount_total      = fields.Float(string='X', compute='_compute_subscription', default=0)
    month_11_subscription_amount_total      = fields.Float(string='XI', compute='_compute_subscription', default=0)
    month_12_subscription_amount_total      = fields.Float(string='XII', compute='_compute_subscription', default=0)
    sub_total_subscription_amount_total     = fields.Float(string='Total', compute='_compute_subscription', default=0, store=True)

    water_usage          = fields.Float(string='Pemakaian Air', default=0, required=True)
    price_average = fields.Float(string='Harga Rata-rata Air/m3 ', default=0, required=True)

    month_1_amount       = fields.Float(string='I', default=0, compute='_compute_amount', store=True)
    month_2_amount       = fields.Float(string='II', default=0, compute='_compute_amount', store=True)
    month_3_amount       = fields.Float(string='III', default=0, compute='_compute_amount', store=True)
    month_4_amount       = fields.Float(string='IV',default=0, compute='_compute_amount', store=True)
    month_5_amount       = fields.Float(string='V',default=0, compute='_compute_amount', store=True)
    month_6_amount       = fields.Float(string='VI',default=0, compute='_compute_amount', store=True)
    month_7_amount       = fields.Float(string='VII',default=0, compute='_compute_amount', store=True)
    month_8_amount       = fields.Float(string='VIII',default=0, compute='_compute_amount', store=True)
    month_9_amount       = fields.Float(string='IX',default=0, compute='_compute_amount', store=True)
    month_10_amount      = fields.Float(string='X',default=0, compute='_compute_amount', store=True)
    month_11_amount      = fields.Float(string='XI',default=0, compute='_compute_amount', store=True)
    month_12_amount      = fields.Float(string='XII',default=0, compute='_compute_amount', store=True)
    month_1       = fields.Float(string='I', default=0, compute='_compute_amount', store=True)
    month_2       = fields.Float(string='II', default=0, compute='_compute_amount', store=True)
    month_3       = fields.Float(string='III', default=0, compute='_compute_amount', store=True)
    month_4       = fields.Float(string='IV',default=0, compute='_compute_amount', store=True)
    month_5       = fields.Float(string='V',default=0, compute='_compute_amount', store=True)
    month_6       = fields.Float(string='VI',default=0, compute='_compute_amount', store=True)
    month_7       = fields.Float(string='VII',default=0, compute='_compute_amount', store=True)
    month_8       = fields.Float(string='VIII',default=0, compute='_compute_amount', store=True)
    month_9       = fields.Float(string='IX',default=0, compute='_compute_amount', store=True)
    month_10      = fields.Float(string='X',default=0, compute='_compute_amount', store=True)
    month_11      = fields.Float(string='XI',default=0, compute='_compute_amount', store=True)
    month_12      = fields.Float(string='XII',default=0, compute='_compute_amount', store=True)
    month_1_sales       = fields.Float(string='I', default=0, compute='_compute_amount', store=True)
    month_2_sales       = fields.Float(string='II', default=0, compute='_compute_amount', store=True)
    month_3_sales       = fields.Float(string='III', default=0, compute='_compute_amount', store=True)
    month_4_sales       = fields.Float(string='IV',default=0, compute='_compute_amount', store=True)
    month_5_sales       = fields.Float(string='V',default=0, compute='_compute_amount', store=True)
    month_6_sales       = fields.Float(string='VI',default=0, compute='_compute_amount', store=True)
    month_7_sales       = fields.Float(string='VII',default=0, compute='_compute_amount', store=True)
    month_8_sales       = fields.Float(string='VIII',default=0, compute='_compute_amount', store=True)
    month_9_sales       = fields.Float(string='IX',default=0, compute='_compute_amount', store=True)
    month_10_sales      = fields.Float(string='X',default=0, compute='_compute_amount', store=True)
    month_11_sales      = fields.Float(string='XI',default=0, compute='_compute_amount', store=True)
    month_12_sales      = fields.Float(string='XII',default=0, compute='_compute_amount', store=True)

    installment_fee = fields.Float(string='Biaya Pemasangan Baru', default=0, compute='_compute_installment')  #Real
    installment_fee_amount = fields.Float(string='Biaya Pemasangan Baru', required=True, default=0)             #Divide by 1000

    month_1_installment_new       = fields.Float(string='I', compute='_compute_installment', default=0)
    month_2_installment_new       = fields.Float(string='II', compute='_compute_installment', default=0)
    month_3_installment_new       = fields.Float(string='III', compute='_compute_installment', default=0)
    month_4_installment_new       = fields.Float(string='IV', compute='_compute_installment', default=0)
    month_5_installment_new       = fields.Float(string='V', compute='_compute_installment', default=0)
    month_6_installment_new       = fields.Float(string='VI', compute='_compute_installment', default=0)
    month_7_installment_new       = fields.Float(string='VII', compute='_compute_installment', default=0)
    month_8_installment_new       = fields.Float(string='VIII', compute='_compute_installment', default=0)
    month_9_installment_new       = fields.Float(string='IX', compute='_compute_installment', default=0)
    month_10_installment_new      = fields.Float(string='X', compute='_compute_installment', default=0)
    month_11_installment_new      = fields.Float(string='XI', compute='_compute_installment', default=0)
    month_12_installment_new      = fields.Float(string='XII', compute='_compute_installment', default=0)
    sub_total_installment_new     = fields.Float(string='Total', compute='_compute_installment', default=0, store=True)

    month_1_installment_amount_new       = fields.Float(string='I', compute='_compute_installment', default=0)
    month_2_installment_amount_new       = fields.Float(string='II', compute='_compute_installment', default=0)
    month_3_installment_amount_new       = fields.Float(string='III', compute='_compute_installment', default=0)
    month_4_installment_amount_new       = fields.Float(string='IV', compute='_compute_installment', default=0)
    month_5_installment_amount_new       = fields.Float(string='V', compute='_compute_installment', default=0)
    month_6_installment_amount_new       = fields.Float(string='VI', compute='_compute_installment', default=0)
    month_7_installment_amount_new       = fields.Float(string='VII', compute='_compute_installment', default=0)
    month_8_installment_amount_new       = fields.Float(string='VIII', compute='_compute_installment', default=0)
    month_9_installment_amount_new       = fields.Float(string='IX', compute='_compute_installment', default=0)
    month_10_installment_amount_new      = fields.Float(string='X', compute='_compute_installment', default=0)
    month_11_installment_amount_new      = fields.Float(string='XI', compute='_compute_installment', default=0)
    month_12_installment_amount_new      = fields.Float(string='XII', compute='_compute_installment', default=0)
    sub_total_installment_amount_new     = fields.Float(string='Total', compute='_compute_installment', default=0, store=True)

    @api.depends('month_1_new', 'month_2_new', 'month_3_new', 'month_4_new', 'month_5_new', 'month_6_new', 'month_7_new', 'month_8_new', 'month_9_new', 'month_10_new', 'month_11_new', 'month_12_new')
    def _compute_sub_total_new(self):

        self.sub_total_new = self.month_1_new + self.month_2_new + self.month_3_new + self.month_4_new + self.month_5_new + self.month_6_new + self.month_7_new + self.month_8_new + self.month_9_new + self.month_10_new + self.month_11_new + self.month_12_new

    @api.depends('month_1_lost', 'month_2_lost', 'month_3_lost', 'month_4_lost', 'month_5_lost', 'month_6_lost', 'month_7_lost', 'month_8_lost', 'month_9_lost', 'month_10_lost', 'month_11_lost', 'month_12_lost')
    def _compute_sub_total_lost(self):

        self.sub_total_lost = self.month_1_lost + self.month_2_lost + self.month_3_lost + self.month_4_lost + self.month_5_lost + self.month_6_lost + self.month_7_lost + self.month_8_lost + self.month_9_lost + self.month_10_lost + self.month_11_lost + self.month_12_lost

    def _count_total(self, month_previous, month_new, month_lost):
        return month_previous + month_new - month_lost

    @api.depends('total_last_year', 'month_1_new', 'month_2_new', 'month_3_new', 'month_4_new', 'month_5_new', 'month_6_new', 'month_7_new', 'month_8_new', 'month_9_new', 'month_10_new', 'month_11_new', 'month_12_new',
                 'month_1_lost', 'month_2_lost', 'month_3_lost', 'month_4_lost', 'month_5_lost', 'month_6_lost', 'month_7_lost', 'month_8_lost', 'month_9_lost', 'month_10_lost', 'month_11_lost', 'month_12_lost')
    def _compute_total(self):
        self.month_1_total = self._count_total(self.total_last_year, self.month_1_new, self.month_1_lost)
        self.month_2_total = self._count_total(self.month_1_total, self.month_2_new, self.month_2_lost)
        self.month_3_total = self._count_total(self.month_2_total, self.month_3_new, self.month_3_lost)
        self.month_4_total = self._count_total(self.month_3_total, self.month_4_new, self.month_4_lost)
        self.month_5_total = self._count_total(self.month_4_total, self.month_5_new, self.month_5_lost)
        self.month_6_total = self._count_total(self.month_5_total, self.month_6_new, self.month_6_lost)
        self.month_7_total = self._count_total(self.month_6_total, self.month_7_new, self.month_7_lost)
        self.month_8_total = self._count_total(self.month_7_total, self.month_8_new, self.month_8_lost)
        self.month_9_total = self._count_total(self.month_8_total, self.month_9_new, self.month_9_lost)
        self.month_10_total = self._count_total(self.month_9_total, self.month_10_new, self.month_10_lost)
        self.month_11_total = self._count_total(self.month_10_total, self.month_11_new, self.month_11_lost)
        self.month_12_total = self._count_total(self.month_11_total, self.month_12_new, self.month_12_lost)

    def _count_subscription_amount_new(self, subscription_fee_amount, month_new):
        return round(subscription_fee_amount * month_new)

    def _count_subscription_amount_total(self, subscription_fee_amount, month_total):
        return round(subscription_fee_amount * month_total)

    @api.depends('subscription_fee_amount')
    def _compute_subscription(self):

        self.subscription_fee = self.subscription_fee_amount * 1000

        self.month_1_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_1_new)
        self.month_2_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_2_new)
        self.month_3_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_3_new)
        self.month_4_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_4_new)
        self.month_5_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_5_new)
        self.month_6_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_6_new)
        self.month_7_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_7_new)
        self.month_8_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_8_new)
        self.month_9_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_9_new)
        self.month_10_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_10_new)
        self.month_11_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_11_new)
        self.month_12_subscription_amount_new = self._count_subscription_amount_new(self.subscription_fee_amount, self.month_12_new)

        self.sub_total_subscription_amount_new = self.month_1_subscription_amount_new + self.month_2_subscription_amount_new + self.month_3_subscription_amount_new + self.month_4_subscription_amount_new + self.month_5_subscription_amount_new + self.month_6_subscription_amount_new + self.month_7_subscription_amount_new + self.month_8_subscription_amount_new + self.month_9_subscription_amount_new + self.month_10_subscription_amount_new + self.month_11_subscription_amount_new + self.month_12_subscription_amount_new

        self.month_1_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_2_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_3_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_4_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_5_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_6_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_7_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_8_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_9_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_10_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_11_subscription_new = self.month_1_subscription_amount_new * 1000
        self.month_12_subscription_new = self.month_1_subscription_amount_new * 1000

        self.sub_total_subscription_new = self.month_1_subscription_new + self.month_2_subscription_new +  self.month_3_subscription_new + self.month_4_subscription_new + self.month_5_subscription_new + self.month_6_subscription_new + self.month_7_subscription_new + self.month_8_subscription_new + self.month_9_subscription_new + self.month_10_subscription_new + self.month_11_subscription_new + self.month_12_subscription_new

        self.month_1_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.total_last_year)
        self.month_2_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_1_total)
        self.month_3_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_2_total)
        self.month_4_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_3_total)
        self.month_5_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_4_total)
        self.month_6_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_5_total)
        self.month_7_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_6_total)
        self.month_8_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_7_total)
        self.month_9_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_8_total)
        self.month_10_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_9_total)
        self.month_11_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_10_total)
        self.month_12_subscription_amount_total = self._count_subscription_amount_total(self.subscription_fee_amount, self.month_11_total)

        self.sub_total_subscription_amount_total = self.month_1_subscription_amount_total + self.month_2_subscription_amount_total + self.month_3_subscription_amount_total + self.month_4_subscription_amount_total + self.month_5_subscription_amount_total + self.month_6_subscription_amount_total + self.month_7_subscription_amount_total + self.month_8_subscription_amount_total + self.month_9_subscription_amount_total + self.month_10_subscription_amount_total + self.month_11_subscription_amount_total + self.month_12_subscription_amount_total

        self.month_1_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_2_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_3_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_4_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_5_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_6_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_7_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_8_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_9_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_10_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_11_subscription_total = self.month_1_subscription_amount_total * 1000
        self.month_12_subscription_total = self.month_1_subscription_amount_total * 1000

        self.sub_total_subscription_total = self.month_1_subscription_total + self.month_2_subscription_total + self.month_3_subscription_total + self.month_4_subscription_total + self.month_5_subscription_total + self.month_6_subscription_total + self.month_7_subscription_total + self.month_8_subscription_total + self.month_9_subscription_total + self.month_10_subscription_total + self.month_11_subscription_total + self.month_12_subscription_total

    def _count_amount(self, month_number, qty, water_usage):
        day_in_month = monthrange(int(self.forecast_customer_id.years), month_number)
        capacity = 100 - self.forecast_customer_id.water_usage
        result = ((water_usage * qty * int(day_in_month[1])) * capacity / 100)

        # _logger.debug("Debug message result : %s", result)

        return round(result)

    def _count_sales(self, month_number, price_average, amount):
        rate_increase_month = int(self.forecast_customer_id.rate_increase_month)

        if month_number < rate_increase_month:
            result = price_average * amount
        else:
            rate_increase = 1 + (self.forecast_customer_id.rate_increase / 100)
            result = price_average * amount * rate_increase 

        return round(result)

    @api.depends('rate_increase_month', 'water_usage', 'price_average', 'rate_increase', 'month_1_total', 'month_2_total', 'month_3_total', 'month_4_total', 'month_5_total', 'month_6_total', 'month_7_total', 'month_8_total', 'month_9_total', 'month_10_total', 'month_11_total', 'month_12_total')
    def _compute_amount(self):
        self.month_1_amount = self._count_amount(1, self.total_last_year, self.water_usage)
        self.month_2_amount = self._count_amount(2, self.month_1_total, self.water_usage)
        self.month_3_amount = self._count_amount(3, self.month_2_total, self.water_usage)
        self.month_4_amount = self._count_amount(4, self.month_3_total, self.water_usage)
        self.month_5_amount = self._count_amount(5, self.month_4_total, self.water_usage)
        self.month_6_amount = self._count_amount(6, self.month_5_total, self.water_usage)
        self.month_7_amount = self._count_amount(7, self.month_6_total, self.water_usage)
        self.month_8_amount = self._count_amount(8, self.month_7_total, self.water_usage)
        self.month_9_amount = self._count_amount(9, self.month_8_total, self.water_usage)
        self.month_10_amount= self._count_amount(10, self.month_9_total, self.water_usage)
        self.month_11_amount= self._count_amount(11, self.month_10_total, self.water_usage)
        self.month_12_amount= self._count_amount(12, self.month_11_total, self.water_usage)

        self.month_1 = self._count_sales(1, self.price_average, self.month_1_amount)
        self.month_2 = self._count_sales(2, self.price_average, self.month_2_amount)
        self.month_3 = self._count_sales(3, self.price_average, self.month_3_amount)
        self.month_4 = self._count_sales(4, self.price_average, self.month_4_amount)
        self.month_5 = self._count_sales(5, self.price_average, self.month_5_amount)
        self.month_6 = self._count_sales(6, self.price_average, self.month_6_amount)
        self.month_7 = self._count_sales(7, self.price_average, self.month_7_amount)
        self.month_8 = self._count_sales(8, self.price_average, self.month_8_amount)
        self.month_9 = self._count_sales(9, self.price_average, self.month_9_amount)
        self.month_10= self._count_sales(10, self.price_average, self.month_10_amount)
        self.month_11= self._count_sales(11, self.price_average, self.month_11_amount)
        self.month_12= self._count_sales(12, self.price_average, self.month_12_amount)

        self.month_1_sales = self.month_1 / 1000
        self.month_2_sales = self.month_2 / 1000
        self.month_3_sales = self.month_3 / 1000
        self.month_4_sales = self.month_4 / 1000
        self.month_5_sales = self.month_5 / 1000
        self.month_6_sales = self.month_6 / 1000
        self.month_7_sales = self.month_7 / 1000
        self.month_8_sales = self.month_8 / 1000
        self.month_9_sales = self.month_9 / 1000
        self.month_10_sales= self.month_10 / 1000
        self.month_11_sales= self.month_11 / 1000
        self.month_12_sales= self.month_12 / 1000

    def _count_installment_amount_new(self, installment_fee_amount, month_new):
        return round(installment_fee_amount * month_new)

    @api.depends('installment_fee_amount', 'month_1_new', 'month_2_new', 'month_3_new', 'month_4_new', 'month_5_new', 'month_6_new', 'month_7_new', 'month_8_new', 'month_9_new', 'month_10_new', 'month_11_new', 'month_12_new')
    def _compute_installment(self):
        self.installment_fee = self.installment_fee_amount * 1000

        self.month_1_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_1_new)
        self.month_2_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_2_new)
        self.month_3_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_3_new)
        self.month_4_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_4_new)
        self.month_5_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_5_new)
        self.month_6_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_6_new)
        self.month_7_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_7_new)
        self.month_8_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_8_new)
        self.month_9_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_9_new)
        self.month_10_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_10_new)
        self.month_11_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_11_new)
        self.month_12_installment_amount_new = self._count_installment_amount_new(self.installment_fee_amount, self.month_12_new)

        self.sub_total_installment_amount_new = self.month_1_installment_amount_new + self.month_2_installment_amount_new + self.month_3_installment_amount_new + self.month_4_installment_amount_new + self.month_5_installment_amount_new + self.month_6_installment_amount_new + self.month_7_installment_amount_new + self.month_8_installment_amount_new + self.month_9_installment_amount_new + self.month_10_installment_amount_new + self.month_11_installment_amount_new + self.month_12_installment_amount_new

        self.month_1_installment_new = self.month_1_installment_amount_new * 1000
        self.month_2_installment_new = self.month_1_installment_amount_new * 1000
        self.month_3_installment_new = self.month_1_installment_amount_new * 1000
        self.month_4_installment_new = self.month_1_installment_amount_new * 1000
        self.month_5_installment_new = self.month_1_installment_amount_new * 1000
        self.month_6_installment_new = self.month_1_installment_amount_new * 1000
        self.month_7_installment_new = self.month_1_installment_amount_new * 1000
        self.month_8_installment_new = self.month_1_installment_amount_new * 1000
        self.month_9_installment_new = self.month_1_installment_amount_new * 1000
        self.month_10_installment_new = self.month_1_installment_amount_new * 1000
        self.month_11_installment_new = self.month_1_installment_amount_new * 1000
        self.month_12_installment_new = self.month_1_installment_amount_new * 1000

        self.sub_total_installment_new = self.month_1_installment_new + self.month_2_installment_new +  self.month_3_installment_new + self.month_4_installment_new + self.month_5_installment_new + self.month_6_installment_new + self.month_7_installment_new + self.month_8_installment_new + self.month_9_installment_new + self.month_10_installment_new + self.month_11_installment_new + self.month_12_installment_new
