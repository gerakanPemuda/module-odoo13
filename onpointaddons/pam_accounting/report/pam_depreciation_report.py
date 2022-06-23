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


class PamDepreciationReport(models.TransientModel):
    _name = 'pam.depreciation.report'

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

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    report_html = fields.Html(string="Laba Rugi")
    tf = fields.Boolean()

    def calculate_depreciation_line(self, group_pay_id, category_id):
        sql = """
            select coalesce(SUM(c.price)) as price
            from pam_asset a
            inner join pam_asset_line b on a.id = b.asset_id
            inner join pam_asset_detail c on b.id = c.asset_line_id
            inner join (

            select x.id as group_pay_id, x.name as asset_type, y.id as category_id, y.name as group_name, y.sequence, z.coa_id, zz.code as coa_code, zz.name as coa_name
            from pam_asset_group_pay x
            inner join pam_asset_category y on x.id = y.group_pay
            inner join pam_asset_reduction z on y.id = z.category_id
            inner join pam_coa zz on zz.id = z.coa_id


            ) e on e.coa_id = a.coa_id
            where c.months = %s and c.years = %s and e.group_pay_id = %s and e.category_id = %s

            """

        self._cr.execute(sql, (self.months, self.years, group_pay_id, category_id))
        result = self._cr.fetchone()
        price = 0

        if result:
            price = result[0]

        return price

    def calculate_depreciation_detail(self, coa_id):

        sql = """
            select coalesce(SUM(c.price),0) as price
            from pam_asset a
            inner join pam_asset_line b on a.id = b.asset_id
            inner join pam_asset_detail c on b.id = c.asset_line_id
            where c.months = %s and c.years = %s and a.coa_id = %s
            """

        self._cr.execute(sql, (self.months, self.years, coa_id))
        result = self._cr.fetchone()
        price = 0

        if result:
            price = result[0]

        return price

    def calculate_price(self, coa_id):

        sql = """
            select coalesce(SUM(a.price),0) as price
            from pam_asset a
            where a.coa_id = %s
            """

        self._cr.execute(sql, (coa_id,))
        result = self._cr.fetchone()
        price = 0

        if result:
            price = result[0]

        return price

    def create_html_line_row(self, 
        html, 
        class_name, 
        romans,
        asset_category_name, 
        coa_code,
        price=0):

        html = html + "<tr>"
        html = html + "<td width='50px'>" + romans + "</td>"
        html = html + "<td colspan='2'>" + asset_category_name + "</td>"
        html = html + "<td width='100px'>" + coa_code + "</td>"
        html = html + "<td></td>"
        html = html + "<td></td>"
        html = html + "<td></td>"
        html = html + "<td></td>"

        if price == "":
            html = html + "<td></td>"
        else:
            if price == None:
                price = 0

            html = html + "<td>" + '{0:,.2f}'.format(price) + "</td>"

        html = html + "</tr>"

        html = html + "</tr>"

        return html

    def create_html_detail_row(self, 
        html, 
        class_name, 
        no,
        coa_name, 
        coa_code,
        price,
        price_nett=-1):

        html = html + "<tr>"
        html = html + "<td></td>"
        html = html + "<td width='50px'>" + str(no) + "</td>"
        html = html + "<td width='300px'>" + coa_name + "</td>"
        html = html + "<td>" + coa_code + "</td>"
        html = html + "<td>Rp</td>"

        if price == None:
            price = 0

        html = html + "<td>" + '{0:,.2f}'.format(price) + "</td>"
        html = html + "<td>=</td>"

        if price_nett != -1:
            html = html + "<td>" + '{0:,.2f}'.format(price_nett) + "</td>"
        else:
            html = html + "<td>" + '{0:,.2f}'.format(price) + "</td>"

        html = html + "<td></td>"
        html = html + "</tr>"

        return html

    def get_data(self):
        html = ""

        asset_group_pays = self.env['pam.asset.group.pay'].search([('name', '=', 'Aktiva Tetap')])

        for asset_group_pay in asset_group_pays:

            html = html + "<table width='1000px'>"

            html = html + "<tr>"
            html = html + "<td colspan='9'><b>" + asset_group_pay.name + "</b></td>"
            html = html + "</tr>"

            romans = ['I', 'II', 'III', 'IV', 'V', 'VI']
            idx = 0
            asset_categories = self.env['pam.asset.category'].search([('group_pay', '=', asset_group_pay.id)])
            for asset_category in asset_categories:

                price = self.calculate_depreciation_line(asset_group_pay.id, asset_category.id)
                html = self.create_html_line_row(html, "", romans[idx], asset_category.name, asset_category.coa_id_debit.code, price)

                no = 1
                for reduction in asset_category.reduction_ids:
                    
                    price = self.calculate_depreciation_detail(reduction.coa_id.id)
                    html = self.create_html_detail_row(html, "", no, reduction.coa_id.name, reduction.coa_id.code, price)
                    no += 1

                idx += 1

            html = html + "</table>"

        asset_group_pays = self.env['pam.asset.group.pay'].search([('name', '=', 'Amortisasi Tanah')])

        for asset_group_pay in asset_group_pays:

            html = html + "<table width='1000px'>"

            html = html + "<tr>"
            html = html + "<td colspan='9'><b>" + asset_group_pay.name + "</b></td>"
            html = html + "</tr>"

            romans = ['I', 'II', 'III', 'IV', 'V', 'VI']
            idx = 0
            asset_categories = self.env['pam.asset.category'].search([('group_pay', '=', asset_group_pay.id)])
            for asset_category in asset_categories:

                lands = self.env['pam.asset'].search([('category_id', '=', asset_category.id), ('depreciation_id', '!=', False)])

                sub_html = "<table width='100%' style='border:1px solid #000'>"
                sub_html = sub_html + "<tr>"
                sub_html = sub_html + "<td width='50px'  style='border:1px solid #000'><b>No.</b></td>"
                sub_html = sub_html + "<td width='300px' style='border:1px solid #000'><b>Keterangan</b></td>"
                sub_html = sub_html + "<td style='border:1px solid #000'><b>COA</b></td>"
                sub_html = sub_html + "<td style='border:1px solid #000'><b>Rp</b></td>"
                sub_html = sub_html + "<td style='border:1px solid #000'><b>Harga Perolehan</b></td>"
                sub_html = sub_html + "<td style='border:1px solid #000'></td>"
                sub_html = sub_html + "<td style='border:1px solid #000'><b>Tanggal Perolehan</b></td>"
                sub_html = sub_html + "<td style='border:1px solid #000'><b>Disusutkan Sampai</b></td>"
                sub_html = sub_html + "</tr>"

                no = 1
                for land in lands:
                    
                    land_line = self.env['pam.asset.line'].search([('asset_id', '=', land.id), ('years', '=', self.years)])
                    land_detail = self.env['pam.asset.detail'].search([('asset_line_id', '=', land_line.id), ('months', '=', self.months), ('years', '=', self.years)])
                    
                    line_id = []
                    for land_line in land.line_ids:
                        line_id.append(land_line.id)

                    last_land_detail = self.env['pam.asset.detail'].search([('asset_line_id', 'in', line_id), ('price', '>', 0)], order='years desc, months desc', limit=1)
                    html = self.create_html_detail_row(html, "", no, land.name, land.coa_id.code, land.price, land_detail.price)

                    sub_html = sub_html + "<tr>"
                    sub_html = sub_html + "<td style='border:1px solid #000'>" + str(no) + "</td>"
                    sub_html = sub_html + "<td style='border:1px solid #000'>" + land.name + "</td>"
                    sub_html = sub_html + "<td style='border:1px solid #000'>" + land.coa_id.code + "</td>"
                    sub_html = sub_html + "<td style='border:1px solid #000'></td>"
                    sub_html = sub_html + "<td style='border:1px solid #000'>" + '{0:,.2f}'.format(land.price) +"</td>"
                    sub_html = sub_html + "<td style='border:1px solid #000'></td>"
                    sub_html = sub_html + "<td style='border:1px solid #000'>" + dict(land._fields['months'].selection).get(land.months) + " " + land.years + "</td>"
                    sub_html = sub_html + "<td style='border:1px solid #000'>" + dict(land._fields['months'].selection).get(land.months) + " " + last_land_detail.years + "</td>"
                    sub_html = sub_html + "</tr>"

                    no += 1

                idx += 1
                sub_html = sub_html + "</table>"

                price = self.calculate_depreciation_line(asset_group_pay.id, asset_category.id)
                html = self.create_html_line_row(html, "", "", "<b>Amortisasi Tiap Bulan</b>", "", price)

                html = html + "<tr>"
                html = html + "<td></td>"
                html = html + "<td colspan=8'>" + sub_html + "</td>"
                html = html + "</tr>"

            html = html + "</table>"

        asset_group_pays = self.env['pam.asset.group.pay'].search([('name', 'in', ('Properti Investasi', 'Aktiva Tak Berwujud'))])

        for asset_group_pay in asset_group_pays:

            html = html + "<table width='1000px'>"

            html = html + "<tr>"
            html = html + "<td colspan='9'><b>" + asset_group_pay.name + "</b></td>"
            html = html + "</tr>"

            romans = ['I', 'II', 'III', 'IV', 'V', 'VI']
            idx = 0
            asset_categories = self.env['pam.asset.category'].search([('group_pay', '=', asset_group_pay.id)])
            for asset_category in asset_categories:

                monthly_price = self.calculate_depreciation_line(asset_group_pay.id, asset_category.id)
                html = self.create_html_line_row(html, "", romans[idx], asset_category.name, asset_category.coa_id_debit.code, "")

                no = 1
                for reduction in asset_category.reduction_ids:
                    
                    if reduction.coa_id.code in ('14111110', '12120110'):
                        price = self.calculate_price(reduction.coa_id.id)

                        assets = self.env['pam.asset'].search([('coa_id', '=', reduction.coa_id.id), ('depreciation_id', '!=', False)])

                        sub_html = "<table width='100%' style='border:1px solid #000'>"
                        sub_html = sub_html + "<tr>"
                        sub_html = sub_html + "<td width='50px'  style='border:1px solid #000'><b>No.</b></td>"
                        sub_html = sub_html + "<td width='300px' style='border:1px solid #000'><b>Keterangan</b></td>"
                        sub_html = sub_html + "<td style='border:1px solid #000'><b>COA</b></td>"
                        sub_html = sub_html + "<td style='border:1px solid #000'><b>Rp</b></td>"
                        sub_html = sub_html + "<td style='border:1px solid #000'><b>Harga Perolehan</b></td>"
                        sub_html = sub_html + "<td style='border:1px solid #000'></td>"
                        sub_html = sub_html + "<td style='border:1px solid #000'><b>Tanggal Perolehan</b></td>"
                        sub_html = sub_html + "<td style='border:1px solid #000'><b>Disusutkan Sampai</b></td>"
                        sub_html = sub_html + "</tr>"

                        no_sub = 1
                        for asset in assets:
                            
                            line_id = []
                            for asset_line in asset.line_ids:
                                line_id.append(asset_line.id)

                            last_asset_detail = self.env['pam.asset.detail'].search([('asset_line_id', 'in', line_id), ('price', '>', 0)], order='years desc, months desc', limit=1)

                            sub_html = sub_html + "<tr>"
                            sub_html = sub_html + "<td style='border:1px solid #000'>" + str(no_sub) + "</td>"
                            sub_html = sub_html + "<td style='border:1px solid #000'>" + asset.name + "</td>"
                            sub_html = sub_html + "<td style='border:1px solid #000'>" + asset.coa_id.code + "</td>"
                            sub_html = sub_html + "<td style='border:1px solid #000'></td>"
                            sub_html = sub_html + "<td style='border:1px solid #000'>" + '{0:,.2f}'.format(asset.price) +"</td>"
                            sub_html = sub_html + "<td style='border:1px solid #000'></td>"
                            sub_html = sub_html + "<td style='border:1px solid #000'>" + dict(asset._fields['months'].selection).get(asset.months) + " " + asset.years + "</td>"
                            sub_html = sub_html + "<td style='border:1px solid #000'>" + dict(asset._fields['months'].selection).get(asset.months) + " " + last_asset_detail.years + "</td>"
                            sub_html = sub_html + "</tr>"

                            no_sub += 1

                        idx += 1
                        sub_html = sub_html + "</table>"

                    else:
                        if reduction.coa_id.code == '14121110':
                            reduction_coa = self.env['pam.coa'].search([('code', '=', '14111110')])
                        elif reduction.coa_id.code == '12121220':
                            reduction_coa = self.env['pam.coa'].search([('code', '=', '12120110')])

                        price = self.calculate_depreciation_detail(reduction_coa.id)
                    
                    html = self.create_html_detail_row(html, "", no, reduction.coa_id.name, reduction.coa_id.code, price)
                    no += 1

                html = self.create_html_line_row(html, "", "", "<b>Penyusutan Tiap Bulan</b>", "", monthly_price)

                html = html + "<tr>"
                html = html + "<td></td>"
                html = html + "<td colspan=8'>" + sub_html + "</td>"
                html = html + "</tr>"
                
                idx += 1

            html = html + "</table>"

        report = self.env['pam.depreciation.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': html,
            'tf': True,
        })

    def create_excel_line_row(self, sheet, y, col, format_cells, 
        romans,
        asset_category_name, 
        coa_code,
        price=0):

        sheet.write(y, col, romans, format_cells[0])
        col += 1
        sheet.write(y, col, asset_category_name, format_cells[1])
        col += 2
        sheet.write(y, col, coa_code, format_cells[2])
        col += 5

        if price == "":
            sheet.write(y, col, "", format_cells[3])
        else:
            if price == None:
                price = 0

            sheet.write(y, col, price, format_cells[3])

        y = y + 1

        return sheet, y

    def create_excel_detail_row(self, sheet, y, col, format_cells, 
        no,
        coa_name, 
        coa_code,
        price,
        price_nett=-1):

        if price == None:
            price = 0

        sheet.write(y, col, "", format_cells[0])
        col += 1
        sheet.write(y, col, str(no), format_cells[0])
        col += 1
        sheet.write(y, col, coa_name, format_cells[1])
        col += 1
        sheet.write(y, col, coa_code, format_cells[2])
        col += 1
        sheet.write(y, col, "Rp", format_cells[0])
        col += 1
        sheet.write(y, col, price, format_cells[3])
        col += 1
        sheet.write_string(y, col, "=", format_cells[0])
        col += 1

        if price_nett != -1:
            sheet.write(y, col, price_nett, format_cells[4])
        else:
            sheet.write(y, col, price, format_cells[4])

        col += 1
        sheet.write(y, col, "", format_cells[0])

        y += 1

        return sheet, y

    def create_excel_sub_header_row(self, sheet, y, col, format_cells):
        sheet.write(y, col, "No", format_cells[0])
        col += 1
        sheet.write(y, col, "Keterangan", format_cells[0])
        col += 1
        sheet.write(y, col, "COA", format_cells[1])
        col += 1
        sheet.write(y, col, "Rp", format_cells[0])
        col += 1
        sheet.write(y, col, "Harga Perolehan", format_cells[0])
        col += 1
        sheet.write(y, col, "", format_cells[0])
        col += 1
        sheet.write(y, col, "Tanggal Perolehan", format_cells[0])
        col += 1
        sheet.write(y, col, "Disusutkan Sampai", format_cells[0])

        y += 1

        return sheet, y

    def create_excel_sub_detail_row(self, sheet, y, col, format_cells, 
        no,
        name, 
        coa_code,
        price,
        start_date,
        end_date):

        if price == None:
            price = 0

        sheet.write(y, col, "", format_cells[0])
        col += 1
        sheet.write(y, col, str(no), format_cells[1])
        col += 1
        sheet.write(y, col, name, format_cells[2])
        col += 1
        sheet.write(y, col, coa_code, format_cells[3])
        col += 1
        sheet.write(y, col, "", format_cells[0])
        col += 1
        sheet.write(y, col, price, format_cells[4])
        col += 1
        sheet.write_string(y, col, "", format_cells[0])
        col += 1
        sheet.write_string(y, col, start_date, format_cells[5])
        col += 1
        sheet.write(y, col, end_date, format_cells[6])

        y += 1

        return sheet, y

    def create_excel_journal(self, sheet, y, col, format_cells, journal_debits, journal_credits):
        col_name = col
        col_coa = col + 1
        col_debit = col + 2
        col_credit = col + 3

        company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        logo = BytesIO(base64.b64decode(company.logo))

        sheet.insert_image(y, col_name, 'logo.jpg', {'image_data' : logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})

        sheet.merge_range(y, col_name, y, col_credit, "JURNAL UMUM", format_cells[0])
        y += 3
        sheet.write(y, col_credit, "Nomor :    / JU / " + self.months + " / " + self.years, format_cells[1])
        y += 1
        sheet.write(y, col_credit, "Tanggal :    / " + dict(self._fields['months'].selection).get(self.months) + " " + self.years, format_cells[1])
        y += 2

        sheet.merge_range(y, col_name, y+1, col_name, "NAMA PERKIRAAN", format_cells[2])
        sheet.merge_range(y, col_coa, y+1, col_coa, "KODE PERKIRAAN", format_cells[2])
        sheet.merge_range(y, col_debit, y, col_credit, "JUMLAH", format_cells[2])
        y += 1
        sheet.write(y, col_debit, "DEBET", format_cells[2])
        sheet.write(y, col_credit, "KREDIT", format_cells[2])
        y += 1

        for journal_debit in journal_debits:
            sheet.write(y, col_name, journal_debit[0], format_cells[3])
            sheet.write(y, col_coa, journal_debit[1], format_cells[4])
            sheet.write(y, col_debit, journal_debit[2], format_cells[5])
            sheet.write(y, col_credit, "", format_cells[5])
            y += 1

        for journal_credit in journal_credits:
            sheet.write(y, col_name, "    " + journal_credit[0], format_cells[3])
            sheet.write(y, col_coa, journal_credit[1], format_cells[4])
            sheet.write(y, col_debit, "", format_cells[5])
            sheet.write(y, col_credit, journal_credit[3], format_cells[5])
            y += 1

        sheet.write(y, col_name, "", format_cells[3])
        sheet.write(y, col_coa, "", format_cells[4])
        sheet.write(y, col_debit, "", format_cells[5])
        sheet.write(y, col_credit, "", format_cells[5])
        y += 1

        sheet.write(y, col_name, "", format_cells[3])
        sheet.write(y, col_coa, "", format_cells[4])
        sheet.write(y, col_debit, "", format_cells[5])
        sheet.write(y, col_credit, "", format_cells[5])
        y += 1

        sheet.merge_range(y, col_name, y, col_credit, "Penjelasan : Biaya Penyusutan per " + dict(self._fields['months'].selection).get(self.months) + " " + self.years, format_cells[3])

        y += 2

        sheet.merge_range(y, col_name, y, col_credit, "Dibukukan oleh,          Dibuat oleh,            Diperiksa oleh,         Disetujui oleh, " + dict(self._fields['months'].selection).get(self.months) + " " + self.years, format_cells[4])
        y += 3
        sheet.merge_range(y, col_name, y, col_credit, "_______________          ____________            _______________         _______________ " + dict(self._fields['months'].selection).get(self.months) + " " + self.years, format_cells[4])

        return sheet

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN LABA RUGI'
            filename = '%s.xlsx' % ('Laporan Penyusutan',)

            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Laporan Penyusutan',
                'report_format': 'Laporan Excel'
            })

            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 14, 'bold': True})
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
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'right': 1, 'left': 1, 'align': 'right'})
            jumlah = workbook.add_format({'right': 1, 'left': 1, 'num_format': '#,##0.00'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            str_total = workbook.add_format(
                {'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
            no_total = workbook.add_format({'text_wrap': True, 'bold': True, 'top': 1, 'bottom': 1, 'align': 'center'})
            footer = workbook.add_format(
                {'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1,
                 'left': 1})

            style_bold = {'bold': True}
            style_border_left = {'left': 1}
            style_border_top = {'top': 1}
            style_border_right = {'right': 1}
            style_border_bottom = {'bottom': 1}
            style_alignment_left = {'align': 'left'}
            style_alignment_center = {'align': 'center'}
            style_alignment_right = {'align': 'right'}
            style_currency_format = {'num_format': '#,##0.00'}
            style_backrgound_gray = {'bg_color': '#BFBFBF'}
            font_title = {'font_size': 16}

            cell_text = {}
            cell_text.update(style_alignment_center)
            cell_text.update(style_bold)
            format_cell_text_center_bold = workbook.add_format(cell_text)

            cell_text = {}
            cell_text.update(style_alignment_center)
            format_cell_text_center_normal = workbook.add_format(cell_text)

            cell_text = {}
            # cell_text.update(style_border_left)
            # cell_text.update(style_border_right)
            cell_text.update(style_alignment_left)

            format_cell_text_normal = workbook.add_format(cell_text)

            cell_text.update(style_bold)
            format_cell_text_bold = workbook.add_format(cell_text)

            # cell_text.update(style_border_top)
            # cell_text.update(style_border_bottom)
            cell_text.update(style_backrgound_gray)
            format_cell_text_bold_highlight = workbook.add_format(cell_text)

            cell_number = {}
            # cell_number.update(style_border_left)
            # cell_number.update(style_border_right)
            cell_number.update(style_alignment_right)
            cell_number.update(style_currency_format)
            format_cell_number_normal = workbook.add_format(cell_number)

            cell_number.update(style_bold)
            format_cell_number_bold = workbook.add_format(cell_number)

            # cell_number.update(style_border_top)
            # cell_number.update(style_border_bottom)
            cell_number.update(style_backrgound_gray)
            format_cell_number_bold_highlight = workbook.add_format(cell_number)

            cell_text = {}
            cell_text.update(font_title)
            cell_number.update(style_bold)
            cell_text.update(style_alignment_center)

            format_cell_title_bold = workbook.add_format(cell_text)

            cell_text = {}
            cell_text.update(style_border_top)
            cell_text.update(style_border_bottom)
            cell_text.update(style_border_left)
            cell_text.update(style_border_right)
            cell_text.update(style_bold)
            cell_text.update(style_alignment_center)

            format_cell_header_bold = workbook.add_format(cell_text)

            cell_text = {}
            cell_text.update(style_border_left)
            cell_text.update(style_border_right)
            cell_text.update(style_alignment_left)

            format_cell_content_text = workbook.add_format(cell_text)

            cell_text = {}
            cell_text.update(style_border_left)
            cell_text.update(style_border_right)
            cell_text.update(style_alignment_center)

            format_cell_content_text_center = workbook.add_format(cell_text)

            cell_number = {}
            cell_number.update(style_border_left)
            cell_number.update(style_border_right)
            cell_number.update(style_alignment_right)
            cell_number.update(style_currency_format)
            format_cell_content_number = workbook.add_format(cell_number)

            sheet.set_column(0, 0, 4)
            sheet.set_column(1, 1, 4)
            sheet.set_column(2, 2, 40)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 4, 4)
            sheet.set_column(5, 5, 25)
            sheet.set_column(6, 6, 4)
            sheet.set_column(7, 7, 25)
            sheet.set_column(8, 8, 25)
            sheet.set_column(9, 9, 10)
            sheet.set_column(10, 10, 60)
            sheet.set_column(11, 11, 15)
            sheet.set_column(12, 13, 25)

            code_iso = self.env['pam.code.iso'].search([('name', '=', 'laporan_penyusutan')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 12, 2, 12, code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 12, 2, 12, ' ', judul)

            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))

            sheet.insert_image(0, 1, 'logo.jpg', {'image_data': logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})

            y = 4
            col = 0

            asset_group_pays = self.env['pam.asset.group.pay'].search([('name', '=', 'Aktiva Tetap')])

            format_cells_line = [format_cell_text_bold, format_cell_text_bold, format_cell_text_center_bold,
                                 format_cell_number_normal]
            format_cells_detail = [format_cell_text_normal, format_cell_text_normal, format_cell_text_center_normal,
                                   format_cell_number_normal, format_cell_number_normal, format_cell_number_normal,
                                   format_cell_number_normal]
            format_cells_journal = [format_cell_title_bold, format_cell_text_normal, format_cell_header_bold,
                                    format_cell_content_text, format_cell_content_text_center,
                                    format_cell_content_number]

            journal_start_row = y
            journal_start_col = 10

            for asset_group_pay in asset_group_pays:

                sheet.merge_range(y, 0, y, 9, 'BIAYA PENYUSUTAN ' + (asset_group_pay.name).upper(),
                                  format_cell_title_bold)
                y += 1
                sheet.merge_range(y, 0, y, 9, 'BULAN : ' + (
                    datetime.strptime(record.months, '%m').strftime("%B")).upper() + ' ' + record.years,
                                  format_cell_title_bold)
                y += 2

                romans = ['I', 'II', 'III', 'IV', 'V', 'VI']
                idx = 0
                asset_categories = self.env['pam.asset.category'].search([('group_pay', '=', asset_group_pay.id)])
                journal_debits = []
                journal_credits = []
                for asset_category in asset_categories:

                    price = record.calculate_depreciation_line(asset_group_pay.id, asset_category.id)
                    sheet, y = record.create_excel_line_row(sheet, y, col, format_cells_line, romans[idx],
                                                            asset_category.name, asset_category.coa_id_debit.code,
                                                            price)

                    journal_debit = ['Biaya Penyusutan ' + asset_category.name, asset_category.coa_id_debit.code, price,
                                     0]
                    journal_credit = ['Akumulasi Penyusutan ' + asset_category.name, asset_category.coa_id_credit.code,
                                      0, price]
                    journal_debits.append(journal_debit)
                    journal_credits.append(journal_credit)

                    no = 1
                    for reduction in asset_category.reduction_ids:
                        price = record.calculate_depreciation_detail(reduction.coa_id.id)
                        sheet, y = record.create_excel_detail_row(sheet, y, col, format_cells_detail, no,
                                                                  reduction.coa_id.name, reduction.coa_id.code, price)
                        no += 1

                    idx += 1

            y += 4

            sheet = record.create_excel_journal(sheet, journal_start_row, journal_start_col, format_cells_journal,
                                                journal_debits, journal_credits)

            asset_group_pays = self.env['pam.asset.group.pay'].search([('name', '=', 'Amortisasi Tanah')])

            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))

            sheet.insert_image(y, 1, 'logo.jpg', {'image_data': logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})

            journal_start_row = y
            journal_start_col = 10

            for asset_group_pay in asset_group_pays:

                sheet.merge_range(y, 0, y, 9, 'BIAYA PENYUSUTAN ' + (asset_group_pay.name).upper(),
                                  format_cell_title_bold)
                y += 1
                sheet.merge_range(y, 0, y, 9, 'BULAN : ' + (
                    datetime.strptime(record.months, '%m').strftime("%B")).upper() + ' ' + record.years,
                                  format_cell_title_bold)
                y += 2

                romans = ['I', 'II', 'III', 'IV', 'V', 'VI']
                idx = 0
                asset_categories = self.env['pam.asset.category'].search([('group_pay', '=', asset_group_pay.id)])
                for asset_category in asset_categories:

                    lands = self.env['pam.asset'].search(
                        [('category_id', '=', asset_category.id), ('depreciation_id', '!=', False)])

                    no = 1
                    for land in lands:

                        land_line = self.env['pam.asset.line'].search(
                            [('asset_id', '=', land.id), ('years', '=', record.years)])
                        land_detail = self.env['pam.asset.detail'].search(
                            [('asset_line_id', '=', land_line.id), ('months', '=', record.months),
                             ('years', '=', record.years)])

                        line_id = []
                        for land_line in land.line_ids:
                            line_id.append(land_line.id)

                        last_land_detail = self.env['pam.asset.detail'].search(
                            [('asset_line_id', 'in', line_id), ('price', '>', 0)], order='years desc, months desc',
                            limit=1)
                        sheet, y = record.create_excel_detail_row(sheet, y, col, format_cells_detail, no, land.name,
                                                                  land.coa_id.code, land.price, land_detail.price)

                        no += 1

                    idx += 1

                    price = record.calculate_depreciation_line(asset_group_pay.id, asset_category.id)
                    sheet, y = record.create_excel_line_row(sheet, y, col, format_cells_line, "",
                                                            "Amortisasi Tiap Bulan", "", price)

                    journal_debits = []
                    journal_credits = []

                    journal_debit = ['Biaya Penyusutan Sumber Air', '41131110', 682411.60, 0]
                    journal_debits.append(journal_debit)
                    journal_debit = ['Biaya Penyusutan Instalasi Trans. Distr.', '41131110', 31916.67, 0]
                    journal_debits.append(journal_debit)

                    journal_credit = ['Amortisasi Beban Tangguhan Hak Atas Tanah', '12121190', 0, price]
                    journal_credits.append(journal_credit)

                    y += 2

                    sheet, y = record.create_excel_sub_header_row(sheet, y, 1, format_cells_line)

                    no = 1
                    for land in lands:

                        land_line = self.env['pam.asset.line'].search(
                            [('asset_id', '=', land.id), ('years', '=', record.years)])
                        land_detail = self.env['pam.asset.detail'].search(
                            [('asset_line_id', '=', land_line.id), ('months', '=', record.months),
                             ('years', '=', record.years)])

                        line_id = []
                        for land_line in land.line_ids:
                            line_id.append(land_line.id)

                        last_land_detail = self.env['pam.asset.detail'].search(
                            [('asset_line_id', 'in', line_id), ('price', '>', 0)], order='years desc, months desc',
                            limit=1)

                        sheet, y = record.create_excel_sub_detail_row(sheet, y, col, format_cells_detail, no, land.name,
                                                                      land.coa_id.code, land.price,
                                                                      dict(land._fields['months'].selection).get(
                                                                          land.months) + " " + land.years,
                                                                      dict(land._fields['months'].selection).get(
                                                                          land.months) + " " + last_land_detail.years)

                        no += 1

                    idx += 1

            sheet = record.create_excel_journal(sheet, journal_start_row, journal_start_col, format_cells_journal,
                                                journal_debits, journal_credits)

            y += 4

            asset_group_pays = self.env['pam.asset.group.pay'].search(
                [('name', 'in', ('Properti Investasi', 'Aktiva Tak Berwujud'))])

            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))

            sheet.insert_image(y, 1, 'logo.jpg', {'image_data': logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})

            for asset_group_pay in asset_group_pays:

                journal_start_row = y
                journal_start_col = 10

                sheet.merge_range(y, 0, y, 9, 'BIAYA PENYUSUTAN ' + (asset_group_pay.name).upper(),
                                  format_cell_title_bold)
                y += 1
                sheet.merge_range(y, 0, y, 9, 'BULAN : ' + (
                    datetime.strptime(record.months, '%m').strftime("%B")).upper() + ' ' + record.years,
                                  format_cell_title_bold)
                y += 2

                romans = ['I', 'II', 'III', 'IV', 'V', 'VI']
                idx = 0
                asset_categories = self.env['pam.asset.category'].search([('group_pay', '=', asset_group_pay.id)])

                journal_debits = []
                journal_credits = []

                for asset_category in asset_categories:

                    monthly_price = record.calculate_depreciation_line(asset_group_pay.id, asset_category.id)
                    sheet, y = record.create_excel_line_row(sheet, y, col, format_cells_line, romans[idx],
                                                            asset_category.name, asset_category.coa_id_debit.code, "")

                    journal_debit = ['Biaya Penyusutan ' + asset_category.name, asset_category.coa_id_debit.code,
                                     monthly_price, 0]
                    journal_debits.append(journal_debit)

                    journal_credit = ['Akumulasi Penyusutan ' + asset_category.name, asset_category.coa_id_credit.code,
                                      0, monthly_price]
                    journal_credits.append(journal_credit)

                    no = 1
                    for reduction in asset_category.reduction_ids:

                        if reduction.coa_id.code in ('14111110', '12120110'):
                            price = record.calculate_price(reduction.coa_id.id)

                            assets = self.env['pam.asset'].search(
                                [('coa_id', '=', reduction.coa_id.id), ('depreciation_id', '!=', False)])

                            no_sub = 1
                            for asset in assets:

                                line_id = []
                                for asset_line in asset.line_ids:
                                    line_id.append(asset_line.id)

                                last_asset_detail = self.env['pam.asset.detail'].search(
                                    [('asset_line_id', 'in', line_id), ('price', '>', 0)],
                                    order='years desc, months desc', limit=1)

                            idx += 1

                        else:
                            if reduction.coa_id.code == '14121110':
                                reduction_coa = self.env['pam.coa'].search([('code', '=', '14111110')])
                            elif reduction.coa_id.code == '12121220':
                                reduction_coa = self.env['pam.coa'].search([('code', '=', '12120110')])

                            price = record.calculate_depreciation_detail(reduction_coa.id)

                        sheet, y = record.create_excel_detail_row(sheet, y, col, format_cells_detail, no,
                                                                  reduction.coa_id.name, reduction.coa_id.code, price)
                        no += 1

                    sheet, y = record.create_excel_line_row(sheet, y, col, format_cells_line, "",
                                                            "Penyusutan Tiap Bulan", "", monthly_price)

                    idx += 1

                    y += 2

                    sheet, y = record.create_excel_sub_header_row(sheet, y, 1, format_cells_line)

                    for reduction in asset_category.reduction_ids:

                        if reduction.coa_id.code in ('14111110', '12120110'):
                            price = record.calculate_price(reduction.coa_id.id)

                            assets = self.env['pam.asset'].search(
                                [('coa_id', '=', reduction.coa_id.id), ('depreciation_id', '!=', False)])

                            no_sub = 1
                            for asset in assets:

                                line_id = []
                                for asset_line in asset.line_ids:
                                    line_id.append(asset_line.id)

                                last_asset_detail = self.env['pam.asset.detail'].search(
                                    [('asset_line_id', 'in', line_id), ('price', '>', 0)],
                                    order='years desc, months desc', limit=1)

                                sheet, y = record.create_excel_sub_detail_row(sheet, y, col, format_cells_detail,
                                                                              no_sub, asset.name, asset.coa_id.code,
                                                                              asset.price, dict(
                                        asset._fields['months'].selection).get(asset.months) + " " + land.years, dict(
                                        asset._fields['months'].selection).get(
                                        asset.months) + " " + last_asset_detail.years)

                                no_sub += 1

                            idx += 1

                    idx += 1

                sheet = record.create_excel_journal(sheet, journal_start_row, journal_start_col, format_cells_journal,
                                                    journal_debits, journal_credits)

                y += 10

            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename

    def export_report_pdf(self):
        for record in self:
            # asset_group_pays = self.env['pam.asset.group.pay'].search([])
            # # for asset_group_pay in asset_group_pays:
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Laporan Penyusutan',
                'report_format': 'Laporan PDF'
                })
    
            data = {
                'ids': record.ids,
                'model': record._name,
                'form': {
                    # 'asset_group_pays': asset_group_pays,
                    'months': record.months,
                    'years': record.years,
                    'datetime_cetak': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                    'html': record.report_html
                },
            }
    
            return self.env.ref('pam_accounting.action_pam_depreciation_report').report_action(record, data=data)


class PamDepreciationReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_depreciation_template'
    _template = 'pam_accounting.report_depreciation_template'

    @api.model
    def get_report_values(self, docids, data=None):
        # asset_group_pays = data['form']['asset_group_pays']
        months = data['form']['months']
        years = data['form']['years']
        datetime_cetak = data['form']['datetime_cetak']
        html = data['form']['html']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            # 'asset_group_pays': asset_group_pays,
            'months': months,
            'years': years,
            'datetime_cetak': datetime_cetak,
            'html': html
        }
