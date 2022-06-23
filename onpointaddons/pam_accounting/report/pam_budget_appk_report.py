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

class PamBudgetAppkReport(models.TransientModel):
    _name = 'pam.budget.appk.report'

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
        empty=False):

        html = html + "<tr class='" + class_name + "'>"

        html = html + "<td>" + name + "</td>"

        for month in range(16):
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
        html = html + "<th rowspan='2' width='700px'>Perkiraan</td>"
        html = html + "<th colspan='12'>Bulan</td>"
        html = html + "<th rowspan='2' width='300px'>Anggaran Tahun 2019</td>"
        html = html + "<th rowspan='2' width='300px'>Anggaran Tahun 2018</td>"
        html = html + "<th colspan='2'>Selisih</td>"
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
        html = html + "<th width='300px'>+/-</td>"
        html = html + "<th width='300px'>%</td>"
        html = html + "</tr>"


        html = self.create_html_row(html, "", "<b>PROYEKSI PENERIMAAN KAS</b>", True)
        html = self.create_html_row(html, "", "", True)
        html = self.create_html_row(html, "", "<b>Penerimaan Operasional:</b>", True)
        html = self.create_html_row(html, "", "a. Tagihan Rekening Air")
        html = self.create_html_row(html, "", "b. Tagihan Rekening Non Air")
        html = self.create_html_row(html, "", "c. Denda")
        html = self.create_html_row(html, "total-cell", "Jumlah Penerimaan Operasional")

        html = self.create_html_row(html, "", "", True)

        html = self.create_html_row(html, "", "<b>Penerimaan Non Operasional:</b>", True)
        html = self.create_html_row(html, "", "a. PPn Masukan")
        html = self.create_html_row(html, "", "b. Jasa Giro")
        html = self.create_html_row(html, "", "c. Bunga Deposito")
        html = self.create_html_row(html, "", "d. Retribusi Kebersihan")
        html = self.create_html_row(html, "", "e. Penyertaan Modal Pemda")
        html = self.create_html_row(html, "", "f. Rupa - rupa Non Operasional")
        html = self.create_html_row(html, "total-cell", "Jumlah Penerimaan Non Operasional")

        html = self.create_html_row(html, "", "", True)

        html = self.create_html_row(html, "total-cell", "JUMLAH PENERIMAAN KAS")

        html = self.create_html_row(html, "", "", True)

        html = self.create_html_row(html, "", "<b>PROYEKSI PENGELUARAN KAS</b>", True)
        html = self.create_html_row(html, "", "", True)
        html = self.create_html_row(html, "", "<b>Pengeluaran Operasional:</b>", True)
        html = self.create_html_row(html, "", "a. Biaya Tenaga Kerja")
        html = self.create_html_row(html, "", "b. Pembelian Bahan/Persediaan")
        html = self.create_html_row(html, "", "c. Pengeluaran Biaya Usaha")
        html = self.create_html_row(html, "total-cell", "Jumlah Pengeluaran Operasional")

        html = self.create_html_row(html, "", "", True)

        html = self.create_html_row(html, "", "<b>Pengeluaran Investasi:</b>", True)
        html = self.create_html_row(html, "", "a. Investasi")
        html = self.create_html_row(html, "", "b. Investasi Dana Pemda")
        html = self.create_html_row(html, "total-cell", "Jumlah Pengeluaran Investasi")

        html = self.create_html_row(html, "", "", True)

        html = self.create_html_row(html, "", "<b>Pengeluaran Pembiayaan:</b>", True)
        html = self.create_html_row(html, "", "a. Pembayaran Pemasangan Baru")
        html = self.create_html_row(html, "", "b. Kewajiban Hutang Jangka Panjang", True)
        html = self.create_html_row(html, "", "    -  Angsuran Pokok Pinjaman ADB")
        html = self.create_html_row(html, "", "    -  Angsuran Pokok Pinjaman World Bank")
        html = self.create_html_row(html, "", "    -  Angsuran Bunga  Pinjaman World Bank")
        html = self.create_html_row(html, "", "    -  Angsuran Bunga Pinjaman ADB")
        html = self.create_html_row(html, "", "    -  Angsuran Bunga Transmisi air baku")
        html = self.create_html_row(html, "", "    -  Jasa Bank ADB")
        html = self.create_html_row(html, "total-cell", "Jumlah Pengeluaran Pembiayaan")

        html = self.create_html_row(html, "", "", True)

        html = self.create_html_row(html, "", "<b>Pengeluaran Non Operasional:</b>", True)
        html = self.create_html_row(html, "", "a. Pembayaran Berbagai Pajak")
        html = self.create_html_row(html, "", "b. Zakat Perusahaan")
        html = self.create_html_row(html, "", "c. Retribusi Kebersihan")
        html = self.create_html_row(html, "", "d. Setoran Bagian Laba PEMDA")
        html = self.create_html_row(html, "", "e. Sumbangan")
        html = self.create_html_row(html, "", "f. Premi Asuransi")
        html = self.create_html_row(html, "", "g. Lain-Lain  Non Operasional", True)
        html = self.create_html_row(html, "", "    - Pendidikan dan Pelatihan")
        html = self.create_html_row(html, "", "    - Bantuan Kesejahteraan")
        html = self.create_html_row(html, "", "    - Pensiun dan Sokongan")
        html = self.create_html_row(html, "", "h. Rupa2 Pengeluaran Non Op.")
        html = self.create_html_row(html, "total-cell", "Jumlah Pengeluaran Non Operasional")

        html = self.create_html_row(html, "", "", True)

        html = self.create_html_row(html, "total-cell", "Jumlah Pengeluaran Kas")

        html = self.create_html_row(html, "", "", True)

        html = self.create_html_row(html, "total-cell", "KENAIKAN [ PENURUNAN ]  KAS")
        html = self.create_html_row(html, "total-cell", "SALDO AWAL KAS")
        html = self.create_html_row(html, "total-cell", "SALDO AKHIR KAS")

        html = html + "</table>"
        html = html + "</div>"

        report = self.env['pam.budget.appk.report'].search([('id', '=', self.id)])
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
        name,
        empty=False):

        sheet.write(y, col, name, format_cells[0])
        col += 1

        for month in range(15):
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
            filename = '%s.xlsx' % ('Anggaran Penerimaan dan Pengeluaran Kas (APPK)',)
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Anggaran Penerimaan Dan Pengeluaran Kas (APPK)',
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
    
            sheet.set_column(0, 0, 50)
            sheet.set_column(1, 15, 15)
    
            # code_iso = self.env['pam.code.iso'].search([('name','=','sak_etap')])
            # if code_iso:
            #     sheet.merge_range(0, 16, 3, 16,code_iso.code_iso, judul)
            # else:
            #     sheet.merge_range(0, 16, 3, 16,' ', judul)
    
            sheet.merge_range(0, 0, 0, 15, 'PDAM TIRTA PAKUAN KOTA BOGOR', center)
            sheet.merge_range(1, 0, 1, 15, 'Anggaran Penerimaan dan Pengeluaran Kas (APPK)', center)
            sheet.merge_range(2, 0, 2, 15, 'PERIODE : ' + record.years, center)
    
            sheet.merge_range(4, 0, 5, 0, 'Perkiraan', border)
            sheet.merge_range(4, 1, 4, 11, 'Bulan', border)
            sheet.merge_range(4, 12, 5, 12,'Anggaran Tahun 2019', border)
            sheet.merge_range(4, 13, 5, 13,'Anggaran Tahun 2018', border)
            sheet.merge_range(4, 14, 4, 15, 'Selisih', border)
    
            sheet.write(5, 1, 'I', border)
            sheet.write(5, 2, 'II', border)
            sheet.write(5, 3, 'III', border)
            sheet.write(5, 4, 'IV', border)
            sheet.write(5, 5, 'V', border)
            sheet.write(5, 6, 'VI', border)
            sheet.write(5, 7, 'VII', border)
            sheet.write(5, 8, 'IX', border)
            sheet.write(5, 9, 'X', border)
            sheet.write(5, 10, 'XI', border)
            sheet.write(5, 11, 'XII', border)
            sheet.write(5, 14, '+/-', border)
            sheet.write(5, 15, '%', border)
    
            y = 6
            col = 0
    
            format_cells = [format_cell_text_normal, format_cell_number_normal]
            format_total_cells = [format_cell_text_bold_highlight, format_cell_number_bold_highlight]
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "PROYEKSI PENERIMAAN KAS", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Penerimaan Operasional:", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "a. Tagihan Rekening Air")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "b. Tagihan Rekening Non Air")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "c. Denda")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "Jumlah Penerimaan Operasional")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Penerimaan Non Operasional:", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "a. PPn Masukan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "b. Jasa Giro")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "c. Bunga Deposito")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "d. Retribusi Kebersihan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "e. Penyertaan Modal Pemda")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "f. Rupa - rupa Non Operasional")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "Jumlah Penerimaan Non Operasional")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "JUMLAH PENERIMAAN KAS")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "PROYEKSI PENGELUARAN KAS", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pengeluaran Operasional:", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "a. Biaya Tenaga Kerja")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "b. Pembelian Bahan/Persediaan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "c. Pengeluaran Biaya Usaha")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "Jumlah Pengeluaran Operasional")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pengeluaran Investasi:", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "a. Investasi")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "b. Investasi Dana Pemda")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "Jumlah Pengeluaran Investasi")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pengeluaran Pembiayaan:", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "a. Pembayaran Pemasangan Baru")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "b. Kewajiban Hutang Jangka Panjang", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    -  Angsuran Pokok Pinjaman ADB")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    -  Angsuran Pokok Pinjaman World Bank")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    -  Angsuran Bunga  Pinjaman World Bank")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    -  Angsuran Bunga Pinjaman ADB")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    -  Angsuran Bunga Transmisi air baku")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    -  Jasa Bank ADB")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "Jumlah Pengeluaran Pembiayaan")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pengeluaran Non Operasional:", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "a. Pembayaran Berbagai Pajak")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "b. Zakat Perusahaan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "c. Retribusi Kebersihan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "d. Setoran Bagian Laba PEMDA")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "e. Sumbangan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "f. Premi Asuransi")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "g. Lain-Lain  Non Operasional", True)
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    - Pendidikan dan Pelatihan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    - Bantuan Kesejahteraan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "    - Pensiun dan Sokongan")
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "h. Rupa2 Pengeluaran Non Op.")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "Jumlah Pengeluaran Non Operasional")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "Jumlah Pengeluaran Kas")
    
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", True)
    
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "KENAIKAN [ PENURUNAN ]  KAS")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "SALDO AWAL KAS")
            sheet, y = record.create_excel_row(sheet, y, col, format_total_cells, "SALDO AKHIR KAS")
    
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename