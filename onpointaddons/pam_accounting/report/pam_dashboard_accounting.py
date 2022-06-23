import xlsxwriter
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import StringIO, BytesIO
from xlsxwriter.utility import xl_rowcol_to_cell

import logging
_logger = logging.getLogger(__name__)


class PamDashboardAccounting(models.TransientModel):
    _name = 'pam.dashboard.accounting'
    _inherit = ['pam.profit.loss', 'pam.balance.sheet']

    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = int(current_year) - 3
        results = []
        for year in range(min_year, current_year):
            results.append((str(year), str(year)))
        return results

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
    ], default='01', required=True)
    years = fields.Selection(_get_years, string='Tahun Neraca', default=_default_year, required=True)
    period = fields.Char(compute='set_period')
    start_date = fields.Date(compute='set_period_date')
    end_date = fields.Date(compute='set_period_date')
    last_posted_period = fields.Integer(compute='set_last_posted_period')
    range_start_date = fields.Date(compute='set_last_posted_period')
    range_end_date = fields.Date(compute='set_last_posted_period')

    def set_period(self):
        self.period = self.years + self.months

    def set_period_date(self):
        self.start_date = self.years + '-' + self.months + '-01'
        self.end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

    def set_last_posted_period(self):
        _logger.debug("PAM Balance Name : %s", self.period)

        pam_balance = self.env['pam.balance'].search([('name', '<', self.period)], order='name desc', limit=1)
        _logger.debug("PAM Balance Name : %s", pam_balance.name)

        if pam_balance:

            last_posted_year = pam_balance.name[:4]
            last_posted_month = pam_balance.name[4:]

            _logger.debug("Last Posted Year : %s", last_posted_year)
            _logger.debug("Last Posted Month : %s", last_posted_month)

            last_posted_start_date = last_posted_year + '-' + last_posted_month + '-01'
            last_posted_next_start_date = (datetime.strptime(last_posted_start_date, "%Y-%m-%d") + relativedelta(months=1)).strftime("%Y-%m-%d")

            start_date = self.years + '-' + self.months + '-01'
            last_posted_next_end_date = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)

            self.last_posted_period = pam_balance.id
            self.range_start_date = last_posted_next_start_date
            self.range_end_date = last_posted_next_end_date

        else:
            self.last_posted_period = 0

    @api.model
    def create(self, vals):
        years = str(datetime.today().year)
        months = '01'

        vals.update({
            'months': months,
            'years': years
        })
        res = super(PamDashboardAccounting, self).create(vals)
        return res

    @api.model
    def get_data(self):
        vals = {'months': '01', 'years': '2019'}
        self = self.create(vals)

        years = str(datetime.today().year)
        xAxis = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        income = []
        outcome = []
        profit_loss = []
        balance = []

        for x in range(12):
            months = x + 1

            start_date = years + '-' + str(months) + '-01'
            end_date = (datetime.strptime(years + '-' + str(months) + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

            business_income = self.calculate_profit_loss(start_date, end_date, 'PU', '%', 'credit')
            other_income = self.calculate_profit_loss(start_date, end_date, 'PU', 'Pendapatan lain - lain', 'credit')
            total_income = business_income + other_income
            income.append(total_income)

            operation_cost = self.calculate_operation_cost(start_date, end_date)
            other_cost = self.calculate_profit_loss(start_date, end_date, 'PU', 'Biaya lain lain', 'debit')
            total_cost = operation_cost + other_cost
            outcome.append(total_cost)

            total_profit_loss = self.calculate_profit_loss_after_tax(start_date, end_date)
            profit_loss.append(total_profit_loss)

            debit, credit = self.calculate_balance_sheet(start_date, end_date, 'AL', 'Kas dan Bank')
            if months <= int(self.months):
                ending_balance = self.get_last_balance('AL', 'Kas dan Bank')
            else:
                ending_balance = 0
            cash_and_bank = (ending_balance + debit) - credit
            balance.append(cash_and_bank)

        data = {
            'xAxis': xAxis,
            'series': [{
                'name' : 'Pendapatan',
                'data': income
                },
                {
                'name': 'Biaya',
                'data': outcome
                },
                {
                'name': 'Laba/Rugi',
                'data': profit_loss
                },
                {
                'name': 'Saldo Akhir Kas',
                'data': balance
                }]
        }

        return data
