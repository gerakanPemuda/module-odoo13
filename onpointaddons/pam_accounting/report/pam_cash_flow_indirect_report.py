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

class PamCashFlowInidirectReport(models.TransientModel):
    _name = 'pam.cash.flow.indirect.report'
    # _inherit = ['pam.profit.loss', 'pam.cost.breakdown']

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
    until_months = fields.Selection([
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
    until_start_date = fields.Date(compute='set_period_date')
    until_end_date = fields.Date(compute='set_period_date')

    last_posted_period = fields.Integer(compute='set_last_posted_period')
    range_start_date = fields.Date(compute='set_last_posted_period')
    range_end_date = fields.Date(compute='set_last_posted_period')

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    report_html = fields.Html(string="Arus Kas (Tidak Langsung)")
    tf = fields.Boolean()

    def set_period(self):
        self.period = self.years + self.months

    def set_period_date(self):
        self.start_date = self.years + '-' + self.months + '-01'
        self.end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        self.until_start_date = self.years + '-' + self.until_months + '-01'
        self.until_end_date = (datetime.strptime(self.years + '-' + self.until_months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

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
        value_until_this_month=0):

        html = html + "<tr class='" + class_name + "'>"

        html = html + "<td>" + name + "</td>"

        html = html + "<td></td>"

        if value_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_this_year) + "</td>"
        else:
            html = html + "<td></td>"

        if value_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_until_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        html = html + "</tr>"

        return html

    def get_data(self):

        # starting div
        html = "<table class='report-table'>"

        html = html + "<tr>"
        html = html + "<th width='500px'></td>"
        html = html + "<th width='100px'>Catatan</td>"
        html = html + "<th width='500px'>" + self.years + "</td>"
        # html = html + "<th width='500px'>" + dict(self._fields['years'].selection).get(self.years) + "</td>"
        html = html + "<th width='500px'>" + str(int(self.years) - 1) + "</td>"
        # html = html + "<th width='500px'>" + dict(self._fields['years'].selection).get(self.years) + "</td>"
        html = html + "</tr>"

        # before_month_start_date = str(int(self.years) - 1) + '-' + self.months + '-01'
        # before_month_end_date = (datetime.strptime(str(int(self.years) - 1) + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        # current_month_start_date = self.years + '-' + self.months+ '-01'
        # current_month_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        # if self.months == '01':
        #     last_month = '12'
        #     last_month_year = str(int(self.years) - 1)
        # else:
        #     last_month = str(int(self.months) - 1)
        #     last_month_year = self.years

        # last_month_start_date = last_month_year + '-' + last_month + '-01'
        # last_month_end_date = (datetime.strptime(last_month_start_date, "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")


        # before_year_start_date = str(int(self.years) - 1) + '-01-01'
        # before_year_end_date = (datetime.strptime(self.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
        # current_year_start_date = self.years + '-01-01'
        # current_year_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        html = self.create_html_row(html, "", "<b>Arus Kas dari Aktivitas Operasi</b>", "", "")

        html = self.create_html_row(html, "", "<b>&nbsp;&nbsp;Laba Sebelum Pajak</b>", 0, 0)

        html = self.create_html_row(html, "", "<b>&nbsp;&nbsp;Penyesuaian untuk :</b>", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Penyisihan Hutang", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Penyusutan Aset Tetap", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Penyusutan Properti Investasi", 0, 0)
        html = self.create_html_row(html, "total-cell", "&nbsp;&nbsp;Laba operasi sebelum perubahan modal kerja", 0, 0)

        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Penurunan (Kenaikan) Piutang Usaha", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Penurunan (Kenaikan) Piutang Lain-Lain", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Penurunan (Kenaikan) Pendapatan Yang Akan Diterima", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Penurunan (Kenaikan) Persediaan", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Penurunan (Kenaikan) Biaya Dibayar Dimuka", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Kenaikan (Penurunan) utang usaha", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Kenaikan (Penurunan) utang lain-lain", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Kenaikan (Penurunan) Biaya Yang Masih Harus Dibayar", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Kenaikan (Penurunan) Pendapatan Diterima Dimuka", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Kenaikan (Penurunan) Utang Pajak", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Kenaikan (Penurunan) Bagian utang jangka panjang jatuh tempo", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Kenaikan (Penurunan) Titipan Retribusi", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;&nbsp;&nbsp;Kenaikan (Penurunan) Liabilitas Jangka Pendek Lainnya", 0, 0)
        html = self.create_html_row(html, "total-cell", "&nbsp;&nbsp;Kas dihasilkan dari operasi", 0, 0)

        html = self.create_html_row(html, "total-cell", "Kas Neto Dari Aktivitas Operasi", 0, 0)

        html = self.create_html_row(html, "", "<b>Arus Kas Dari Aktivitas Investasi</b>", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Penurunan (Kenaikan) Aset Tetap", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Penurunan (Kenaikan) Aset Tidak Berwujud", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Penurunan (Kenaikan) Deposito", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Penurunan (Kenaikan)Aset Tetap dalam Penyelesaian", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Penurunan (Kenaikan) Uang Jaminan", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Penurunan (Kenaikan) Sewa Dibayar Dimuka", 0, 0)
        html = self.create_html_row(html, "total-cell", "Kas Neto Dari Aktivitas Investasi", 0, 0)

        html = self.create_html_row(html, "", "<b>Arus Kas dari Aktivitas Pendanaan</b>", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Kenaikan (Penurunan) Liabilitas Jangka Panjang", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Kenaikan (Penurunan)Uang Jaminan Pelanggan", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Kenaikan (Penurunan) Liabilitas Imbalan Pasca Kerja", 0, 0)
        html = self.create_html_row(html, "", "&nbsp;&nbsp;Kenaikan (Penurunan) Modal Dikurangi Laba Tahun Berjalan", 0, 0)
        html = self.create_html_row(html, "total-cell", "Kas Neto Dari Aktivitas Pendanaan", 0, 0)

        html = self.create_html_row(html, "total-cell", "Kenaikan neto kas dan setara kas", 0, 0)
        html = self.create_html_row(html, "total-cell", "Kas dan setara kas pada awal periode", 0, 0)
        html = self.create_html_row(html, "total-cell", "Kas dan setara kas pada akhir periode", 0, 0)

        html = html + "</table>"

        report = self.env['pam.cash.flow.indirect.report'].search([('id', '=', self.id)])
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
        notes, 
        value_this_year=0, 
        value_until_this_month=0):

        sheet.write(y, col, name, format_cells[0])
        # col += 1
        sheet.write(y, 3, notes, format_cells[1])
        # col += 1
        sheet.write(y, 5, value_this_year, format_cells[2])
        # col += 1
        sheet.write(y, 7, value_until_this_month, format_cells[3])

        y = y + 1

        return sheet, y

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN LABA RUGI'
            filename = '%s.xlsx' % ('Laporan Arus Kas (Tidak Langsung)',)
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Laporan Arus Kas (Tidak Langsung)',
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
            header = workbook.add_format({'bold': True, 'align': 'center', 'bottom': 1})
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
            # cell_text.update(style_border_left)
            # cell_text.update(style_border_right)
            cell_text.update(style_alignment_left)
            cell_text.update(style_font)
            cell_text.update(style_font_size)
            format_cell_text_normal = workbook.add_format(cell_text)
    
            cell_text = {}
            # cell_text.update(style_border_left)
            # cell_text.update(style_border_right)
            # cell_text.update(style_border_bottom)
            cell_text.update(style_bold)
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
            # cell_number.update(style_border_left)
            # cell_number.update(style_border_right)
            cell_number.update(style_alignment_right)
            cell_number.update(style_currency_format)
            cell_number.update(style_font)
            cell_number.update(style_font_size)
            format_cell_number_normal = workbook.add_format(cell_number)
    
            cell_number.update(style_border_top)
            cell_number.update(style_border_bottom)
            cell_number.update(style_font)
            cell_number.update(style_font_size)
            format_cell_number_normal_highlight = workbook.add_format(cell_number)
    
            cell_number.update(style_bold)
            cell_number.update(style_font)
            cell_number.update(style_font_size)
            format_cell_number_bold = workbook.add_format(cell_number)
    
            cell_number.update(style_border_top)
            cell_number.update(style_border_bottom)
            cell_number.update(style_font)
            cell_number.update(style_font_size)
            format_cell_number_bold_highlight = workbook.add_format(cell_number)
    
    
            sheet.set_column(0, 1, 5)
            sheet.set_column(2, 2, 50)
            sheet.set_column(3, 3, 10)
            sheet.set_column(4, 4, 1)
            sheet.set_column(5, 5, 20)
            sheet.set_column(6, 6, 1)
            sheet.set_column(7, 7, 20)
    
            # code_iso = self.env['pam.code.iso'].search([('name','=','sak_etap')])
            # if code_iso:
            #     wrap_text = workbook.add_format()
            #     wrap_text.set_text_wrap()
            #     sheet.merge_range(0, 4, 3, 4,code_iso.code_iso, wrap_text)
            # else:
            #     sheet.merge_range(0, 4, 3, 4,' ', judul)
    
            sheet.merge_range(0, 0, 0, 7, 'PDAM TIRTA PAKUAN KOTA BOGOR', center)
            sheet.merge_range(1, 0, 1, 7, 'LAPORAN ARUS KAS (TIDAK LANGSUNG)', center)
            sheet.merge_range(2, 0, 2, 7, 'Untuk Tahun Yang Berakhir Tanggal ' + (datetime.strptime(record.end_date, '%Y-%m-%d').strftime("%d %B %Y")), center)
            sheet.merge_range(3, 0, 3, 7, '(Dinyatakan Dalam Rupiah)', center)
    
            sheet.write(6, 3, 'Catatan', header)
            sheet.write(6, 5, record.years, header)
            sheet.write(6, 7, str(int(record.years) - 1), header)
            
            y = 8
            
            format_cells = [format_cell_name, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Arus Kas dari Aktivitas Operasi", "","", "")
    
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Laba Sebelum Pajak", "", 0, 0)
            y += 1
    
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Penyesuaian untuk:", "", "","")
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Penyisihan Hutang", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Penyusutan Aset Tetap", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Penyusutan Properti Investasi", "", 0, 0)
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal_highlight, format_cell_number_normal_highlight]
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Laba operasi sebelum perubahan modal kerja", "", 0, 0)
            y += 1
    
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Penurunan (Kenaikan) Piutang Usaha", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Penurunan (Kenaikan) Piutang Lain-Lain", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Penurunan (Kenaikan) Pendapatan Yang Akan Diterima", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Penurunan (Kenaikan) Persediaan", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Penurunan (Kenaikan) Biaya Dibayar Dimuka", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Kenaikan (Penurunan) utang usaha", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Kenaikan (Penurunan) utang lain-lain", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Kenaikan (Penurunan) Biaya Yang Masih Harus Dibayar", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Kenaikan (Penurunan) Pendapatan Diterima Dimuka", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Kenaikan (Penurunan) Utang Pajak", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Kenaikan (Penurunan) Bagian utang jangka panjang jatuh tempo", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Kenaikan (Penurunan) Titipan Retribusi", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 2, format_cells, "Kenaikan (Penurunan) Liabilitas Jangka Pendek Lainnya", "", 0, 0)
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal_highlight, format_cell_number_normal_highlight]
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Kas dihasilkan dari operasi", "", 0, 0)
            y += 1
    
            format_cells = [format_cell_text_bold, format_cell_text_bold, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Kas Neto Dari Aktivitas Operasi", "", 0, 0)
            y += 1
    
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Arus Kas Dari Aktivitas Investasi", "", 0, 0)
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Penurunan (Kenaikan) Aset Tetap", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Penurunan (Kenaikan) Aset Tidak Berwujud", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Penurunan (Kenaikan) Deposito", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Penurunan (Kenaikan)Aset Tetap dalam Penyelesaian", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Penurunan (Kenaikan) Uang Jaminan", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Penurunan (Kenaikan) Sewa Dibayar Dimuka", "", 0, 0)
            format_cells = [format_cell_text_bold, format_cell_text_bold, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Kas Neto Dari Aktivitas Investasi", "", 0, 0)
            y += 1
    
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Arus Kas dari Aktivitas Pendanaan", "", 0, 0)
            format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Kenaikan (Penurunan) Liabilitas Jangka Panjang", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Kenaikan (Penurunan)Uang Jaminan Pelanggan", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Kenaikan (Penurunan) Liabilitas Imbalan Pasca Kerja", "", 0, 0)
            sheet, y = record.create_excel_row(sheet, y, 1, format_cells, "Kenaikan (Penurunan) Modal Dikurangi Laba Tahun Berjalan", "", 0, 0)
            format_cells = [format_cell_text_bold, format_cell_text_bold, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Kas Neto Dari Aktivitas Pendanaan", "", 0, 0)
            y += 1
    
            format_cells = [format_cell_text_bold, format_cell_text_bold, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Kenaikan neto kas dan setara kas", "", 0, 0)
            format_cells = [format_cell_text_bold, format_cell_text_bold, format_cell_number_normal, format_cell_number_normal]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Kas dan setara kas pada awal periode", "", 0, 0)
            
            format_cells = [format_cell_text_bold, format_cell_text_bold, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, 0, format_cells, "Kas dan setara kas pada akhir periode", "", 0, 0)
            
            # html = record.create_html_row(html, "total-cell", "", 0, 0)
            # html = record.create_html_row(html, "total-cell", "", 0, 0)
            # html = record.create_html_row(html, "total-cell", "", 0, 0)
    
    
            # before_month_start_date = str(int(record.years) - 1) + '-' + record.months + '-01'
            # before_month_end_date = (datetime.strptime(str(int(record.years) - 1) + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
            # current_month_start_date = record.years + '-' + record.months+ '-01'
            # current_month_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
            # if record.months == '01':
            #     last_month = '12'
            #     last_month_year = str(int(record.years) - 1)
            # else:
            #     last_month = str(int(record.months) - 1)
            #     last_month_year = record.years
    
            # last_month_start_date = last_month_year + '-' + last_month + '-01'
            # last_month_end_date = (datetime.strptime(last_month_start_date, "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
    
    
            # before_year_start_date = str(int(record.years) - 1) + '-01-01'
            # before_year_end_date = (datetime.strptime(record.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
            # current_year_start_date = record.years + '-01-01'
            # current_year_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
            # report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
            # report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id)])
    
            # y = 6
            # col = 0
    
            # format_cells = [format_cell_name, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "PENDAPATAN", "","", "")
    
            # col += 1
            # y -= 1
            # total_income_this_year = 0
            # totai_income_until_this_month = 0
    
            # value_this_year = record.calculate_profit_loss(record.start_date, record.end_date, 'PU', 'Penjualan Air', 'credit')
            # value_until_this_month = record.calculate_profit_loss(current_year_start_date, record.until_end_date, 'PU', 'Penjualan Air', 'credit')
            # format_cells = [format_cell_name_2, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pendapatan Penjualan Air", "",value_this_year, value_until_this_month)
    
            # total_income_this_year += value_this_year
            # totai_income_until_this_month += value_until_this_month
    
            # value_this_year = record.calculate_profit_loss(record.start_date, record.end_date, 'PU', 'Penjualan Non Air', 'credit')
            # value_until_this_month = record.calculate_profit_loss(current_year_start_date, record.until_end_date, 'PU', 'Penjualan Non Air', 'credit')
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pendapatan Non Air", "",value_this_year, value_until_this_month)
    
            # total_income_this_year += value_this_year
            # totai_income_until_this_month += value_until_this_month
    
            # format_cells = [format_cell_jumlah, format_cell_text_normal, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah Pendapatan", "",total_income_this_year, totai_income_until_this_month)
    
            # col = 0
    
            # format_cells = [format_cell_name, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Usaha", "", "", "")
    
            # col += 1
            # y -= 1
            # total_cost_this_year = 0
            # totai_cost_until_this_month = 0
    
            # report_type_line_code = ('SA', 'PH', 'TD', 'PP', 'PT', 'AUK', 'HL')
            # report_configuration_name = ('Gaji & Honor', 'Gaji dan Honor')
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # format_cells = [format_cell_name_2, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Pegawai", "",value_this_year, value_until_this_month)
    
            # report_type_line_code = ('AUK',)
            # report_configuration_name = ('Gaji & Honor Direksi', 'Honor Badan Pegawas')
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Direksi dan Dewan Pengawas", "",value_this_year, value_until_this_month)
    
            # report_type_line_code = ('SA', 'PH')
            # report_configuration_name = ('Biaya Bahan Kimia', )
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pemakaian Bahan Kimia", "",value_this_year, value_until_this_month)
    
            # report_type_line_code = ('TD', )
            # report_configuration_name = ('Biaya Bhn Perlengkapan Lap.', 'Biaya Pemakaian Pipa Persil', 'Biaya Bukaan Tutupan')
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pemakaian Bahan/Perlengkapan & Pipa Persil", "",value_this_year, value_until_this_month)
    
            # report_type_line_code = ('SA', 'PH', 'TD', 'AUK')
            # report_configuration_name = ('Biaya Pemeliharaan', 'Biaya Pemeliharaan Inventaris', 'Biaya Pemeliharaan Kendaraan', 'Biaya Pemb.Bhn Bakar & Plms.', 'Biaya Pemeliharaan Bangunan', 'Biaya Pemeliharaan Instalasi', 'Biaya Pemel.Tmn & Lapangan')
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Pemeliharaan", "",value_this_year, value_until_this_month)
    
            # report_type_line_code = ('AUK', )
            # report_configuration_name = ('Biaya Alat Tulis Kantor', 'Biaya Foto Copy & Cetakan', 'Biaya Perlengkapan Komputer', 'Biaya Telepon', 'Biaya Jastel Sirkit Lang./LC', 'Biaya Jamuan Tamu', 'Biaya Meterai Pos', 'Biaya Air', 'Biaya Cleaning Service', 'Biaya Jasa Peng. & Sekre.', 'Biaya Jasa Penagihan Bank', 'Biaya Rupa - Rupa Kantor')
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Kantor", "", value_this_year, value_until_this_month)
    
            # report_type_line_code = ('AUK', )
            # report_configuration_name = ('Biaya Keuangan',)
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Keuangan", "", value_this_year, value_until_this_month)
    
            # report_type_line_code = ('SA', )
            # report_configuration_name = ('Biaya Pajak Pemanfaatan Air',)
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Pajak Pemanfaatan Air", "", value_this_year, value_until_this_month)
    
            # report_type_line_code = ('AUK', )
            # report_configuration_name = ('Biaya Penyisihan Piutang',)
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Penyisihan Piutang", "", value_this_year, value_until_this_month)
    
            # report_type_line_code = ('SA', 'PH', 'TD', 'PP', 'AUK')
            # report_configuration_name = ('Biaya Penyusutan',)
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Penyusutan dan Amortisasi", "", value_this_year, value_until_this_month)
    
            # report_type_line_code = ('HL', )
            # report_configuration_name = ('Rupa - Rupa Operasi', 'Discount PB')
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Rupa-rupa Beban Hubungan Pelanggan", "", value_this_year, value_until_this_month)
    
            # report_type_line_code = ('PT', )
            # report_configuration_name = ('Biaya Rupa - Rupa Operasi', )
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Rupa-rupa Beban Perencanaan", "", value_this_year, value_until_this_month)
    
            # report_type_line_code = ('AUK', )
            # report_configuration_name = ('Biaya Iuran Berlangganan', 'Biaya Iuran Benchmarking', 'Rupa - rupa  Honor BP', 'Biaya Perjalanan Dinas', 'Biaya Profesional', 'Biaya Sewa', 'Biaya Asuransi Kendaraan', 'Biaya Asuransi Pegawai', 'Biaya Asuransi Bangunan', 'Biaya PBB', 'Biaya Ret. Pemakaian Air Tanah', 'Kesejahteraan Kary. O R', 'Kesejahteraan Kar.Seni', 'Kesejahteraan Kary.Lain2', 'Biaya Pos Pimpinan', 'Biaya Umum Lainnya', 'Biaya Pendidikan,Pelatihan,Diklat', 'Biaya Katinueng/Pensiun Kary/ti', 'Biaya sosial & kesejahteraan', 'Biaya Sumbangan', 'Biaya Zakat Perusahaan', 'Beban PPh Final Psl 4 ayat 2', 'Biaya Keuangan', 'Biaya rapat & Koordinasi', 'Honor Tim PDAM', 'Imbalan paska kerja')
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Rupa-rupa Beban Umum", "", value_this_year, value_until_this_month)
    
            # report_type_line_code = ('SA', 'PH', 'TD')
            # report_configuration_name = ('Biaya Operasi Lainnya',)
            # value_this_year = record.calculate_cost_breakdown_multiple(record.start_date, record.end_date, report_type_line_code, report_configuration_name)
            # value_until_this_month = record.calculate_cost_breakdown_multiple(record.start_date, record.until_end_date, report_type_line_code, report_configuration_name)
            # total_cost_this_year += value_this_year
            # totai_cost_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Operasional Lainnya", "", value_this_year, value_until_this_month)
    
            # format_cells = [format_cell_jumlah, format_cell_text_normal, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah Beban Usaha", "", total_cost_this_year, totai_cost_until_this_month)
            # format_cells = [format_cell_jumlah, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
    
            # col = 0
            # total_profit_loss_this_year = total_income_this_year - total_cost_this_year
            # total_profit_loss_until_this_month = totai_income_until_this_month - totai_cost_until_this_month
    
            # format_cells = [format_cell_name, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "LABA / RUGI USAHA", "", "", "")
            # y -= 1
            # col += 1
            # format_cells = [format_cell_name_2, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", total_profit_loss_this_year, total_profit_loss_until_this_month)
            # col = 0
            # format_cells = [format_cell_name, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
            # y -= 1
            # col += 1
            # format_cells = [format_cell_name_2, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
    
            # col = 0
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "PENDAPATAN (BEBAN) LAIN-LAIN", "", "", "")
    
            # col += 1
            # y -= 1
            # total_other_income_this_year = 0
            # total_other_income_until_this_month = 0
    
            # value_this_year = record.calculate_profit_loss(record.start_date, record.end_date, 'PLL', 'Pendapatan lain - lain', 'credit')
            # value_until_this_month = record.calculate_profit_loss(current_year_start_date, record.until_end_date, 'PLL', 'Pendapatan lain - lain', 'credit')
            # total_other_income_this_year += value_this_year
            # total_other_income_until_this_month += value_until_this_month
            # format_cells = [format_cell_name_2, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Pendapatan Lain-lain", "", value_this_year, value_until_this_month)
    
            # value_this_year = record.calculate_profit_loss(record.start_date, record.end_date, 'PLL', 'Biaya lain lain', 'credit')
            # value_until_this_month = record.calculate_profit_loss(current_year_start_date, record.until_end_date, 'PLL', 'Biaya lain lain', 'credit')
            # total_other_income_this_year += value_this_year
            # total_other_income_until_this_month += value_until_this_month
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Beban Lain-lain", "", value_this_year, value_until_this_month)
    
            # format_cells = [format_cell_jumlah, format_cell_text_normal, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "JUMLAH PENDAPATAN/BEBAN LAIN-LAIN", "", total_other_income_this_year, total_other_income_until_this_month)
            # format_cells = [format_cell_jumlah, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
    
            # col = 0
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "LABA/RUGI USAHA SEBELUM KERUGIAN LUAR BIASA", "", "", "")
            # y -= 1
            # col += 1
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", (total_profit_loss_this_year + total_other_income_this_year), (total_profit_loss_until_this_month + total_other_income_until_this_month))
            
            # col = 0
            # format_cells = [format_cell_name, format_cell_text_normal, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "KERUGIAN/KEUNTUNGAN LUAR BIASA", "", "", "")
            # col += 1
            # y -= 1
            # format_cells = [format_cell_name_2, format_cell_text_normal, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
    
            # format_cells = [format_cell_last, format_cell_text_normal, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            # col = 0
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "LABA/RUGI SEBELUM PAJAK PENGHASILAN", "", "", "")
            # y -= 1
            # col += 1
            # format_cells = [format_cell_last, format_cell_text_bold, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            # sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", (total_profit_loss_this_year + total_other_income_this_year), (total_profit_loss_until_this_month + total_other_income_until_this_month))
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename

    def export_report_pdf(self):
        for record in sel:
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Laporan Arus Kas (Tidak Langsung)',
                'report_format': 'Laporan PDF'
                })
    
            data = {
                'ids': record.ids,
                'model': record._name,
                'form': {
                    'end_date': record.end_date,
                    # 'years': record.years,
                    'datetime_cetak': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                    'html': record.report_html
                },
            }
    
            return self.env.ref('pam_accounting.action_pam_cash_flow_indirect_report').report_action(record, data=data)


class PamCashFlowIndirectReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_cash_flow_indirect_template'
    _template = 'pam_accounting.report_cash_flow_indirect_template'

    @api.model
    def get_report_values(self, docids, data=None):
        end_date = data['form']['end_date']
        # years = data['form']['years']
        datetime_cetak = data['form']['datetime_cetak']
        html = data['form']['html']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'end_date': end_date,
            # 'years': years,
            'datetime_cetak': datetime_cetak,
            'html': html
        }
