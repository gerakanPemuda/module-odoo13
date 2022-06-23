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


class PamCostBreakdownReport(models.TransientModel):
    _name = 'pam.cost.breakdown.report'
    _inherit = ['pam.cost.breakdown']

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
    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    report_html = fields.Html(string="Perincian Biaya")
    tf = fields.Boolean()

    def create_html_row(self, html, class_name, name, value_this_month=0, budget_this_month=0, value_diff=0, value_until_this_month=0, budget_until_this_month=0, value_until_diff=0):

        html = html + "<tr class='" + class_name + "'>"

        if value_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        if budget_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        if value_diff != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_diff) + "</td>"
        else:
            html = html + "<td></td>"

        html = html + "<td>" + name + "</td>"

        if value_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_until_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        if budget_until_this_month != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(budget_until_this_month) + "</td>"
        else:
            html = html + "<td></td>"

        if value_until_diff != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(value_until_diff) + "</td>"
        else:
            html = html + "<td></td>"

        html = html + "</tr>"

        return html

    def get_data(self):

        # starting div
        html = "<table class='report-table'>"

        html = html + "<tr>"
        html = html + "<th colspan='3'>REALISASI BULAN INI</td>"
        html = html + "<th width='500px' rowspan='2'>URAIAN BIAYA</td>"
        html = html + "<th colspan='3'>REALISASI S/D BULAN INI</td>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th width='300px'>JUMLAH REALISASI</td>"
        html = html + "<th width='300px'>ANGGARAN</td>"
        html = html + "<th width='300px'>+/-</td>"
        html = html + "<th width='300px'>JUMLAH REALISASI</td>"
        html = html + "<th width='300px'>ANGGARAN</td>"
        html = html + "<th width='300px'>+/-</td>"
        html = html + "</tr>"

        report_type = self.env['pam.report.type'].search([('code', '=', 'LPB')])
        report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id)])
        
        current_year_start_date = self.years + '-01-01'
        current_month_start_date = self.years + '-' + self.months+ '-01'
        current_month_end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        before_month_start_date = str(int(self.years) - 1) + '-' + self.months + '-01'
        before_month_end_date = (datetime.strptime(str(int(self.years) - 1) + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        anggaran = 0

        grand_total_realisasi_left = 0
        grand_total_anggaran_left = 0
        grand_total_left = 0
        grand_total_realisasi_right = 0
        grand_total_anggaran_right = 0
        grand_total_right = 0

        for report_type_line in report_type_lines:
            report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
            report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')

            html = self.create_html_row(html, "", "<b>" + report_type_line.name + "</b>", "", "", "", "", "", "")

            group_ids = []

            total_realisasi_left = 0
            total_anggaran_left = 0
            total_left = 0
            total_realisasi_right = 0
            total_anggaran_right = 0
            total_right = 0

            for report_configuration_line in report_configuration_lines:

                value_this_month = self.calculate_cost_breakdown(current_month_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name)
                budget_this_month = 0
                value_diff =  value_this_month - budget_this_month
                value_until_this_month = self.calculate_cost_breakdown(current_year_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name)
                budget_until_this_month = 0
                value_until_diff = value_until_this_month - budget_until_this_month 

                html = self.create_html_row(html, "", report_configuration_line.name, value_this_month, budget_this_month, value_diff, value_until_this_month, budget_until_this_month, value_until_diff)

                total_realisasi_left += value_this_month
                total_anggaran_left += anggaran
                total_left += value_diff
                total_realisasi_right += value_until_this_month
                total_anggaran_right += budget_until_this_month
                total_right += value_until_diff

            html = self.create_html_row(html, "total-cell", "Jumlah " + report_type_line.name, total_realisasi_left, total_anggaran_left, total_left, total_realisasi_right, total_anggaran_right, total_right)

            grand_total_realisasi_left += total_realisasi_left
            grand_total_anggaran_left += total_anggaran_left
            grand_total_left += total_left
            grand_total_realisasi_right += total_realisasi_right
            grand_total_anggaran_right += total_anggaran_right
            grand_total_right += total_right

        html = self.create_html_row(html, "total-cell", "Total Biaya", grand_total_realisasi_left, grand_total_anggaran_left, grand_total_left, grand_total_realisasi_right, grand_total_anggaran_right, grand_total_right)

        html = html + "</table>"

        report = self.env['pam.cost.breakdown.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True
        })

    def create_excel_row(self, sheet, y, col, format_cells, name, value_this_month=0, budget_this_month=0, value_diff=0, value_until_this_month=0, budget_until_this_month=0, value_until_diff=0):

        sheet.write(y, col, value_this_month, format_cells[0])
        col += 1
        sheet.write(y, col, budget_this_month, format_cells[1])
        col += 1
        sheet.write(y, col, value_diff, format_cells[2])
        col += 1
        sheet.write(y, col, name, format_cells[3])
        col += 1
        sheet.write(y, col, value_until_this_month, format_cells[4])
        col += 1
        sheet.write(y, col, budget_until_this_month, format_cells[5])
        col += 1
        sheet.write(y, col, value_until_diff, format_cells[6])
        col += 1

        y = y + 1

        return sheet, y

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN PERINCIAN BIAYA'
            filename = '%s.xlsx' % ('LAPORAN PERINCIAN BIAYA', )
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 11, 'font': 'Tahoma'})
            judul = workbook.add_format({'font_size': 16, 'bold': True})
            payment_date = workbook.add_format({'font_size': 12})
            jalan = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
            bold = workbook.add_format({'bold': True, 'align': 'center'})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1})
            top = workbook.add_format({'top': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'center'})
            right = workbook.add_format({'right': 1})
            center = workbook.add_format({'align': 'center', 'bold': True, 'font': 'Tahoma', 'font_size': 11, 'bg_color': '#ffff66'})
            merge = workbook.add_format({'bold': True, 'border': True, 'align': 'center', 'font': 'Tahoma', 'font_size': 11, 'bg_color': '#b7dee8'})
            header = workbook.add_format({'bold': True, 'border': True, 'align': 'center', 'font': 'Tahoma', 'font_size': 11, 'bg_color': '#ccffcc'})
            center_bottom = workbook.add_format({'align': 'center', 'bottom': 1})
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'right': 1,'left': 1, 'align': 'right'})
            jumlah = workbook.add_format({'right': 1,'left': 1, 'num_format': '#,##0.00'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            str_total = workbook.add_format({'text_wrap': True, 'bold': True, 'border': 1, 'num_format': '#,##0.00'})
            no_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'align': 'center'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            style_bold = {'bold': True}
            style_font = {'font': 'Tahoma'}
            style_size = {'font_size': 11}
            style_bg_color = {'bg_color': 'ffff66'}
            style_border = {'border': True}
            style_border_left = {'left': 1}
            style_border_top = {'top': 1}
            style_border_right = {'right': 1}
            style_border_bottom = {'bottom': 1}
            style_alignment_left = {'align': 'left'}
            style_alignment_center = {'align': 'center'}
            style_alignment_right = {'align': 'right'}
            style_currency_format = {'num_format': '#,##0.00'}
    
            cell_text = {}
            cell_text.update(style_border)
            cell_text.update(style_alignment_center)
            cell_text.update(style_font)
            cell_text.update(style_size)
            cell_text.update(style_bg_color)
            format_cell_text_normal = workbook.add_format(cell_text)
    
            cell_text.update(style_bold)
            cell_text.update(style_font)
            cell_text.update(style_size)
            cell_text.update(style_font)
            cell_text.update(style_size)
            cell_text.update(style_border)
            format_cell_text_bold = workbook.add_format(cell_text)
    
            cell_text.update(style_border_top)
            cell_text.update(style_border_bottom)
            cell_text.update(style_font)
            cell_text.update(style_size)
            cell_text.update(style_border)
            format_cell_text_bold_highlight = workbook.add_format(cell_text)
    
            cell_number = {}
            cell_number.update(style_border_left)
            cell_number.update(style_border_right)
            cell_number.update(style_alignment_center)
            cell_number.update(style_currency_format)
            cell_number.update(style_font)
            cell_number.update(style_size)
            cell_number.update(style_border)
            format_cell_number_normal = workbook.add_format(cell_number)
    
            cell_number.update(style_bold)
            cell_number.update(style_font)
            cell_number.update(style_size)
            cell_number.update(style_border)
            format_cell_number_bold = workbook.add_format(cell_number)
    
            cell_number.update(style_border_top)
            cell_number.update(style_border_bottom)
            cell_number.update(style_font)
            cell_number.update(style_size)
            cell_number.update(style_border)
            format_cell_number_bold_highlight = workbook.add_format(cell_number)
    
            sheet.set_column(7, 0, 25)
            sheet.set_column(7, 1, 25)
            sheet.set_column(7, 2, 25)
            sheet.set_column(7, 3, 50)
            sheet.set_column(7, 4, 25)
            sheet.set_column(7, 5, 25)
            sheet.set_column(7, 6, 25)
            sheet.set_column(7, 7, 25)
            sheet.set_column(7, 8, 25)
            sheet.set_column(7, 9, 25)
            sheet.set_column(7, 10, 25)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','perincian_biaya')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 6, 2, 6,code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 6, 2, 6,' ', bold)
    
            sheet.merge_range(4, 0, 4, 6, 'PDAM TIRTA PAKUAN KOTA BOGOR', center)
            sheet.merge_range(5, 0, 5, 6, 'LAPORAN PERINCIAN BIAYA', center)
            sheet.merge_range(6, 0, 6, 6, 'BULAN : ' + (datetime.strptime(record.months, '%m').strftime("%B")) + ' ' + record.years, center)
    
            sheet.write(7, 6, (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'), title)
    
            sheet.merge_range(8, 0, 8, 2, 'REALISASI BULAN INI', merge)
            sheet.merge_range(9, 0, 10, 0, 'JUMLAH REALISASI', merge)
            sheet.merge_range(9, 1, 10, 1, 'ANGGARAN', header)
            sheet.merge_range(9, 2, 10, 2, ' + / -', merge)
            sheet.merge_range(8, 3, 10, 3,'URAIAN BIAYA', merge) # MIDDLE
            sheet.merge_range(8, 4, 8, 6,'SAMPAI DENGAN BULAN INI', merge)
            sheet.merge_range(9, 4, 10, 4, 'JUMLAH REALISASI', merge)
            sheet.merge_range(9, 5, 10, 5, 'ANGGARAN', merge)
            sheet.merge_range(9, 6, 10, 6, ' + / - ', merge)
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'LPB')])
            report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id)])
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan Excel'
                })
            
            current_year_start_date = record.years + '-01-01'
            current_month_start_date = record.years + '-' + record.months+ '-01'
            current_month_end_date = (datetime.strptime(record.years + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
            before_month_start_date = str(int(record.years) - 1) + '-' + record.months + '-01'
            before_month_end_date = (datetime.strptime(str(int(record.years) - 1) + '-' + record.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
            anggaran = 0
    
            grand_total_realisasi_left = 0
            grand_total_anggaran_left = 0
            grand_total_left = 0
            grand_total_realisasi_right = 0
            grand_total_anggaran_right = 0
            grand_total_right = 0
    
            col = 0
            y = 11
            for report_type_line in report_type_lines:
                report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
                report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')
    
                format_cells = [format_cell_text_normal, format_cell_text_normal, format_cell_text_normal, format_cell_text_normal, format_cell_text_normal, format_cell_text_normal, format_cell_text_normal]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, report_type_line.name, "", "", "", "", "", "")
    
                group_ids = []
    
                total_realisasi_left = 0
                total_anggaran_left = 0
                total_left = 0
                total_realisasi_right = 0
                total_anggaran_right = 0
                total_right = 0
    
                for report_configuration_line in report_configuration_lines:
    
                    value_this_month = record.calculate_cost_breakdown(current_month_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name)
                    budget_this_month = 0
                    value_diff =  value_this_month - budget_this_month
                    value_until_this_month = record.calculate_cost_breakdown(current_year_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name)
                    budget_until_this_month = 0
                    value_until_diff = value_until_this_month - budget_until_this_month 
    
                    format_cells = [format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal, format_cell_number_normal]
                    sheet, y = record.create_excel_row(sheet, y, col, format_cells, report_configuration_line.name, value_this_month, budget_this_month, value_diff, value_until_this_month, budget_until_this_month, value_until_diff)
    
                    total_realisasi_left += value_this_month
                    total_anggaran_left += anggaran
                    total_left += value_diff
                    total_realisasi_right += value_until_this_month
                    total_anggaran_right += budget_until_this_month
                    total_right += value_until_diff
    
                format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
                sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Jumlah " + report_type_line.name, total_realisasi_left, total_anggaran_left, total_left, total_realisasi_right, total_anggaran_right, total_right)
    
                grand_total_realisasi_left += total_realisasi_left
                grand_total_anggaran_left += total_anggaran_left
                grand_total_left += total_left
                grand_total_realisasi_right += total_realisasi_right
                grand_total_anggaran_right += total_anggaran_right
                grand_total_right += total_right
    
            format_cells = [format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight, format_cell_number_bold_highlight]
            sheet, y = record.create_excel_row(sheet, y, col, format_cells, "Total Biaya", grand_total_realisasi_left, grand_total_anggaran_left, grand_total_left, grand_total_realisasi_right, grand_total_anggaran_right, grand_total_right)
    
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','periksa')])
            y += 2
            sheet.write(y, 2, report_type_ttd.name, center)
            y += 1        
            sheet.write(y, 2, report_type_ttd.position, center)        
            y += 3        
            sheet.write(y, 2, report_type_ttd.name_ttd, center)        
    
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
            y -= 4
            sheet.write(y, 4, report_type_ttd.name, center)
            y += 1        
            sheet.write(y, 4, report_type_ttd.position, center)        
            y += 3        
            sheet.write(y, 4, report_type_ttd.name_ttd, center)        
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename

    def export_report_pdf(self):
        for record in self:
            report_type = self.env['pam.report.type'].search([('code', '=', 'LPB')])
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': report_type.name,
                'report_format': 'Laporan PDF'
                })
    
            rpt = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','periksa')])
            name1 = rpt.name
            position1 = rpt.position
            name_ttd1 = rpt.name_ttd
    
            rpt2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
            name2 = rpt2.name
            position2 = rpt2.position
            name_ttd2 = rpt2.name_ttd
    
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
                    'html': record.report_html
                },
            }
    
            return self.env.ref('pam_accounting.action_pam_cost_breakdown_report').report_action(record, data=data)


class PamCostBreakdownReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_cost_breakdown_template'
    _template = 'pam_accounting.report_cost_breakdown_template'

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
            'html': html
        }
