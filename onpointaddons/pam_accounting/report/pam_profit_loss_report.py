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


class PamProfitLossReport(models.TransientModel):
    _name = 'pam.profit.loss.report'
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
    years = fields.Selection(_get_years, string='Tahun Laba Rugi', default=_default_year, required=True)

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
        value_last_year=0, 
        budget_last_year=0, 
        value_compare_last_year=0, 
        budget_compare_last_year=0,
        value_until_this_month=0,
        value_until_this_month_last_year=0,
        budget_this_year=0,
        value_compare_this_year=0,
        budget_compare_this_year=0):

        html = html + "<tr class='" + class_name + "'>"

        if value_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_this_year) + "</td>"
        else:
            html = html + "<td></td>"

        if value_last_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_last_year) + "</td>"
        else:
            html = html + "<td></td>"

        if budget_last_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_last_year) + "</td>"
        else:
            html = html + "<td></td>"

        if value_compare_last_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_compare_last_year) + "</td>"
        else:
            html = html + "<td></td>"

        if budget_compare_last_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_compare_last_year) + "</td>"
        else:
            html = html + "<td></td>"

        html = html + "<td>" + name + "</td>"

        if value_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_until_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        if value_until_this_month_last_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_until_this_month_last_year) + "</td>"
        else:
            html = html + "<td></td>"

        if budget_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_this_year) + "</td>"
        else:
            html = html + "<td></td>"

        if value_compare_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_compare_this_year) + "</td>"
        else:
            html = html + "<td></td>"

        if budget_compare_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_compare_this_year) + "</td>"
        else:
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

        report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
        report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id)])

        for report_type_line in report_type_lines:
            report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
            report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')

            html = self.create_html_row(html, "", "<b>" + report_type_line.name + "</b>", "", "", "", "", "", "", "", "", "", "")

            total_value_this_year = 0
            total_value_last_year = 0
            total_budget_last_year = 0
            total_value_compare_last_year = 0
            total_budget_compare_last_year = 0
            total_value_until_this_month = 0
            total_value_until_this_month_last_year = 0
            total_budget_this_year = 0
            total_value_compare_this_year = 0
            total_budget_compare_this_year = 0

            totals = {}
            for report_configuration_line in report_configuration_lines:

                # ending_balance = self.get_last_balance(report_type_line.code, report_configuration_line.name)
                value_this_year = self.calculate_profit_loss(self.start_date, self.end_date, report_type_line.code, report_configuration_line.name, report_type_line.coa_type)

                # ending_balance = self.get_last_balance(report_type_line.code, report_configuration_line.name)
                value_last_year = self.calculate_profit_loss(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name, report_type_line.coa_type)

                budget_last_year = 0
                
                value_compare_last_year = value_this_year - value_last_year
                
                budget_compare_last_year = value_this_year - budget_last_year

                # ending_balance = self.get_last_balance(report_type_line.code, report_configuration_line.name)
                value_until_this_month = self.calculate_profit_loss(current_year_start_date, self.end_date, report_type_line.code, report_configuration_line.name, report_type_line.coa_type)

                # ending_balance = self.get_last_balance(report_type_line.code, report_configuration_line.name)
                value_until_this_month_last_year = self.calculate_profit_loss(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name, report_type_line.coa_type)

                budget_this_year = 0

                value_compare_this_year = value_until_this_month - value_until_this_month_last_year

                budget_compare_this_year = value_until_this_month - budget_this_year

                html = self.create_html_row(html, "", report_configuration_line.name, value_this_year, value_last_year, budget_last_year, value_compare_last_year, budget_compare_last_year, value_until_this_month, value_until_this_month_last_year, budget_this_year, value_compare_this_year, budget_compare_this_year)

                total_value_this_year += value_this_year
                total_value_last_year += value_last_year
                total_budget_last_year += budget_last_year
                total_value_compare_last_year += value_compare_last_year
                total_budget_compare_last_year += budget_compare_last_year
                total_value_until_this_month += value_until_this_month
                total_value_until_this_month_last_year += value_until_this_month_last_year
                total_budget_this_year += budget_this_year
                total_value_compare_this_year += value_compare_this_year
                total_budget_compare_this_year += budget_compare_this_year

            html = self.create_html_row(html, "total-cell", "Jumlah " + report_type_line.name, total_value_this_year, total_value_last_year, total_budget_last_year, total_value_compare_last_year, total_budget_compare_last_year, total_value_until_this_month, total_value_until_this_month_last_year, total_budget_this_year, total_value_compare_this_year, total_budget_compare_this_year)

            if report_type_line.sequence == 2:
                gross_profit_loss_this_year = self.calculate_gross_profit_loss(self.start_date, self.end_date)
                gross_profit_loss_last_year = self.calculate_gross_profit_loss(before_month_start_date, before_month_end_date)
                gross_profit_loss_budget_last_year = 0
                gross_profit_loss_compare_last_year = gross_profit_loss_this_year - gross_profit_loss_last_year
                gross_profit_loss_budget_compare_last_year = gross_profit_loss_this_year - gross_profit_loss_budget_last_year
                gross_profit_loss_until_this_month = self.calculate_gross_profit_loss(current_year_start_date, self.end_date)
                gross_profit_loss_until_this_month_last_year = self.calculate_gross_profit_loss(before_month_start_date, before_month_end_date)
                gross_profit_loss_budget_this_year = 0
                gross_profit_loss_compare_this_year = gross_profit_loss_until_this_month_last_year - gross_profit_loss_until_this_month_last_year
                gross_profit_loss_compare_this_year = gross_profit_loss_until_this_month - gross_profit_loss_budget_this_year

                html = self.create_html_row(html, "total-cell", "Laba (Rugi) Kotor Usaha", 
                    gross_profit_loss_this_year, 
                    gross_profit_loss_last_year, 
                    gross_profit_loss_budget_last_year, 
                    gross_profit_loss_compare_last_year, 
                    gross_profit_loss_budget_compare_last_year, 
                    gross_profit_loss_until_this_month, 
                    gross_profit_loss_until_this_month_last_year, 
                    gross_profit_loss_budget_this_year, 
                    gross_profit_loss_compare_this_year, 
                    gross_profit_loss_compare_this_year)

            if report_type_line.sequence == 3:
                profit_loss_business_this_year = self.calculate_profit_loss_business(self.start_date, self.end_date)
                profit_loss_business_last_year = self.calculate_profit_loss_business(before_month_start_date, before_month_end_date)
                profit_loss_business_budget_last_year = 0
                profit_loss_business_compare_last_year = profit_loss_business_this_year - profit_loss_business_last_year
                profit_loss_business_budget_compare_last_year = profit_loss_business_this_year - profit_loss_business_budget_last_year
                profit_loss_business_until_this_month = self.calculate_profit_loss_business(current_year_start_date, self.end_date)
                profit_loss_business_until_this_month_last_year = self.calculate_profit_loss_business(before_month_start_date, before_month_end_date)
                profit_loss_business_budget_this_year = 0
                profit_loss_business_compare_this_year = profit_loss_business_until_this_month_last_year - profit_loss_business_until_this_month_last_year
                profit_loss_business_compare_this_year = profit_loss_business_until_this_month - profit_loss_business_budget_this_year

                html = self.create_html_row(html, "total-cell", "Laba (Rugi) Usaha", 
                    profit_loss_business_this_year, 
                    profit_loss_business_last_year, 
                    profit_loss_business_budget_last_year, 
                    profit_loss_business_compare_last_year, 
                    profit_loss_business_budget_compare_last_year, 
                    profit_loss_business_until_this_month, 
                    profit_loss_business_until_this_month_last_year, 
                    profit_loss_business_budget_this_year, 
                    profit_loss_business_compare_this_year, 
                    profit_loss_business_compare_this_year)

            if report_type_line.sequence == 4:
                profit_loss_before_tax_this_year = self.calculate_profit_loss_before_tax(self.start_date, self.end_date)
                profit_loss_before_tax_last_year = self.calculate_profit_loss_before_tax(before_month_start_date, before_month_end_date)
                profit_loss_before_tax_budget_last_year = 0
                profit_loss_before_tax_compare_last_year = profit_loss_before_tax_this_year - profit_loss_before_tax_last_year
                profit_loss_before_tax_budget_compare_last_year = profit_loss_before_tax_this_year - profit_loss_before_tax_budget_last_year
                profit_loss_before_tax_until_this_month = self.calculate_profit_loss_before_tax(current_year_start_date, self.end_date)
                profit_loss_before_tax_until_this_month_last_year = self.calculate_profit_loss_before_tax(before_month_start_date, before_month_end_date)
                profit_loss_before_tax_budget_this_year = 0
                profit_loss_before_tax_compare_this_year = profit_loss_before_tax_until_this_month_last_year - profit_loss_before_tax_until_this_month_last_year
                profit_loss_before_tax_compare_this_year = profit_loss_before_tax_until_this_month - profit_loss_before_tax_budget_this_year

                html = self.create_html_row(html, "total-cell", "Laba (Rugi) Usaha Sebelum Pajak", 
                    profit_loss_before_tax_this_year, 
                    profit_loss_before_tax_last_year, 
                    profit_loss_before_tax_budget_last_year, 
                    profit_loss_before_tax_compare_last_year, 
                    profit_loss_before_tax_budget_compare_last_year, 
                    profit_loss_before_tax_until_this_month, 
                    profit_loss_before_tax_until_this_month_last_year, 
                    profit_loss_before_tax_budget_this_year, 
                    profit_loss_before_tax_compare_this_year, 
                    profit_loss_before_tax_compare_this_year)

            if report_type_line.sequence == 5:
                profit_loss_after_tax_this_year = self.calculate_profit_loss_after_tax(self.start_date, self.end_date)
                profit_loss_after_tax_last_year = self.calculate_profit_loss_after_tax(before_month_start_date, before_month_end_date)
                profit_loss_after_tax_budget_last_year = 0
                profit_loss_after_tax_compare_last_year = profit_loss_after_tax_this_year - profit_loss_after_tax_last_year
                profit_loss_after_tax_budget_compare_last_year = profit_loss_after_tax_this_year - profit_loss_after_tax_budget_last_year
                profit_loss_after_tax_until_this_month = self.calculate_profit_loss_after_tax(current_year_start_date, self.end_date)
                profit_loss_after_tax_until_this_month_last_year = self.calculate_profit_loss_after_tax(before_month_start_date, before_month_end_date)
                profit_loss_after_tax_budget_this_year = 0
                profit_loss_after_tax_compare_this_year = profit_loss_after_tax_until_this_month_last_year - profit_loss_after_tax_until_this_month_last_year
                profit_loss_after_tax_compare_this_year = profit_loss_after_tax_until_this_month - profit_loss_after_tax_budget_this_year

                html = self.create_html_row(html, "total-cell", "Laba (Rugi) Usaha Setelah Pajak", 
                    profit_loss_after_tax_this_year, 
                    profit_loss_after_tax_last_year, 
                    profit_loss_after_tax_budget_last_year, 
                    profit_loss_after_tax_compare_last_year, 
                    profit_loss_after_tax_budget_compare_last_year, 
                    profit_loss_after_tax_until_this_month, 
                    profit_loss_after_tax_until_this_month_last_year, 
                    profit_loss_after_tax_budget_this_year, 
                    profit_loss_after_tax_compare_this_year, 
                    profit_loss_after_tax_compare_this_year)

        html = html + "</table>"

        report = self.env['pam.profit.loss.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True,
        })

    def create_excel_row(self, sheet, y, col, format_cells, 
        name, 
        value_this_year=0, 
        value_last_year=0, 
        budget_last_year=0, 
        value_compare_last_year=0, 
        budget_compare_last_year=0,
        value_until_this_month=0,
        value_until_this_month_last_year=0,
        budget_this_year=0,
        value_compare_this_year=0,
        budget_compare_this_year=0):

        sheet.write(y, col, value_this_year, format_cells[0])
        col += 1
        sheet.write(y, col, value_last_year, format_cells[1])
        col += 1
        sheet.write(y, col, budget_last_year, format_cells[2])
        col += 1
        sheet.write(y, col, value_compare_last_year, format_cells[3])
        col += 1
        sheet.write(y, col, budget_compare_last_year, format_cells[4])
        col += 1
        sheet.write(y, col, name, format_cells[5])
        col += 1
        sheet.write(y, col, value_until_this_month, format_cells[6])
        col += 1
        sheet.write(y, col, value_until_this_month_last_year, format_cells[7])
        col += 1
        sheet.write(y, col, budget_this_year, format_cells[8])
        col += 1
        sheet.write(y, col, value_compare_this_year, format_cells[9])
        col += 1
        sheet.write(y, col, budget_compare_this_year, format_cells[10])

        y = y + 1

        return sheet, y

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN LABA RUGI'
            filename = '%s.xlsx' % ('Laporan Laba Rugi',)
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 11, 'font': 'Tahoma'})
            judul = workbook.add_format({'bold': True, 'align': 'center'})
            payment_date = workbook.add_format({'font_size': 12})
            jalan = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
            bold = workbook.add_format({'bold': True})
            merge = workbook.add_format({'bold': True, 'border': True})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1})
            top = workbook.add_format({'top': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'center'})
            right = workbook.add_format({'right': 1})
            center = workbook.add_format({'align': 'center', 'top': 1})
            center_bottom = workbook.add_format({'align': 'center', 'bottom': 1})
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'right': 1,'left': 1, 'align': 'right'})
            jumlah = workbook.add_format({'right': 1,'left': 1, 'num_format': '#,##0.00'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'font': 'Tahoma', 'align': 'center', 'font_size': 14, 'bold': True})
            border = workbook.add_format({'font': 'Tahoma', 'align': 'center', 'font_size': 14, 'bold': True, 'border': True, 'bg_color': '#ffff00'})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            str_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
            no_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'align': 'center'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            style_bold = {'bold': True}
            style_font = {'font': 'Tahoma'}
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
    
            sheet.set_column(0, 4, 30)
            sheet.set_column(5, 5, 50)
            sheet.set_column(6, 10, 30)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','laba_rugi')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 10, 2, 10,code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 10, 2, 10,' ', judul)
    
            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))
    
            sheet.insert_image(0, 0, 'logo.jpg', {'image_data' : logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})
    
            sheet.merge_range(0, 0, 0, 9, 'PDAM TIRTA PAKUAN KOTA BOGOR', str_format)
            sheet.merge_range(1, 0, 1, 9, 'LAPORAN LABA RUGI', str_format)
            sheet.merge_range(2, 0, 2, 9, 'BULAN : ' + (datetime.strptime(record.months, '%m').strftime("%B")) + ' ' + record.years, str_format)
    
            sheet.write(4, 10, (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'), title)
    
            sheet.merge_range(5, 0, 5, 2, 'B U L A N  I N I', border)
            sheet.merge_range(6, 0, 6, 1, 'REALISASI', border)
            sheet.write(7, 0, 'TAHUN INI', border)
            sheet.write(7, 1, 'TAHUN LALU', border)
            sheet.merge_range(6, 2, 7, 2,'ANGGARAN', border)
            sheet.merge_range(5, 3, 5, 4, 'PERBANDINGAN TAHUN INI', border)
            sheet.merge_range(6, 3, 7, 3, 'Realisasi Dengan Tahun Lalu', border)
            sheet.merge_range(6, 4, 7, 4, 'Realisasi Dengan Anggaran', border)
            sheet.merge_range(5, 5, 7, 5, 'P E R K I R A A N', border)
            sheet.merge_range(5, 6, 5, 8, 'S/D BULAN INI', border)
            sheet.merge_range(6, 6, 6, 7, 'REALISASI', border)
            sheet.write(7, 6, 'TAHUN INI', border)
            sheet.write(7, 7, 'TAHUN LALU', border)
            sheet.merge_range(6, 8, 7, 8, 'ANGGARAN', border)
            sheet.merge_range(5, 9, 5, 10, 'PERBANDINGAN TAHUN INI', border)
            sheet.merge_range(6, 9, 7, 9, 'TAHUN LALU', border)
            sheet.merge_range(6, 10, 7, 10, 'ANGGARAN', border)
    
            before_month_start_date = str(int(record.years) - 1) + '-' + record.months + '-01'
            before_month_end_date = (datetime.strptime(str(int(record.years) - 1) + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
            current_month_start_date = record.years + '-' + record.months+ '-01'
            current_month_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
            before_year_start_date = str(int(record.years) - 1) + '-01-01'
            before_year_end_date = (datetime.strptime(record.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
            current_year_start_date = record.years + '-01-01'
            current_year_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
            report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id)])
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan Excel'
                })
    
            y = 8
            col = 0
            for report_type_line in report_type_lines:
                report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
                report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')
    
                format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_bold, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "", "", "", "", "", "")
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, report_type_line.name, "", "", "", "", "", "", "", "", "", "")
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "", "", "", "", "", "")
    
                total_value_this_year = 0
                total_value_last_year = 0
                total_budget_last_year = 0
                total_value_compare_last_year = 0
                total_budget_compare_last_year = 0
                total_value_until_this_month = 0
                total_value_until_this_month_last_year = 0
                total_budget_this_year = 0
                total_value_compare_this_year = 0
                total_budget_compare_this_year = 0
    
                totals = {}
                for report_configuration_line in report_configuration_lines:
    
                    value_this_year = record.calculate_profit_loss(record.start_date, record.end_date, report_type_line.code, report_configuration_line.name, report_type_line.coa_type)
                    value_last_year = record.calculate_profit_loss(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name, report_type_line.coa_type)
                    budget_last_year = 0
                    value_compare_last_year = value_this_year - value_last_year
                    budget_compare_last_year = value_this_year - budget_last_year
                    value_until_this_month = record.calculate_profit_loss(current_year_start_date, record.end_date, report_type_line.code, report_configuration_line.name, report_type_line.coa_type)
                    value_until_this_month_last_year = record.calculate_profit_loss(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name, report_type_line.coa_type)
                    budget_this_year = 0
                    value_compare_this_year = value_until_this_month - value_until_this_month_last_year
                    budget_compare_this_year = value_until_this_month - budget_this_year
    
    
                    format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_text_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "  - " + report_configuration_line.name, value_this_year, value_last_year, budget_last_year, value_compare_last_year, budget_compare_last_year, value_until_this_month, value_until_this_month_last_year, budget_this_year, value_compare_this_year, budget_compare_this_year)
    
                    total_value_this_year += value_this_year
                    total_value_last_year += value_last_year
                    total_budget_last_year += budget_last_year
                    total_value_compare_last_year += value_compare_last_year
                    total_budget_compare_last_year += budget_compare_last_year
                    total_value_until_this_month += value_until_this_month
                    total_value_until_this_month_last_year += value_until_this_month_last_year
                    total_budget_this_year += budget_this_year
                    total_value_compare_this_year += value_compare_this_year
                    total_budget_compare_this_year += budget_compare_this_year
    
                format_cells = [right, right, right, right, right, right, right, right, right, right, right]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "", "", "", "", "", "")
                format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah " + report_type_line.name, total_value_this_year, total_value_last_year, total_budget_last_year, total_value_compare_last_year, total_budget_compare_last_year, total_value_until_this_month, total_value_until_this_month_last_year, total_budget_this_year, total_value_compare_this_year, total_budget_compare_this_year)
    
                if report_type_line.sequence == 2:
                    gross_profit_loss_this_year = record.calculate_gross_profit_loss(record.start_date, record.end_date)
                    gross_profit_loss_last_year = record.calculate_gross_profit_loss(before_month_start_date, before_month_end_date)
                    gross_profit_loss_budget_last_year = 0
                    gross_profit_loss_compare_last_year = gross_profit_loss_this_year - gross_profit_loss_last_year
                    gross_profit_loss_budget_compare_last_year = gross_profit_loss_this_year - gross_profit_loss_budget_last_year
                    gross_profit_loss_until_this_month = record.calculate_gross_profit_loss(current_year_start_date, record.end_date)
                    gross_profit_loss_until_this_month_last_year = record.calculate_gross_profit_loss(before_month_start_date, before_month_end_date)
                    gross_profit_loss_budget_this_year = 0
                    gross_profit_loss_compare_this_year = gross_profit_loss_until_this_month_last_year - gross_profit_loss_until_this_month_last_year
                    gross_profit_loss_compare_this_year = gross_profit_loss_until_this_month - gross_profit_loss_budget_this_year
    
                    format_cells = [right, right, right, right, right, right, right, right, right, right, right]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "", "", "", "", "", "")
                    format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Laba (Rugi) Kotor Usaha", 
                        gross_profit_loss_this_year, 
                        gross_profit_loss_last_year, 
                        gross_profit_loss_budget_last_year, 
                        gross_profit_loss_compare_last_year, 
                        gross_profit_loss_budget_compare_last_year, 
                        gross_profit_loss_until_this_month, 
                        gross_profit_loss_until_this_month_last_year, 
                        gross_profit_loss_budget_this_year, 
                        gross_profit_loss_compare_this_year, 
                        gross_profit_loss_compare_this_year)
        
                if report_type_line.sequence == 3:
                    profit_loss_business_this_year = record.calculate_profit_loss_business(record.start_date, record.end_date)
                    profit_loss_business_last_year = record.calculate_profit_loss_business(before_month_start_date, before_month_end_date)
                    profit_loss_business_budget_last_year = 0
                    profit_loss_business_compare_last_year = profit_loss_business_this_year - profit_loss_business_last_year
                    profit_loss_business_budget_compare_last_year = profit_loss_business_this_year - profit_loss_business_budget_last_year
                    profit_loss_business_until_this_month = record.calculate_profit_loss_business(current_year_start_date, record.end_date)
                    profit_loss_business_until_this_month_last_year = record.calculate_profit_loss_business(before_month_start_date, before_month_end_date)
                    profit_loss_business_budget_this_year = 0
                    profit_loss_business_compare_this_year = profit_loss_business_until_this_month_last_year - profit_loss_business_until_this_month_last_year
                    profit_loss_business_compare_this_year = profit_loss_business_until_this_month - profit_loss_business_budget_this_year
    
                    format_cells = [right, right, right, right, right, right, right, right, right, right, right]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "", "", "", "", "", "")
                    format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Laba (Rugi) Usaha", 
                        profit_loss_business_this_year, 
                        profit_loss_business_last_year, 
                        profit_loss_business_budget_last_year, 
                        profit_loss_business_compare_last_year, 
                        profit_loss_business_budget_compare_last_year, 
                        profit_loss_business_until_this_month, 
                        profit_loss_business_until_this_month_last_year, 
                        profit_loss_business_budget_this_year, 
                        profit_loss_business_compare_this_year, 
                        profit_loss_business_compare_this_year)
    
                if report_type_line.sequence == 4:
                    profit_loss_before_tax_this_year = record.calculate_profit_loss_before_tax(record.start_date, record.end_date)
                    profit_loss_before_tax_last_year = record.calculate_profit_loss_before_tax(before_month_start_date, before_month_end_date)
                    profit_loss_before_tax_budget_last_year = 0
                    profit_loss_before_tax_compare_last_year = profit_loss_before_tax_this_year - profit_loss_before_tax_last_year
                    profit_loss_before_tax_budget_compare_last_year = profit_loss_before_tax_this_year - profit_loss_before_tax_budget_last_year
                    profit_loss_before_tax_until_this_month = record.calculate_profit_loss_before_tax(current_year_start_date, record.end_date)
                    profit_loss_before_tax_until_this_month_last_year = record.calculate_profit_loss_before_tax(before_month_start_date, before_month_end_date)
                    profit_loss_before_tax_budget_this_year = 0
                    profit_loss_before_tax_compare_this_year = profit_loss_before_tax_until_this_month_last_year - profit_loss_before_tax_until_this_month_last_year
                    profit_loss_before_tax_compare_this_year = profit_loss_before_tax_until_this_month - profit_loss_before_tax_budget_this_year
    
                    format_cells = [right, right, right, right, right, right, right, right, right, right, right]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "", "", "", "", "", "")
                    format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Laba (Rugi) Usaha Sebelum Pajak", 
                        profit_loss_before_tax_this_year, 
                        profit_loss_before_tax_last_year, 
                        profit_loss_before_tax_budget_last_year, 
                        profit_loss_before_tax_compare_last_year, 
                        profit_loss_before_tax_budget_compare_last_year, 
                        profit_loss_before_tax_until_this_month, 
                        profit_loss_before_tax_until_this_month_last_year, 
                        profit_loss_before_tax_budget_this_year, 
                        profit_loss_before_tax_compare_this_year, 
                        profit_loss_before_tax_compare_this_year)
        
                if report_type_line.sequence == 5:
                    profit_loss_after_tax_this_year = record.calculate_profit_loss_after_tax(record.start_date, record.end_date)
                    profit_loss_after_tax_last_year = record.calculate_profit_loss_after_tax(before_month_start_date, before_month_end_date)
                    profit_loss_after_tax_budget_last_year = 0
                    profit_loss_after_tax_compare_last_year = profit_loss_after_tax_this_year - profit_loss_after_tax_last_year
                    profit_loss_after_tax_budget_compare_last_year = profit_loss_after_tax_this_year - profit_loss_after_tax_budget_last_year
                    profit_loss_after_tax_until_this_month = record.calculate_profit_loss_after_tax(current_year_start_date, record.end_date)
                    profit_loss_after_tax_until_this_month_last_year = record.calculate_profit_loss_after_tax(before_month_start_date, before_month_end_date)
                    profit_loss_after_tax_budget_this_year = 0
                    profit_loss_after_tax_compare_this_year = profit_loss_after_tax_until_this_month_last_year - profit_loss_after_tax_until_this_month_last_year
                    profit_loss_after_tax_compare_this_year = profit_loss_after_tax_until_this_month - profit_loss_after_tax_budget_this_year
    
                    format_cells = [right, right, right, right, right, right, right, right, right, right, right]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "", "", "", "", "", "", "", "", "", "", "")
                    format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_text_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Laba (Rugi) Usaha Setelah Pajak", 
                        profit_loss_after_tax_this_year, 
                        profit_loss_after_tax_last_year, 
                        profit_loss_after_tax_budget_last_year, 
                        profit_loss_after_tax_compare_last_year, 
                        profit_loss_after_tax_budget_compare_last_year, 
                        profit_loss_after_tax_until_this_month, 
                        profit_loss_after_tax_until_this_month_last_year, 
                        profit_loss_after_tax_budget_this_year, 
                        profit_loss_after_tax_compare_this_year, 
                        profit_loss_after_tax_compare_this_year)
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename

    def export_report_pdf(self):
        for record in self:
            report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
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
    
            return self.env.ref('pam_accounting.action_pam_profit_loss_report').report_action(record, data=data)

class PamProfitLossReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_profit_loss_template'
    _template = 'pam_accounting.report_profit_loss_template'

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
