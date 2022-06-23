import xlsxwriter
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import time
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from io import StringIO, BytesIO
from xlsxwriter.utility import xl_rowcol_to_cell

import logging
_logger = logging.getLogger(__name__)


class PamDetailDhhdOpenReport(models.TransientModel):
    _name = 'pam.detail.dhhd.open.report'

    def _default_start_date(self):
        start_date = datetime.now().strftime('%Y') + '-' + datetime.now().strftime('%m') + '-01'
        return  start_date

    def _default_end_date(self):
        next_month = datetime.strptime(self._default_start_date(), '%Y-%m-%d') + relativedelta(months=1)
        return next_month - relativedelta(days=1)

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
    years = fields.Selection(_get_years, string='Tahun Perincian Biaya', default=_default_year, required=True)
    
    start_date = fields.Date(default=_default_start_date)
    end_date = fields.Date(default=_default_end_date)
    start_date_last_month = fields.Date(default=_default_start_date)
    end_date_last_month = fields.Date(default=_default_end_date)
    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)

    total_jumlah = fields.Float(compute='compute_total_jumlah')
    total_hutang_usaha = fields.Float(compute='compute_total_hutang_usaha')
    total_hutang_lainnya = fields.Float(compute='compute_total_hutang_lainnya')
    total_by_ymh_dibayar = fields.Float(compute='compute_total_by_ymh_dibayar')

    account_payable_this_month = fields.Float(compute='compute_account_payable_this_month')
    other_debt_this_month = fields.Float(compute='compute_other_debt_this_month')
    accrued_cost_this_month = fields.Float(compute='compute_accrued_cost_this_month')
    total_this_month = fields.Float(compute='compute_total_this_month')

    account_payable_this_month_only = fields.Float(compute='compute_account_payable_this_month_only')
    other_debt_this_month_only = fields.Float(compute='compute_other_debt_this_month_only')
    accrued_cost_this_month_only = fields.Float(compute='compute_accrued_cost_this_month_only')
    total_this_month_only = fields.Float(compute='compute_total_this_month_only')

    account_payable_last_month = fields.Float(compute='compute_account_payable_last_month')
    other_debt_last_month = fields.Float(compute='compute_other_debt_last_month')
    accrued_cost_last_month = fields.Float(compute='compute_accrued_cost_last_month')
    total_last_month = fields.Float(compute='compute_total_last_month')

    total_account_payable = fields.Float(compute='compute_total_account_payable')
    total_other_debt_payable = fields.Float(compute='compute_total_other_debt_payable')
    total_accrued_cost_payable = fields.Float(compute='compute_total_accrued_cost_payable')
    total = fields.Float(compute='compute_total')

    # Jurnal Umum
    account_payable_cancel = fields.Float(compute='compute_account_payable_cancel')
    other_debt_cancel = fields.Float(compute='compute_other_debt_cancel')
    accrued_cost_cancel = fields.Float(compute='compute_accrued_cost_cancel')
    total_cancel = fields.Float(compute='compute_total_cancel')

    total_ap = fields.Float(compute='compute_total_ap')
    total_od = fields.Float(compute='compute_total_od')
    total_ac = fields.Float(compute='compute_total_ac')
    total_all = fields.Float(compute='compute_total_all')

    count_lines = fields.Float(compute='compute_lines')
    report_html = fields.Html(string="Rekap DHHD")

    line_ids = fields.One2many('pam.detail.dhhd.open.report.line', 'detail_dhhd_open_report_id')
    detail_ids = fields.One2many('pam.detail.dhhd.open.report.detail', 'detail_dhhd_open_report_id', domain=[('this_month', '=', True)])
    detail2_ids = fields.One2many('pam.detail.dhhd.open.report.detail2', 'detail_dhhd_open_report_id')

    def compute_lines(self):
        self.count_lines = len(self.line_ids)

    @api.depends('line_ids.jumlah')
    def compute_total_jumlah(self):
        for record in self:
            self.total_jumlah = sum(line.jumlah for line in record.line_ids)

    @api.depends('line_ids.hutang_usaha')
    def compute_total_hutang_usaha(self):
        for record in self:
            self.total_hutang_usaha = sum(line.hutang_usaha for line in record.line_ids)

    @api.depends('line_ids.hutang_lainnya')
    def compute_total_hutang_lainnya(self):
        for record in self:
            self.total_hutang_lainnya = sum(line.hutang_lainnya for line in record.line_ids)

    @api.depends('line_ids.by_ymh_dibayar')
    def compute_total_by_ymh_dibayar(self):
        for record in self:
            self.total_by_ymh_dibayar = sum(line.by_ymh_dibayar for line in record.line_ids)

    def get_month_day_range(self, date):
        """
        For a date 'date' returns the start and end date for the month of 'date'.

        Month with 31 days:
        >>> date = datetime.date(2011, 7, 27)
        >>> get_month_day_range(date)
        (datetime.date(2011, 7, 1), datetime.date(2011, 7, 31))

        Month with 28 days:
        >>> date = datetime.date(2011, 2, 15)
        >>> get_month_day_range(date)
        (datetime.date(2011, 2, 1), datetime.date(2011, 2, 28))
        """
        first_day = date.replace(day = 1)
        last_day = date.replace(day = calendar.monthrange(date.year, date.month)[1])
        return first_day, last_day

    @api.onchange('years', 'months')
    def generate_date_range(self):
        
        self.start_date = self.years + '-' + self.months + '-01'
        self.end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        if self.months == '01':
            last_month = 12
            last_year = int(self.years) - 1
        else:
            last_month = int(self.months) - 1
            last_year = int(self.years)
        
        last_day = datetime.strptime(self.start_date, "%Y-%m-%d") - relativedelta(days=1)

        start_date_last_month, end_date_last_month = self.get_month_day_range(last_day)

        self.start_date_last_month = start_date_last_month
        self.end_date_last_month = end_date_last_month

    def _record(self):
        sql = """
            select x.period, x.entry_date, x.name, x.supplier_name, x.code, x.coa_name, x.jumlah, x.hutang_usaha, x.hutang_lainnya, x.by_ymh_dibayar from
            (
                        select 
                            concat(to_char(a.entry_date, 'Month'), ' ',(EXTRACT(year FROM a.entry_date))) as period,
                            a.entry_date,
                            a.name,
                            d.name as supplier_name,
                            c.code,
                            c.name as coa_name,
                            (b.debit + b.credit) as jumlah,
                            (case 
                                when c.code = '21111110' then (b.debit + b.credit)
                                else 0
                            end) as hutang_usaha,
                            (case 
                                when c.code = '21121110' then (b.debit + b.credit)
                                else 0
                            end) as hutang_lainnya,
                            (case 
                                when c.code = '21131110' then (b.debit + b.credit)
                                else 0
                            end) as by_ymh_dibayar
                        from 
                            pam_journal_entry a
                            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
                            inner join pam_coa c on c.id = b.coa_id
                            inner join pam_vendor d on d.id = a.vendor_id
                        where 
                    a.journal_type = 'ap'
                    and a.entry_date <= %s
                    and a.state in ('payment','paid')
                    
                union

                        select 
                            concat(to_char(a.entry_date, 'Month'), ' ',(EXTRACT(year FROM a.entry_date))) as period,
                            a.entry_date,
                            a.name,
                            d.name as supplier_name,
                            c.code,
                            c.name as coa_name,
                            (b.debit + b.credit) as jumlah,
                            (case 
                                when c.code = '21111110' then (b.debit + b.credit)
                                else 0
                            end) as hutang_usaha,
                            (case 
                                when c.code = '21121110' then (b.debit + b.credit)
                                else 0
                            end) as hutang_lainnya,
                            (case 
                                when c.code = '21131110' then (b.debit + b.credit)
                                else 0
                            end) as by_ymh_dibayar
                        from 
                            pam_journal_entry a
                            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
                            inner join pam_coa c on c.id = b.coa_id
                            inner join pam_vendor d on d.id = a.vendor_id
                        where 
                    a.journal_type = 'ap'
                    and a.entry_date <= %s
                    and a.payment_date > %s
                    and a.state in ('submit','posted')
            ) x
            order by 
            x.entry_date, x.name
            """

        self._cr.execute(sql, (self.end_date,self.end_date,self.end_date))
        result = self._cr.fetchall()

        return result

    def _record_detail(self, start_date, end_date):
        sql = """
            SELECT d.code, d.name, c.coa_type,
            (
            SELECT coalesce(SUM(y.debit), 0) as debit
                        FROM 
                            pam_journal_entry as x
                            inner join pam_journal_entry_line as y on x.id = y.journal_entry_id
                        WHERE 
                            x.entry_date BETWEEN %s and %s AND 
                            x.journal_type = 'ap' and 
                            x.state != 'draft' and
                            y.coa_id = d.id
            ) as debit,
            (
            SELECT coalesce(SUM(y.credit), 0) as credit
                        FROM 
                            pam_journal_entry as x
                            inner join pam_journal_entry_line as y on x.id = y.journal_entry_id
                        WHERE 
                            x.entry_date BETWEEN %s and %s AND 
                            x.journal_type = 'ap' and 
                            x.state != 'draft' and
                            y.coa_id = d.id
            ) as credit,
            (
                SELECT coalesce(SUM(xx.debit - xx.credit), 0)
                FROM
                (
                SELECT y.debit , y.credit
                from 
                    pam_journal_entry x
                    inner join pam_journal_entry_line y on x.id = y.journal_entry_id
                where 
                    x.code_journal_type = 'AP' and
                    x.entry_date between %s and %s and
                    x.state = 'payment' and
                    y.coa_id = d.id
                union

                select y.debit, y.credit
                from 
                    pam_journal_entry x
                    inner join pam_journal_entry_line y on x.id = y.journal_entry_id
                where
                    x.code_journal_type = 'AP' and
                    x.entry_date <= %s and
                    x.payment_date > %s and
                    x.state not in ('submit','payment') and
                    y.coa_id = d.id
                ) as xx
            ) as voucher_open,
            (
                SELECT coalesce(SUM(xx.debit), 0)
                FROM
                (
                SELECT y.debit , y.credit
                from 
                    pam_journal_entry x
                    inner join pam_journal_entry_line y on x.id = y.journal_entry_id
                where 
                    x.code_journal_type = 'AP' and
                    x.entry_date between %s and %s and
                    x.state = 'payment' and
                    y.coa_id = d.id
                union

                select y.debit, y.credit
                from 
                    pam_journal_entry x
                    inner join pam_journal_entry_line y on x.id = y.journal_entry_id
                where
                    x.code_journal_type = 'AP' and
                    x.entry_date <= %s and
                    x.payment_date > %s and
                    x.state not in ('submit','payment') and
                    y.coa_id = d.id
                ) as xx
            ) as voucher_open_debit
            from 
                pam_report_configuration a
                inner join pam_report_configuration_line b on a.id = b.report_id
                inner join pam_report_configuration_detail c on b.id = c.report_line_id
                inner join pam_coa d on d.id = c.coa_id
                inner join pam_report_type e on e.id = a.report_type_id
            where
                e.code = 'DHHD'
            order by 
                d.code
            """
        self._cr.execute(sql, (start_date,end_date,start_date,end_date,start_date,end_date,end_date,end_date,start_date,end_date,end_date,end_date))
        result = self._cr.fetchall()

        return result

    def _record_detail2(self, id):
        sql = """
            select b.name, d.code, d.name as coa_name,
            (
            select coalesce((x.paid_dhhd), 0)
            from
                pam_detail_dhhd_open_report_detail x
            where
                w.id = x.detail_dhhd_open_report_id and
                x.code = d.code and
                x.this_month = True
            ) as sub_total,
            (
            select coalesce((x.paid_dhhd), 0)
            from 
                pam_detail_dhhd_open_report_detail x
            where
                w.id = x.detail_dhhd_open_report_id and
                x.code = d.code and
                x.this_month = False
            ) as month_before
            from
                pam_detail_dhhd_open_report w,
                pam_report_configuration a
                inner join pam_report_configuration_line b on a.id = b.report_id
                inner join pam_report_configuration_detail c on b.id = c.report_line_id
                inner join pam_coa d on d.id = c.coa_id
                inner join pam_report_type e on e.id = a.report_type_id
            where
                e.code = 'dhhd_total' and
                w.id = %s
            order by
                b.sequence
            """
        self._cr.execute(sql, (id, ))
        result = self._cr.fetchall()

        return result

    def get_data(self):
        records = self._record()
        # records = self.env['pam.vw.dhhd'].search(['&', ('entry_date', '<=', self.end_date), '|', ('payment_date', '>', self.end_date), ('payment_date', '=', False)])

        self.env['pam.detail.dhhd.open.report.line'].search([('detail_dhhd_open_report_id','=', self.id)]).unlink()

        data = []
        last_voucher = ""
        display_date = ""
        # for period, entry_date, name, supplier_name, code, coa_name, jumlah, hutang_usaha, hutang_lainnya, by_ymh_dibayar in records:
        for period, entry_date, name, supplier_name, code, coa_name, jumlah, hutang_usaha, hutang_lainnya, by_ymh_dibayar in records:

            if last_voucher != name:
                last_voucher = name
                display_date = datetime.strptime(entry_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                name = name
                supplier_name = supplier_name
            else:
                display_date = ""
                name = ""
                supplier_name = ""

            # if code in ['21111110', '21121110', '21131110']:
            #     jumlah = 0

            vals = {
                'detail_dhhd_open_report_id' : self.id,
                'period' : period,
                'entry_date' : display_date,
                'name' : name,
                'supplier_name' : supplier_name,
                'code' : code,
                'coa_name' : coa_name,
                'jumlah' : jumlah,
                'hutang_usaha' : hutang_usaha,
                'hutang_lainnya' : hutang_lainnya,
                'by_ymh_dibayar' : by_ymh_dibayar
            }

            row = (0, 0, vals)
            data.append(row)

        report_html = self.get_recap_html()

        # DETAIL 1

        record_details = self._record_detail(self.start_date, self.end_date)
        
        self.env['pam.detail.dhhd.open.report.detail'].search([('detail_dhhd_open_report_id','=', self.id)]).unlink()

        data_detail = []

        for code, name, coa_type, debit, credit, voucher_open, voucher_open_debit in record_details:
            if coa_type == 'debit':
                vals = {
                    'detail_dhhd_open_report_id': self.id,
                    'this_month': 1,
                    'code' : code,
                    'remark' : name,
                    'debit' : debit,
                    'credit' : credit,
                    'total' : debit,
                    'open_dhhd' : voucher_open_debit,
                    'paid_dhhd' : (debit - debit) - voucher_open_debit
                }

                row = (0, 0, vals)
                data_detail.append(row)

            else:
                vals = {
                    'detail_dhhd_open_report_id': self.id,
                    'this_month': 1,
                    'code' : code,
                    'remark' : name,
                    'debit' : debit,
                    'credit' : credit,
                    'total' : debit - credit,
                    'open_dhhd' : voucher_open,
                    'paid_dhhd' : (debit - credit) - voucher_open
                }

                row = (0, 0, vals)
                data_detail.append(row)

        record_details = self._record_detail(self.start_date_last_month, self.end_date_last_month)
        
        for code, name, coa_type, debit, credit, voucher_open, voucher_open_debit in record_details:
            if coa_type == 'debit':
                vals = {
                    'detail_dhhd_open_report_id': self.id,
                    'this_month': 0,
                    'code' : code,
                    'remark' : name,
                    'debit' : debit,
                    'credit' : credit,
                    'total' : debit,
                    'open_dhhd' : voucher_open_debit,
                    'paid_dhhd' : (debit - debit) - voucher_open_debit
                }

                row = (0, 0, vals)
                data_detail.append(row)

            else:
                vals = {
                    'detail_dhhd_open_report_id': self.id,
                    'this_month': 0,
                    'code' : code,
                    'remark' : name,
                    'debit' : debit,
                    'credit' : credit,
                    'total' : debit - credit,
                    'open_dhhd' : voucher_open,
                    'paid_dhhd' : (debit - credit) - voucher_open
                }

                row = (0, 0, vals)
                data_detail.append(row)

        recap_report = self.env['pam.detail.dhhd.open.report'].search([('id', '=', self.id)])
        recap_report.update({
            'line_ids': data,
            'report_html': report_html,
            'detail_ids': data_detail
        })

        # DETAIL 2

        record_details2 = self._record_detail2(self.id)
        # raise ValidationError(_('%s')%(record_details2))
        
        self.env['pam.detail.dhhd.open.report.detail2'].search([('detail_dhhd_open_report_id','=', self.id)]).unlink()

        _logger.debug("ess : %s", self.id)

        data_detail2 = []
        for name, code, coa_name, sub_total, month_before in record_details2:

            vals = {
                'detail_dhhd_open_report_id': self.id,
                'name' : name,
                'code' : code,
                'remark' : coa_name,
                'sub_total' : sub_total,
                'total_this_month' : '',
                'total_last_month' : month_before,
                'total' : sub_total + month_before
            }

            row = (0, 0, vals)
            data_detail2.append(row)

        recap_report = self.env['pam.detail.dhhd.open.report'].search([('id', '=', self.id)])
        recap_report.update({
            'detail2_ids': data_detail2
        })

    def get_recap_ap(self, coa_code):

        sql = """
            SELECT (SUM(b.credit) - SUM(b.debit)) as total
            FROM 
                pam_journal_entry as a
                inner join pam_journal_entry_line as b on a.id = b.journal_entry_id
                inner join pam_coa as c on b.coa_id = c."id"
            WHERE 
                a.entry_date BETWEEN %s and %s AND a.journal_type = 'ap' and a.state != 'draft' and c.code = %s
            group by c.code, c."name"
            order by c.code
            """

        self._cr.execute(sql, (self.start_date, self.end_date, coa_code))
        result = self._cr.fetchone()
        if result:
            return result[0] 
        else:
            return 0

    def get_ju_cancel(self, coa_code):

        sql = """
            SELECT (SUM(b.credit) - SUM(b.debit)) as total
            FROM 
                pam_journal_entry as a
                inner join pam_journal_entry_line as b on a.id = b.journal_entry_id
                inner join pam_coa as c on b.coa_id = c."id"
            WHERE 
                a.entry_date BETWEEN %s and %s AND a.journal_type = 'ju' and a.state != 'draft' and a.is_cancellation = 'True' and c.code = %s
            group by c.code, c."name"
            order by c.code
            """

        self._cr.execute(sql, (self.start_date, self.end_date, coa_code))
        result = self._cr.fetchone()
        if result:
            return result[0] 
        else:
            return 0

    def _generate_recap_html(self, title, account_payable, other_debt, accrued_cost):

        total = account_payable + other_debt + accrued_cost

        html = ""
        html = html + "<div class='row'>"
        html = html + "<div class='col-md-6'><h4>" + title + " :</h4></div>"
        html = html + "</div>"

        html = html + "<div class='row'>"
        html = html + " <div class='col-md-6'>"
        html = html + "     <div class='col-md-4'>211.11.110</div>"
        html = html + "     <div class='col-md-1'>Rp.</div>"
        html = html + "     <div class='col-md-3 number-cell'>" + '{0:,.2f}'.format(account_payable) + "</div>"
        html = html + "     <div class='col-md-4 number-cell'></div>"
        html = html + " </div>"
        html = html + "</div>"

        html = html + "<div class='row'>"
        html = html + " <div class='col-md-6'>"
        html = html + "     <div class='col-md-4'>211.21.110</div>"
        html = html + "     <div class='col-md-1'>Rp.</div>"
        html = html + "     <div class='col-md-3 number-cell'>" + '{0:,.2f}'.format(other_debt) + "</div>"
        html = html + "     <div class='col-md-4 number-cell'></div>"
        html = html + " </div>"
        html = html + "</div>"

        html = html + "<div class='row'>"
        html = html + " <div class='col-md-6'>"
        html = html + "     <div class='col-md-4'>211.31.110</div>"
        html = html + "     <div class='col-md-1'>Rp.</div>"
        html = html + "     <div class='col-md-3 number-cell'>" + '{0:,.2f}'.format(accrued_cost) + "</div>"
        html = html + "     <div class='col-md-4 number-cell'></div>"
        html = html + " </div>"
        html = html + "</div>"

        html = html + "<div class='row'>"
        html = html + " <div class='col-md-6'>"
        html = html + "     <div class='col-md-4'></div>"
        html = html + "     <div class='col-md-1'></div>"
        html = html + "     <div class='col-md-3'></div>"
        html = html + "     <div class='col-md-4 number-cell'><b>" + '{0:,.2f}'.format(total) + "</b></div>"
        html = html + " </div>"
        html = html + "</div>"

        return html

    def compute_account_payable_this_month(self):
        self.account_payable_this_month = self.get_recap_ap('21111110')

    def compute_other_debt_this_month(self):
        self.other_debt_this_month = self.get_recap_ap('21121110')

    def compute_accrued_cost_this_month(self):
        self.accrued_cost_this_month = self.get_recap_ap('21131110')

    def compute_total_this_month(self):
        self.total_this_month = self.account_payable_this_month + self.other_debt_this_month + self.accrued_cost_this_month

    def compute_account_payable_this_month_only(self):
        dhhd_ap = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21111110'), ('entry_date', '>=', self.start_date), ('entry_date', '<=', self.end_date), '|', ('payment_date', '>', self.end_date), ('payment_date', '=', False)])
        self.account_payable_this_month_only = self.account_payable_this_month - sum(line.account_payable for line in dhhd_ap)

    def compute_other_debt_this_month_only(self):
        dhhd_other_debt = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21121110'), ('entry_date', '>=', self.start_date), ('entry_date', '<=', self.end_date), '|', ('payment_date', '>', self.end_date), ('payment_date', '=', False)])
        self.other_debt_this_month_only = self.other_debt_this_month - sum(line.other_debt for line in dhhd_other_debt)

    def compute_accrued_cost_this_month_only(self):
        dhhd_accrued_cost = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21131110'), ('entry_date', '>=', self.start_date), ('entry_date', '<=', self.end_date), '|', ('payment_date', '>', self.end_date), ('payment_date', '=', False)])
        self.accrued_cost_this_month_only = self.accrued_cost_this_month - sum(line.accrued_cost for line in dhhd_accrued_cost)

    def compute_total_this_month_only(self):
        self.total_this_month_only = self.account_payable_this_month_only + self.other_debt_this_month_only + self.accrued_cost_this_month_only

    def compute_account_payable_last_month(self):
        dhhd_ap_before = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21111110'), ('entry_date', '<', self.start_date), '|', ('payment_date', '>=', self.start_date), ('payment_date', '=', False)])
        dhhd_ap_last_month = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21111110'), ('entry_date', '>=', self.start_date_last_month), ('entry_date', '<=', self.end_date_last_month), '|', ('payment_date', '>=', self.start_date), ('payment_date', '=', False)])
        self.account_payable_last_month = sum(line.account_payable for line in dhhd_ap_before) - sum(line.account_payable for line in dhhd_ap_last_month)

    def compute_other_debt_last_month(self):
        dhhd_other_debt_before = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21121110'), ('entry_date', '<', self.start_date), '|', ('payment_date', '>=', self.start_date), ('payment_date', '=', False)])
        dhhd_other_debt_last_month = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21121110'), ('entry_date', '>=', self.start_date_last_month), ('entry_date', '<=', self.end_date_last_month), '|', ('payment_date', '>=', self.start_date), ('payment_date', '=', False)])
        self.other_debt_last_month = sum(line.other_debt for line in dhhd_other_debt_before) - sum(line.other_debt for line in dhhd_other_debt_last_month)

    def compute_accrued_cost_last_month(self):
        dhhd_accrued_cost_before = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21131110'), ('entry_date', '<', self.start_date), '|', ('payment_date', '>=', self.start_date), ('payment_date', '=', False)])
        dhhd_accrued_cost_last_month = self.env['pam.vw.dhhd'].search([('coa_code', '=', '21131110'), ('entry_date', '>=', self.start_date_last_month), ('entry_date', '<=', self.end_date_last_month), '|', ('payment_date', '>=', self.start_date), ('payment_date', '=', False)])
        self.accrued_cost_last_month = sum(line.accrued_cost for line in dhhd_accrued_cost_before) - sum(line.accrued_cost for line in dhhd_accrued_cost_last_month)

    def compute_total_last_month(self):
        self.total_last_month = self.account_payable_last_month + self.other_debt_last_month + self.accrued_cost_last_month

    def compute_total_account_payable(self):
        self.total_account_payable = self.account_payable_this_month_only + self.account_payable_last_month

    def compute_total_other_debt_payable(self):
        self.total_other_debt_payable = self.other_debt_this_month_only + self.other_debt_last_month

    def compute_total_accrued_cost_payable(self):
        self.total_accrued_cost_payable = self.accrued_cost_this_month_only + self.accrued_cost_last_month

    def compute_total(self):
        total = self.total_account_payable + self.total_other_debt_payable + self.total_accrued_cost_payable

    def compute_account_payable_cancel(self):
        self.account_payable_cancel = self.get_ju_cancel('21111110')

    def compute_other_debt_cancel(self):
        self.other_debt_cancel = self.get_ju_cancel('21121110')

    def compute_accrued_cost_cancel(self):
        self.accrued_cost_cancel = self.get_ju_cancel('21131110')

    def compute_total_cancel(self):
        self.total_cancel = self.account_payable_cancel + self.other_debt_cancel + self.accrued_cost_cancel

    def compute_total_ap(self):
        self.total_ap = self.total_account_payable + self.account_payable_cancel

    def compute_total_od(self):
        self.total_od = self.total_other_debt_payable + self.other_debt_cancel

    def compute_total_ac(self):
        self.total_ac = self.total_accrued_cost_payable + self.accrued_cost_cancel

    def compute_total_all(self):
        self.total_all = self.total_ap + self.total_od + self.total_ac

    def get_recap_html(self):

        html = "<div class='container'>"

        html = html + self._generate_recap_html("DHHD Bulan ini", self.account_payable_this_month, self.other_debt_this_month, self.accrued_cost_this_month)
        html = html + self._generate_recap_html("Pengeluaran Bulan ini", self.account_payable_this_month_only, self.other_debt_this_month_only, self.accrued_cost_this_month_only)
        html = html + self._generate_recap_html("Pengeluaran Bulan lalu", self.account_payable_last_month, self.other_debt_last_month, self.accrued_cost_last_month)
        html = html + self._generate_recap_html("Jurnal Bayar Kas", self.total_account_payable, self.total_other_debt_payable, self.total_accrued_cost_payable)
        html = html + self._generate_recap_html("Jurnal Umum", self.account_payable_cancel, self.other_debt_cancel, self.accrued_cost_cancel)
        html = html + self._generate_recap_html("Jurnal Bayar Kas + Jurnal Umum", self.total_ap, self.total_od, self.total_ac)

        html = html + "</div>"

        return html

    def export_report_pdf(self):
        report_log = self.env['pam.report.log'].create({
            'name': self.env.user.name,
            'report_type': 'Detail DHHD TERBUKA',
            'report_format': 'Laporan PDF'
            })

        recaps = []
        for line in self.line_ids:
            recaps.append([line.period, line.entry_date, line.name, line.supplier_name, line.code, line.coa_name, line.jumlah, line.hutang_usaha, line.hutang_lainnya, line.by_ymh_dibayar])

        details = []
        for detail in self.detail_ids:
            details.append([detail.code, detail.remark, detail.debit, detail.credit, detail.total, detail.open_dhhd, detail.paid_dhhd])
                    
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': (datetime.strptime(self.start_date, "%Y-%m-%d")).strftime("%d %B %Y"),
                'end_date': (datetime.strptime(self.end_date, "%Y-%m-%d")).strftime("%d %B %Y"),
                'months': (datetime.strptime(self.months, "%m")).strftime("%B"),
                'years': self.years,
                'html': self.report_html,
                'recaps': recaps,
                'details': details,
            },
        }

        return self.env.ref('pam_accounting.action_pam_detail_dhhd_open_report').report_action(self, data=data)

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'Detail DHHD TERBUKA'
            filename = '%s.xlsx' % ('Detail DHHD TERBUKA', )
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Detail DHHD TERBUKA',
                'report_format': 'Laporan Excel'
                })
            
            title = workbook.add_format({'font_size': 14, 'bold': True, 'align': 'center', 'font': 'Tahoma'})
            bold = workbook.add_format({'bold': True, 'align': 'center'})
            bold_left = workbook.add_format({'bold': True, 'align': 'left', 'font_size': 12, 'font': 'Tahoma'})
            merge = workbook.add_format({'bold': True, 'border': True, 'font_size': 12, 'font': 'Tahoma', 'align': 'center'})
            merge_left = workbook.add_format({'bold': True, 'border': True, 'font_size': 12, 'font': 'Tahoma', 'align': 'left'})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1, 'right': 1, 'left': 1})
            period = workbook.add_format({'bottom': 1, 'top': 1, 'align': 'left', 'right': 1, 'left': 1})
            jumlah = workbook.add_format({'top': 1, 'align': 'right'})
            top = workbook.add_format({'top': 1, 'right': 1, 'left': 1})
            right = workbook.add_format({'right': 1, 'align': 'center'})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'center', 'right': 1, 'left': 1})
            left = workbook.add_format({'left': 1, 'align': 'center'})
            border_bold = workbook.add_format({'border': True, 'align': 'center', 'bold': True, 'bg_color': '#ffff00', 'font_size': 12, 'font': 'Tahoma'})
            border2_bold = workbook.add_format({'border': True, 'align': 'center', 'bold': True, 'bg_color': '#9966ff', 'font_size': 12, 'font': 'Tahoma'})
            border = workbook.add_format({'border': True, 'align': 'center', 'font_size': 12, 'font': 'Tahoma'})
            border_left = workbook.add_format({'border': True, 'align': 'left', 'font_size': 12, 'font': 'Tahoma'})
            judul = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 14, 'font': 'Tahoma'})
            str_format = workbook.add_format({'text_wrap': True})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'border': 1, 'font': 'Tahoma', 'font_size': 12})
            currency_format_no_border = workbook.add_format({'font_size': 12, 'num_format': '#,##0.00', 'font': 'Tahoma'})
            currency_format_no_border_bold = workbook.add_format({'font': 'Tahoma', 'num_format': '#,##0.00', 'font_size': 12, 'bold': True})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
    
            # Recap DHHD
            sheet1 = workbook.add_worksheet('Rekap')
    
            sheet1.set_column(0, 0, 10)
            sheet1.set_column(1, 1, 15)
            sheet1.set_column(2, 2, 10)
            sheet1.set_column(3, 3, 80)
            sheet1.set_column(4, 7, 20)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','dhhd_terbuka_detail')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet1.write(0, 6, code_iso.code_iso, wrap_text)
            else:
                sheet1.write(0, 3, '', bold)
    
            sheet1.merge_range(2, 0, 2, 3, 'DHHD TERBUKA UNTUK BULAN : ' + datetime.strptime(record.start_date, "%Y-%m-%d").strftime("%d %B %Y") + ' s/d ' + datetime.strptime(record.end_date, "%Y-%m-%d").strftime("%d %B %Y"), title)
    
            y = 5
            sheet1.merge_range(y, 0, y, 3, 'DHHD Bulan Ini', bold_left)
    
            y += 1
            sheet1.write(y, 0, '211.11.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.account_payable_this_month, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.21.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.other_debt_this_month, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.31.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.accrued_cost_this_month, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 3, record.total_this_month, currency_format_no_border_bold)
    
    
            y += 2
            sheet1.merge_range(y, 0, y, 3, 'Pengeluaran Bulan Ini', bold_left)
    
            y += 1
            sheet1.write(y, 0, '211.11.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.account_payable_this_month_only, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.21.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.other_debt_this_month_only, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.31.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.accrued_cost_this_month_only, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 3, record.total_this_month_only, currency_format_no_border_bold)
    
    
            y += 2
            sheet1.merge_range(y, 0, y, 3, 'Pengeluaran Bulan Lalu', bold_left)
    
            y += 1
            sheet1.write(y, 0, '211.11.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.account_payable_last_month, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.21.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.other_debt_last_month, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.31.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.accrued_cost_last_month, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 3, record.total_last_month, currency_format_no_border_bold)
    
    
            y += 2
            sheet1.merge_range(y, 0, y, 3, 'Jurnal Bayar Kas', bold_left)
    
            y += 1
            sheet1.write(y, 0, '211.11.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.total_account_payable, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.21.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.total_other_debt_payable, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.31.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.total_accrued_cost_payable, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 3, record.total, currency_format_no_border_bold)
    
    
            y += 2
            sheet1.merge_range(y, 0, y, 3, 'Jurnal Umum', bold_left)
    
            y += 1
            sheet1.write(y, 0, '211.11.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.account_payable_cancel, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.21.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.other_debt_cancel, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.31.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.accrued_cost_cancel, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 3, record.total_cancel, currency_format_no_border_bold)
    
            y += 2
            sheet1.merge_range(y, 0, y, 3, 'Jurnal Bayar Kas + Jurnal Umum', bold_left)
    
            y += 1
            sheet1.write(y, 0, '211.11.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.total_ap, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.21.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.total_od, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 0, '211.31.110')
            sheet1.write(y, 1, 'Rp.')
            sheet1.write(y, 2, record.total_ac, currency_format_no_border)
    
            y += 1
            sheet1.write(y, 3, record.total_all, currency_format_no_border_bold)
    
            # Detail DHHD
            sheet = workbook.add_worksheet('Detil')
    
            sheet.set_column(0, 0, 10)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 2, 10)
            sheet.set_column(3, 3, 80)
            sheet.set_column(4, 7, 20)
    
            sheet.merge_range(0, 0, 0, 7, 'DAFTAR HUTANG YANG MASIH DIBAYAR (D H H D) TERBUKA', title)
            sheet.merge_range(1, 0, 1, 7, 'SAMPAI DENGAN BULAN : ' + datetime.strptime(record.start_date, "%Y-%m-%d").strftime("%d %B %Y") + ' s/d ' + datetime.strptime(record.end_date, "%Y-%m-%d").strftime("%d %B %Y"), bold)
    
            sheet.merge_range(3, 0, 4, 0, 'TGL', top)
            sheet.merge_range(3, 1, 4, 1, 'No VOUCHER', top)
            sheet.merge_range(3, 2, 4, 2, 'Penerima', top)
            sheet.write(3, 3, 'KODE', top)
            sheet.merge_range(3, 4, 4, 4, 'NAMA PERKIRAAN', top)
            sheet.merge_range(3, 5, 4, 5, 'Jumlah AP', top)
            sheet.write(3, 6, 'Hutang Usaha', top_bottom)
            sheet.write(3, 7, 'Hutang Lainnya', top_bottom)
            sheet.write(3, 8, 'By ymh dibayar', top_bottom)
    
            sheet.write(4, 3, 'PERK', bottom)
            sheet.write(4, 6, '211.11.110', bottom)
            sheet.write(4, 7, '211.21.110', bottom)
            sheet.write(4, 8, '211.31.110', bottom)
    
            before_period = 0
            before_no = 0
            y = 5
            
            for line in record.line_ids:
                code = line.code
                if before_period != line.period:
                    sheet.merge_range(y, 0, y, 7, line.period, period)
                    # sheet.write(y, 0, line.period, bottom)
                    y +=1
    
                if before_no != line.name:
                    sheet.write(y, 0, line.entry_date, bottom)
                    sheet.write(y, 1, line.name, bottom)
                    sheet.write(y, 2, line.supplier_name, bottom)
                    sheet.write(y, 3, line.code, bottom)
                    sheet.write(y, 4, line.coa_name, bottom)
    
                    if code not in ['21111110', '21121110', '21131110']:
                        sheet.write(y, 5, line.jumlah, currency_format)
                    else:
                        sheet.write(y, 5, 0, currency_format)
    
                    sheet.write(y, 6, line.hutang_usaha, currency_format)
                    sheet.write(y, 7, line.hutang_lainnya, currency_format)
                    sheet.write(y, 8, line.by_ymh_dibayar, currency_format)
    
                else:
                    sheet.write(y, 0, '', bottom)
                    sheet.write(y, 1, '', bottom)
                    sheet.write(y, 2, '', bottom)
                    sheet.write(y, 3, line.code, bottom)
                    sheet.write(y, 4, line.coa_name, bottom)
                    
                    if code not in ['21111110', '21121110', '21131110']:
                        sheet.write(y, 5, line.jumlah, currency_format)
                    else:
                        sheet.write(y, 5, 0, currency_format)
    
                    sheet.write(y, 6, line.hutang_usaha, currency_format)
                    sheet.write(y, 7, line.hutang_lainnya, currency_format)
                    sheet.write(y, 8, line.by_ymh_dibayar, currency_format)
    
                before_period = line.period
                before_no = line.name
                y += 1
    
            y = 2
    
            # Detail 2
            sheet = workbook.add_worksheet('Detil2')
    
            sheet.set_column(0, 0, 10)
            sheet.set_column(1, 7, 25)
    
            y += 1
            sheet.merge_range(y, 0, y, 7, 'BULAN : ' + datetime.strptime(record.months, "%m").strftime("%B") + ' ' + record.years, judul)
            y += 2
            sheet.write(y, 0, 'No', border_bold)
            sheet.write(y, 1, 'K O D E  P E R K I R A A N', border_bold)
            sheet.write(y, 2, 'U R A I A N', border_bold)
            sheet.merge_range(y, 3, y, 5, 'DHHD BLN INI', border_bold)
            sheet.write(y, 6, 'DHHD TERBUKA', border_bold)
            sheet.write(y, 7, 'DHHD LUNAS', border_bold)
    
            y += 1
            total_total = 0
            total_open_dhhd = 0
            total_paid_dhhd = 0
            no = 1
            for detail in record.detail_ids:
                sheet.write(y, 0, no, border)
                sheet.write(y, 1, detail.code, border)
                sheet.write(y, 2, detail.remark, border_left)
                sheet.write(y, 3, detail.debit, currency_format)
                sheet.write(y, 4, detail.credit, currency_format)
                sheet.write(y, 5, detail.total, currency_format)
                sheet.write(y, 6, detail.open_dhhd, currency_format)
                sheet.write(y, 7, detail.paid_dhhd, currency_format)
                no += 1
                total_total += detail.total
                total_open_dhhd += detail.open_dhhd
                total_paid_dhhd += detail.paid_dhhd
                y += 1
                
            sheet.write(y, 0, '', border)
            sheet.write(y, 1, '', border)
            sheet.write(y, 2, '', border_left)
            sheet.write(y, 3, '', currency_format)
            sheet.write(y, 4, 'Jumlah', border)
            sheet.write(y, 5, total_total, currency_format)
            sheet.write(y, 6, total_open_dhhd, currency_format)
            sheet.write(y, 7, total_paid_dhhd, currency_format)
            y += 4
    
            sheet.merge_range(y, 0, y, 6, 'BULAN : ' + datetime.strptime(record.months, "%m").strftime("%B") + ' ' + record.years, judul)
            y += 2
            sheet.write(y, 0, 'No', border2_bold)
            sheet.write(y, 1, 'KODE', border2_bold)
            sheet.write(y, 2, 'URAIAN', border2_bold)
            sheet.write(y, 3, 'SUB TOTAL (I)', border2_bold)
            sheet.write(y, 4, 'TOTAL BULAN INI', border2_bold)
            sheet.write(y, 5, 'TOTAL BULAN LALU (II)', border2_bold)
            sheet.write(y, 6, 'TOTAL PENGELUARAN', border2_bold)
    
            y += 1
            total_total = 0
            total_this_month = 0
            total_last_month = 0
    
            report_type = self.env['pam.report.type'].search([('code','=','dhhd_total')])
            report_type_lines = self.env['pam.report.type.line'].search([('report_id','=',report_type.id)])
            for report_type_line in report_type_lines:
                sheet.merge_range(y, 0, y, 1, (report_type_line.name).upper(), merge_left)
                sheet.write(y, 2, '', border)
                sheet.write(y, 3, '', border)
                sheet.write(y, 4, '', border)
                sheet.write(y, 5, '', border)
                sheet.write(y, 6, '', border)
                y += 1
    
                report_configuration = self.env['pam.report.configuration'].search([('report_type_id','=',report_type.id)])
                report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id','=',report_configuration.id), ('group_id','=',report_type_line.id)])
                no = 1
                for report_line in report_configuration_lines:
                    sheet.write(y, 0, no, merge)
                    sheet.write(y, 1, (report_line.name).upper(), merge)
                    sheet.write(y, 2, '', border)
                    sheet.write(y, 3, '', border)
                    sheet.write(y, 4, '', border)
                    sheet.write(y, 5, '', border)
                    sheet.write(y, 6, '', border)
                    y += 1
    
                    details = self.env['pam.detail.dhhd.open.report.detail2'].search([('detail_dhhd_open_report_id', '=', record.id), ('name', '=', report_line.name)], order='code asc')
                    for detail in details:
                        sheet.write(y, 0, '', border)
                        sheet.write(y, 1, detail.code, currency_format)
                        sheet.write(y, 2, detail.remark, currency_format)
                        sheet.write(y, 3, detail.sub_total, currency_format)
                        sheet.write(y, 4, detail.total_this_month, currency_format)
                        sheet.write(y, 5, detail.total_last_month, currency_format)
                        sheet.write(y, 6, detail.total, currency_format)
                    
                        total_total += detail.total
                        total_this_month += detail.sub_total
                        total_last_month += detail.total_last_month
                        y += 1
                    no += 1
                
                sheet.write(y, 0, '', border)
                sheet.write(y, 1, '', border_left)
                sheet.write(y, 2, 'Jumlah', border)
                sheet.write(y, 3, '', currency_format)
                sheet.write(y, 4, total_this_month, currency_format)
                sheet.write(y, 5, total_last_month, currency_format)
                sheet.write(y, 6, total_total, currency_format)
                y += 1
    
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename
    
            # return{
            #     'view_mode': 'form',
            #     'res_id': record.id,
            #     'res_model': 'pam.journal.verification.report',
            #     'view_type': 'form',
            #     'type': 'ir.actions.act_window',
            #     'context': self.env.context,
            #     'target': 'new',
            #     }


class PamDetailDhhdOpenReportLine(models.TransientModel):
    _name = 'pam.detail.dhhd.open.report.line'

    detail_dhhd_open_report_id = fields.Many2one('pam.detail.dhhd.open.report', required=True, index=True)
    period = fields.Char()
    entry_date = fields.Char(string='Tanggal')
    name = fields.Char(string='No Voucher')
    supplier_name = fields.Char(string='Supplier')
    code = fields.Char(string='Kode Perk')
    coa_name = fields.Char(string='Nama Perkiraan')
    jumlah = fields.Float(default=0, string='Jumlah')
    hutang_usaha = fields.Float(string='Hutang Usaha')
    hutang_lainnya = fields.Float(string='Hutang Lainnya')
    by_ymh_dibayar = fields.Float(string='By Ymh Di Bayar')


class PamDetailDhhdOpenReportDetail(models.TransientModel):
    _name = 'pam.detail.dhhd.open.report.detail'

    detail_dhhd_open_report_id = fields.Many2one('pam.detail.dhhd.open.report', required=True, index=True)
    this_month = fields.Boolean()
    code = fields.Char(string='Kode Perkiraan')
    remark = fields.Char(string='Uraian')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Kredit')
    total = fields.Float(string='Total')
    open_dhhd = fields.Float(string='DHHD Terbuka')
    paid_dhhd = fields.Float(string='DHHD Lunas')


class PamDetailDhhdOpenReportDetail2(models.TransientModel):
    _name = 'pam.detail.dhhd.open.report.detail2'

    detail_dhhd_open_report_id = fields.Many2one('pam.detail.dhhd.open.report', required=True, index=True)
    name = fields.Char(string='Nama')
    code = fields.Char(string='Kode Perkiraan')
    remark = fields.Char(string='Uraian')
    sub_total = fields.Float(string='Sub Total')
    total_this_month = fields.Float(string='Total Bulan Ini')
    total_last_month = fields.Float(string='Total Bulan Lalu')
    total = fields.Float(string='Total Pengeluaran')
    

class PamCoRecapReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_detail_dhhd_open_report_template'
    _template ='pam_accounting.report_detail_dhhd_open_report_template'

    @api.model
    def get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        months = data['form']['months']
        years = data['form']['years']
        html = data['form']['html']
        recaps = data['form']['recaps']
        details = data['form']['details']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'months': months,
            'years': years,
            'html': html,
            'recaps': recaps,
            'details': details,
        }
