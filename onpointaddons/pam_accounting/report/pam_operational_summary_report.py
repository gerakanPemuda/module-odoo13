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


class PamOperationalSummaryReport(models.TransientModel):
    _name = 'pam.operational.summary.report'
    _inherit = ['pam.profit.loss']

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
    years = fields.Selection(_get_years, string='Tahun', default=_default_year, required=True)

    period = fields.Char(compute='set_period')
    start_date = fields.Date(compute='set_period_date')
    end_date = fields.Date(compute='set_period_date')
    last_posted_period = fields.Integer(compute='set_last_posted_period')
    range_start_date = fields.Date(compute='set_last_posted_period')
    range_end_date = fields.Date(compute='set_last_posted_period')

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    report_html = fields.Html(string="Laba Rugi")
    tf = fields.Boolean()

    def set_period(self):
        self.period = self.years + self.months

    def set_period_date(self):
        self.start_date = self.years + '-' + self.months + '-01'
        self.end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

    def set_last_posted_period(self):
        pam_balance = self.env['pam.balance'].search([('name', '<', self.period)], order='name desc', limit=1)
        if pam_balance:

            last_posted_year = pam_balance.name[:4]
            last_posted_month = pam_balance.name[4:]

            last_posted_start_date = last_posted_year + '-' + last_posted_month + '-01'
            last_posted_next_start_date = (datetime.strptime(last_posted_start_date, "%Y-%m-%d") + relativedelta(months=1)).strftime("%Y-%m-%d")

            start_date = self.years + '-' + self.months + '-01'
            last_posted_next_end_date = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)

            self.last_posted_period = pam_balance.id
            self.range_start_date = last_posted_next_start_date
            self.range_end_date = last_posted_next_end_date

        else:
            self.last_posted_period = 0

    def create_html_row(self, 
        html, 
        class_name, 
        name, 
        value_this_year=0, 
        budget_this_year=0, 
        value_until_this_month=0,
        budget_until_this_month=0,
        percentage=False):

        html = html + "<tr class='" + class_name + "'>"

        value_diff_this_year = 0
        percentage_diff_this_year = 0
        value_diff_until_this_month = 0
        percentage_diff_until_this_month = 0

        if percentage:
            percentage_symbol = "%"
        else:
            percentage_symbol = ""

        if value_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_this_year) + percentage_symbol + "</td>"
        else:
            html = html + "<td></td>"

        if budget_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_this_year) + percentage_symbol + "</td>"
        else:
            html = html + "<td></td>"

        if value_this_year != "":
            value_diff_this_year = value_this_year - budget_this_year
            if budget_this_year > 0 :
                percentage_diff_this_year = (value_diff_this_year / budget_this_year) * 100

            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff_this_year) + percentage_symbol + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(percentage_diff_this_year) + "</td>"
        else:
            html = html + "<td></td>"
            html = html + "<td></td>"

        html = html + "<td>" + name + "</td>"

        if value_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_until_this_month) + percentage_symbol + "</td>"
        else:
            html = html + "<td></td>"

        if budget_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_until_this_month) + percentage_symbol + "</td>"
        else:
            html = html + "<td></td>"

        if value_until_this_month != "":
            value_diff_until_this_month = value_until_this_month - budget_until_this_month
            if budget_until_this_month > 0 :
                percentage_diff_until_this_month = (value_diff_until_this_month / budget_until_this_month) * 100

            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff_until_this_month) + percentage_symbol + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(percentage_diff_until_this_month) + "</td>"
        else:
            html = html + "<td></td>"
            html = html + "<td></td>"

        html = html + "</tr>"

        return html

    def get_data(self):
        # starting div
        html = "<table class='report-table'>"

        html = html + "<tr>"
        html = html + "<th colspan='4'>BULAN INI</td>"
        html = html + "<th width='500px' rowspan='3'>URAIAN</td>"
        html = html + "<th colspan='4'>SAMPAI DENGAN BULAN INI</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th width='200px' rowspan='2'>REALISASI</td>"
        html = html + "<th width='200px' rowspan='2'>ANGGARAN</td>"
        html = html + "<th width='200px'>LEBIH/(KURANG)</td>"
        html = html + "<th width='200px' rowspan='2'>%</td>"
        html = html + "<th width='200px' rowspan='2'>REALISASI</td>"
        html = html + "<th width='200px' rowspan='2'>ANGGARAN</td>"
        html = html + "<th width='200px'>LEBIH/(KURANG)</td>"
        html = html + "<th width='200px' rowspan='2'>%</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th>JUMLAH</td>"
        html = html + "<th>JUMLAH</td>"
        html = html + "</tr>"

        before_month_start_date = str(int(self.years) - 1) + '-' + self.months + '-01'
        before_month_end_date = (datetime.strptime(str(int(self.years) - 1) + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        current_month_start_date = self.years + '-' + self.months+ '-01'
        current_month_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        if self.months == '01':
            last_month = '12'
            last_month_year = str(int(self.years) - 1)
        else:
            last_month = str(int(self.months) - 1)
            last_month_year = self.years

        last_month_start_date = last_month_year + '-' + last_month + '-01'
        last_month_end_date = (datetime.strptime(last_month_start_date, "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        before_year_start_date = str(int(self.years) - 1) + '-01-01'
        before_year_end_date = (datetime.strptime(self.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
        current_year_start_date = self.years + '-01-01'
        current_year_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        html = self.create_html_row(html, "", "<b>KEUANGAN</b>", "", "", "", "")
        html = self.create_html_row(html, "", "A. REKENING AIR YANG DITERBITKAN", "", "", "", "")

        water_price_this_year = self.calculate_water_price(self.start_date, self.end_date, 'credit')
        water_price_until_this_month = self.calculate_water_price(current_year_start_date, self.end_date, 'credit')
        html = self.create_html_row(html, "", "A.1. Pemjualan Air (Harga Air)", water_price_this_year, 0, water_price_until_this_month, 0)

        admin_this_year = self.calculate_profit_loss(self.start_date, self.end_date, 'PU', 'Penjualan Air', 'credit') - water_price_this_year
        admin_until_this_month = self.calculate_profit_loss(current_year_start_date, self.end_date, 'PU', 'Penjualan Air', 'credit') - water_price_until_this_month
        html = self.create_html_row(html, "", "A.2. Beban Tetap (Adm, Pend Penj. Air Lainnya )", admin_this_year, 0, admin_until_this_month, 0)

        total_water_account_released_this_year = water_price_this_year + admin_this_year
        total_water_account_released_until_this_month = water_price_this_year + admin_this_year

        html = self.create_html_row(html, "", "B. PENDAPATAN USAHA LAINNYA", "", "", "", "")

        total_other_income_this_year = 0
        total_other_income_until_this_month = 0

        value_this_year = self.calculate_profit_loss(self.start_date, self.end_date, 'PU', 'Penjualan Non Air', 'credit')
        value_until_this_month = self.calculate_profit_loss(current_year_start_date, self.end_date, 'PU', 'Penjualan Non Air', 'credit')
        html = self.create_html_row(html, "", "B.1. Pendapatan Non Air", value_this_year, 0, value_until_this_month, 0)

        total_other_income_this_year += value_this_year
        total_other_income_until_this_month += value_until_this_month

        value_this_year = self.calculate_profit_loss(self.start_date, self.end_date, 'PLL', 'Pendapatan lain - lain', 'credit')
        value_until_this_month = self.calculate_profit_loss(current_year_start_date, self.end_date, 'PLL', 'Pendapatan lain - lain', 'credit')
        html = self.create_html_row(html, "", "B.2. Pendapatan Lain-lain", value_this_year, 0, value_until_this_month, 0)

        total_other_income_this_year += value_this_year
        total_other_income_until_this_month += value_until_this_month

        html = self.create_html_row(html, "", "C. BIAYA USAHA", "", "", "", "")

        total_cost_this_year = 0
        total_cost_until_this_month = 0

        direct_operation_cost_this_year = self.calculate_direct_operation_cost(self.start_date, self.end_date)
        direct_operation_cost_until_this_month = self.calculate_direct_operation_cost(current_year_start_date, self.end_date)
        html = self.create_html_row(html, "", "C.1. Biaya Langsung Usaha.", direct_operation_cost_this_year, 0, direct_operation_cost_until_this_month, 0)

        total_cost_this_year += direct_operation_cost_this_year
        total_cost_until_this_month += direct_operation_cost_until_this_month

        value_this_year = self.calculate_indirect_operation_cost(self.start_date, self.end_date)
        value_until_this_month = self.calculate_indirect_operation_cost(current_year_start_date, self.end_date)
        html = self.create_html_row(html, "", "C.2  Biaya Umum dan Administrasi", value_this_year, 0, value_until_this_month, 0)

        total_cost_this_year += value_this_year
        total_cost_until_this_month += value_until_this_month

        value_this_year = self.calculate_profit_loss(self.start_date, self.end_date, 'PLL', 'Biaya lain lain', 'debit')
        value_until_this_month = self.calculate_profit_loss(current_year_start_date, self.end_date, 'PLL', 'Biaya lain lain', 'debit')
        html = self.create_html_row(html, "", "C.3. Biaya Lain-lain", value_this_year, 0, value_until_this_month, 0)

        total_cost_this_year += value_this_year
        total_cost_until_this_month += value_until_this_month

        total_gross_profit_this_year = total_water_account_released_this_year + total_other_income_this_year - total_cost_this_year
        total_gross_profit_until_this_month = total_water_account_released_until_this_month + total_other_income_until_this_month - total_cost_until_this_month

        html = self.create_html_row(html, "", "D. LABA KOTOR", total_gross_profit_this_year, 0, total_gross_profit_until_this_month, 0)

        html = self.create_html_row(html, "", "E. REKENING AIR YANG  DITERBITKAN  BULAN  LALU", "", "", "", "")

        if last_month_start_date < '2019-01-01':
            water_price_last_month = 0
            water_price_until_this_month = 0
            admin_last_month = 0
            admin_until_this_month = 0
        else:
            water_price_last_month = self.calculate_water_price(last_month_start_date, last_month_end_date, 'credit')
            water_price_until_this_month = self.calculate_water_price(last_month_start_date, self.end_date, 'credit')
            admin_last_month = self.calculate_profit_loss(last_month_start_date, last_month_end_date, 'PU', 'Penjualan Air', 'credit') - water_price_last_month
            admin_until_this_month = self.calculate_profit_loss(last_month_start_date, self.end_date, 'PU', 'Penjualan Air', 'credit') - water_price_until_this_month

        html = self.create_html_row(html, "", "E.1. Pemjualan Air (Harga Air)", water_price_last_month, 0, water_price_until_this_month, 0)
        html = self.create_html_row(html, "", "E.2. Beban Tetap (Adm, Pend Penj. Air Lainnya )", admin_last_month, 0, admin_until_this_month, 0)

        html = self.create_html_row(html, "", "F. PENERIMAAN TAGIHAN REKENING AIR", "", "", "", "")

        water_account = self.env['pam.water.account'].search([('months', '=', self.months), ('years', '=', self.years)])
        html = self.create_html_row(html, "", "F.1 Bulan ini", water_account.payment_receive, 0, water_account.payment_receive, 0)
        html = self.create_html_row(html, "", "F.2 Sampai dengan Bulan ini", water_account.payment_receive_until_this_month, 0, water_account.payment_receive_until_this_month, 0)

        html = self.create_html_row(html, "", "<b>KAPASITAS PRODUKSI DAN DISTRIBUSI</b>", "", "", "", "")

        html = self.create_html_row(html, "", "H. AIR YANG DIPRODUKSI   (Kapasitas....M3) Debet ....... M3", water_account.water_productivity, 0, water_account.water_productivity, 0)
        html = self.create_html_row(html, "", "I. DISTRIBUSI AIR PADA METER INDUK (Kapasitas....M3)", water_account.water_distribution, 0, water_account.water_distribution, 0)
        html = self.create_html_row(html, "", "I.1. Dapat Dipertanggung Jawabkan", water_account.water_accounted, 0, water_account.water_accounted, 0)

        non_revenue_water = water_account.water_distribution - water_account.water_accounted
        html = self.create_html_row(html, "", "I.2 Taksiran Kehilangan Air", non_revenue_water, 0, non_revenue_water, 0)

        html = self.create_html_row(html, "", "J. AIR YANG DAPAT DIPERTANGGUNG JAWABKAN", "", "", "", "")
        html = self.create_html_row(html, "", "J.1. Tercatat dalam rekening", water_account.recorded_account, 0, water_account.recorded_account, 0)

        not_for_sale = water_account.water_accounted - water_account.recorded_account
        html = self.create_html_row(html, "", "J.2. Tidak dijual", not_for_sale, 0, not_for_sale, 0)

        html = self.create_html_row(html, "", "<b>LAIN - LAIN</b>", "", "", "", "")
        html = self.create_html_row(html, "", "K. JUMLAH PELANGGAN", water_account.number_of_customers, 0, water_account.number_of_customers, 0)
        html = self.create_html_row(html, "", "L. BANYAKNYA PERSONALIA/PEGAWAI", water_account.number_of_employee, 0, water_account.number_of_employee, 0)

        price_average = water_price_this_year / water_account.recorded_account
        price_average_until_this_month = water_price_until_this_month / water_account.recorded_account

        html = self.create_html_row(html, "", "M. RATA-RATA HARGA AIR SETIAP M3 (A.1 / J.1)", price_average, 0, price_average_until_this_month, 0)
        
        profit_average = total_gross_profit_this_year / water_account.recorded_account
        profit_average_until_this_month = total_gross_profit_until_this_month / water_account.recorded_account
        html = self.create_html_row(html, "", "N. LABA KOTOR SETIAP M3 ( D / J.1 )", profit_average, 0, profit_average_until_this_month, 0)

        if (water_price_last_month + admin_last_month) > 0:
            percentage_billing = water_account.payment_receive / (water_price_last_month + admin_last_month)
            percentage_billing2 = water_account.payment_receive_until_this_month /  (water_price_last_month + admin_last_month)
        else:
            percentage_billing = 0
            percentage_billing2 = 0

        if (water_price_until_this_month + admin_until_this_month) > 0:
            percentage_billing_until_this_month = water_account.payment_receive / (water_price_until_this_month + admin_until_this_month)
            percentage_billing2_until_this_month = water_account.payment_receive_until_this_month /  (water_price_last_month + admin_last_month)
        else:
            percentage_billing_until_this_month = 0
            percentage_billing2_until_this_month = 0

        html = self.create_html_row(html, "", "O. PERSENTASE TAGIHAN REKENING BULAN BERJALAN ( F.1 / E )", percentage_billing, 0, percentage_billing_until_this_month, 0, True)
        html = self.create_html_row(html, "", "P. PERSENTASE TAGIHAN REK S/D BULAN INI ( F / E )", percentage_billing2, 0, percentage_billing2_until_this_month, 0, True)

        percentage_water_accounted = (water_account.water_accounted / water_account.water_productivity) * 100
        percentage_water_accounted_until_this_month = (water_account.water_accounted / water_account.water_productivity) * 100

        html = self.create_html_row(html, "", "Q. PERSENTASE AIR YANG DIPERTANGGUNGJAWABKAN ( I.1 / H x 100% )", percentage_water_accounted, 0, percentage_water_accounted_until_this_month, 0, True)

        percentage_non_revenue_water = (non_revenue_water / water_account.water_distribution) * 100
        percentage_non_revenue_water_until_this_month = (non_revenue_water / water_account.water_distribution) * 100
        html = self.create_html_row(html, "", "R. PERSENTASE KEHILANGAN AIR ( I.2 / I X 100% )", percentage_non_revenue_water, 0, percentage_non_revenue_water_until_this_month, 0, True)

        percentage_recorded_account = (water_account.recorded_account / water_account.water_productivity) * 100
        percentage_recorded_account_until_this_month = (water_account.recorded_account / water_account.water_productivity) * 100
        html = self.create_html_row(html, "", "S. PERSENTASE AIR YANG TERCATAT DALAM REKENING (J.1 / H X 100% ))", percentage_recorded_account, 0, percentage_recorded_account_until_this_month, 0, True)

        percentage_not_for_sale = (not_for_sale / water_account.water_productivity) * 100
        percentage_not_for_sale_until_this_month = (not_for_sale / water_account.water_productivity) * 100

        html = self.create_html_row(html, "", "T. PERSENTASE AIR YG TDK DIJUAL (J.2 / H X 100%)", percentage_not_for_sale, 0, percentage_not_for_sale_until_this_month, 0, True)

        average_sales = direct_operation_cost_this_year / water_account.recorded_account
        average_sales_until_this_month = direct_operation_cost_until_this_month / water_account.recorded_account
        html = self.create_html_row(html, "", "U. RATA-RATA BIAYA PRODUKSI DAN DISTRIBUSI AIR YANG TERJUAL (C.1/J.1 )", average_sales, 0, average_sales_until_this_month, 0)

        html = html + "</table>"

        report = self.env['pam.operational.summary.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True,
        })

    def create_excel_row(self, sheet, y, col, format_cells, 
        name, 
        value_this_year=0, 
        budget_this_year=0, 
        value_until_this_month=0,
        budget_until_this_month=0,
        percentage=False):

        value_diff_this_year = 0
        percentage_diff_this_year = 0
        value_diff_until_this_month = 0
        percentage_diff_until_this_month = 0

        if value_this_year != "":
            value_diff_this_year = value_this_year - budget_this_year
            if budget_this_year > 0 :
                percentage_diff_this_year = (value_diff_this_year / budget_this_year) * 100

        sheet.write(y, col, value_this_year, format_cells[0])
        col += 1
        sheet.write(y, col, budget_this_year, format_cells[1])
        col += 1
        sheet.write(y, col, value_diff_this_year, format_cells[2])
        col += 1
        sheet.write(y, col, percentage_diff_this_year, format_cells[3])
        col += 1
        sheet.write(y, col, name, format_cells[4])
        col += 1
        sheet.write(y, col, value_until_this_month, format_cells[5])
        col += 1
        sheet.write(y, col, budget_until_this_month, format_cells[6])
        col += 1
        sheet.write(y, col, value_diff_until_this_month, format_cells[7])
        col += 1
        sheet.write(y, col, percentage_diff_until_this_month, format_cells[8])

        y = y + 1

        return sheet, y

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN LABA RUGI'
            filename = '%s.xlsx' % ('Laporan Ringkasan Kegiatan Utama',)
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 14, 'bold': True})
            judul = workbook.add_format({'bold': True, 'align': 'center'})
            bold = workbook.add_format({'bold': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            top = workbook.add_format({'top': 1})
            bottom = workbook.add_format({'bottom': 1, 'left': 1, 'right': 1, 'num_format': '#,##0.00', 'font': 'Tahoma', 'font_size': 11})
            bottom_left = workbook.add_format({'bottom': 1, 'left': 1, 'right': 1, 'align': 'left', 'num_format': '#,##0.00', 'font': 'Tahoma', 'font_size': 11})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'center', 'bold': True, 'font_size': 11, 'font': 'Tahoma', 'bg_color': '#e6e6e6'})
            right_left = workbook.add_format({'right': 1, 'left': 1, 'align': 'center', 'bold': True, 'font_size': 11, 'font': 'Tahoma', 'bg_color': '#e6e6e6'})
            right_left_bottom = workbook.add_format({'right': 1, 'left': 1, 'bottom': 1, 'align': 'center', 'bold': True, 'font_size': 11, 'font': 'Tahoma', 'bg_color': '#e6e6e6'})
            right_left_top = workbook.add_format({'right': 1, 'left': 1, 'top': 1, 'align': 'center', 'bold': True, 'font_size': 11, 'font': 'Tahoma', 'bg_color': '#e6e6e6'})
            border = workbook.add_format({'font': 'Tahoma', 'align': 'center', 'font_size': 11, 'bold': True, 'border': True, 'bg_color': '#e6e6e6'})
            right = workbook.add_format({'right': 1})
            center = workbook.add_format({'align': 'center'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'font': 'Tahoma', 'align': 'center', 'font_size': 11, 'bold': True})
            code_iso = workbook.add_format({'font': 'Tahoma', 'align': 'center', 'font_size': 11, 'bold': True, 'border': True})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            str_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
            no_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'align': 'center'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            style_bold = {'bold': True}
            style_font = {'font': 'Tahoma'}
            style_size = {'font_size': 11}
            style_border_left = {'left': 1}
            style_border_top = {'top': 1}
            style_border_right = {'right': 1}
            style_border_bottom = {'bottom': 1}
            style_alignment_left = {'align': 'left'}
            style_alignment_center = {'align': 'center'}
            style_alignment_right = {'align': 'right'}
            style_currency_format = {'num_format': '#,##0.00'}
    
            cell_text = {}
            cell_text.update(style_border_left)
            cell_text.update(style_border_right)
            cell_text.update(style_alignment_left)
            cell_text.update(style_font)
            cell_text.update(style_size)
            format_cell_text_normal = workbook.add_format(cell_text)
    
            cell_text.update(style_bold)
            cell_text.update(style_font)
            format_cell_text_bold = workbook.add_format(cell_text)
    
            cell_text.update(style_border_top)
            cell_text.update(style_border_bottom)
            cell_text.update(style_font)
            cell_text.update(style_size)
            format_cell_text_bold_highlight = workbook.add_format(cell_text)
    
            cell_number = {}
            cell_number.update(style_border_left)
            cell_number.update(style_border_right)
            cell_number.update(style_alignment_right)
            cell_number.update(style_currency_format)
            cell_number.update(style_font)
            cell_number.update(style_size)
            format_cell_number_normal = workbook.add_format(cell_number)
    
            cell_number.update(style_bold)
            cell_number.update(style_font)
            format_cell_number_bold = workbook.add_format(cell_number)
    
            cell_number.update(style_border_top)
            cell_number.update(style_border_bottom)
            cell_number.update(style_font)
            cell_number.update(style_size)
            format_cell_number_bold_highlight = workbook.add_format(cell_number)
    
            sheet.set_column(0, 3, 25)
            sheet.set_column(4, 4, 40)
            sheet.set_column(5, 8, 25)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','r_k_s')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.write(1, 7, code_iso.code_iso, wrap_text)
            else:
                sheet.write(1, 7, ' ', code_iso)
    
            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))
    
            sheet.insert_image(4, 1, 'logo.jpg', {'image_data' : logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})
    
            sheet.merge_range(4, 0, 4, 8, 'PDAM TIRTA PAKUAN KOTA BOGOR', str_format)
            sheet.merge_range(5, 0, 5, 8, 'LAPORAN RINGKASAN KEGIATAN UTAMA', str_format)
            sheet.merge_range(6, 0, 6, 8, 'PERIODE : ' + (datetime.strptime(record.months, '%m').strftime("%B")) + ' ' + record.years, str_format)
    
            sheet.merge_range(9, 0, 9, 3, 'BULAN INI', border)
            sheet.merge_range(9, 4, 12, 4, 'U R A I A N', border)
            sheet.merge_range(9, 5, 9, 8, 'SAMPAI DENGAN BULAN INI', border)
    
            sheet.merge_range(10, 0, 12, 0, 'REALISASI', border)
            sheet.merge_range(10, 1, 12, 1, 'ANGGARAN', border)
            sheet.write(10, 2, 'LEBIH/(KURANG)', border)
            sheet.merge_range(11, 2, 12, 2, 'JUMLAH', border)
            sheet.merge_range(10, 3, 12, 3, '%', border)
    
            sheet.merge_range(10, 5, 12, 5, 'REALISASI', border)
            sheet.merge_range(10, 6, 12, 6, 'ANGGARAN', border)
            sheet.write(10, 7, 'LEBIH/(KURANG)', border)
            sheet.merge_range(11, 7, 12, 7, 'JUMLAH', border)
            sheet.merge_range(10, 8, 12, 8, '%', border)
    
    
            before_month_start_date = str(int(record.years) - 1) + '-' + record.months + '-01'
            before_month_end_date = (datetime.strptime(str(int(record.years) - 1) + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
            current_month_start_date = record.years + '-' + record.months+ '-01'
            current_month_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
            if record.months == '01':
                last_month = '12'
                last_month_year = str(int(record.years) - 1)
            else:
                last_month = str(int(record.months) - 1)
                last_month_year = record.years
    
            last_month_start_date = last_month_year + '-' + last_month + '-01'
            last_month_end_date = (datetime.strptime(last_month_start_date, "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
    
    
            before_year_start_date = str(int(record.years) - 1) + '-01-01'
            before_year_end_date = (datetime.strptime(record.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
            current_year_start_date = record.years + '-01-01'
            current_year_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
            y = 13
            col = 0
    
    
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_bold, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "KEUANGAN", "", "", "", "")
    
    
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "A. REKENING AIR YANG DITERBITKAN", "", "", "", "")
    
            water_price_this_year = record.calculate_water_price(record.start_date, record.end_date, 'credit')
            water_price_until_this_month = record.calculate_water_price(current_year_start_date, record.end_date, 'credit')
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     A.1. Pemjualan Air (Harga Air)", water_price_this_year, 0, water_price_until_this_month, 0)
    
            admin_this_year = record.calculate_profit_loss(record.start_date, record.end_date, 'PU', 'Penjualan Air', 'credit') - water_price_this_year
            admin_until_this_month = record.calculate_profit_loss(current_year_start_date, record.end_date, 'PU', 'Penjualan Air', 'credit') - water_price_until_this_month
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     A.2. Beban Tetap (Adm, Pend Penj. Air Lainnya )", admin_this_year, 0, admin_until_this_month, 0)
    
            total_water_account_released_this_year = water_price_this_year + admin_this_year
            total_water_account_released_until_this_month = water_price_this_year + admin_this_year
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "B. PENDAPATAN USAHA LAINNYA", "", "", "", "")
    
            total_other_income_this_year = 0
            total_other_income_until_this_month = 0
    
            value_this_year = record.calculate_profit_loss(record.start_date, record.end_date, 'PU', 'Penjualan Non Air', 'credit')
            value_until_this_month = record.calculate_profit_loss(current_year_start_date, record.end_date, 'PU', 'Penjualan Non Air', 'credit')
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     B.1. Pendapatan Non Air", value_this_year, 0, value_until_this_month, 0)
    
            total_other_income_this_year += value_this_year
            total_other_income_until_this_month += value_until_this_month
    
            value_this_year = record.calculate_profit_loss(record.start_date, record.end_date, 'PLL', 'Pendapatan lain - lain', 'credit')
            value_until_this_month = record.calculate_profit_loss(current_year_start_date, record.end_date, 'PLL', 'Pendapatan lain - lain', 'credit')
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     B.2. Pendapatan Lain-lain", value_this_year, 0, value_until_this_month, 0)
    
            total_other_income_this_year += value_this_year
            total_other_income_until_this_month += value_until_this_month
    
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "C. BIAYA USAHA", "", "", "", "")
    
            total_cost_this_year = 0
            total_cost_until_this_month = 0
    
            direct_operation_cost_this_year = record.calculate_direct_operation_cost(record.start_date, record.end_date)
            direct_operation_cost_until_this_month = record.calculate_direct_operation_cost(current_year_start_date, record.end_date)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     C.1. Biaya Langsung Usaha.", direct_operation_cost_this_year, 0, direct_operation_cost_until_this_month, 0)
    
            total_cost_this_year += direct_operation_cost_this_year
            total_cost_until_this_month += direct_operation_cost_until_this_month
    
    
            value_this_year = record.calculate_indirect_operation_cost(record.start_date, record.end_date)
            value_until_this_month = record.calculate_indirect_operation_cost(current_year_start_date, record.end_date)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     C.2  Biaya Umum dan Administrasi", value_this_year, 0, value_until_this_month, 0)
    
            total_cost_this_year += value_this_year
            total_cost_until_this_month += value_until_this_month
    
            value_this_year = record.calculate_profit_loss(record.start_date, record.end_date, 'PLL', 'Biaya lain lain', 'debit')
            value_until_this_month = record.calculate_profit_loss(current_year_start_date, record.end_date, 'PLL', 'Biaya lain lain', 'debit')
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     C.3. Biaya Lain-lain", value_this_year, 0, value_until_this_month, 0)
    
            total_cost_this_year += value_this_year
            total_cost_until_this_month += value_until_this_month
    
            total_gross_profit_this_year = total_water_account_released_this_year + total_other_income_this_year - total_cost_this_year
            total_gross_profit_until_this_month = total_water_account_released_until_this_month + total_other_income_until_this_month - total_cost_until_this_month
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "D. LABA KOTOR", total_gross_profit_this_year, 0, total_gross_profit_until_this_month, 0)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "E. REKENING AIR YANG  DITERBITKAN  BULAN  LALU", "", "", "", "")
    
            if last_month_start_date < '2019-01-01':
                water_price_last_month = 0
                water_price_until_this_month = 0
                admin_last_month = 0
                admin_until_this_month = 0
            else:
                water_price_last_month = record.calculate_water_price(last_month_start_date, last_month_end_date, 'credit')
                water_price_until_this_month = record.calculate_water_price(last_month_start_date, record.end_date, 'credit')
                admin_last_month = record.calculate_profit_loss(last_month_start_date, last_month_end_date, 'PU', 'Penjualan Air', 'credit') - water_price_last_month
                admin_until_this_month = record.calculate_profit_loss(last_month_start_date, record.end_date, 'PU', 'Penjualan Air', 'credit') - water_price_until_this_month
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     E.1. Pemjualan Air (Harga Air)", water_price_last_month, 0, water_price_until_this_month, 0)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     E.2. Beban Tetap (Adm, Pend Penj. Air Lainnya )", admin_last_month, 0, admin_until_this_month, 0)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "F. PENERIMAAN TAGIHAN REKENING AIR", "", "", "", "")
    
            water_account = self.env['pam.water.account'].search([('months', '=', record.months), ('years', '=', record.years)])
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     F.1 Bulan ini", water_account.payment_receive, 0, water_account.payment_receive, 0)
            format_cells = [bottom, bottom, bottom, bottom, bottom, bottom, bottom, bottom, bottom]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     F.2 Sampai dengan Bulan ini", water_account.payment_receive_until_this_month, 0, water_account.payment_receive_until_this_month, 0)
    
    # BATES 1
            
            # y ke 9
            y += 1
            sheet.merge_range(y, 0, y, 3, 'BULAN INI', border)
            sheet.write(y, 4, ' ', right_left_top)
            sheet.merge_range(y, 5, y, 8, 'SAMPAI DENGAN BULAN INI', border)
    
            # y ke 10
            y += 1
            sheet.write(y, 0, ' ', right_left)
            sheet.write(y, 0, ' ', right_left)
            sheet.write(y, 1, ' ', right_left)
            sheet.write(y, 2, 'LEBIH/(KURANG)', border)
            sheet.write(y, 3, ' ', right_left)
            sheet.write(y, 4, ' ', right_left)
            sheet.write(y, 5, ' ', right_left)
            sheet.write(y, 6, ' ', right_left)
            sheet.write(y, 7, 'LEBIH/(KURANG)', border)
            sheet.write(y, 8, ' ', right_left)
    
            # y ke 11
            y += 1
            sheet.write(y, 0, ' ', right_left)
            sheet.write(y, 1, ' ', right_left)
            sheet.write(y, 2, ' ', right_left)
            sheet.write(y, 3, ' ', right_left)
            sheet.write(y, 4, ' ', right_left)
            sheet.write(y, 5, ' ', right_left)
            sheet.write(y, 6, ' ', right_left)
            sheet.write(y, 7, ' ', right_left)
            sheet.write(y, 8, ' ', right_left)
    
            # y ke 12
            y += 1
            sheet.write(y, 0, 'REALISASI', right_left_bottom)
            sheet.write(y, 1, 'ANGGARAN', right_left_bottom)
            sheet.write(y, 2, 'JUMLAH', right_left_bottom)
            sheet.write(y, 3, '%', right_left_bottom)
            sheet.write(y, 4, 'U R A I A N', right_left_bottom)
            sheet.write(y, 5, 'REALISASI', right_left_bottom)
            sheet.write(y, 6, 'ANGGARAN', right_left_bottom)
            sheet.write(y, 7, 'JUMLAH', right_left_bottom)
            sheet.write(y, 8, '%', right_left_bottom)
    
            y += 1
    
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "KAPASITAS PRODUKSI DAN DISTRIBUSI", "", "", "", "")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "H. AIR YANG DIPRODUKSI   (Kapasitas....M3) Debet ....... M3", water_account.water_productivity, 0, water_account.water_productivity, 0)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "I. DISTRIBUSI AIR PADA METER INDUK (Kapasitas....M3)", water_account.water_distribution, 0, water_account.water_distribution, 0)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     I.1. Dapat Dipertanggung Jawabkan", water_account.water_accounted, 0, water_account.water_accounted, 0)
    
            non_revenue_water = water_account.water_distribution - water_account.water_accounted
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     I.2 Taksiran Kehilangan Air", non_revenue_water, 0, non_revenue_water, 0)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "J. AIR YANG DAPAT DIPERTANGGUNG JAWABKAN", "", "", "", "")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     J.1. Tercatat dalam rekening", water_account.recorded_account, 0, water_account.recorded_account, 0)
    
            not_for_sale = water_account.water_accounted - water_account.recorded_account
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     J.2. Tidak dijual", not_for_sale, 0, not_for_sale, 0)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "LAIN - LAIN", "", "", "", "")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "K. JUMLAH PELANGGAN", water_account.number_of_customers, 0, water_account.number_of_customers, 0)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "L. BANYAKNYA PERSONALIA/PEGAWAI", water_account.number_of_employee, 0, water_account.number_of_employee, 0)
    
            price_average = water_price_this_year / water_account.recorded_account
            price_average_until_this_month = water_price_until_this_month / water_account.recorded_account
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "M. RATA-RATA HARGA AIR SETIAP M3 (A.1 / J.1)", price_average, 0, price_average_until_this_month, 0)
            
            profit_average = total_gross_profit_this_year / water_account.recorded_account
            profit_average_until_this_month = total_gross_profit_until_this_month / water_account.recorded_account
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "N. LABA KOTOR SETIAP M3 ( D / J.1 )", profit_average, 0, profit_average_until_this_month, 0)
    
    
            if (water_price_last_month + admin_last_month) > 0:
                percentage_billing = (water_account.payment_receive / (water_price_last_month + admin_last_month)) * 100
                percentage_billing2 = (water_account.payment_receive_until_this_month /  (water_price_last_month + admin_last_month)) * 100
            else:
                percentage_billing = 0
                percentage_billing2 = 0
    
            if (water_price_until_this_month + admin_until_this_month) > 0:
                percentage_billing_until_this_month = (water_account.payment_receive / (water_price_until_this_month + admin_until_this_month)) * 100
                percentage_billing2_until_this_month = (water_account.payment_receive_until_this_month /  (water_price_last_month + admin_last_month)) * 100
            else:
                percentage_billing_until_this_month = 0
                percentage_billing2_until_this_month = 0
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "O. PERSENTASE TAGIHAN REKENING BULAN BERJALAN ( F.1 / E )", percentage_billing, 0, percentage_billing_until_this_month, 0, True)
            format_cells = [bottom, bottom, bottom, bottom, bottom, bottom, bottom, bottom, bottom]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "P. PERSENTASE TAGIHAN REK S/D BULAN INI ( F / E )", percentage_billing2, 0, percentage_billing2_until_this_month, 0, True)
    
    # BATES 2
            
            # y ke 9
            y += 1
            sheet.merge_range(y, 0, y, 3, 'BULAN INI', border)
            sheet.write(y, 4, ' ', right_left_top)
            sheet.merge_range(y, 5, y, 8, 'SAMPAI DENGAN BULAN INI', border)
    
            # y ke 10
            y += 1
            sheet.write(y, 0, ' ', right_left)
            sheet.write(y, 0, ' ', right_left)
            sheet.write(y, 1, ' ', right_left)
            sheet.write(y, 2, 'LEBIH/(KURANG)', border)
            sheet.write(y, 3, ' ', right_left)
            sheet.write(y, 4, ' ', right_left)
            sheet.write(y, 5, ' ', right_left)
            sheet.write(y, 6, ' ', right_left)
            sheet.write(y, 7, 'LEBIH/(KURANG)', border)
            sheet.write(y, 8, ' ', right_left)
    
            # y ke 11
            y += 1
            sheet.write(y, 0, ' ', right_left)
            sheet.write(y, 1, ' ', right_left)
            sheet.write(y, 2, ' ', right_left)
            sheet.write(y, 3, ' ', right_left)
            sheet.write(y, 4, ' ', right_left)
            sheet.write(y, 5, ' ', right_left)
            sheet.write(y, 6, ' ', right_left)
            sheet.write(y, 7, ' ', right_left)
            sheet.write(y, 8, ' ', right_left)
    
            # y ke 12
            y += 1
            sheet.write(y, 0, 'REALISASI', right_left_bottom)
            sheet.write(y, 1, 'ANGGARAN', right_left_bottom)
            sheet.write(y, 2, 'JUMLAH', right_left_bottom)
            sheet.write(y, 3, '%', right_left_bottom)
            sheet.write(y, 4, 'U R A I A N', right_left_bottom)
            sheet.write(y, 5, 'REALISASI', right_left_bottom)
            sheet.write(y, 6, 'ANGGARAN', right_left_bottom)
            sheet.write(y, 7, 'JUMLAH', right_left_bottom)
            sheet.write(y, 8, '%', right_left_bottom)
    
            y += 1
    
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            percentage_water_accounted = (water_account.water_accounted / water_account.water_productivity) * 100
            percentage_water_accounted_until_this_month = (water_account.water_accounted / water_account.water_productivity) * 100
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Q. PERSENTASE AIR YANG DIPERTANGGUNGJAWABKAN ( I.1 / H x 100% )", percentage_water_accounted, 0, percentage_water_accounted_until_this_month, 0, True)
    
            percentage_non_revenue_water = (non_revenue_water / water_account.water_distribution) * 100
            percentage_non_revenue_water_until_this_month = (non_revenue_water / water_account.water_distribution) * 100
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "R. PERSENTASE KEHILANGAN AIR ( I.2 / I X 100% )", percentage_non_revenue_water, 0, percentage_non_revenue_water_until_this_month, 0, True)
    
            percentage_recorded_account = (water_account.recorded_account / water_account.water_productivity) * 100
            percentage_recorded_account_until_this_month = (water_account.recorded_account / water_account.water_productivity) * 100
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "S. PERSENTASE AIR YANG TERCATAT DALAM REKENING (J.1 / H X 100% ))", percentage_recorded_account, 0, percentage_recorded_account_until_this_month, 0, True)
    
            percentage_not_for_sale = (not_for_sale / water_account.water_productivity) * 100
            percentage_not_for_sale_until_this_month = (not_for_sale / water_account.water_productivity) * 100
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "T. PERSENTASE AIR YG TDK DIJUAL (J.2 / H X 100%)", percentage_recorded_account, 0, percentage_recorded_account_until_this_month, 0, True)
    
            average_sales = direct_operation_cost_this_year / water_account.recorded_account
            average_sales_until_this_month = direct_operation_cost_until_this_month / water_account.recorded_account
            format_cells = [bottom, bottom, bottom, bottom, bottom, bottom, bottom, bottom, bottom]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "U. RATA-RATA BIAYA PRODUKSI DAN DISTRIBUSI AIR YANG TERJUAL (C.1/J.1 )", average_sales, 0, average_sales_until_this_month, 0, True)
            
            report_type = self.env['pam.report.type'].search([('code', '=', 'RKU')])
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan Excel'
                })
            
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','sah')])
            y += 2
            sheet.write(y, 1, report_type_ttd.name, center)
            y += 1        
            sheet.write(y, 1, report_type_ttd.position, center)        
            y += 3        
            sheet.write(y, 1, report_type_ttd.name_ttd, center)        
    
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','se7')])
            y -= 4
            sheet.write(y, 3, report_type_ttd.name, center)
            y += 1        
            sheet.write(y, 3, report_type_ttd.position, center)        
            y += 3        
            sheet.write(y, 3, report_type_ttd.name_ttd, center)        
    
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','periksa')])
            y -= 4
            sheet.write(y, 5, report_type_ttd.name, center)
            y += 1        
            sheet.write(y, 5, report_type_ttd.position, center)        
            y += 3        
            sheet.write(y, 5, report_type_ttd.name_ttd, center)        
    
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
            y -= 4
            sheet.write(y, 7, report_type_ttd.name, center)
            y += 1        
            sheet.write(y, 7, report_type_ttd.position, center)        
            y += 3        
            sheet.write(y, 7, report_type_ttd.name_ttd, center)        

            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename
    
    def export_report_pdf(self):
        for record in self:
            report_type = self.env['pam.report.type'].search([('code', '=', 'RKU')])
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan PDF'
                })

            rpt = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','sah')])
            name1 = rpt.name
            position1 = rpt.position
            name_ttd1 = rpt.name_ttd

            rpt2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','se7')])
            name2 = rpt2.name
            position2 = rpt2.position
            name_ttd2 = rpt2.name_ttd

            rpt3 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','periksa')])
            name3 = rpt3.name
            position3 = rpt3.position
            name_ttd3 = rpt3.name_ttd

            rpt4 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
            name4 = rpt4.name
            position4 = rpt4.position
            name_ttd4 = rpt4.name_ttd

            # reports = []
            # for report_type_ttd in report_type_ttds:
            #     reports.append([report_type_ttd.code, report_type_ttd.name, report_type_ttd.position, report_type_ttd.name_ttd])
            # raise ValidationError(_('%s')%(reports))

            data = {
                'ids': record.ids,
                'model': record._name,
                'form': {
                    'months': record.months,
                    'years': record.years,
                    'datetime_cetak': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                    # 'reports': reports,
                    'name1': name1,
                    'position1': position1,
                    'name_ttd1': name_ttd1,
                    'name2': name2,
                    'position2': position2,
                    'name_ttd2': name_ttd2,
                    'name3': name3,
                    'position3': position3,
                    'name_ttd3': name_ttd3,
                    'name4': name4,
                    'position4': position4,
                    'name_ttd4': name_ttd4,
                    'html': record.report_html
                },
            }

            return self.env.ref('pam_accounting.action_pam_operational_summary_report').report_action(record, data=data)


class PamOperationalSummaryReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_operational_summary_template'
    _template = 'pam_accounting.report_operational_summary_template'

    @api.model
    def get_report_values(self, docids, data=None):
        months = data['form']['months']
        years = data['form']['years']
        datetime_cetak = data['form']['datetime_cetak']
        # reports = data['form']['reports']
        name1 = data['form']['name1']
        position1 = data['form']['position1']
        name_ttd1 = data['form']['name_ttd1']
        name2 = data['form']['name2']
        position2 = data['form']['position2']
        name_ttd2 = data['form']['name_ttd2']
        name3 = data['form']['name3']
        position3 = data['form']['position3']
        name_ttd3 = data['form']['name_ttd3']
        name4 = data['form']['name4']
        position4 = data['form']['position4']
        name_ttd4 = data['form']['name_ttd4']
        html = data['form']['html']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'months': months,
            'years': years,
            'datetime_cetak': datetime_cetak,
            # 'reports': reports,
            'name1': name1,
            'position1': position1,
            'name_ttd1': name_ttd1,
            'name2': name2,
            'position2': position2,
            'name_ttd2': name_ttd2,
            'name3': name3,
            'position3': position3,
            'name_ttd3': name_ttd3,
            'name4': name4,
            'position4': position4,
            'name_ttd4': name_ttd4,
            'html': html
        }
