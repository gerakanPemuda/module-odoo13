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


class PamCashTurnoverReport(models.TransientModel):
    _name = 'pam.cash.turnover.report'
    _inherit= ['pam.cash.flow', 'pam.balance.sheet']

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
    years = fields.Selection(_get_years, string='Tahun Perpustakaan Kas', default=_default_year, required=True)
    period = fields.Char(compute='set_period')
    start_date = fields.Date(compute='set_period_date')
    end_date = fields.Date(compute='set_period_date')
    last_posted_period = fields.Integer(compute='set_last_posted_period')
    range_start_date = fields.Date(compute='set_last_posted_period')
    range_end_date = fields.Date(compute='set_last_posted_period')

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    report_html = fields.Html(string="Perputaran Kas")
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
        value_last_year=0, 
        budget_this_year=0, 
        value_this_year_until_this_month = 0, 
        value_last_year_until_this_month = 0, 
        budget_this_year_until_this_month=0):

        html = html + "<tr class='" + class_name + "'>"

        if value_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_this_year) + "</td>"
        else:
            html = html + "<td></td>"

        if value_last_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_last_year) + "</td>"
        else:
            html = html + "<td></td>"

        if budget_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_this_year) + "</td>"
        else:
            html = html + "<td></td>"

        if value_this_year != "":
            value_diff = value_this_year - value_last_year
            value_budget_diff = value_this_year -budget_this_year
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff) + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_budget_diff) + "</td>"
        else:
            html = html + "<td></td>"
            html = html + "<td></td>"

        html = html + "<td>" + name + "</td>"

        if value_this_year_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_this_year_until_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        if value_last_year_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_last_year_until_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        if budget_this_year_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_this_year_until_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        if value_this_year_until_this_month != "":
            value_diff = value_this_year_until_this_month - value_last_year_until_this_month
            value_budget_diff = value_this_year_until_this_month -budget_this_year_until_this_month
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff) + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_budget_diff) + "</td>"
        else:
            html = html + "<td></td>"
            html = html + "<td></td>"

        html = html + "</tr>"

        return html

    def get_data(self):

        # starting div
        html = "<table class='report-table'>"

        html = html + "<tr>"
        html = html + "<th colspan='2'>REALISASI BULAN INI</td>"
        html = html + "<th width='300px' rowspan='2'>ANGGARAN</td>"
        html = html + "<th colspan='2'>PERBANDINGAN THN. INI DGN REALISASI</td>"
        html = html + "<th width='500px' rowspan='2'>PERKIRAAN</td>"
        html = html + "<th colspan='2'>REALISASI S/D BULAN INI</td>"
        html = html + "<th width='300px' rowspan='2'>ANGGARAN</td>"
        html = html + "<th colspan='2'>PERBANDINGAN THN. INI DGN REALISASI</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th width='300px'>TAHUN INI</td>"
        html = html + "<th width='300px'>TAHUN LALU</td>"
        html = html + "<th width='300px'>TAHUN LALU</td>"
        html = html + "<th width='300px'>ANGGARAN</td>"
        html = html + "<th width='300px'>TAHUN INI</td>"
        html = html + "<th width='300px'>TAHUN LALU</td>"
        html = html + "<th width='300px'>TAHUN LALU</td>"
        html = html + "<th width='300px'>ANGGARAN</td>"
        html = html + "</tr>"

        before_month_start_date = str(int(self.years) - 1) + '-' + self.months + '-01'
        before_month_end_date = (datetime.strptime(str(int(self.years) - 1) + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        current_month_start_date = self.years + '-' + self.months+ '-01'
        current_month_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        before_year_start_date = str(int(self.years) - 1) + '-01-01'
        before_year_end_date = (datetime.strptime(self.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
        current_year_start_date = self.years + '-01-01'
        current_year_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        html = self.create_html_row(html, "", "<b>A. Penerimaan</b>", "", "", "", "", "", "")

        total_income_this_year = 0
        total_income_last_year = 0
        total_income_budget_this_year = 0
        total_income_this_year_until_this_month = 0
        total_income_last_year_until_this_month = 0
        total_income_budget_this_year_until_this_month = 0

        report_type_code = ['PO']
        total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month = self.calculate_cash_turnover(report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date)
        html = self.create_html_row(html, "", "A.1. Pnerimaan Operasional", total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month)

        total_income_this_year += total_value_this_year
        total_income_last_year += total_value_last_year
        total_income_budget_this_year += total_budget_this_year
        total_income_this_year_until_this_month += total_value_this_year_until_this_month
        total_income_last_year_until_this_month += total_value_last_year_until_this_month
        total_income_budget_this_year_until_this_month += total_budget_this_year_until_this_month

        report_type_code = ['PNO']
        total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month = self.calculate_cash_turnover(report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date)
        html = self.create_html_row(html, "", "A.2. Pnerimaan Non Operasional", total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month)

        total_income_this_year += total_value_this_year
        total_income_last_year += total_value_last_year
        total_income_budget_this_year += total_budget_this_year
        total_income_this_year_until_this_month += total_value_this_year_until_this_month
        total_income_last_year_until_this_month += total_value_last_year_until_this_month
        total_income_budget_this_year_until_this_month += total_budget_this_year_until_this_month

        html = self.create_html_row(html, "total-cell", "Jumlah Penerimaan", total_income_this_year, total_income_last_year, total_income_budget_this_year, total_income_this_year_until_this_month, total_income_last_year_until_this_month, total_income_budget_this_year_until_this_month)

        html = self.create_html_row(html, "", "<b>B. Pengeluaran</b>", "", "", "", "", "", "")

        total_cost_this_year = 0
        total_cost_last_year = 0
        total_cost_budget_this_year = 0
        total_cost_this_year_until_this_month = 0
        total_cost_last_year_until_this_month = 0
        total_cost_budget_this_year_until_this_month = 0

        report_type_code = ['PLO']
        total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month = self.calculate_cash_turnover(report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date)
        html = self.create_html_row(html, "", "B.1. Pengeluaran Operasional", total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month)

        total_cost_this_year += total_value_this_year
        total_cost_last_year += total_value_last_year
        total_cost_budget_this_year += total_budget_this_year
        total_cost_this_year_until_this_month += total_value_this_year_until_this_month
        total_cost_last_year_until_this_month += total_value_last_year_until_this_month
        total_cost_budget_this_year_until_this_month += total_budget_this_year_until_this_month

        report_type_code = ['PI', 'PLNO']
        total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month = self.calculate_cash_turnover(report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date)
        html = self.create_html_row(html, "", "B.2. Pengeluaran Non Operasional", total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month)

        total_cost_this_year += total_value_this_year
        total_cost_last_year += total_value_last_year
        total_cost_budget_this_year += total_budget_this_year
        total_cost_this_year_until_this_month += total_value_this_year_until_this_month
        total_cost_last_year_until_this_month += total_value_last_year_until_this_month
        total_cost_budget_this_year_until_this_month += total_budget_this_year_until_this_month

        html = self.create_html_row(html, "total-cell", "Jumlah Pengeluaran", total_cost_this_year, total_cost_last_year, total_cost_budget_this_year, total_cost_this_year_until_this_month, total_cost_last_year_until_this_month, total_cost_budget_this_year_until_this_month)

        total_this_year = total_income_this_year + total_cost_this_year
        total_last_year = total_income_last_year + total_cost_last_year
        total_budget_this_year = total_income_budget_this_year + total_cost_budget_this_year
        total_this_year_until_this_month = total_income_this_year_until_this_month + total_cost_this_year_until_this_month
        total_last_year_until_this_month = total_income_last_year_until_this_month + total_cost_last_year_until_this_month
        total_budget_until_this_month = total_cost_budget_this_year_until_this_month + total_cost_budget_this_year_until_this_month

        html = self.create_html_row(html, "total-cell", "C. Kenaikan / Penurunan Kas", total_this_year, total_last_year, total_budget_this_year, total_this_year_until_this_month, total_last_year_until_this_month, total_budget_until_this_month)

        ending_balance = self.get_last_balance('AL', 'Kas dan Bank')
        html = self.create_html_row(html, "total-cell", "D. Saldo Awal Kas", ending_balance, 0, 0, ending_balance, 0, 0)

        total_this_year += ending_balance
        total_last_year += 0
        total_budget_this_year += 0
        total_this_year_until_this_month += ending_balance
        total_last_year_until_this_month += 0
        total_budget_until_this_month += 0

        html = self.create_html_row(html, "total-cell", "E. Saldo Akhir Kas", total_this_year, total_last_year, total_budget_this_year, total_this_year_until_this_month, total_last_year_until_this_month, total_budget_until_this_month)

        html = html + "</table>"

        report = self.env['pam.cash.turnover.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True
        })

    def create_excel_row(self, sheet, y, col, format_cells, 
        name, 
        value_this_year=0, 
        value_last_year=0, 
        budget_this_year=0, 
        value_this_year_until_this_month = 0, 
        value_last_year_until_this_month = 0, 
        budget_this_year_until_this_month=0):

        if value_this_year != "":
            value_diff_this_year = value_this_year - value_last_year
            value_budget_diff_this_year = value_this_year - budget_this_year
        else:
            value_diff_this_year = ""
            value_budget_diff_this_year = ""

        if value_this_year_until_this_month != "":
            value_diff_this_year_until_this_month = value_this_year_until_this_month - value_last_year_until_this_month
            value_budget_diff_this_year_until_this_month = value_this_year_until_this_month - budget_this_year_until_this_month
        else:
            value_diff_this_year_until_this_month = ""
            value_budget_diff_this_year_until_this_month = ""

        sheet.write(y, col, value_this_year, format_cells[0])
        col += 1
        sheet.write(y, col, value_last_year, format_cells[1])
        col += 1
        sheet.write(y, col, budget_this_year, format_cells[2])
        col += 1
        sheet.write(y, col, value_diff_this_year, format_cells[3])
        col += 1
        sheet.write(y, col, value_budget_diff_this_year, format_cells[4])
        col += 1
        sheet.write(y, col, name, format_cells[5])
        col += 1
        sheet.write(y, col, value_this_year_until_this_month, format_cells[6])
        col += 1
        sheet.write(y, col, value_last_year_until_this_month, format_cells[7])
        col += 1
        sheet.write(y, col, budget_this_year_until_this_month, format_cells[8])
        col += 1
        sheet.write(y, col, value_diff_this_year_until_this_month, format_cells[9])
        col += 1
        sheet.write(y, col, value_budget_diff_this_year_until_this_month, format_cells[10])

        y = y + 1

        return sheet, y

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN PERPUTARAN KAS'
            filename = '%s.xlsx' % ('LAPORAN PERPUTARAN KAS', )
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font': 'Arial', 'align': 'center', 'font_size': 12, 'font_color': '#993300', 'bold': True})
            judul = workbook.add_format({'font': 'Tahoma', 'align': 'center', 'font_size': 14})
            payment_date = workbook.add_format({'font_size': 12})
            jalan = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
            bold = workbook.add_format({'bold': True})
            merge = workbook.add_format({'bold': True, 'border': True, 'font': 'Arial', 'font_size': 14, 'bg_color': '#00ffff'})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1})
            top = workbook.add_format({'top': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'center'})
            right = workbook.add_format({'right': 1})
            center = workbook.add_format({'align': 'center', 'bold': 1, 'font_size': 16, 'font': 'Tahoma', 'font_color': '#0000ff'})
            center_bottom = workbook.add_format({'align': 'center', 'bottom': 1})
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'right': 1,'left': 1, 'align': 'right'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'left': 1, 'right': 1})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'border': True})
            jumlah = workbook.add_format({'text_wrap': True, 'bold': True, 'border': True})
            str_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
            no_total = workbook.add_format({'text_wrap': True, 'bold': True, 'left': 1, 'right': 1})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            style_bold = {'bold': True}
            style_font = {'font': 'Arial'}
            style_size = {'font_size': 14}
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
    
            cell_title = {}
            cell_title.update(style_border_left)
            cell_title.update(style_border_right)
            cell_title.update(style_alignment_left)
            cell_title.update(style_font)
            cell_title.update(style_size)
            format_cell_title = workbook.add_format(cell_title)
    
            cell_text.update(style_bold)
            cell_text.update(style_font)
            format_cell_text_bold = workbook.add_format(cell_text)
    
            cell_text.update(style_border_top)
            cell_text.update(style_font)
            cell_text.update(style_size)
            format_cell_text_bold_highlight = workbook.add_format(cell_text)
    
            cell_center = {}
            cell_center.update(style_bold)
            cell_center.update(style_alignment_center)
            cell_center.update(style_font)
            cell_center.update(style_size)
            format_cell_center = workbook.add_format(cell_center)
    
            cell_bottom = {}
            cell_bottom.update(style_bold)
            cell_bottom.update(style_border_bottom)
            cell_bottom.update(style_alignment_left)
            cell_bottom.update(style_font)
            cell_bottom.update(style_size)
            format_cell_bottom = workbook.add_format(cell_bottom)
    
            cell_number = {}
            cell_number.update(style_border_left)
            cell_number.update(style_border_right)
            cell_number.update(style_alignment_right)
            cell_number.update(style_currency_format)
            cell_number.update(style_font)
            cell_number.update(style_size)
            format_cell_number_normal = workbook.add_format(cell_number)
    
            # cell_number.update(style_bold)
            # cell_number.update(style_font)
            # format_cell_number_bold = workbook.add_format(cell_number)
    
            cell_number.update(style_border_top)
            cell_number.update(style_border_bottom)
            cell_number.update(style_font)
            cell_number.update(style_size)
            format_cell_number_bold_highlight = workbook.add_format(cell_number)
    
    
            sheet.set_column(0, 4, 25)
            sheet.set_column(5, 5, 45)
            sheet.set_column(6, 10, 25)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','perputaran_kas')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.write(1, 10, code_iso.code_iso, wrap_text)
            else:
                sheet.write(1, 10, ' ', title)
    
            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))
    
            sheet.insert_image(1, 1, 'logo.jpg', {'image_data' : logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})
    
            sheet.merge_range(3, 0, 3, 10, 'LAPORAN PERPUTARAN KAS', center)
            sheet.merge_range(4, 0, 4, 10, 'BULAN : ' + (datetime.strptime(record.months, '%m').strftime("%B")) + ' ' + record.years, center)
    
            sheet.merge_range(6, 0, 6, 2, 'B U L A N  I N I', merge)
            sheet.merge_range(7, 0, 7, 1, 'REALISASI', merge)
            sheet.merge_range(7, 2, 8, 2, 'ANGGARAN', merge)
            sheet.write(8, 0, 'TAHUN INI', merge)
            sheet.write(8, 1, 'TAHUN LALU', merge)
    
            sheet.merge_range(6, 3, 6, 4, 'PERBANDINGAN TAHUN LALU', merge)
            sheet.merge_range(7, 3, 8, 3, 'REALISASI DENGAN TAHUN LALU', merge)
            sheet.merge_range(7, 4, 8, 4, 'REALISASI DENGAN ANGGARAN', merge)
    
            sheet.merge_range(6, 5, 8, 5, 'U R A I A N', merge)
    
            sheet.merge_range(6, 6, 6, 8, 'S/D B U L A N  I N I', merge)
            sheet.merge_range(7, 6, 7, 7, 'REALISASI', merge)
            sheet.merge_range(7, 8, 8, 8, 'ANGGARAN', merge)
            sheet.write(8, 6, 'TAHUN INI', merge)
            sheet.write(8, 7, 'TAHUN LALU', merge)
    
            sheet.merge_range(6, 9, 6, 10, 'PERBANDINGAN TAHUN INI', merge)
            sheet.merge_range(7, 9, 8, 9, 'REALISASI DENGAN TAHUN LALU', merge)
            sheet.merge_range(7, 10, 8, 10, 'REALISASI DENGAN ANGGARAN', merge)
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'LPK')])
            report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id)])
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan Excel'
                })
            
            before_month_start_date = str(int(record.years) - 1) + '-' + record.months + '-01'
            before_month_end_date = (datetime.strptime(str(int(record.years) - 1) + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
            current_month_start_date = record.years + '-' + record.months+ '-01'
            current_month_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
            before_year_start_date = str(int(record.years) - 1) + '-01-01'
            before_year_end_date = (datetime.strptime(record.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
            current_year_start_date = record.years + '-01-01'
            current_year_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
            y = 9
            col = 0
    
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_bold, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "", "" )
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "A. Penerimaan", "", "", "", "", "", "" )
    
            total_income_this_year = 0
            total_income_last_year = 0
            total_income_budget_this_year = 0
            total_income_this_year_until_this_month = 0
            total_income_last_year_until_this_month = 0
            total_income_budget_this_year_until_this_month = 0
    
            report_type_code = ['PO']
            total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month = record.calculate_cash_turnover(report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date)
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_title, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     A.1. Pnerimaan Operasional", total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month)
    
            total_income_this_year += total_value_this_year
            total_income_last_year += total_value_last_year
            total_income_budget_this_year += total_budget_this_year
            total_income_this_year_until_this_month += total_value_this_year_until_this_month
            total_income_last_year_until_this_month += total_value_last_year_until_this_month
            total_income_budget_this_year_until_this_month += total_budget_this_year_until_this_month
    
            report_type_code = ['PNO']
            total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month = record.calculate_cash_turnover(report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date)
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_title, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     A.2. Pnerimaan Non Operasional", total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month)
    
            total_income_this_year += total_value_this_year
            total_income_last_year += total_value_last_year
            total_income_budget_this_year += total_budget_this_year
            total_income_this_year_until_this_month += total_value_this_year_until_this_month
            total_income_last_year_until_this_month += total_value_last_year_until_this_month
            total_income_budget_this_year_until_this_month += total_budget_this_year_until_this_month
    
            format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_center, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah Penerimaan", total_income_this_year, total_income_last_year, total_income_budget_this_year, total_income_this_year_until_this_month, total_income_last_year_until_this_month, total_income_budget_this_year_until_this_month)
    
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_bold, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "B. Pengeluaran", "", "", "", "", "", "")
    
            total_cost_this_year = 0
            total_cost_last_year = 0
            total_cost_budget_this_year = 0
            total_cost_this_year_until_this_month = 0
            total_cost_last_year_until_this_month = 0
            total_cost_budget_this_year_until_this_month = 0
    
            report_type_code = ['PLO']
            total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month = record.calculate_cash_turnover(report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date)
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_title, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     B.1. Pengeluaran Operasional", total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month)
    
            total_cost_this_year += total_value_this_year
            total_cost_last_year += total_value_last_year
            total_cost_budget_this_year += total_budget_this_year
            total_cost_this_year_until_this_month += total_value_this_year_until_this_month
            total_cost_last_year_until_this_month += total_value_last_year_until_this_month
            total_cost_budget_this_year_until_this_month += total_budget_this_year_until_this_month
    
            report_type_code = ['PI', 'PLNO']
            total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month = record.calculate_cash_turnover(report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date)
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_title, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "     B.2. Pengeluaran Non Operasional", total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month)
    
            total_cost_this_year += total_value_this_year
            total_cost_last_year += total_value_last_year
            total_cost_budget_this_year += total_budget_this_year
            total_cost_this_year_until_this_month += total_value_this_year_until_this_month
            total_cost_last_year_until_this_month += total_value_last_year_until_this_month
            total_cost_budget_this_year_until_this_month += total_budget_this_year_until_this_month
    
            format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_center, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah Pengeluaran", total_cost_this_year, total_cost_last_year, total_cost_budget_this_year, total_cost_this_year_until_this_month, total_cost_last_year_until_this_month, total_cost_budget_this_year_until_this_month)
    
            total_this_year = total_income_this_year + total_cost_this_year
            total_last_year = total_income_last_year + total_cost_last_year
            total_budget_this_year = total_income_budget_this_year + total_cost_budget_this_year
            total_this_year_until_this_month = total_income_this_year_until_this_month + total_cost_this_year_until_this_month
            total_last_year_until_this_month = total_income_last_year_until_this_month + total_cost_last_year_until_this_month
            total_budget_until_this_month = total_cost_budget_this_year_until_this_month + total_cost_budget_this_year_until_this_month
    
            format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_bold, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "C. Kenaikan / Penurunan Kas", total_this_year, total_last_year, total_budget_this_year, total_this_year_until_this_month, total_last_year_until_this_month, total_budget_until_this_month)
    
            ending_balance = record.get_last_balance('AL', 'Kas dan Bank')
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "D. Saldo Awal Kas", ending_balance, 0, 0, ending_balance, 0, 0)
    
            total_this_year += ending_balance
            total_last_year += 0
            total_budget_this_year += 0
            total_this_year_until_this_month += ending_balance
            total_last_year_until_this_month += 0
            total_budget_until_this_month += 0
    
            format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_bottom, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "E. Saldo Akhir Kas", total_this_year, total_last_year, total_budget_this_year, total_this_year_until_this_month, total_last_year_until_this_month, total_budget_until_this_month)
    
            # y += 2
            # sheet.merge_range(y, 0, y, 1, 'Disetujui', judul)
            # sheet.merge_range(y, 4, y, 6, 'Diperiksa,', judul)
            # sheet.merge_range(y, 8, y, 10, 'Dibuat oleh,', judul)
    
            # y += 1
            # sheet.merge_range(y, 0, y, 1, 'Direktur Utama', judul)
            # sheet.merge_range(y, 4, y, 6, 'Assisten Manajer Akuntansi & Perpajakan', judul)
            # sheet.merge_range(y, 8, y, 10, 'Staf Akuntansi & Perpajakan', judul)
            # y += 1
    
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','se7')])
            y += 2
            sheet.write(y, 1, report_type_ttd.name, judul)
            y += 1        
            sheet.write(y, 1, report_type_ttd.position, judul)        
            y += 3        
            sheet.write(y, 1, report_type_ttd.name_ttd, judul)        
    
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','periksa')])
            y -= 4
            sheet.write(y, 5, report_type_ttd.name, judul)
            y += 1        
            sheet.write(y, 5, report_type_ttd.position, judul)        
            y += 3        
            sheet.write(y, 5, report_type_ttd.name_ttd, judul)        
    
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
            y -= 4
            sheet.write(y, 9, report_type_ttd.name, judul)
            y += 1        
            sheet.write(y, 9, report_type_ttd.position, judul)        
            y += 3        
            sheet.write(y, 9, report_type_ttd.name_ttd, judul)        
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename

    def export_report_pdf(self):
        for record in self:
            report_type = self.env['pam.report.type'].search([('code', '=', 'LPK')])
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan PDF'
                })
    
            rpt = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','se7')])
            name1 = rpt.name
            position1 = rpt.position
            name_ttd1 = rpt.name_ttd
    
            rpt2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','periksa')])
            name2 = rpt2.name
            position2 = rpt2.position
            name_ttd2 = rpt2.name_ttd
    
            rpt3 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
            name3 = rpt3.name
            position3 = rpt3.position
            name_ttd3 = rpt3.name_ttd
    
            data = {
                'ids': record.ids,
                'model': record._name,
                'form': {
                    'months': record.months,
                    'years': record.years,
                    'datetime_cetak': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                    'name1': name1,
                    'position1': position1,
                    'name_ttd1': name_ttd1,
                    'name2': name2,
                    'position2': position2,
                    'name_ttd2': name_ttd2,
                    'name3': name3,
                    'position3': position3,
                    'name_ttd3': name_ttd3,
                    'html': record.report_html
                },
            }
    
            return self.env.ref('pam_accounting.action_pam_cash_turnover_report').report_action(record, data=data)


class PamCashTurnoverReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_cash_turnover_template'
    _template = 'pam_accounting.report_cash_turnover_template'

    @api.model
    def get_report_values(self, docids, data=None):
        months = data['form']['months']
        years = data['form']['years']
        datetime_cetak = data['form']['datetime_cetak']
        name1 = data['form']['name1']
        position1 = data['form']['position1']
        name_ttd1 = data['form']['name_ttd1']
        name2 = data['form']['name2']
        position2 = data['form']['position2']
        name_ttd2 = data['form']['name_ttd2']
        name3 = data['form']['name3']
        position3 = data['form']['position3']
        name_ttd3 = data['form']['name_ttd3']
        html = data['form']['html']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'months': months,
            'years': years,
            'datetime_cetak': datetime_cetak,
            'name1': name1,
            'position1': position1,
            'name_ttd1': name_ttd1,
            'name2': name2,
            'position2': position2,
            'name_ttd2': name_ttd2,
            'name3': name3,
            'position3': position3,
            'name_ttd3': name_ttd3,
            'html': html
        }
