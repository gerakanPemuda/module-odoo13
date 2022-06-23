from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta
from calendar import monthrange

import logging
_logger = logging.getLogger(__name__)


class PamForecastOther(models.Model):
    _name = 'pam.forecast.other'
    _rec_name = 'years'
    _description = 'Rencana Pendapatan'
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

    years = fields.Selection(_get_years, string='Tahun Anggaran', default=_default_year, required=True)

    other_type = fields.Selection([
        ('rpna', 'Rencana Pendapatan Non Air'),
        ('rpdu', 'Rencana Pendapatan Diluar Usaha')
    ], default='rpna', string='Rencana Pendapatan', required=True)

    line_ids= fields.One2many('pam.forecast.other.line', 'forecast_other_id')

    def get_classifications(self):
        classifications = self.env['pam.other.classification'].search([])

        data = []
        for classification in classifications:
            vals = {
                'forecast_other_id' : self.id,
                'other_classification_id' : classification.id
            }

            row = (0, 0, vals)
            data.append(row)
        
        self.env['pam.forecast.other.line'].search([('forecast_other_id','=', self.id)]).unlink()

        other = self.env['pam.forecast.other'].search([('id', '=', self.id)])

        other.update({
            'new_other_ids': data
        })


class PamForecastOtherLine(models.Model):
    _name = 'pam.forecast.other.line'

    forecast_other_id  = fields.Many2one('pam.forecast.other', required=True, index=True, ondelete='cascade')
    name = fields.Char(string='Uraian', required=True)

    month_1       = fields.Float(string='I', default=0)
    month_2       = fields.Float(string='II', default=0)
    month_3       = fields.Float(string='III', default=0)
    month_4       = fields.Float(string='IV', default=0)
    month_5       = fields.Float(string='V', default=0)
    month_6       = fields.Float(string='VI', default=0)
    month_7       = fields.Float(string='VII', default=0)
    month_8       = fields.Float(string='VIII', default=0)
    month_9       = fields.Float(string='IX', default=0)
    month_10      = fields.Float(string='X', default=0)
    month_11      = fields.Float(string='XI', default=0)
    month_12      = fields.Float(string='XII', default=0)
    sub_total_month = fields.Float(string='Jumlah', default=0, compute='_compute_sub_total', store=True)

    month_1_amount       = fields.Float(string='I', required=True, default=0)
    month_2_amount       = fields.Float(string='II', required=True, default=0)
    month_3_amount       = fields.Float(string='III', required=True, default=0)
    month_4_amount       = fields.Float(string='IV', required=True, default=0)
    month_5_amount       = fields.Float(string='V', required=True, default=0)
    month_6_amount       = fields.Float(string='VI', required=True, default=0)
    month_7_amount       = fields.Float(string='VII', required=True, default=0)
    month_8_amount       = fields.Float(string='VIII', required=True, default=0)
    month_9_amount       = fields.Float(string='IX', required=True, default=0)
    month_10_amount      = fields.Float(string='X', required=True, default=0)
    month_11_amount      = fields.Float(string='XI', required=True, default=0)
    month_12_amount      = fields.Float(string='XII', required=True, default=0)
    sub_total_month_amount = fields.Float(string='Jumlah', default=0, compute='_compute_sub_total', store=True)

    @api.depends('month_1_amount', 'month_2_amount', 'month_3_amount', 'month_4_amount', 'month_5_amount', 'month_6_amount', 'month_7_amount', 'month_8_amount', 'month_9_amount', 'month_10_amount', 'month_11_amount', 'month_12_amount')
    def _compute_sub_total(self):

        self.sub_total_month_amount = self.month_1_amount + self.month_2_amount + self.month_3_amount + self.month_4_amount + self.month_5_amount + self.month_6_amount + self.month_7_amount + self.month_8_amount + self.month_9_amount + self.month_10_amount + self.month_11_amount + self.month_12_amount
        self.sub_total_month = self.sub_total_month_amount * 1000

