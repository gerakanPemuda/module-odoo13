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


class PamBalanceSheetReport(models.TransientModel):
    _name = 'pam.balance.sheet.report'
    _inherit = ['pam.balance.sheet', 'pam.profit.loss']

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

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    report_html = fields.Html(string="Neraca")
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

    def create_html_row(self, html, class_name, name, value_this_year=0, value_last_year=0, value_diff=0):

        html = html + "<tr class='" + class_name + "'>"

        html = html + "<td>" + name + "</td>"
        if value_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_this_year) + "</td>"
        else:
            html = html + "<td></td>"

        if value_last_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_last_year) + "</td>"
        else:
            html = html + "<td></td>"

        if value_diff != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff) + "</td>"
        else:
            html = html + "<td></td>"

        html = html + "</tr>"

        return html

    def get_data(self):


        # starting div
        html = "<div class='col-md-12'>"
        
        # starting div for aktiva
        html = html + "<div class='col-md-6'>"

        html = html + "<b>Aktiva</b>"

        html = html + "<table width='100%' class='report-table'>"
        html = html + "<tr>"
        html = html + "<th width='40%' rowspan='2'>URAIAN</td>"
        html = html + "<th width='20%'>TAHUN INI</td>"
        html = html + "<th width='20%'>TAHUN LALU</td>"
        html = html + "<th width='20%'>LEBIH KURANG</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th>(Rp.)</td>"
        html = html + "<th>(Rp.)</td>"
        html = html + "<th>(Rp.)</td>"
        html = html + "</tr>"


        report_type = self.env['pam.report.type'].search([('code', '=', 'NRC')])
        report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', 'in', ('AL','AT', 'ALL', 'PI'))], order='sequence asc')


        grand_total_assets_this_year = 0
        grand_total_assets_last_year = 0
        grand_total_assets_diff = 0

        for report_type_line in report_type_lines:
            report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
            report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')

            _logger.debug("Report Type Line %s", report_type_line.name)


            if report_type_line.is_show == True:
                html = self.create_html_row(html, "", "<b>" + report_type_line.name + "</b>", "", "", "")

            total_ar_this_year = 0
            total_ar_last_year = 0
            total_ar_diff = 0

            total_this_year = 0
            total_last_year = 0
            total_diff = 0
            for report_configuration_line in report_configuration_lines:
                if report_type_line.is_show == True:

                    debit, credit = self.calculate_balance_sheet(self.start_date, self.end_date, report_type_line.code, report_configuration_line.name)
                    ending_balance = self.get_last_balance(report_type_line.code, report_configuration_line.name)

                    # if report_configuration_line.sequence == 6:
                    #     _logger.debug("Debit Piutang Lain - lain : %s", debit)
                    #     _logger.debug("Kredit Piutang Lain - lain : %s", credit)
                    #     _logger.debug("Ending Balance Piutang Lain - lain : %s", ending_balance)

                    value_this_year = (ending_balance + debit) - credit

                    value_last_year = 0
                    value_diff = value_this_year - value_last_year

                    html = self.create_html_row(html, "", report_configuration_line.name, value_this_year, value_last_year, value_diff)

                    if report_configuration_line.sequence in (3,4,5):
                        total_ar_this_year = total_ar_this_year + value_this_year
                        total_ar_last_year = total_ar_last_year + value_last_year
                        total_ar_diff = total_ar_diff + value_diff
                    
                    if report_configuration_line.sequence == 5:
                        html = self.create_html_row(html, "total-cell", "<b>Nilai Buku Piutang Usaha</b>", total_ar_this_year, total_ar_last_year, total_ar_diff)

                    total_this_year = total_this_year + value_this_year
                    total_last_year = total_last_year + value_last_year
                    total_diff = total_diff + value_diff

            html = self.create_html_row(html, "total-cell", "Jumlah " + report_type_line.name, total_this_year, total_last_year, total_diff)

            grand_total_assets_this_year = grand_total_assets_this_year + total_this_year
            grand_total_assets_last_year = grand_total_assets_last_year + total_last_year
            grand_total_assets_diff = grand_total_assets_diff + total_diff


        html = self.create_html_row(html, "total-cell", "JUMLAH AKTIVA", grand_total_assets_this_year, grand_total_assets_last_year, grand_total_assets_diff)

        html = html + "</table>"
        
        # ending div for aktiva
        html = html + "</div>"



        # starting div for pasiva
        html = html + "<div class='col-md-6'>"

        html = html + "<b>Pasiva</b>"

        html = html + "<table width='100%' class='report-table'>"
        html = html + "<tr>"
        html = html + "<th width='40%' rowspan='2'>URAIAN</td>"
        html = html + "<th width='20%'>TAHUN INI</td>"
        html = html + "<th width='20%'>TAHUN LALU</td>"
        html = html + "<th width='20%'>LEBIH KURANG</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th>(Rp.)</td>"
        html = html + "<th>(Rp.)</td>"
        html = html + "<th>(Rp.)</td>"
        html = html + "</tr>"


        report_type = self.env['pam.report.type'].search([('code', '=', 'NRC')])
        report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', 'in', ('KL','KLL', 'ES', 'HJP'))], order='sequence asc')


        grand_total_liabilities_this_year = 0
        grand_total_liabilities_last_year = 0
        grand_total_liabilities_diff = 0

        for report_type_line in report_type_lines:
            report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
            report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')

            if report_type_line.is_show == True:
                html = self.create_html_row(html, "", "<b>" + report_type_line.name + "</b>", "", "", "")

            total_equity_this_year = 0
            total_equity_last_year = 0
            total_equity_diff = 0

            total_this_year = 0
            total_last_year = 0
            total_diff = 0
            current_year_start_date = self.years + '-01-01'

            for report_configuration_line in report_configuration_lines:
                if report_type_line.is_show == True:

                    if report_configuration_line.sequence == 36:
                        value_this_year = self.calculate_profit_loss_last_year(current_year_start_date, self.end_date)
                        value_last_year = 0
                    elif report_configuration_line.sequence == 38:
                        before_month_start_date = str(int(self.years) - 1) + '-' + self.months + '-01'
                        before_month_end_date = (datetime.strptime(str(int(self.years) - 1) + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

                        value_this_year = self.calculate_profit_loss_after_tax(current_year_start_date, self.end_date)
                        value_last_year = self.calculate_profit_loss_after_tax(before_month_start_date, before_month_end_date)
                    else:
                        debit, credit = self.calculate_balance_sheet(self.start_date, self.end_date, report_type_line.code, report_configuration_line.name)
                        ending_balance = self.get_last_balance(report_type_line.code, report_configuration_line.name)
                        value_this_year = (ending_balance + credit) - debit

                        value_last_year = 0
                        
                    value_diff = value_this_year - value_last_year

                    html = self.create_html_row(html, "", report_configuration_line.name, value_this_year, value_last_year, value_diff)

                    if report_configuration_line.sequence in (32,33):
                        total_equity_this_year = total_equity_this_year + value_this_year
                        total_equity_last_year = total_equity_last_year + value_last_year
                        total_equity_diff = total_equity_diff + value_diff
                    
                    if report_configuration_line.sequence == 33:
                        html = self.create_html_row(html, "total-cell", "<b>Jumlah Modal</b>", total_equity_this_year, total_equity_last_year, total_equity_diff)





                    total_this_year = total_this_year + value_this_year
                    total_last_year = total_last_year + value_last_year
                    total_diff = total_diff + value_diff

            html = self.create_html_row(html, "total-cell", "Jumlah " + report_type_line.name, total_this_year, total_last_year, total_diff)

            grand_total_liabilities_this_year = grand_total_liabilities_this_year + total_this_year
            grand_total_liabilities_last_year = grand_total_liabilities_last_year + total_last_year
            grand_total_liabilities_diff = grand_total_liabilities_diff + total_diff

        html = self.create_html_row(html, "total-cell", "JUMLAH PASSIVA", grand_total_liabilities_this_year, grand_total_liabilities_last_year, grand_total_liabilities_diff)

        html = html + "</table>"
        
        # ending div for pasiva
        html = html + "</div>"


        # ending div
        html = html + "</div>"

        report = self.env['pam.balance.sheet.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True,
        })

    def create_excel_row(self, sheet, y, col, format_cells, name, value_this_year=0, value_last_year=0, value_diff=0):

        sheet.write(y, col, name, format_cells[0])
        col += 1
        sheet.write(y, col, value_this_year, format_cells[1])
        col += 1
        sheet.write(y, col, value_last_year, format_cells[2])
        col += 1
        sheet.write(y, col, value_diff, format_cells[3])

        y = y + 1

        return sheet, y

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN NERACA'
            filename = '%s.xlsx' % ('LAPORAN NERACA', )
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 11, 'font': 'Tahoma'})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            judul = workbook.add_format({'align': 'center', 'bold': True, 'font': 'Tahoma', 'font_size': 16})
            jalan = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
            bold = workbook.add_format({'bold': True, 'left': 1, 'right': 1, 'font': 'Tahoma', 'font_size': 12})
            merge = workbook.add_format({'bold': True, 'border': True, 'font': 'Tahoma', 'font_size': 14})
            border = workbook.add_format({'bold': True, 'align': 'center', 'border': True, 'font': 'Tahoma', 'font_size': 14, 'bg_color': '#ffffb3'})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'center'})
            top = workbook.add_format({'top': 1})
            bottom = workbook.add_format({'bottom': 1})
            right = workbook.add_format({'right': 1})
            left = workbook.add_format({'left': 1})
            center = workbook.add_format({'align': 'center', 'top': 1})
            center_bottom = workbook.add_format({'align': 'center', 'bottom': 1})
            jumlah = workbook.add_format({'right': 1,'left': 1, 'num_format': '#,##0.00'})
            str_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'right': 1})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            str_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            style_bold = {'bold': True}
            style_font = {'font': 'Tahoma'}
            style_size = {'font_size': 11}
            style_size_jumlah = {'font_size': 10}
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
            cell_text.update(style_size_jumlah)
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
            cell_number.update(style_size_jumlah)
            format_cell_number_bold_highlight = workbook.add_format(cell_number)
    
    
            sheet.set_column(0, 0, 30)
            sheet.set_column(1, 7, 15)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','neraca')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(2, 7, 4, 7, code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(2, 7, 4, 7,' ', judul)
    
            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))
    
            sheet.insert_image(1, 0, 'logo.jpg', {'image_data' : logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})
    
            sheet.merge_range(2, 0, 2, 6, 'PERUSAHAAN DAERAH AIR MINUM TIRTA PAKUAN KOTA BOGOR', judul)
            sheet.merge_range(3, 0, 3, 6, 'N E R A C A   K O M P A R A T I F', judul)
            sheet.merge_range(4, 0, 4, 6, 'BULAN : ' + (datetime.strptime(record.months, '%m').strftime("%B")) + ' ' + record.years, judul)
            
            sheet.write(5, 7, (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'), title)
    
            sheet.merge_range(6, 0, 6, 3, 'AKTIVA', merge)
            sheet.merge_range(6, 4, 6, 7, 'PASIVA', merge)
            
            sheet.merge_range(7, 0, 8, 0, 'URAIAN', border)
            sheet.write(7, 1, 'TAHUN INI', border)
            sheet.write(7, 2, 'TAHUN LALU', border)
            sheet.write(7, 3, 'LEBIH KURANG', border)
            sheet.merge_range(7, 4, 8, 4, 'URAIAN', border)
            sheet.write(7, 5, 'TAHUN INI', border)
            sheet.write(7, 6, 'TAHUN LALU', border)
            sheet.write(7, 7, 'LEBIH KURANG', border)
    
            sheet.write(8, 1, '(Rp.)', border)
            sheet.write(8, 2, '(Rp.)', border)
            sheet.write(8, 3, '(Rp.)', border)
            sheet.write(8, 5, '(Rp.)', border)
            sheet.write(8, 6, '(Rp.)', border)
            sheet.write(8, 7, '(Rp.)', border)
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'NRC')])
            report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', 'in', ('AL','AT', 'ALL', 'PI'))], order='sequence asc')
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan Excel'
                })
    
            grand_total_assets_this_year = 0
            grand_total_assets_last_year = 0
            grand_total_assets_diff = 0
    
            y = 9
            col = 0
            for report_type_line in report_type_lines:
                report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
                report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')
    
                _logger.debug("Report Type Line %s", report_type_line.name)
    
                if report_type_line.is_show == True:
                    format_cells = [bold, right, right, right]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, report_type_line.name, "", "", "")
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
    
                total_ar_this_year = 0
                total_ar_last_year = 0
                total_ar_diff = 0
    
                total_this_year = 0
                total_last_year = 0
                total_diff = 0
                for report_configuration_line in report_configuration_lines:
                    if report_type_line.is_show == True:
    
                        debit, credit = record.calculate_balance_sheet(record.start_date, record.end_date, report_type_line.code, report_configuration_line.name)
                        ending_balance = record.get_last_balance(report_type_line.code, report_configuration_line.name)
                        value_this_year = (ending_balance + debit) - credit
    
                        value_last_year = 0
                        value_diff = value_this_year - value_last_year
    
    
                        format_cells = [format_cell_text_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
                        sheet, y = record.create_excel_row(sheet, y, col, format_cells, report_configuration_line.name, value_this_year, value_last_year, value_diff)
    
                        if report_configuration_line.sequence in (3,4,5):
                            total_ar_this_year = total_ar_this_year + value_this_year
                            total_ar_last_year = total_ar_last_year + value_last_year
                            total_ar_diff = total_ar_diff + value_diff
                        
                        if report_configuration_line.sequence == 5:
                            format_cells = [bold, right, right, right]
                            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
                            format_cells = [format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Nilai Buku Piutang Usaha", total_ar_this_year, total_ar_last_year, total_ar_diff)
    
                        total_this_year = total_this_year + value_this_year
                        total_last_year = total_last_year + value_last_year
                        total_diff = total_diff + value_diff
    
                format_cells = [bold, right, right, right]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
                format_cells = [format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah " + report_type_line.name, total_this_year, total_last_year, total_diff)
    
                grand_total_assets_this_year = grand_total_assets_this_year + total_this_year
                grand_total_assets_last_year = grand_total_assets_last_year + total_last_year
                grand_total_assets_diff = grand_total_assets_diff + total_diff
    
    
            format_cells = [format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "JUMLAH AKTIVA", grand_total_assets_this_year, grand_total_assets_last_year, grand_total_assets_diff)
    
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'NRC')])
            report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', 'in', ('KL','KLL', 'ES', 'HJP'))], order='sequence asc')
    
    
            grand_total_liabilities_this_year = 0
            grand_total_liabilities_last_year = 0
            grand_total_liabilities_diff = 0
    
            y = 9
            col = 4
            for report_type_line in report_type_lines:
                report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
                report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')
    
                if report_type_line.is_show == True:
                    format_cells = [bold, right, right, right]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, report_type_line.name, "", "", "")
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
    
                total_equity_this_year = 0
                total_equity_last_year = 0
                total_equity_diff = 0
    
                total_this_year = 0
                total_last_year = 0
                total_diff = 0
                for report_configuration_line in report_configuration_lines:
                    if report_type_line.is_show == True:
    
                        if report_configuration_line.sequence == 38:
                            current_year_start_date = record.years + '-01-01'
                            before_month_start_date = str(int(record.years) - 1) + '-' + record.months + '-01'
                            before_month_end_date = (datetime.strptime(str(int(record.years) - 1) + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
                            value_this_year = record.calculate_profit_loss_after_tax(current_year_start_date, record.end_date)
                            value_last_year = record.calculate_profit_loss_after_tax(before_month_start_date, before_month_end_date)
    
                        else:
                            debit, credit = record.calculate_balance_sheet(record.start_date, record.end_date, report_type_line.code, report_configuration_line.name)
                            ending_balance = record.get_last_balance(report_type_line.code, report_configuration_line.name)
                            value_this_year = (ending_balance + credit) - debit
    
                            value_last_year = 0
                            
                        value_diff = value_this_year - value_last_year
    
                        format_cells = [format_cell_text_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
                        sheet, y = record.create_excel_row(sheet, y, col, format_cells, report_configuration_line.name, value_this_year, value_last_year, value_diff)
    
                        if report_configuration_line.sequence in (32,33):
                            total_equity_this_year = total_equity_this_year + value_this_year
                            total_equity_last_year = total_equity_last_year + value_last_year
                            total_equity_diff = total_equity_diff + value_diff
                        
                        if report_configuration_line.sequence == 33:
                            format_cells = [bold, right, right, right]
                            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
                            format_cells = [format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah Modal", total_equity_this_year, total_equity_last_year, total_equity_diff)
    
                        total_this_year = total_this_year + value_this_year
                        total_last_year = total_last_year + value_last_year
                        total_diff = total_diff + value_diff
    
                format_cells = [bold, right, right, right]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "")
                format_cells = [format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah " + report_type_line.name, total_this_year, total_last_year, total_diff)
    
                grand_total_liabilities_this_year = grand_total_liabilities_this_year + total_this_year
                grand_total_liabilities_last_year = grand_total_liabilities_last_year + total_last_year
                grand_total_liabilities_diff = grand_total_liabilities_diff + total_diff
    
            format_cells = [format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "JUMLAH PASSIVA", grand_total_liabilities_this_year, grand_total_liabilities_last_year, grand_total_liabilities_diff)
    
            y += 1
    
            last_row_activa = y
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename
    
            # fp = StringIO()
            # workbook.save(fp)
            # record_id = self.env['pam.excel.report'].create({'file_bin': base64.encodestring(fp.read()),'file_name': filename})
            # fp.close()
            # return {
            #     'view_mode': 'form',
            #     'res_id': record_id,
            #     'res_model': 'pam.excel.report',
            #     'view_type': 'form',
            #     'type': 'ir.actions.act_window',
            #     # 'context': context,
            #     'target': 'new'
            #     }

    def export_report_pdf(self):
        for record in self:
            report_type = self.env['pam.report.type'].search([('code','=', 'NRC')])
            report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id)], order='sequence asc')
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan PDF'
                })
    
            records = []
            for report_type_line in report_type_lines:
                report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
                report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')
                for report_configuration_line in report_configuration_lines:
                    debit, credit = record.calculate_balance_sheet(record.start_date, record.end_date, report_type_line.code, report_configuration_line.name)
                    ending_balance = record.get_last_balance(report_type_line.code, report_configuration_line.name)
                    value_this_year = (ending_balance + debit) - credit
                    value_last_year = 0
                    value_diff = value_this_year - value_last_year
                    records.append([report_configuration_line.name, value_this_year, value_last_year, value_diff])
    
            code_iso = self.env['pam.code.iso'].search([('name','=','neraca')])
    
            data = {
                'ids': record.ids,
                'model': record._name,
                'form': {
                    'code_iso': code_iso.code_iso,
                    'months': (datetime.strptime(record.months, '%m').strftime("%B")),
                    'years': record.years,
                    'datetime_cetak': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                    'report_type_lines': report_type_lines,
                    'html': record.report_html,
                    'records': records
                },
            }
    
            return self.env.ref('pam_accounting.action_pam_balance_sheet_report').report_action(record, data=data)


class PamBalanceSheetReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_balance_sheet_template'
    _template = 'pam_accounting.report_balance_sheet_template'

    @api.model
    def get_report_values(self, docids, data=None):
        code_iso = data['form']['code_iso']
        months = data['form']['months']
        years = data['form']['years']
        datetime_cetak = data['form']['datetime_cetak']
        report_type_lines = data['form']['report_type_lines']
        # raise ValidationError(_('%s')%(report_type_lines.code))
        html = data['form']['html']
        records = data['form']['records']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'code_iso': code_iso,
            'months': months,
            'years': years,
            'datetime_cetak': datetime_cetak,
            'report_type_lines': report_type_lines,
            'html': html,
            'records': records
        }
