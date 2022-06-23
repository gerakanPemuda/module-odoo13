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


class PamCashFlowReport(models.TransientModel):
    _name = 'pam.cash.flow.report'
    _inherit = ['pam.cash.flow', 'pam.balance.sheet']

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
    years = fields.Selection(_get_years, string='Tahun Arus Kas', default=_default_year, required=True)
    period = fields.Char(compute='set_period')
    start_date = fields.Date(compute='set_period_date')
    end_date = fields.Date(compute='set_period_date')
    last_posted_period = fields.Integer(compute='set_last_posted_period')
    range_start_date = fields.Date(compute='set_last_posted_period')
    range_end_date = fields.Date(compute='set_last_posted_period')

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    report_html = fields.Html(string="Arus Kas")
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

    def get_data(self):

        # starting div
        html = "<table class='report-table'>"

        html = html + "<tr>"
        html = html + "<th rowspan='3' width='500px'>URAIAN</td>"
        html = html + "<th colspan='3'>BULAN INI</td>"
        html = html + "<th colspan='2'>PERBANDINGAN TAHUN INI</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th colspan='2'>REALISASI</td>"
        html = html + "<th width='300px' rowspan='2'>ANGGARAN</td>"
        html = html + "<th width='300px' rowspan='2'>Realisasi Dengan Tahun Lalu</td>"
        html = html + "<th width='300px' rowspan='2'>Realisasi Dengan Anggaran</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th width='300px'>Tahun Ini</td>"
        html = html + "<th width='300px'>Tahun Lalu</td>"
        html = html + "</tr>"

        report_type = self.env['pam.report.type'].search([('code', '=', 'LAK')])
        report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id)])
        
        before_month_start_date = str(int(self.years) - 1) + '-' + self.months + '-01'
        before_month_end_date = (datetime.strptime(str(int(self.years) - 1) + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        current_month_start_date = self.years + '-' + self.months+ '-01'
        current_month_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        before_year_start_date = str(int(self.years) - 1) + '-01-01'
        before_year_end_date = (datetime.strptime(self.years + '-01-01', "%Y-%m-%d") - relativedelta(days=1)).strftime("%Y-%m-%d")
        current_year_start_date = self.years + '-01-01'
        current_year_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        y = 6
        total_income_this_year = 0
        total_income_last_year = 0
        total_income_budget = 0

        total_cost_this_year = 0
        total_cost_last_year = 0
        total_cost_budget = 0

        for report_type_line in report_type_lines:
            report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
            report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')
            
            if report_type_line.code == 'PO':
                html = html + "<tr>"
                html = html + "<td><b>Arus Kas dari Aktivitas :</b></td>"
                html = html + "<td></td>"
                html = html + "<td></td>"
                html = html + "<td></td>"
                html = html + "<td></td>"
                html = html + "<td></td>"
                html = html + "</tr>"

            if report_type_line.code == 'PLO':
                html = html + "<tr>"
                html = html + "<td><b>Arus Kas Untuk Kegiatan Operasi :</b></td>"
                html = html + "<td></td>"
                html = html + "<td></td>"
                html = html + "<td></td>"
                html = html + "<td></td>"
                html = html + "<td></td>"
                html = html + "</tr>"

            html = html + "<tr>"
            html = html + "<td>" + report_type_line.name + "</td>"
            html = html + "<td></td>"
            html = html + "<td></td>"
            html = html + "<td></td>"
            html = html + "<td></td>"
            html = html + "<td></td>"
            html = html + "</tr>"

            group_ids = []
            total_cm = 0
            total_bm = 0
            total_cy = 0
            for report_configuration_line in report_configuration_lines:

                if report_type_line.code in ('PO', 'PNO'):
                    if report_configuration_line.name == '- Penerimaan Kas rupa-rupa operasional':
                        value_this_year = self.calculate_other_income(current_month_start_date, current_month_end_date)
                        value_last_year = self.calculate_other_income(before_month_start_date, before_month_end_date)
                    else:
                        value_this_year = self.calculate_income(current_month_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name, 'credit')
                        value_last_year = self.calculate_income(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name, 'credit')

                    total_income_this_year += value_this_year
                    total_income_last_year += value_last_year

                else:
                    value_this_year = (self.calculate_cost(current_month_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name)) * -1
                    value_last_year = (self.calculate_cost(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name)) * -1

                    total_cost_this_year += value_this_year
                    total_cost_last_year += value_last_year

                budget_this_month = 0
                value_diff_last_year = value_this_year - value_last_year
                value_diff_budget = 0

                html = html + "<tr>"
                html = html + "<td>" + report_configuration_line.name + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_this_year) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_last_year) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_this_month) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff_last_year) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff_last_year) + "</td>"
                html = html + "</tr>"

                total_cm += value_this_year
                total_bm += value_last_year
                total_cy += value_diff_last_year
                y += 1
                group_ids.append(report_configuration_line.id)

            group_name = (report_type_line.name.upper()).replace(" ", "")

            html = html + "<tr class='total-cell'>"
            html = html + "<td>Jumlah " + report_type_line.name + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_cm) + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_bm) + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_this_month) + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_cy) + "</td>"
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff_budget) + "</td>"
            html = html + "</tr>"

            if report_type_line.code in ['PNO']:
                total_income_diff = total_income_this_year - total_income_last_year
                total_income_diff_budget = 0
                html = html + "<tr class='total-cell'>"
                html = html + "<td>Jumlah Arus Kas Dari Aktivitas Operasi & non Operasi</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_income_this_year) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_income_last_year) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
                html = html + "<td class='number-cell'>" + '{:,.2f}'.format(total_income_diff) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_income_diff_budget) + "</td>"
                html = html + "</tr>"
            
            if report_type_line.code in ['PLNO']:
                total_cost_diff = total_cost_this_year - total_cost_last_year
                total_cost_diff_budget = 0
                html = html + "<tr class='total-cell'>"
                html = html + "<td>Jumlah Arus Kas Dari Aktivitas Operasi & non Operasi</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_cost_this_year) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_cost_last_year) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_cost_diff) + "</td>"
                html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_cost_diff_budget) + "</td>"
                html = html + "</tr>"

        html = html + "<tr class='total-cell'>"
        html = html + "<td>Kenaikan (Penurunan) Bersih kas (I+II+III)</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format((total_income_this_year + total_cost_this_year)) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format((total_income_last_year + total_cost_last_year)) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format((total_income_diff + total_cost_diff)) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
        html = html + "</tr>"

        ending_balance = self.get_last_balance('AL', 'Kas dan Bank')
        html = html + "<tr class='total-cell'>"
        html = html + "<td>Kas dan Setara Kas pada Awal Periode</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(ending_balance) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(ending_balance) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
        html = html + "</tr>"

        html = html + "<tr class='total-cell'>"
        html = html + "<td>Kas dan Setara Kas pada Akhir Periode</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format((total_income_this_year + total_cost_this_year + ending_balance)) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format((total_income_last_year + total_cost_last_year)) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format((total_income_diff + total_cost_diff + ending_balance)) + "</td>"
        html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(0) + "</td>"
        html = html + "</tr>"

        html = html + "</table>"

        report = self.env['pam.cash.flow.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True
        })

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN ARUS KAS'
            filename = '%s.xlsx' % ('LAPORAN ARUS KAS', )
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 14, 'bold': True})
            judul = workbook.add_format({'font_size': 16, 'bold': True})
            payment_date = workbook.add_format({'font_size': 12})
            jalan = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
            bold = workbook.add_format({'bold': True, 'align': 'center'})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1})
            top = workbook.add_format({'top': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'center'})
            right = workbook.add_format({'right': 1})
            center = workbook.add_format({'align': 'center', 'bold': 1, 'font_size': 18, 'font': 'Tahoma', 'font_color': '#666699'})
            merge = workbook.add_format({'bold': True, 'border': True, 'bg_color': '#ccffff', 'font_size': '16', 'font': 'Tahoma', 'align': 'center'})
            center_bottom = workbook.add_format({'align': 'center', 'bottom': 1})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'font': 'Tahoma', 'num_format': '#,##0.00', 'left': 1, 'right': 1, 'font_size': 16})
            no_format = workbook.add_format({'font': 'Tahoma', 'num_format': '#,##0.00', 'left': 1, 'right': 1, 'font_size': 16, 'bottom': 1, 'bold': True})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'bottom': 1, 'left': 1, 'right': 1})
            jumlah_bottom = workbook.add_format({'font_size': 16, 'bold': True, 'left': 1, 'right': 1, 'font': 'Tahoma', 'num_format': '#,##0.00'})
            jumlah = workbook.add_format({'font_size': 16, 'bold': True, 'bottom': 1, 'left': 1, 'right': 1, 'font': 'Tahoma'})
            str_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
            no_total = workbook.add_format({'font': 'Tahoma', 'bold': True, 'left': 1, 'right': 1, 'font_size': 16})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            sheet.set_column(0, 0, 90)
            sheet.set_column(1, 5, 30)
    
            code_iso = self['pam.code.iso'].search([('name','=','arus_kas')])
            if code_iso:
                wrap_text = workbook.add_format({'bold': True, 'align': 'center'})
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 5, 1, 5,code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 5, 1, 5,' ', bold)
    
            sheet.merge_range(0, 0, 0, 4, 'LAPORAN ARUS KAS (METODE LANGSUNG)', center)
            sheet.merge_range(1, 0, 1, 4, 'BULAN : ' + (datetime.strptime(record.months, '%m').strftime("%B")) + ' ' + record.years, center)
    
            sheet.merge_range(3, 0, 5, 0, 'U R A I A N', merge)
            sheet.merge_range(3, 1, 3, 3, 'BULAN INI', merge)
            sheet.merge_range(4, 1, 4, 2, 'RELASI', merge)
            sheet.write(5, 1, 'Tahun Ini', merge)
            sheet.write(5, 2, 'Tahun Lalu', merge)
            sheet.merge_range(4, 3, 5, 3,'Anggaran', merge)
            sheet.merge_range(3, 4, 3, 5, 'PERBANDINGAN TAHUN INI', merge)
            sheet.merge_range(4, 4, 5, 4, 'Realisasi Dengan Tahun Lalu', merge)
            sheet.merge_range(4, 5, 5, 5, 'Realisasi Dengan Anggaran', merge)
    
            report_type = self['pam.report.type'].search([('code', '=', 'LAK')])
            report_type_lines = self['pam.report.type.line'].search([('report_id', '=', report_type.id)])
     
            report_log = self['pam.report.log'].create({
                'name': self.user.name,
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
    
            total_income_this_year = 0
            total_income_last_year = 0
            total_income_budget = 0
    
            total_cost_this_year = 0
            total_cost_last_year = 0
            total_cost_budget = 0
            y = 6
    
            for report_type_line in report_type_lines:
                report_configuration = self['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
                report_configuration_lines = self['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')
                
                if report_type_line.code == 'PO':
                    sheet.write(y, 0, 'Arus Kas dari Aktivitas :', no_total)
                    sheet.write(y, 1, '', no_total)
                    sheet.write(y, 2, '', no_total)
                    sheet.write(y, 3, '', no_total)
                    sheet.write(y, 4, '', no_total)
                    sheet.write(y, 5, '', no_total)
                    y += 1
    
                if report_type_line.code == 'PLO':
                    sheet.write(y, 0, 'Arus Kas Untuk Kegiatan Operasi :', no_total)
                    sheet.write(y, 1, '', no_total)
                    sheet.write(y, 2, '', no_total)
                    sheet.write(y, 3, '', no_total)
                    sheet.write(y, 4, '', no_total)
                    sheet.write(y, 5, '', no_total)
                    y += 1
    
                sheet.write(y, 0, report_type_line.name, no_total)
                sheet.write(y, 1, '', no_total)
                sheet.write(y, 2, '', no_total)
                sheet.write(y, 3, '', no_total)
                sheet.write(y, 4, '', no_total)
                sheet.write(y, 5, '', no_total)
                y += 1
        
                total_cm = 0
                total_bm = 0
                total_cy = 0
                group_ids = []
                for report_configuration_line in report_configuration_lines:
    
                    if report_type_line.code in ('PO', 'PNO'):
                        if report_configuration_line.name == '- Penerimaan Kas rupa-rupa operasional':
                            value_this_year = record.calculate_other_income(current_month_start_date, current_month_end_date)
                            value_last_year = record.calculate_other_income(before_month_start_date, before_month_end_date)
                        else:
                            value_this_year = record.calculate_income(current_month_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name, 'credit')
                            value_last_year = record.calculate_income(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name, 'credit')
    
                        total_income_this_year += value_this_year
                        total_income_last_year += value_last_year
    
                    else:
                        value_this_year = (record.calculate_cost(current_month_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name)) * -1
                        value_last_year = (record.calculate_cost(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name)) * -1
    
                        total_cost_this_year += value_this_year
                        total_cost_last_year += value_last_year
    
                    budget_this_month = 0
                    value_diff_last_year = value_this_year - value_last_year
                    value_diff_budget = 0
    
                    sheet.write(y, 0, report_configuration_line.name, str_format)
                    sheet.write(y, 1, value_this_year, str_format)
                    sheet.write(y, 2, value_last_year, str_format)
                    sheet.write(y, 3, 0, str_format)
                    sheet.write(y, 4, value_diff_last_year, str_format)
                    sheet.write(y, 5, 0, str_format)
    
                    total_cm += value_this_year
                    total_bm += value_last_year
                    total_cy += value_diff_last_year
                    y += 1
                    group_ids.append(report_configuration_line.id)
    
                group_name = (report_type_line.name.upper()).replace(" ", "")
    
                sheet.write(y, 0, 'Jumlah ' + report_type_line.name, jumlah_bottom)
                sheet.write(y, 1, total_cm, jumlah_bottom)
                sheet.write(y, 2, total_bm, jumlah_bottom)
                sheet.write(y, 3, 0, jumlah_bottom)
                sheet.write(y, 4, total_cy, jumlah_bottom)
                sheet.write(y, 5, 0, jumlah_bottom)
                y += 1
                sheet.write(y, 0, ' ', no_total)
                sheet.write(y, 1, ' ', str_format)
                sheet.write(y, 2, ' ', str_format)
                sheet.write(y, 3, ' ', str_format)
                sheet.write(y, 4, ' ', str_format)
                sheet.write(y, 5, ' ', str_format)
                y += 1
    
                if report_type_line.code in ['PNO']:
                    total_income_diff = total_income_this_year - total_income_last_year
                    total_income_diff_budget = 0
                    sheet.write(y, 0, 'Jumlah Arus Kas Dari Aktivitas Operasi & non Operasi', jumlah_bottom)
                    sheet.write(y, 1, total_income_this_year, jumlah_bottom)
                    sheet.write(y, 2, total_income_last_year, jumlah_bottom)
                    sheet.write(y, 3, 0, jumlah_bottom)
                    sheet.write(y, 4, total_income_diff, jumlah_bottom)
                    sheet.write(y, 5, 0, jumlah_bottom)
                    y += 1
                
                if report_type_line.code in ['PLNO']:
                    total_cost_diff = total_cost_this_year - total_cost_last_year
                    total_cost_diff_budget = 0
                    sheet.write(y, 0, 'Jumlah Arus Kas Untuk Kegiatan Operasi & Non  Operasi', jumlah_bottom)
                    sheet.write(y, 1, total_cost_this_year, jumlah_bottom)
                    sheet.write(y, 2, total_cost_last_year, jumlah_bottom)
                    sheet.write(y, 3, 0, jumlah_bottom)
                    sheet.write(y, 4, total_cost_diff, jumlah_bottom)
                    sheet.write(y, 5, 0, jumlah_bottom)
                    y += 1
                    sheet.write(y, 0, ' ', str_format)
                    sheet.write(y, 1, ' ', str_format)
                    sheet.write(y, 2, ' ', str_format)
                    sheet.write(y, 3, ' ', str_format)
                    sheet.write(y, 4, ' ', str_format)
                    sheet.write(y, 5, ' ', str_format)
                    y += 1
    
            sheet.write(y, 0, 'Kenaikan (Penurunan) Bersih kas (I+II+III)', jumlah_bottom)
            sheet.write(y, 1, (total_income_this_year + total_cost_this_year), jumlah_bottom)
            sheet.write(y, 2, (total_income_last_year + total_cost_last_year), jumlah_bottom)
            sheet.write(y, 3, 0, jumlah_bottom)
            sheet.write(y, 4, (total_income_diff + total_cost_diff), jumlah_bottom)
            sheet.write(y, 5, 0, jumlah_bottom)
            y += 1
    
            ending_balance = record.get_last_balance('AL', 'Kas dan Bank')
            sheet.write(y, 0, 'Kas dan Setara Kas pada Awal Periode', jumlah_bottom)
            sheet.write(y, 1, ending_balance, jumlah_bottom)
            sheet.write(y, 2, 0, jumlah_bottom)
            sheet.write(y, 3, 0, jumlah_bottom)
            sheet.write(y, 4, ending_balance, jumlah_bottom)
            sheet.write(y, 5, 0, jumlah_bottom)
            y += 1
    
            sheet.write(y, 0, 'Kas dan Setara Kas pada Akhir Periode', jumlah)
            sheet.write(y, 1, (total_income_this_year + total_cost_this_year + ending_balance), no_format)
            sheet.write(y, 2, (total_income_last_year + total_cost_last_year), no_format)
            sheet.write(y, 3, 0, no_format)
            sheet.write(y, 4, (total_income_diff + total_cost_diff + ending_balance), no_format)
            sheet.write(y, 5, 0, no_format)
            y += 1
    
    
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename

    def export_report_pdf(self):
        for record in self:
            report_type = self.env['pam.report.type'].search([('code', '=', 'LAK')])
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
    
            return self.env.ref('pam_accounting.action_pam_cash_flow_report').report_action(record, data=data)


class PamCashFlowReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_cash_flow_template'
    _template = 'pam_accounting.report_cash_flow_template'

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
