import xlsxwriter
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from dateutil.relativedelta import relativedelta
from datetime import datetime
import time
from io import StringIO, BytesIO
from xlsxwriter.utility import xl_rowcol_to_cell
from calendar import monthrange

import logging
_logger = logging.getLogger(__name__)


class PamFinancialAspectReport(models.TransientModel):
    _name = 'pam.financial.aspect.report'
    _inherit = ['pam.balance.sheet', 'pam.profit.loss', 'pam.cost.breakdown']

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
    years = fields.Selection(_get_years, string='Tahun Aspek Keuangan', default=_default_year, required=True)

    period = fields.Char(compute='set_period')
    start_date = fields.Date(compute='set_period_date')
    end_date = fields.Date(compute='set_period_date')
    last_posted_period = fields.Integer(compute='set_last_posted_period')
    range_start_date = fields.Date(compute='set_last_posted_period')
    range_end_date = fields.Date(compute='set_last_posted_period')

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    report_html = fields.Html(string="Aspek Keuangan")
    tf = fields.Boolean()

    profit_before_tax = fields.Float(compute='calculate_profit_before_tax')

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

    def total_group(self, report_line_ids, start_date, end_date):
        coas = []
        report_configuration_details = self.env['pam.report.configuration.detail'].search([('report_line_id', 'in', report_line_ids)])
        for report_configuration_detail in report_configuration_details:
            coas.append(report_configuration_detail.coa_id.id)
        
        # raise ValidationError(_("%s")%(coas))
        jour_entries = []
        journals_entries = self.env['pam.journal.entry'].search([('entry_date', '>=', start_date), ('entry_date', '<=', end_date), ('state', 'in', ['submit', 'posted'])])
        for journals_entry in journals_entries:
            jour_entries.append(journals_entry.id)

        # raise ValidationError(_("%s")%(journals_entries))

        journal_entry_lines = self.env['pam.journal.entry.line'].search([('journal_entry_id', 'in', jour_entries), ('coa_id', 'in', coas)])
        debit = sum(journal_entry_line.debit for journal_entry_line in journal_entry_lines)
        credit = sum(journal_entry_line.credit for journal_entry_line in journal_entry_lines)
        total = debit + credit
        
        return total

    def _get_profit_lost(self, coa_type, code):
        if coa_type == 'debit':
            sql = """select coalesce(sum(b.debit - b.credit),0) """
        else:
            sql = """select coalesce(sum(b.credit - b.debit),0) """

        sql = sql + """

            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between '2019-01-01' and '2019-01-31' and b.coa_id in (

            select d.coa_id
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LRB' and e.code = %s
            )
            """

        # _logger.debug("SQL : %s", sql)

        self._cr.execute(sql, (code, ))
        result = self._cr.fetchone()
        if result:
            return result[0] 
        else:
            return 0

    def calculate_profit_before_tax(self):
        # Income
        income = self._get_profit_lost('credit', 'PU')
        direct_cost = self._get_profit_lost('debit', 'BLU') 
        indirect_cost = self._get_profit_lost('debit', 'BTU') 
        other_income_cost = self._get_profit_lost('credit', 'PLL') 

        self.profit_before_tax = income - direct_cost - indirect_cost + other_income_cost

    def create_html_row(self, html, number, name, remark, value_percentage_this_year=0, value_numerator_this_year=0,
                        value_denominator_this_year=0,
                        value_percentage_last_year=0, value_numerator_last_year=0, value_denominator_last_year=0,
                        percentage=False):

        percentage_symbol = ''
        if percentage:
            percentage_symbol = '%'

        html = html + "<tr>"
        html = html + "<td>" + number + "</td>"
        html = html + "<td>" + name + "</td>"
        html = html + "<td class='percentage-cell'>" + remark + "</td>"
        html = html + "<td class='percentage-cell'>" + '{0:,.2f}'.format(value_percentage_this_year) + percentage_symbol + "<br/>" + "<u>" + '{0:,.2f}'.format(value_numerator_this_year) + "</u>" + "<br/>" + '{0:,.2f}'.format(value_denominator_this_year) + "</td>"
        html = html + "<td class='percentage-cell'>" + '{0:,.2f}'.format(value_percentage_last_year) + percentage_symbol + "<br/>" + "<u>" + '{0:,.2f}'.format(value_numerator_last_year) + "</u>" + "<br/>" + '{0:,.2f}'.format(value_denominator_last_year) + "</td>"
        html = html + "</tr>"

        return html

    def get_data(self):
        # starting div
        html = "<table class='report-table'>"

        html = html + "<tr>"
        html = html + "<th width='100px' rowspan='2'>NO.</td>"
        html = html + "<th width='400px' rowspan='2'>RASIO</td>"
        html = html + "<th width='400px' rowspan='2'>URAIAN</td>"
        html = html + "<th colspan='2'>TAHUN</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th width='300px'>" + str(self.years) + "</td>"
        html = html + "<th width='300px'>" + str(int(self.years) - 1) + "</td>"
        html = html + "</tr>"


        before_year_start_date = str(int(self.years) - 1) + '-01-01'
        before_year_end_date = (datetime.strptime(self.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
        current_year_start_date = self.years + '-01-01'
        current_year_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        
        # No. 1
        profit_loss_before_tax_until_this_month = self.calculate_profit_loss_before_tax(current_year_start_date, self.end_date)
        productive_asset = self.calculate_productive_assets(current_year_start_date, self.end_date)
        total_1 = (profit_loss_before_tax_until_this_month / productive_asset) * 100
        html = self.create_html_row(html, "1.", "Ratio Laba Terhadap Aktiva Produktif", "<u>Laba Sebelum Pajak x 100%</u><br/>Aktiva Produktif", total_1, profit_loss_before_tax_until_this_month, productive_asset, 0, 0, 0, True)

        # No. 2
        sales = self.calculate_profit_loss(current_year_start_date, self.end_date, 'PU', '%', 'credit')
        total_2 = (profit_loss_before_tax_until_this_month / sales) * 100
        html = self.create_html_row(html, "2.", "Ratio Laba Terhadap Penjualan", "<u>Laba Sebelum Pajak x 100%</u><br/>Penjualan", total_2, profit_loss_before_tax_until_this_month, sales, 0, 0, 0, True)

        # No. 3
        current_asset = self.calculate_current_asset(current_year_start_date, self.end_date)
        current_liabilities = self.calculate_current_liabilities(current_year_start_date, self.end_date)
        total_3 = current_asset / current_liabilities
        html = self.create_html_row(html, "3.", "Ratio Aktiva Lancar Terhadap Hutang Lancar", "<u>Aktiva Lancar</u><br/>Hutang Lancar", total_3, current_asset, current_liabilities, 0, 0, 0)

        # No. 4
        long_term_debt = self.calculate_long_term_debt(current_year_start_date, self.end_date)
        equity = self.calculate_equity(current_year_start_date, self.end_date)
        total_4 = long_term_debt / equity
        html = self.create_html_row(html, "4.", "Ratio Hutang Jangka Panjang Terhadap Equity", "<u>Hutang Jangka Panjang</u><br/>Ekuitas", total_4, long_term_debt, equity, 0, 0, 0)

        # No. 5
        total_asset = self.calculate_total_asset(current_year_start_date, self.end_date, self.last_posted_period)
        total_liabilities = self.calculate_total_liabilites(current_year_start_date, self.end_date, self.last_posted_period)
        total_5 = total_asset / total_liabilities
        html = self.create_html_row(html, "5.", "Ratio Total Aktiva Terhadap Total Hutang", "<u>Total Aktiva</u><br/>Total Hutang", total_5, total_asset, total_liabilities, 0, 0, 0)

        # No. 6
        operation_cost = self.calculate_operation_cost(current_year_start_date, self.end_date)
        total_6 = operation_cost / sales
        html = self.create_html_row(html, "6.", "Ratio Biaya Operasi Terhadap Pendapatan Operasi", "<u>Biaya Operasi</u><br/>Pendapatan Operasi", total_6, operation_cost, sales, 0, 0, 0)

        # No. 7
        profit_loss_business = self.calculate_profit_loss_business(current_year_start_date, self.end_date)
        reductions = self.calculate_reduction(current_year_start_date, self.end_date)
        profit_loss_business_before_reductions = profit_loss_business + reductions
        html = self.create_html_row(html, "7.", "Ratio Laba Operasional Sebelum Penyusutan Terhadap Angsuran Pokok & Bunga Jatuh Tempo", "<u>Laba Operasional Sebelum Penyusutan</u><br/>(Angs. Pokok + Bunga) Jatuh Tempo", 0, profit_loss_business_before_reductions, 0, 0, 0, 0)

        # No. 8
        water_sales = self.calculate_profit_loss(current_year_start_date, self.end_date, 'PU', 'Penjualan Air', 'credit')
        total_8 = productive_asset / water_sales
        html = self.create_html_row(html, "8.", "Ratio Aktiva Produktif Terhadap Penjualan Air", "<u>Aktiva Produktif</u><br/>Penjualan Air", total_8, productive_asset, water_sales, 0, 0, 0)

        # No. 9
        account_receivable = self.calculate_account_receivable(current_year_start_date, self.end_date, self.last_posted_period)
        num_days = int(self.months) * 30
        sales_per_days = sales / num_days
        total_9 = account_receivable / sales_per_days
        html = self.create_html_row(html, "9.", "Jangka Waktu Penagihan Piutang", "<u>Piutang Usaha</u><br/>Jumlah Penjualan: per bulan (1) (Jumlah Hari)", total_9, account_receivable, sales_per_days, 0, 0, 0)

        # No. 10
        water_account = self.env['pam.water.account'].search([('months', '=', self.months), ('years', '=', self.years)])
        payment_receive = water_account.payment_receive

        last_years = self.years
        if self.months == '01':
            last_months = '12'
            last_years = str(int(self.years) - 1)
        else:
            last_months = str(int(self.months) - 1).zfill(2)

        water_account_last_month = self.env['pam.water.account'].search([('months', '=', last_months), ('years', '=', last_years)])
        if water_account_last_month:
            last_month_water_sales = water_account_last_month.this_month_water_bill + water_account_last_month.this_month_administration_fee
        else:
            last_month_water_sales = 0

        if last_month_water_sales == 0:
            ratio_water_account = 0
        else:
            ratio_water_account = payment_receive / last_month_water_sales

        html = self.create_html_row(html, "10.", "Efektivitas Penagihan", "<u>Rekening Air</u><br/>Penjualan Air", ratio_water_account, payment_receive, last_month_water_sales, 0, 0, 0)

        html = html + "</table>"


        report = self.env['pam.financial.aspect.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True
        })

    def create_excel_row(self, sheet, y, col, format_cells, number, name, remark_numerator, remark_denominator,
                         value_percentage_this_year=0, value_numerator_this_year=0, value_denominator_this_year=0,
                         value_percentage_last_year=0, value_numerator_last_year=0, value_denominator_last_year=0):

        row_1 = y
        row_2 = row_1 + 1
        row_3 = row_2 + 1
        sheet.merge_range(row_1, col, row_3, col, number, format_cells[0])

        col += 1
        sheet.merge_range(row_1, col, row_3, col, name, format_cells[1])

        col += 1
        sheet.write(row_1, col, '', format_cells[2])
        sheet.write(row_2, col, remark_numerator, format_cells[3])
        sheet.write(row_3, col, remark_denominator, format_cells[4])

        col += 1
        sheet.write(row_1, col, value_percentage_this_year, format_cells[5])
        sheet.write(row_2, col, value_numerator_this_year, format_cells[6])
        sheet.write(row_3, col, value_denominator_this_year, format_cells[7])

        col += 1
        sheet.write(row_1, col, value_percentage_last_year, format_cells[5])
        sheet.write(row_2, col, value_numerator_last_year, format_cells[6])
        sheet.write(row_3, col, value_denominator_last_year, format_cells[7])


        y = row_3 + 1

        return sheet, y

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN ASPEK KEUANGAN'
            filename = '%s.xlsx' % ('LAPORAN ASPEK KEUANGAN', )
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'LAPORAN ASPEK KEUANGAN',
                'report_format': 'Laporan Excel'
                })
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 14, 'bold': True})
            judul = workbook.add_format({'font_size': 16, 'bold': True})
            payment_date = workbook.add_format({'font_size': 12})
            jalan = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
            bold = workbook.add_format({'bold': True})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'left': 1, 'right': 1, 'bold': True , 'align': 'center', 'bottom': 1})
            top = workbook.add_format({'top': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1})
            right = workbook.add_format({'right': 1})
            merge = workbook.add_format({'bold': True, 'border': True, 'align': 'center', 'font_size': 11, 'font': 'Tahoma', 'bg_color': '#c0c0c0'})
            center = workbook.add_format({'align': 'center', 'font': 'Tahoma', 'font_size': 11, 'bold': True})
            both_border = workbook.add_format({'left': 1, 'right': 1, 'bold': True ,'align': 'center'})
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'right': 1,'left': 1, 'align': 'right'})
            jumlah = workbook.add_format({'right': 1,'left': 1, 'num_format': '#,##0.00'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00%', 'left': 1, 'right': 1 , 'align': 'center'})
            str_total = workbook.add_format({'text_wrap': True, 'bold': True, 'border': 1, 'num_format': '#,##0.00'})
            no_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'align': 'center'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            style_bold = {'bold': True}
            style_font = {'font': 'Tahoma'}
            style_font_size = {'font_size': 11}
            style_underline = {'underline': True}
            style_border_left = {'left': 1}
            style_border_top = {'top': 1}
            style_border_right = {'right': 1}
            style_border_bottom = {'bottom': 1}
            style_alignment_left = {'align': 'left'}
            style_alignment_center = {'align': 'center'}
            style_alignment_right = {'align': 'right'}
            style_currency_format = {'num_format': '#,##0.00'}
            style_backrgound_gray = {'bg_color': '#BFBFBF'}
    
            cell_underline = {}
            cell_underline.update(style_font)
            cell_underline.update(style_font_size)
            cell_underline.update(style_underline)
            cell_underline.update(style_alignment_center)
            cell_underline.update(style_border_right)
            cell_underline.update(style_border_left)
            format_cell_underline = workbook.add_format(cell_underline)
    
            cell_uraian = {}
            cell_uraian.update(style_font)
            cell_uraian.update(style_font_size)
            cell_uraian.update(style_alignment_center)
            cell_uraian.update(style_border_right)
            cell_uraian.update(style_border_left)
            cell_uraian.update(style_border_bottom)
            format_cell_uraian = workbook.add_format(cell_uraian)
    
            cell_text = {}
            cell_text.update(style_font)
            cell_text.update(style_font_size)
            cell_text.update(style_alignment_center)
            cell_text.update(style_border_right)
            cell_text.update(style_border_left)
            format_cell_text = workbook.add_format(cell_text)
    
            cell_rasio = {}
            cell_rasio.update(style_bold)
            cell_rasio.update(style_font)
            cell_rasio.update(style_font_size)
            cell_rasio.update(style_alignment_left)
            cell_rasio.update(style_border_right)
            cell_rasio.update(style_border_left)
            cell_rasio.update(style_border_bottom)
            format_cell_rasio = workbook.add_format(cell_rasio)
    
            cell_text = {}
            cell_text.update(style_font)
            cell_text.update(style_font_size)
            cell_text.update(style_alignment_center)
            cell_text.update(style_border_right)
            cell_text.update(style_border_left)
            cell_text.update(style_underline)
            cell_text.update(style_currency_format)
            format_cell_number_underline = workbook.add_format(cell_text)
    
            cell_text = {}
            cell_text.update(style_font)
            cell_text.update(style_font_size)
            cell_text.update(style_alignment_center)
            cell_text.update(style_border_right)
            cell_text.update(style_border_left)
            cell_text.update(style_currency_format)
            format_cell_number_normal = workbook.add_format(cell_text)
    
            cell_text = {}
            cell_text.update(style_font)
            cell_text.update(style_font_size)
            cell_text.update(style_alignment_center)
            cell_text.update(style_border_right)
            cell_text.update(style_border_left)
            cell_text.update(style_border_bottom)
            cell_text.update(style_currency_format)
            format_cell_number_bottom = workbook.add_format(cell_text)
    
    
            sheet.set_column(0, 0, 5)
            sheet.set_column(1, 1, 40)
            sheet.set_column(2, 2, 60)
            sheet.set_column(3, 3, 40)
            sheet.set_column(4, 4, 40)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','aspek_keuangan')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(1, 4, 1, 4,code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(1, 4, 1, 4,' ', center)
    
            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))
    
            sheet.insert_image(3, 1, 'logo.jpg', {'image_data' : logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})
    
            sheet.merge_range(4, 0, 4, 4, 'PERHITUNGAN PENILAIAN KINERJA ASPEK KEUANGAN', center)
            sheet.merge_range(5, 0, 5, 4, 'PDAM  TIRTA  PAKUAN  KOTA  BOGOR', center)
            sheet.merge_range(6, 0, 6, 4, 'SESUAI DENGAN KEP. MENDAGRI NO.47 TAHUN 1999', center)
            sheet.merge_range(7, 0, 7, 4, 'BULAN : ' + (datetime.strptime(record.months, '%m').strftime("%B")) + ' ' + record.years, center)
    
            sheet.merge_range(10, 0, 11, 0, 'NO', merge)
            sheet.write(12, 0,'', merge)
            sheet.merge_range(10, 1, 11, 1, 'RASIO', merge)
            sheet.write(12, 1,'', merge)
            sheet.merge_range(10, 2, 11, 2, 'URAIAN', merge)
            sheet.merge_range(10, 3, 10, 4, 'TAHUN', merge)
            sheet.write(11, 3, record.years , merge)
            sheet.write(11, 4, str(int(record.years) - 1), merge)
            sheet.merge_range(12, 2, 12, 4,'', merge)
    
            before_year_start_date = str(int(record.years) - 1) + '-01-01'
            before_year_end_date = (datetime.strptime(record.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
            current_year_start_date = record.years + '-01-01'
            current_year_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
            
            y = 13
            col = 0
    
            format_cells = [format_cell_uraian, format_cell_rasio, format_cell_text, format_cell_underline, format_cell_uraian, format_cell_number_normal, format_cell_number_underline, format_cell_number_bottom]
    
            # No. 1
            profit_loss_before_tax_until_this_month = record.calculate_profit_loss_before_tax(current_year_start_date, record.end_date)
            productive_asset = record.calculate_productive_assets(current_year_start_date, record.end_date)
            total_1 = (profit_loss_before_tax_until_this_month / productive_asset) * 100
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "1.", "Ratio Laba Terhadap Aktiva Produktif", "Laba Sebelum Pajak x 100%", "Aktiva Produktif", str(round(total_1, 2)) + "%", profit_loss_before_tax_until_this_month, productive_asset, 0, 0, 0)
    
            # No. 2
            sales = record.calculate_profit_loss(current_year_start_date, record.end_date, 'PU', '%', 'credit')
            total_2 = (profit_loss_before_tax_until_this_month / sales) * 100
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "2.", "Ratio Laba Terhadap Penjualan", "Laba Sebelum Pajak x 100%", "Penjualan", str(round(total_2, 2)) + "%", profit_loss_before_tax_until_this_month, sales, 0, 0, 0)
    
            # No. 3
            current_asset = record.calculate_current_asset(current_year_start_date, record.end_date)
            current_liabilities = record.calculate_current_liabilities(current_year_start_date, record.end_date)
            total_3 = current_asset / current_liabilities
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "3.", "Ratio Aktiva Lancar Terhadap Hutang Lancar", "Aktiva Lancar", "Hutang Lancar", round(total_3, 2), current_asset, current_liabilities, 0, 0, 0)
    
            # No. 4
            long_term_debt = record.calculate_long_term_debt(current_year_start_date, record.end_date)
            equity = record.calculate_equity(current_year_start_date, record.end_date)
            total_4 = long_term_debt / equity
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "4.", "Ratio Hutang Jangka Panjang Terhadap Equity", "Hutang Jangka Panjang", "Ekuitas", round(total_4, 2), long_term_debt, equity, 0, 0, 0)
    
            # No. 5
            total_asset = record.calculate_total_asset(current_year_start_date, record.end_date, record.last_posted_period)
            total_liabilities = record.calculate_total_liabilites(current_year_start_date, record.end_date, record.last_posted_period)
            total_5 = total_asset / total_liabilities
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "5.", "Ratio Total Aktiva Terhadap Total Hutang", "Total Aktiva", "Total Hutang", round(total_5, 2), total_asset, total_liabilities, 0, 0, 0)
    
            # No. 6
            operation_cost = record.calculate_operation_cost(current_year_start_date, record.end_date)
            total_6 = operation_cost / sales
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "6.", "Ratio Biaya Operasi Terhadap Pendapatan Operasi", "Biaya Operasi", "Pendapatan Operasi", round(total_6, 2), operation_cost, sales, 0, 0, 0)
    
            # No. 7
            profit_loss_business = record.calculate_profit_loss_business(current_year_start_date, record.end_date)
            reductions = record.calculate_reduction(current_year_start_date, record.end_date)
            profit_loss_business_before_reductions = profit_loss_business + reductions
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "7.", "Ratio Laba Operasional Sebelum Penyusutan Terhadap Angsuran Pokok & Bunga Jatuh Tempo", "Laba Operasional Sebelum Penyusutan", "(Angs. Pokok + Bunga) Jatuh Tempo", round(0, 2), profit_loss_business_before_reductions, 0, 0, 0, 0)
    
            # No. 8
            water_sales = record.calculate_profit_loss(current_year_start_date, record.end_date, 'PU', 'Penjualan Air', 'credit')
            total_8 = productive_asset / water_sales
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "8.", "Ratio Aktiva Produktif Terhadap Penjualan Air", "Aktiva Produktif", "Penjualan Air", round(total_8, 2), productive_asset, water_sales, 0, 0, 0)
    
            # No. 9
            account_receivable = record.calculate_account_receivable(current_year_start_date, record.end_date, record.last_posted_period)
            num_days = int(record.months) * 30
            sales_per_days = sales / num_days
            total_9 = account_receivable / sales_per_days
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "9.", "Jangka Waktu Penagihan Piutang", "Piutang Usaha", "Jumlah Penjualan: per bulan (1) (Jumlah Hari)", round(total_9, 2), account_receivable, sales_per_days, 0, 0, 0)
    
            # No. 10
            water_account = self.env['pam.water.account'].search([('months', '=', record.months), ('years', '=', record.years)])
            payment_receive = water_account.payment_receive
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "10", "Efektivitas Penagihan", "Rekening Air", "Penjualan Air", round(0, 2), payment_receive, 0, 0, 0, 0)
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename

    def export_report_pdf(self):
        for record in self:
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'LAPORAN ASPEK KEUANGAN',
                'report_format': 'Laporan PDF'
                })
    
            data = {
                'ids': record.ids,
                'model': record._name,
                'form': {
                    'months': record.months,
                    'years': record.years,
                    'datetime_cetak': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                    'html': record.report_html
                },
            }
    
            return self.env.ref('pam_accounting.action_pam_financial_aspect_report').report_action(record, data=data)


class PamFinancialAspectReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_financial_aspect_template'
    _template = 'pam_accounting.report_financial_aspect_template'

    @api.model
    def get_report_values(self, docids, data=None):
        months = data['form']['months']
        years = data['form']['years']
        datetime_cetak = data['form']['datetime_cetak']
        html = data['form']['html']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'months': months,
            'years': years,
            'datetime_cetak': datetime_cetak,
            'html': html
        }
