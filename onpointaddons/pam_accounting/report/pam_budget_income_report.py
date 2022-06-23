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


class PamBudgetIncomeReport(models.TransientModel):
    _name = 'pam.budget.income.report'
    _inherit = ['pam.profit.loss', 'pam.cost.breakdown']

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
        coa,
        name,
        empty=False):

        html = html + "<tr class='" + class_name + "'>"

        html = html + "<td style='text-align:center'>" + coa + "</td>"
        html = html + "<td>" + name + "</td>"

        for month in range(15):
            if empty:
                html = html + "<td></td>"
            else:
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"

        html = html + "</tr>"
        
        return html

    def get_data(self):

        # starting div
        html = "<div style='overflow:auto; width:2000px'>"
        html = html + "<table class='report-table'>"

        html = html + "<tr>"
        html = html + "<th rowspan='2' width='150px'>Kode Perkiraan</td>"
        html = html + "<th rowspan='2' width='700px'>Perkiraan</td>"
        html = html + "<th colspan='12'>Bulan</td>"
        html = html + "<th rowspan='2' width='300px'>Jumlah th. 2019</td>"
        html = html + "<th rowspan='2' width='300px'>Jumlah th. 2018</td>"
        html = html + "<th rowspan='2' width='300px'>Selisih</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th width='300px'>I</td>"
        html = html + "<th width='300px'>II</td>"
        html = html + "<th width='300px'>III</td>"
        html = html + "<th width='300px'>IV</td>"
        html = html + "<th width='300px'>V</td>"
        html = html + "<th width='300px'>VI</td>"
        html = html + "<th width='300px'>VII</td>"
        html = html + "<th width='300px'>VIII</td>"
        html = html + "<th width='300px'>IX</td>"
        html = html + "<th width='300px'>X</td>"
        html = html + "<th width='300px'>XI</td>"
        html = html + "<th width='300px'>XII</td>"
        html = html + "</tr>"

        html = self.create_html_row(html, "", "", "<b>PENDAPATAN USAHA</b>", True)
        html = self.create_html_row(html, "", "", "", True)
        html = self.create_html_row(html, "", "31111", "<b>PENJUALAN AIR</b>", True)
        html = self.create_html_row(html, "", "31111110", "Harga Air")
        html = self.create_html_row(html, "", "31111120", "Abonemen")
        html = self.create_html_row(html, "total-cell", "", "Jumlah Penjualan Air")
        
        html = self.create_html_row(html, "", "", "", True)

        html = self.create_html_row(html, "", "31121", "<b>PENDAPATAN NON AIR</b>", True)
        html = self.create_html_row(html, "", "31121110", "Sambungan Baru")
        html = self.create_html_row(html, "", "31121120", "Jasa Bukaan Kembali")
        html = self.create_html_row(html, "", "31121130", "Denda Keterlambatan Bayar")
        html = self.create_html_row(html, "", "31121160", "Jasa Penertiban Meter")
        html = self.create_html_row(html, "", "31121220", "Pendapatan Lain-lain", True)
        html = self.create_html_row(html, "", "", "- BBN")
        html = self.create_html_row(html, "", "", "- Pelanggaran")
        html = self.create_html_row(html, "", "", "- Adm Retikulasi")
        html = self.create_html_row(html, "total-cell", "", "Jumlah Pendapatan Non Air")
        html = self.create_html_row(html, "total-cell", "", "Jumlah Pendapatan Usaha")

        html = self.create_html_row(html, "", "", "", True)

        html = self.create_html_row(html, "", "51111111", "<b>PENDAPATAN DILUAR USAHA</b>", True)
        html = self.create_html_row(html, "", "51111110", "Bunga Deposito")
        html = self.create_html_row(html, "", "51111120", "Jasa Giro")
        html = self.create_html_row(html, "", "51111170", "Rupa - rupa Pendapatan Lainnya")
        html = self.create_html_row(html, "total-cell", "", "Jumlah Pendapatan Diluar Usaha")
        html = self.create_html_row(html, "total-cell", "", "Jumlah Seluruh Pendapatan")

        html = html + "</table>"
        html = html + "</div>"


        report = self.env['pam.budget.income.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True,
        })

    def create_excel_group_row(self, sheet, y, col, format_cells, 
        name):

        sheet.write(y, col, name, format_cells[0])

        y = y + 1

        return sheet, y

    def create_excel_row(self, sheet, y, col, format_cells, 
        coa,
        name,
        empty=False):

        sheet.write(y, col, coa, format_cells[0])
        col += 1
        sheet.write(y, col, name, format_cells[0])
        col += 1

        for month in range(14):
            if empty:
                sheet.write(y, col, "", format_cells[0])
            else:
                sheet.write(y, col, "0", format_cells[1])

            col += 1

        y = y + 1

        return sheet, y

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN LABA RUGI'
            filename = '%s.xlsx' % ('Rencana Pendapatan Usaha dan Diluar Usaha',)
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Rencana Pendapatan Usaha Dan Diluar Usaha',
                'report_format': 'Laporan Excel'
                })
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 14, 'bold': True})
            judul = workbook.add_format({'bold': True, 'align': 'center'})
            payment_date = workbook.add_format({'font_size': 12})
            jalan = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
            bold = workbook.add_format({'bold': True})
            merge = workbook.add_format({'bold': True, 'border': True})
            border = workbook.add_format({'bold': True, 'border': True, 'font_size': 11, 'font': 'Tahoma', 'align': 'center'})
            center = workbook.add_format({'bold': True, 'font_size': 12, 'font': 'Tahoma', 'align': 'center'})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1})
            top = workbook.add_format({'top': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'center'})
            right = workbook.add_format({'right': 1})
            center_bottom = workbook.add_format({'align': 'center', 'bottom': 1})
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'right': 1,'left': 1, 'align': 'right'})
            jumlah = workbook.add_format({'right': 1,'left': 1, 'num_format': '#,##0.00'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            str_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
            no_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'align': 'center'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            style_bold = {'bold': True}
            style_font = {'font': 'Tahoma'}
            style_font_size = {'font_size': 11}
            style_border_left = {'left': 1}
            style_border_top = {'top': 1}
            style_border_right = {'right': 1}
            style_border_bottom = {'bottom': 1}
            style_alignment_left = {'align': 'left'}
            style_alignment_center = {'align': 'center'}
            style_alignment_right = {'align': 'right'}
            style_currency_format = {'num_format': '#,##0.00'}
    
            cell_last = {}
            cell_last.update(style_bold)
            cell_last.update(style_border_bottom)
            cell_last.update(style_alignment_left)
            cell_last.update(style_font)
            cell_last.update(style_font_size)
            format_cell_last = workbook.add_format(cell_last)
    
            cell_name = {}
            cell_name.update(style_bold)
            cell_name.update(style_alignment_left)
            cell_name.update(style_font)
            cell_name.update(style_font_size)
            format_cell_name = workbook.add_format(cell_name)
    
            cell_name_2 = {}
            cell_name_2.update(style_alignment_left)
            cell_name_2.update(style_font)
            cell_name_2.update(style_font_size)
            cell_name_2.update(style_border_right)
            format_cell_name_2 = workbook.add_format(cell_name_2)
    
            cell_jumlah = {}
            cell_jumlah.update(style_bold)
            cell_jumlah.update(style_alignment_left)
            cell_jumlah.update(style_font)
            cell_jumlah.update(style_font_size)
            cell_name_2.update(style_border_right)
            format_cell_jumlah = workbook.add_format(cell_jumlah)
    
            cell_text = {}
            cell_text.update(style_border_left)
            cell_text.update(style_border_right)
            cell_text.update(style_alignment_left)
            cell_text.update(style_font)
            cell_text.update(style_font_size)
            format_cell_text_normal = workbook.add_format(cell_text)
    
            cell_text = {}
            cell_text.update(style_border_left)
            cell_text.update(style_border_right)
            cell_text.update(style_border_bottom)
            cell_text.update(style_alignment_left)
            cell_text.update(style_font)
            cell_text.update(style_font_size)
            format_cell_text_bold = workbook.add_format(cell_text)
    
            cell_text = {}
            cell_text.update(style_border_left)
            cell_text.update(style_border_right)
            cell_text.update(style_alignment_left)
            cell_text.update(style_bold)
            cell_text.update(style_border_top)
            cell_text.update(style_border_bottom)
            cell_text.update(style_font)
            cell_text.update(style_font_size)
            format_cell_text_bold_highlight = workbook.add_format(cell_text)
    
            cell_number = {}
            cell_number.update(style_border_left)
            cell_number.update(style_border_right)
            cell_number.update(style_alignment_right)
            cell_number.update(style_currency_format)
            cell_number.update(style_font)
            cell_number.update(style_font_size)
            format_cell_number_normal = workbook.add_format(cell_number)
    
            cell_number.update(style_bold)
            cell_number.update(style_font)
            cell_number.update(style_font_size)
            format_cell_number_bold = workbook.add_format(cell_number)
    
            cell_number.update(style_border_top)
            cell_number.update(style_border_bottom)
            cell_number.update(style_font)
            cell_number.update(style_font_size)
            format_cell_number_bold_highlight = workbook.add_format(cell_number)
    
            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 1, 50)
            sheet.set_column(2, 12, 15)
            sheet.set_column(13, 15, 30)
    
            # code_iso = self.env['pam.code.iso'].search([('name','=','sak_etap')])
            # if code_iso:
            #     sheet.merge_range(0, 16, 3, 16,code_iso.code_iso, judul)
            # else:
            #     sheet.merge_range(0, 16, 3, 16,' ', judul)
    
            sheet.merge_range(0, 0, 0, 15, 'PDAM TIRTA PAKUAN KOTA BOGOR', center)
            sheet.merge_range(1, 0, 1, 15, 'Rencana Pendapatan Usaha dan Diluar Usaha', center)
            sheet.merge_range(2, 0, 2, 15, 'PERIODE : ' + (datetime.strptime(record.months, '%m').strftime("%B")) + ' ' + record.years, center)
    
            sheet.merge_range(4, 0, 5, 0,'Kode Perkiraan', border)
            sheet.merge_range(4, 1, 5, 1,'Perkiraan', border)
            sheet.merge_range(4, 2, 4, 12,'Bulan', border)
            sheet.merge_range(4, 13, 5, 13,'Jumlah Tahun 2019', border)
            sheet.merge_range(4, 14, 5, 14,'Jumlah Tahun 2018', border)
            sheet.merge_range(4, 15, 5, 15,'Selisih', border)
    
            sheet.write(5, 2, 'I', border)
            sheet.write(5, 3, 'II', border)
            sheet.write(5, 4, 'III', border)
            sheet.write(5, 5, 'IV', border)
            sheet.write(5, 6, 'V', border)
            sheet.write(5, 7, 'VI', border)
            sheet.write(5, 8, 'VII', border)
            sheet.write(5, 9, 'IX', border)
            sheet.write(5, 10, 'X', border)
            sheet.write(5, 11, 'XI', border)
            sheet.write(5, 12, 'XII', border)
    
            y = 6
            col = 0
    
            format_cells = [format_cell_text_normal, format_cell_number_normal]
            format_total_cells = [format_cell_text_bold_highlight, format_cell_number_bold_highlight]
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "PENDAPATAN USAHA", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31111", "PENJUALAN AIR", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31111110", "Harga Air")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31111120", "Abonemen")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "", "Jumlah Penjualan Air")
            
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31121", "PENDAPATAN NON AIR", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31121110", "Sambungan Baru")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31121120", "Jasa Bukaan Kembali")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31121130", "Denda Keterlambatan Bayar")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31121160", "Jasa Penertiban Meter")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "31121220", "Pendapatan Lain-lain", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "- BBN")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "- Pelanggaran")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "- Adm Retikulasi")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "", "Jumlah Pendapatan Non Air")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "", "Jumlah Pendapatan Usaha")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "51111111", "PENDAPATAN DILUAR USAHA", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "51111110", "Bunga Deposito")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "51111120", "Jasa Giro")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "51111170", "Rupa - rupa Pendapatan Lainnya")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "", "Jumlah Pendapatan Diluar Usaha")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "", "Jumlah Seluruh Pendapatan")
    
    
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah Pendapatan", "",total_income_this_year, totai_income_until_this_month)
    
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename