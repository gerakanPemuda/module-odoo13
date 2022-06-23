import xlsxwriter
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from io import StringIO, BytesIO
from xlsxwriter.utility import xl_rowcol_to_cell
from PIL import Image


class PamAssetRecapReport(models.TransientModel):
    _name = 'pam.asset.recap.report'

    def _default_year(self):
        return str(datetime.today().year)

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
    years = fields.Char(string='Tahun', default=_default_year, required=True)

    report_html = fields.Html(string="Akumulasi Penyusutan Aset Tetap")
    report_land_html = fields.Html(string="Reklasifikasi Nilai Tanah Yang Dibatasi Nilai Pemakaiannya")
    report_property_html = fields.Html(string="Bangunan Properti Investasi (Bangunan ATM)")
    report_software_html = fields.Html(string="Aktiva Tidak Berwujud (Software)")

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    tf = fields.Boolean()

    def _record(self):
    # def _record(self, asset_category_id):
        sql = """
            select
                aaaa.category_id,
                aaaa.coa_id,
                aaaa.name,
                aaaa.code,
                aaaa.price,
                aaaa.price_audit,
                aaaa.price_add,
                aaaa.price_subtract,
                aaaa.price_nett,
                aaaa.before_depreciation,
                aaaa.current_price_add,
                aaaa.current_price_subtract,
                aaaa.transfer_depreciation,
                (aaaa.before_depreciation + aaaa.current_price_add) - aaaa.current_price_subtract as current_depreciation,
                aaaa.price_nett - ((aaaa.before_depreciation + aaaa.current_price_add) - aaaa.current_price_subtract) as nett_depreciation,
                aaaa.sequence
            from
                (select
                    aaa.category_id,
                    aaa.coa_id,
                    aaa.name,
                    aaa.code,
                    aaa.price,
                    aaa.price_audit,
                    aaa.price_add,
                    aaa.price_subtract,
                    (aaa.price_audit + aaa.price_add) - aaa.price_subtract as price_nett,
                    coalesce((
                        select 
                            sum(x.price)
                        from 
                            pam_asset as z,
                            pam_asset_line as y,
                            pam_asset_detail as x
                        where 
                            z.coa_id = aaa.coa_id
                            and z.id = y.asset_id
                            and y.id = x.asset_line_id
                            and concat(x.years, x.months) <= concat(cast((cast(%s as integer) - 1) as varchar), %s)
                        group by
                            z.coa_id),0) as before_depreciation,
                    coalesce((
                        select 
                            sum(x.price)
                        from 
                            pam_asset as z,
                            pam_asset_line as y,
                            pam_asset_detail as x
                        where 
                            z.coa_id = aaa.coa_id
                            and z.id = y.asset_id
                            and y.id = x.asset_line_id
                            and concat(x.years, x.months) >= concat(%s, '01')
                            and concat(x.years, x.months) <= concat(%s, %s)
                        group by
                            z.coa_id),0) as current_price_add,
                    0 as current_price_subtract,
                    '' as transfer_depreciation,
                    aaa.sequence
                from
                    (select
                        aa.category_id,
                        bb.id as coa_id,
                        bb.name,
                        bb.code,
                        coalesce((
                            select 
                                sum(z.price)
                            from 
                                pam_asset as z 
                            where 
                                z.coa_id = bb.id
                                and concat(z.years, z.get_month) <= concat(cast((cast(%s as integer) - 1) as varchar), '12')
                            group by
                                z.coa_id),0) as price,
                        coalesce((
                            select 
                                sum(z.price)
                            from 
                                pam_asset as z 
                            where 
                                z.coa_id = bb.id
                                and concat(z.years, z.get_month) <= concat(cast((cast(%s as integer) - 1) as varchar), '12')
                            group by
                                z.coa_id),0) as price_audit,
                        coalesce((
                            select 
                                sum(z.price)
                            from 
                                pam_asset as z 
                            where 
                                z.coa_id = bb.id
                                and concat(z.years, z.get_month) >= concat(%s, '01')
                                and concat(z.years, z.get_month) <= concat(%s, %s)
                            group by
                                z.coa_id),0) as price_add,
                        coalesce((
                            select 
                                sum(z.price_subtract)
                            from 
                                pam_asset as z 
                            where 
                                z.coa_id = bb.id
                                and concat(z.years, z.get_month) >= concat(%s, '01')
                                and concat(z.years, z.get_month) <= concat(%s, %s)
                            group by
                                z.coa_id),0) as price_subtract,
                        aa.sequence
                    from
                        (select
                            b.id as category_id,
                            a.coa_id,
                            b.sequence
                        from
                            pam_asset as a,
                            pam_asset_category as b
                        where
                            a.category_id = b.id
                            and concat(a.years, a.get_month) <= concat(%s, %s)
                        group by
                            b.id, a.coa_id, b.sequence
                        ) as aa,
                        pam_coa as bb
                where
                    aa.coa_id = bb.id) as aaa) as aaaa
            order by
                aaaa.sequence asc
            """

        self._cr.execute(sql, (
            self.years,
            self.months,
            self.years,
            self.years,
            self.months,
            self.years,
            self.years,
            self.years,
            self.years,
            self.months,
            self.years,
            self.years,
            self.months,
            # asset_category_id,
            self.years,
            self.months,
        ))
        result = self._cr.fetchall()

        return result

    def make_row(self, datas):
        # if datas[1] == 'II':
            # raise ValidationError(_("%s")%(str(datas[0])))
        y = datas[0]
        sheet = datas[4]
        center = datas[5]
        left = datas[6]
        currency_format = datas[7]
        str_footer = datas[8]
        currency_footer = datas[9]

        sheet.write(y, 0, datas[1], center)
        sheet.write(y, 1, datas[3], left)
        sheet.write(y, 2, '', left)
        sheet.write(y, 3, '', currency_format)
        sheet.write(y, 4, '', currency_format)
        sheet.write(y, 5, '', currency_format)
        sheet.write(y, 6, '', currency_format)
        sheet.write(y, 7, '', currency_format)
        sheet.write(y, 8, '', currency_format)
        sheet.write(y, 9, '', currency_format)
        sheet.write(y, 10, '', currency_format)
        sheet.write(y, 11, '', currency_format)
        sheet.write(y, 12, '', currency_format)
        sheet.write(y, 13, '', currency_format)
        
        y += 1

        no = 1
        start_row = y + 1
        for category_id, coa_id, name, code, price, price_audit, price_add, price_subtract, price_nett, before_depreciation, current_price_add, current_price_subtract, transfer_depreciation, current_depreciation, nett_depreciation, sequence in self._record():
            sheet.write(y, 0, '', left)
            sheet.write(y, 1, str(no) + '. ' + name, left)
            sheet.write(y, 2, code, left)
            sheet.write(y, 3, price, currency_format)
            sheet.write(y, 4, price_audit, currency_format)
            sheet.write(y, 5, price_add, currency_format)
            sheet.write(y, 6, price_subtract, currency_format)
            sheet.write(y, 7, price_nett, currency_format)
            sheet.write(y, 8, before_depreciation, currency_format)
            sheet.write(y, 9, current_price_add, currency_format)
            sheet.write(y, 10, current_price_subtract, currency_format)
            sheet.write(y, 11, transfer_depreciation, currency_format)
            sheet.write(y, 12, current_depreciation, currency_format)
            sheet.write(y, 13, nett_depreciation, currency_format)

            y += 1
            no += 1

        end_row = y
        
        sheet.write(y, 0, '', str_footer)
        sheet.write(y, 1, 'Jumlah ' + datas[3], str_footer)
        sheet.write(y, 2, '', str_footer)
        sheet.write(y, 3, '=SUM(D' + str(start_row) + ':D' + str(end_row) +')', currency_footer)
        sheet.write(y, 4, '=SUM(E' + str(start_row) + ':E' + str(end_row) +')', currency_footer)
        sheet.write(y, 5, '=SUM(F' + str(start_row) + ':F' + str(end_row) +')', currency_footer)
        sheet.write(y, 6, '=SUM(G' + str(start_row) + ':G' + str(end_row) +')', currency_footer)
        sheet.write(y, 7, '=SUM(H' + str(start_row) + ':H' + str(end_row) +')', currency_footer)
        sheet.write(y, 8, '=SUM(I' + str(start_row) + ':I' + str(end_row) +')', currency_footer)
        sheet.write(y, 9, '=SUM(J' + str(start_row) + ':J' + str(end_row) +')', currency_footer)
        sheet.write(y, 10, '=SUM(K' + str(start_row) + ':K' + str(end_row) +')', currency_footer)
        sheet.write(y, 11, '=SUM(L' + str(start_row) + ':L' + str(end_row) +')', currency_footer)
        sheet.write(y, 12, '=SUM(M' + str(start_row) + ':M' + str(end_row) +')', currency_footer)
        sheet.write(y, 13, '=SUM(N' + str(start_row) + ':N' + str(end_row) +')', currency_footer)
            
        y += 1

        return [y, end_row]

    def _create_excel_row(self, 
        sheet,
        y, 
        format_cells,
        name, 
        coa_code, 
        total_price=0, 
        total_price_audit=0, 
        total_price_add=0, 
        total_price_subtract=0, 
        total_price_all=0, 
        total_depreciation_last_year=0, 
        total_depreciation_this_year=0,
        total_depreciation_this_year_subtract=0,
        total_mutation=0,
        total_depreciation=0,
        total_price_depreciation=0
        ):

        left = format_cells[0]
        center = format_cells[1]
        currency_format = format_cells[2]

        sheet.write(y, 1, name, left)
        sheet.write(y, 2, coa_code, left)
        sheet.write(y, 3, total_price, currency_format)
        sheet.write(y, 4, total_price_audit, currency_format)
        sheet.write(y, 5, total_price_add, currency_format)
        sheet.write(y, 6, total_price_subtract, currency_format)
        sheet.write(y, 7, total_price_all, currency_format)
        sheet.write(y, 8, total_depreciation_last_year, currency_format)
        sheet.write(y, 9, total_depreciation_this_year, currency_format)
        sheet.write(y, 10, total_depreciation_this_year_subtract, currency_format)
        sheet.write(y, 11, total_mutation, currency_format)
        sheet.write(y, 12, total_depreciation, currency_format)
        sheet.write(y, 13, total_price_depreciation, currency_format)

        y = y + 1

        return sheet, y

    def _generate_excel(self, workbook, sheet, y, report_type_code, only_depreciation = False):
        title = workbook.add_format({'font_size': 14, 'bold': True, 'align': 'center'})
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        bold_left = workbook.add_format({'bold': True, 'left': 1, 'align': 'center'})
        bold_right = workbook.add_format({'bold': True, 'right':1, 'align': 'center'})
        merge = workbook.add_format({'bold': True, 'border': True})
        header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
        date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
        num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
        bottom_left = workbook.add_format({'bottom': 1, 'left': 1, 'bold': True, 'align': 'center'})
        bottom_right = workbook.add_format({'bottom': 1, 'right': 1, 'bold': True, 'align': 'center'})
        top_left = workbook.add_format({'top': 1, 'left': 1, 'bold': True, 'align': 'center'})
        top_right = workbook.add_format({'top': 1, 'right': 1, 'bold': True, 'align': 'center'})
        top_bottom = workbook.add_format({'border': True, 'bold': True})
        left = workbook.add_format({'left': 1})
        right = workbook.add_format({'right': 1})
        center = workbook.add_format({'align': 'center'})
        str_format = workbook.add_format({'text_wrap': True, 'right': 1, 'left': 1})
        currency_format = workbook.add_format({'text_wrap': True, 'align': 'right', 'num_format': '#,##0.00', 'right': 1, 'left': 1})
        str_footer = workbook.add_format({'bold': True, 'align': 'left', 'top': 1, 'bottom': 1, 'right': 1, 'left': 1})
        currency_footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})

        format_cells = [left, center, currency_format]

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 13, 20)
        
        code_iso = self.env['pam.code.iso'].search([('name','=','aset_tetap')])
        if code_iso:
            wrap_text = workbook.add_format()
            wrap_text.set_text_wrap()
            sheet.merge_range(y, 13, y + 1, 13,code_iso.code_iso, wrap_text)
        else:
            sheet.merge_range(y, 13, y + 1, 13,' ', bold)


        end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%d-%m-%Y")

        company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        logo = BytesIO(base64.b64decode(company.logo))

        sheet.merge_range(y, 0, y, 12, 'PERUSAHAAN DAERAH AIR MINUM', title)
        sheet.insert_image(y, 0, 'logo.jpg', {'image_data' : logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})
        y += 1
        sheet.merge_range(y, 0, y, 12, 'AKUMULASI PENYUSUTAN ASET TETAP PER ' + end_date, title)
        y += 3
        sheet.write(y, 1, 'Saldo Per. ' + end_date)

        y += 1
        sheet.merge_range(y, 0, y + 2, 0, 'No. ', top_bottom)
        sheet.merge_range(y, 1, y + 2, 1, 'U r a i a n', top_bottom)
        sheet.merge_range(y, 2, y + 2, 2, 'Kode', top_bottom)
        sheet.write(y, 3, 'Harga Perolehan', top_right)
        sheet.write(y, 4, 'Harga Perolehan', top_right)
        sheet.merge_range(y, 5, y, 6, 'Mutasi', top_bottom)
        sheet.write(y, 7, 'Harga Perolehan', top_right)
        sheet.write(y, 8, 'Akumulasi Penyusutan', top_right)
        sheet.merge_range(y, 9, y, 10, 'Mutasi Biaya Penyusutan', top_bottom)
        sheet.write(y, 11, 'MUTASI', top_right)
        sheet.write(y, 12, 'Akumulasi Penyusutan', top_right)
        sheet.write(y, 13, 'Nilai Buku', top_right)

        y += 1
        sheet.write(y, 3, 'Per ' + end_date, bold_right)
        sheet.write(y, 4, 'Per ' + end_date, bold_right)
        sheet.write(y, 5, 'Penambahan', bold_right)
        sheet.write(y, 6, 'Pengurangan', bold_right)
        sheet.write(y, 7, 'Per ' + end_date, bold_right)
        sheet.write(y, 8, 's/d tgl ' + end_date, bold_right)
        sheet.write(y, 9, 'Penambahan', bold_right)
        sheet.write(y, 10, 'Pengurangan', bold_right)
        sheet.write(y, 11, 'AKUMULASI', bold_right)
        sheet.write(y, 12, 'Per ' + end_date, bold_right)
        sheet.write(y, 13, 'Per ' + end_date, bold_right)

        y += 1
        sheet.write(y, 3, '(Rp)', bottom_right)
        sheet.write(y, 4, 'Audit(Rp)', bottom_right)
        sheet.write(y, 5, '(Rp)', bottom_right)
        sheet.write(y, 6, '(Rp)', bottom_right)
        sheet.write(y, 7, '(Rp)', bottom_right)
        sheet.write(y, 8, '(Rp)', bottom_right)
        sheet.write(y, 9, '(Rp)', bottom_right)
        sheet.write(y, 10, '(Rp)', bottom_right)
        sheet.write(y, 11, 'PENYUSUTAN', bottom_right)
        sheet.write(y, 12, '(Rp)', bottom_right)
        sheet.write(y, 13, '(Rp)', bottom_right)

        no = 1

        report_type = self.env['pam.report.type'].search([('code', '=', report_type_code)])

        grand_total_price = 0
        grand_total_price_audit = 0
        grand_total_price_add = 0
        grand_total_price_subtract = 0
        grand_total_price_all = 0
        grand_total_depreciation_last_year = 0
        grand_total_depreciation_this_year = 0
        grand_total_depreciation_this_year_subtract = 0
        grand_total_mutation = 0
        grand_total_depreciation = 0
        grand_total_price_depreciation = 0

        y += 1
        for line in report_type.line_ids:

            report_config = self.env['pam.report.configuration'].search([('report_type_id', '=', line.report_id.id)])
            report_config_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_config.id), ('group_id', '=', line.id)])

            count_lines = len(report_config_lines)

            if count_lines == 1:
                count_details = len(report_config_lines.detail_ids)
                if count_details == 1:
                    total_price, total_price_audit, total_price_add, total_price_subtract, total_price_all, total_depreciation_last_year, total_depreciation_this_year, total_depreciation_this_year_subtract, total_mutation, total_depreciation, total_price_depreciation = self._get_row_data(report_config_lines.detail_ids.coa_id.id, only_depreciation)
                    sheet, y = self._create_excel_row(
                                    sheet,
                                    y,
                                    format_cells,
                                    line.name, 
                                    report_config_lines.detail_ids.coa_id.code,
                                    total_price,
                                    total_price_audit,
                                    total_price_add,
                                    total_price_subtract, 
                                    total_price_all, 
                                    total_depreciation_last_year,
                                    total_depreciation_this_year, 
                                    total_depreciation_this_year_subtract, 
                                    total_mutation, 
                                    total_depreciation, 
                                    total_price_depreciation)

                    grand_total_price = grand_total_price + total_price
                    grand_total_price_audit = grand_total_price_audit + total_price_audit
                    grand_total_price_add = grand_total_price_add + total_price_add
                    grand_total_price_subtract = grand_total_price_subtract + total_price_subtract
                    grand_total_price_all = grand_total_price_all + total_price_all
                    grand_total_depreciation_last_year = grand_total_depreciation_last_year + total_depreciation_last_year
                    grand_total_depreciation_this_year = grand_total_depreciation_this_year + total_depreciation_this_year
                    grand_total_depreciation_this_year_subtract = grand_total_depreciation_this_year_subtract + total_depreciation_this_year_subtract
                    grand_total_mutation = grand_total_mutation + total_mutation
                    grand_total_depreciation = grand_total_depreciation + total_depreciation
                    grand_total_price_depreciation = grand_total_price_depreciation + total_price_depreciation


                else:
                    sheet, y = self._create_excel_row(sheet, y, format_cells, line.name, "", "", "", "", "", "", "", "", "", "", "", "")
            else:
                count_details = 0

                sheet, y = self._create_excel_row(sheet, y, format_cells, line.name, "", "", "", "", "", "", "", "", "", "", "", "")

                sum_total_price = 0
                sum_total_price_audit = 0
                sum_total_price_add = 0
                sum_total_price_subtract = 0
                sum_total_price_all = 0
                sum_total_depreciation_last_year = 0
                sum_total_depreciation_this_year = 0
                sum_total_depreciation_this_year_subtract = 0
                sum_total_mutation = 0
                sum_total_depreciation = 0
                sum_total_price_depreciation = 0
                for config_line in report_config_lines:
                    total_price, total_price_audit, total_price_add, total_price_subtract, total_price_all, total_depreciation_last_year, total_depreciation_this_year, total_depreciation_this_year_subtract, total_mutation, total_depreciation, total_price_depreciation = self._get_row_data(config_line.detail_ids.coa_id.id, only_depreciation)
                    sheet, y = self._create_excel_row(
                                    sheet,
                                    y, 
                                    format_cells, 
                                    config_line.name, 
                                    config_line.detail_ids.coa_id.code, 
                                    total_price,
                                    total_price_audit,
                                    total_price_add,
                                    total_price_subtract, 
                                    total_price_all, 
                                    total_depreciation_last_year,
                                    total_depreciation_this_year, 
                                    total_depreciation_this_year_subtract, 
                                    total_mutation, 
                                    total_depreciation, 
                                    total_price_depreciation)

                    sum_total_price = sum_total_price + total_price
                    sum_total_price_audit = sum_total_price_audit + total_price_audit
                    sum_total_price_add = sum_total_price_add + total_price_add
                    sum_total_price_subtract = sum_total_price_subtract + total_price_subtract
                    sum_total_price_all = sum_total_price_all + total_price_all
                    sum_total_depreciation_last_year = sum_total_depreciation_last_year + total_depreciation_last_year
                    sum_total_depreciation_this_year = sum_total_depreciation_this_year + total_depreciation_this_year
                    sum_total_depreciation_this_year_subtract = sum_total_depreciation_this_year_subtract + total_depreciation_this_year_subtract
                    sum_total_mutation = sum_total_mutation + total_mutation
                    sum_total_depreciation = sum_total_depreciation + total_depreciation
                    sum_total_price_depreciation = sum_total_price_depreciation + total_price_depreciation

                sheet, y = self._create_excel_row(
                                sheet,
                                y,
                                format_cells, 
                                line.name, 
                                " ", 
                                sum_total_price,
                                sum_total_price_audit,
                                sum_total_price_add,
                                sum_total_price_subtract, 
                                sum_total_price_all,
                                sum_total_depreciation_last_year,
                                sum_total_depreciation_this_year, 
                                sum_total_depreciation_this_year_subtract, 
                                sum_total_mutation, 
                                sum_total_depreciation, 
                                sum_total_price_depreciation)

                grand_total_price = grand_total_price + sum_total_price
                grand_total_price_audit = grand_total_price_audit + sum_total_price_audit
                grand_total_price_add = grand_total_price_add + sum_total_price_add
                grand_total_price_subtract = grand_total_price_subtract + sum_total_price_subtract
                grand_total_price_all = grand_total_price_all + sum_total_price_all
                grand_total_depreciation_last_year = grand_total_depreciation_last_year + sum_total_depreciation_last_year
                grand_total_depreciation_this_year = grand_total_depreciation_this_year + sum_total_depreciation_this_year
                grand_total_depreciation_this_year_subtract = grand_total_depreciation_this_year_subtract + sum_total_depreciation_this_year_subtract
                grand_total_mutation = grand_total_mutation + sum_total_mutation
                grand_total_depreciation = grand_total_depreciation + sum_total_depreciation
                grand_total_price_depreciation = grand_total_price_depreciation + sum_total_price_depreciation

        sheet, y = self._create_excel_row(
                        sheet,
                        y,
                        format_cells, 
                        "Jumlah", 
                        " ", 
                        grand_total_price,
                        grand_total_price_audit,
                        grand_total_price_add,
                        grand_total_price_subtract, 
                        grand_total_price_all,
                        grand_total_depreciation_last_year,
                        grand_total_depreciation_this_year, 
                        grand_total_depreciation_this_year_subtract, 
                        grand_total_mutation, 
                        grand_total_depreciation, 
                        grand_total_price_depreciation)

        y += 1
        return sheet, y    

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            filename = '%s.xlsx' % ('Rekap Aset Per Bulan',)
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Rekap Aset Per Bulan',
                'report_format': 'Laporan Excel'
                })
            
            sheet = workbook.add_worksheet()
    
            y = 2
    
            sheet, y = record._generate_excel(workbook, sheet, y, 'LAT')
            y += 2
            sheet, y = record._generate_excel(workbook, sheet, y, 'LRNT', True)
            y += 2
            sheet, y = record._generate_excel(workbook, sheet, y, 'LBPI')
            y += 2
            sheet, y = record._generate_excel(workbook, sheet, y, 'LATB')
            y += 2
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename
    
            # report = self.env['pam.asset.recap.report'].search([('id', '=', record.id)])
            # report.update({
            #     'report_html': fix_asset,
            #     'report_land_html' : land_asset,
            #     'report_property_html' : property_asset,
            #     'report_software_html' : software_asset,
            #     'tf': True,
            # })
    
    
            # land = record.make_row([y, 'I', '1', 'Tanah dan Hak Atas Tanah', sheet, center, left, currency_format, str_footer, currency_footer])
            # fount = record.make_row([land[0], 'II', '2', 'Sumber Air', sheet, center, left, currency_format, str_footer, currency_footer])
            # pump = record.make_row([fount[0], 'III', '3', 'Instalasi Perpompaan', sheet, center, left, currency_format, str_footer, currency_footer])
            # ipa = record.make_row([pump[0], 'IV', '4', 'Instalasi Pengolahan Air', sheet, center, left, currency_format, str_footer, currency_footer])
            # transdis = record.make_row([ipa[0], 'V', '5', 'Instalasi Transmisi dan Distribusi', sheet, center, left, currency_format, str_footer, currency_footer])
            # building = record.make_row([transdis[0], 'VI', '6', 'Bangunan dan Gedung', sheet, center, left, currency_format, str_footer, currency_footer])
            # nonwater = record.make_row([building[0], 'VII', '7', 'Instalasi Non Pabrik Air', sheet, center, left, currency_format, str_footer, currency_footer])
            # transportation = record.make_row([nonwater[0], 'VIII', '8', 'Alat Pengangkut-Kendaraan', sheet, center, left, currency_format, str_footer, currency_footer])
            # furniture = record.make_row([transportation[0], 'VIIII', '9', 'Perabotan dan Inventaris Kantor', sheet, center, left, currency_format, str_footer, currency_footer])
            
            # sheet.write(furniture[0], 0, '', str_footer)
            # sheet.write(furniture[0], 1, 'Jumlah', str_footer)
            # sheet.write(furniture[0], 2, '', str_footer)
            # sheet.write(furniture[0], 3, '=(D' + str(land[1]) + '+D' + str(fount[1]) + '+D' + str(pump[1]) + '+D' + str(ipa[1]) + '+D' + str(transdis[1]) + '+D' + str(building[1]) + '+D' + str(nonwater[1]) + '+D' + str(transportation[1]) + '+D' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 4, '=(E' + str(land[1]) + '+E' + str(fount[1]) + '+E' + str(pump[1]) + '+E' + str(ipa[1]) + '+E' + str(transdis[1]) + '+E' + str(building[1]) + '+E' + str(nonwater[1]) + '+E' + str(transportation[1]) + '+E' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 5, '=(F' + str(land[1]) + '+F' + str(fount[1]) + '+F' + str(pump[1]) + '+F' + str(ipa[1]) + '+F' + str(transdis[1]) + '+F' + str(building[1]) + '+F' + str(nonwater[1]) + '+F' + str(transportation[1]) + '+F' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 6, '=(G' + str(land[1]) + '+G' + str(fount[1]) + '+G' + str(pump[1]) + '+G' + str(ipa[1]) + '+G' + str(transdis[1]) + '+G' + str(building[1]) + '+G' + str(nonwater[1]) + '+G' + str(transportation[1]) + '+G' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 7, '=(H' + str(land[1]) + '+H' + str(fount[1]) + '+H' + str(pump[1]) + '+H' + str(ipa[1]) + '+H' + str(transdis[1]) + '+H' + str(building[1]) + '+H' + str(nonwater[1]) + '+H' + str(transportation[1]) + '+H' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 8, '=(I' + str(land[1]) + '+I' + str(fount[1]) + '+I' + str(pump[1]) + '+I' + str(ipa[1]) + '+I' + str(transdis[1]) + '+I' + str(building[1]) + '+I' + str(nonwater[1]) + '+I' + str(transportation[1]) + '+I' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 9, '=(J' + str(land[1]) + '+J' + str(fount[1]) + '+J' + str(pump[1]) + '+J' + str(ipa[1]) + '+J' + str(transdis[1]) + '+J' + str(building[1]) + '+J' + str(nonwater[1]) + '+J' + str(transportation[1]) + '+J' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 10, '=(K' + str(land[1]) + '+K' + str(fount[1]) + '+K' + str(pump[1]) + '+K' + str(ipa[1]) + '+K' + str(transdis[1]) + '+K' + str(building[1]) + '+K' + str(nonwater[1]) + '+K' + str(transportation[1]) + '+K' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 11, '=(L' + str(land[1]) + '+L' + str(fount[1]) + '+L' + str(pump[1]) + '+L' + str(ipa[1]) + '+L' + str(transdis[1]) + '+L' + str(building[1]) + '+L' + str(nonwater[1]) + '+L' + str(transportation[1]) + '+L' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 12, '=(M' + str(land[1]) + '+M' + str(fount[1]) + '+M' + str(pump[1]) + '+M' + str(ipa[1]) + '+M' + str(transdis[1]) + '+M' + str(building[1]) + '+M' + str(nonwater[1]) + '+M' + str(transportation[1]) + '+M' + str(furniture[1]) +')', currency_footer)
            # sheet.write(furniture[0], 13, '=(N' + str(land[1]) + '+N' + str(fount[1]) + '+N' + str(pump[1]) + '+N' + str(ipa[1]) + '+N' + str(transdis[1]) + '+N' + str(building[1]) + '+N' + str(nonwater[1]) + '+N' + str(transportation[1]) + '+N' + str(furniture[1]) +')', currency_footer)

    def _create_report_header(self, html):

        html = html + "<tr>"
        html = html + "<th rowspan='3' width='1000px'>Uraian</th>"
        html = html + "<th rowspan='3' width='100px'>Kode</th>"
        html = html + "<th width='500px'>Harga Perolehan</th>"
        html = html + "<th width='500px'>Harga Perolehan</th>"
        html = html + "<th colspan='2'>Mutasi</th>"
        html = html + "<th width='500px'>Harga Perolehan</th>"
        html = html + "<th width='500px'>Akumlasi Penyusutan</th>"
        html = html + "<th colspan='2'>Mutasi Biaya Penyusutan</th>"
        html = html + "<th width='500px'>Mutasi</th>"
        html = html + "<th width='500px'>Akumlasi Penyusutan</th>"
        html = html + "<th width='500px'>Nilai Buku</th>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th>Per 01 Januari 2019</th>"
        html = html + "<th>Per 01 Januari 2019</th>"
        html = html + "<th>Penambahan</th>"
        html = html + "<th>Pengurangan</th>"
        html = html + "<th>Per 30 Juni 2019</th>"
        html = html + "<th>s/d tgl 31 Des 2018</th>"
        html = html + "<th>Penambahan 2019</th>"
        html = html + "<th>Pengurangan 2019</th>"
        html = html + "<th>Akumulasi</th>"
        html = html + "<th>Per 30 Juni 2019</th>"
        html = html + "<th>Per 30 Juni 2019</th>"
        html = html + "</tr>"

        html = html + "<tr>"
        html = html + "<th>(Rp)</th>"
        html = html + "<th>Audit (Rp)</th>"
        html = html + "<th>(Rp)</th>"
        html = html + "<th>(Rp)</th>"
        html = html + "<th>(Rp)</th>"
        html = html + "<th>(Rp)</th>"
        html = html + "<th>(Rp)</th>"
        html = html + "<th>(Rp)</th>"
        html = html + "<th>Penyusutan</th>"
        html = html + "<th>(Rp)</th>"
        html = html + "<th>(Rp)</th>"
        html = html + "</tr>"

        return html

    def _create_report_row(self, html, row_class, 
        name, 
        coa_code, 
        total_price=0, 
        total_price_audit=0, 
        total_price_add=0, 
        total_price_subtract=0, 
        total_price_all=0, 
        total_depreciation_last_year=0, 
        total_depreciation_this_year=0,
        total_depreciation_this_year_subtract=0,
        total_mutation=0,
        total_depreciation=0,
        total_price_depreciation=0
        ):

        html = html + "<tr class='" + row_class + "'>"
        html = html + "<td>" + name + "</td>"
        html = html + "<td>" + coa_code + "</td>"
        if total_price != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_price) + "</td>"
        else:
            html = html + "<td></td>"

        if total_price_audit != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_price_audit) + "</td>"
        else:
            html = html + "<td></td>"

        if total_price_add != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_price_add) + "</td>"
        else:
            html = html + "<td></td>"

        if total_price_subtract != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_price_subtract) + "</td>"
        else:
            html = html + "<td></td>"

        if total_price_all != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_price_all) + "</td>"
        else:
            html = html + "<td></td>"

        if total_depreciation_last_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_depreciation_last_year) + "</td>"
        else:
            html = html + "<td></td>"

        if total_depreciation_this_year != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_depreciation_this_year) + "</td>"
        else:
            html = html + "<td></td>"

        if total_depreciation_this_year_subtract != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_depreciation_this_year_subtract) + "</td>"
        else:
            html = html + "<td></td>"

        if total_mutation != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_depreciation_this_year_subtract) + "</td>"
        else:
            html = html + "<td></td>"

        if total_depreciation != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_depreciation) + "</td>"
        else:
            html = html + "<td></td>"

        if total_price_depreciation != "":
            html = html + "<td class='number-cell'>" + '{0:,.2f}'.format(total_price_depreciation) + "</td>"
        else:
            html = html + "<td></td>"

        html = html + "</tr>"

        return html

    def _get_asset_depreciation_last_year(self, coa_id):

        sql = """
            select  coalesce(sum(c.price),0) as price
            from pam_asset a
            inner join pam_asset_line b on a.id = b.asset_id
            inner join pam_asset_detail c on b.id = c.asset_line_id
            where a.coa_id = %s and c.years < %s
            """

        self._cr.execute(sql, (coa_id, self.years))
        result = self._cr.fetchone()
        if result:
            return result[0] 
        else:
            return 0

    def _get_asset_depreciation_this_year(self, coa_id):

        sql = """
            select  coalesce(sum(c.price),0) as price
            from pam_asset a
            inner join pam_asset_line b on a.id = b.asset_id
            inner join pam_asset_detail c on b.id = c.asset_line_id
            where a.coa_id = %s and c.months <= %s and c.years = %s
            """

        self._cr.execute(sql, (coa_id, self.months, self.years))
        result = self._cr.fetchone()
        if result:
            return result[0] 
        else:
            return 0

    def _get_row_data(self, coa_id, only_depreciation = False):

        if only_depreciation:
            assets = self.env['pam.asset'].search([('years', '<', self.years), ('coa_id', '=', coa_id), ('depreciation_id', '!=', False)])
            this_year_assets = self.env['pam.asset'].search([('years', '=', self.years), ('coa_id', '=', coa_id), ('depreciation_id', '!=', False)])
        else:
            assets = self.env['pam.asset'].search([('years', '<', self.years), ('coa_id', '=', coa_id)])
            this_year_assets = self.env['pam.asset'].search([('years', '=', self.years), ('coa_id', '=', coa_id)])

        total_price = sum(line.price  for line in assets)
        total_price_audit = sum(line.price  for line in assets)
        total_price_add = sum(line.price_add  for line in this_year_assets)
        total_price_subtract = sum(line.price_subtract  for line in this_year_assets)

        total_price_all = (total_price_audit + total_price_add) - total_price_subtract

        total_depreciation_last_year = self._get_asset_depreciation_last_year(coa_id)
        total_depreciation_this_year = self._get_asset_depreciation_this_year(coa_id)
        total_depreciation_this_year_subtract = 0
        total_mutation = 0
        total_depreciation = (total_depreciation_last_year + total_depreciation_this_year) - total_depreciation_this_year_subtract - total_mutation
        total_price_depreciation = total_price_all - total_depreciation

        return total_price, total_price_audit, total_price_add, total_price_subtract, total_price_all, total_depreciation_last_year, total_depreciation_this_year, total_depreciation_this_year_subtract, total_mutation, total_depreciation, total_price_depreciation

    def _generate_html(self, report_type_code, only_depreciation = False):

        html = "<div style='overflow:auto; width:1500px'><table class='report-table'>"
        # html = "<img src='/pam_accounting/static/src/img/logopdam.jpg'/>"
        html = html + "<table class='report-table'>"

        html = self._create_report_header(html)

        report_type = self.env['pam.report.type'].search([('code', '=', report_type_code)])


        grand_total_price = 0
        grand_total_price_audit = 0
        grand_total_price_add = 0
        grand_total_price_subtract = 0
        grand_total_price_all = 0
        grand_total_depreciation_last_year = 0
        grand_total_depreciation_this_year = 0
        grand_total_depreciation_this_year_subtract = 0
        grand_total_mutation = 0
        grand_total_depreciation = 0
        grand_total_price_depreciation = 0


        for line in report_type.line_ids:

            report_config = self.env['pam.report.configuration'].search([('report_type_id', '=', line.report_id.id)])
            report_config_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_config.id), ('group_id', '=', line.id)])

            count_lines = len(report_config_lines)

            if count_lines == 1:
                count_details = len(report_config_lines.detail_ids)
                if count_details == 1:

                    total_price, total_price_audit, total_price_add, total_price_subtract, total_price_all, total_depreciation_last_year, total_depreciation_this_year, total_depreciation_this_year_subtract, total_mutation, total_depreciation, total_price_depreciation = self._get_row_data(report_config_lines.detail_ids.coa_id.id, only_depreciation)
                    html = self._create_report_row(
                                    html, 
                                    "total-cell",
                                    line.name, 
                                    report_config_lines.detail_ids.coa_id.code,
                                    total_price,
                                    total_price_audit,
                                    total_price_add,
                                    total_price_subtract, 
                                    total_price_all, 
                                    total_depreciation_last_year,
                                    total_depreciation_this_year, 
                                    total_depreciation_this_year_subtract, 
                                    total_mutation, 
                                    total_depreciation, 
                                    total_price_depreciation)

                    grand_total_price = grand_total_price + total_price
                    grand_total_price_audit = grand_total_price_audit + total_price_audit
                    grand_total_price_add = grand_total_price_add + total_price_add
                    grand_total_price_subtract = grand_total_price_subtract + total_price_subtract
                    grand_total_price_all = grand_total_price_all + total_price_all
                    grand_total_depreciation_last_year = grand_total_depreciation_last_year + total_depreciation_last_year
                    grand_total_depreciation_this_year = grand_total_depreciation_this_year + total_depreciation_this_year
                    grand_total_depreciation_this_year_subtract = grand_total_depreciation_this_year_subtract + total_depreciation_this_year_subtract
                    grand_total_mutation = grand_total_mutation + total_mutation
                    grand_total_depreciation = grand_total_depreciation + total_depreciation
                    grand_total_price_depreciation = grand_total_price_depreciation + total_price_depreciation


                else:
                    html = self._create_report_row(html, "", line.name, "", "", "", "", "", "", "", "", "", "", "", "")
            else:
                count_details = 0

                html = self._create_report_row(html, "", line.name, "", "", "", "", "", "", "", "", "", "", "", "")

                sum_total_price = 0
                sum_total_price_audit = 0
                sum_total_price_add = 0
                sum_total_price_subtract = 0
                sum_total_price_all = 0
                sum_total_depreciation_last_year = 0
                sum_total_depreciation_this_year = 0
                sum_total_depreciation_this_year_subtract = 0
                sum_total_mutation = 0
                sum_total_depreciation = 0
                sum_total_price_depreciation = 0
                for config_line in report_config_lines:

                    total_price, total_price_audit, total_price_add, total_price_subtract, total_price_all, total_depreciation_last_year, total_depreciation_this_year, total_depreciation_this_year_subtract, total_mutation, total_depreciation, total_price_depreciation = self._get_row_data(config_line.detail_ids.coa_id.id, only_depreciation)

                    html = self._create_report_row(
                                    html, 
                                    " ",
                                    config_line.name, 
                                    config_line.detail_ids.coa_id.code, 
                                    total_price,
                                    total_price_audit,
                                    total_price_add,
                                    total_price_subtract, 
                                    total_price_all, 
                                    total_depreciation_last_year,
                                    total_depreciation_this_year, 
                                    total_depreciation_this_year_subtract, 
                                    total_mutation, 
                                    total_depreciation, 
                                    total_price_depreciation)

                    sum_total_price = sum_total_price + total_price
                    sum_total_price_audit = sum_total_price_audit + total_price_audit
                    sum_total_price_add = sum_total_price_add + total_price_add
                    sum_total_price_subtract = sum_total_price_subtract + total_price_subtract
                    sum_total_price_all = sum_total_price_all + total_price_all
                    sum_total_depreciation_last_year = sum_total_depreciation_last_year + total_depreciation_last_year
                    sum_total_depreciation_this_year = sum_total_depreciation_this_year + total_depreciation_this_year
                    sum_total_depreciation_this_year_subtract = sum_total_depreciation_this_year_subtract + total_depreciation_this_year_subtract
                    sum_total_mutation = sum_total_mutation + total_mutation
                    sum_total_depreciation = sum_total_depreciation + total_depreciation
                    sum_total_price_depreciation = sum_total_price_depreciation + total_price_depreciation
                
                html = self._create_report_row(
                                html,
                                "total-cell", 
                                line.name, 
                                " ", 
                                sum_total_price,
                                sum_total_price_audit,
                                sum_total_price_add,
                                sum_total_price_subtract, 
                                sum_total_price_all,
                                sum_total_depreciation_last_year,
                                sum_total_depreciation_this_year, 
                                sum_total_depreciation_this_year_subtract, 
                                sum_total_mutation, 
                                sum_total_depreciation, 
                                sum_total_price_depreciation)

                grand_total_price = grand_total_price + sum_total_price
                grand_total_price_audit = grand_total_price_audit + sum_total_price_audit
                grand_total_price_add = grand_total_price_add + sum_total_price_add
                grand_total_price_subtract = grand_total_price_subtract + sum_total_price_subtract
                grand_total_price_all = grand_total_price_all + sum_total_price_all
                grand_total_depreciation_last_year = grand_total_depreciation_last_year + sum_total_depreciation_last_year
                grand_total_depreciation_this_year = grand_total_depreciation_this_year + sum_total_depreciation_this_year
                grand_total_depreciation_this_year_subtract = grand_total_depreciation_this_year_subtract + sum_total_depreciation_this_year_subtract
                grand_total_mutation = grand_total_mutation + sum_total_mutation
                grand_total_depreciation = grand_total_depreciation + sum_total_depreciation
                grand_total_price_depreciation = grand_total_price_depreciation + sum_total_price_depreciation


        html = self._create_report_row(
                        html,
                        "total-cell", 
                        "Jumlah", 
                        " ", 
                        grand_total_price,
                        grand_total_price_audit,
                        grand_total_price_add,
                        grand_total_price_subtract, 
                        grand_total_price_all,
                        grand_total_depreciation_last_year,
                        grand_total_depreciation_this_year, 
                        grand_total_depreciation_this_year_subtract, 
                        grand_total_mutation, 
                        grand_total_depreciation, 
                        grand_total_price_depreciation)

        html = html + "</table></div>"

        return html

    def get_data(self):
        fix_asset = self._generate_html('LAT')
        land_asset = self._generate_html('LRNT', True)
        property_asset = self._generate_html('LBPI')
        software_asset = self._generate_html('LATB')

        report = self.env['pam.asset.recap.report'].search([('id', '=', self.id)])
        report.update({
            'report_html': fix_asset,
            'report_land_html' : land_asset,
            'report_property_html' : property_asset,
            'report_software_html' : software_asset,
            'tf': True,
        })

    def export_report_pdf(self):
        for record in self:
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'Rekap Aset Per Bulan',
                'report_format': 'Laporan PDF'
                })
    
            lat = self.env['pam.report.type'].search([('code', '=', 'LAT')])
            lrnt = self.env['pam.report.type'].search([('code', '=', 'LRNT')])
            lpbi = self.env['pam.report.type'].search([('code', '=', 'LBPI')])
            latb = self.env['pam.report.type'].search([('code', '=', 'LATB')])
    
            data = {
                'ids': record.ids,
                'model': record._name,
                'form': {
                    'months': record.months,
                    'years': record.years,
                    'datetime_cetak': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                    'html': record.report_html,
                    'html_land': record.report_land_html,
                    'html_property': record.report_property_html,
                    'html_software': record.report_software_html,
                    'lat': lat,
                    'lrnt': lrnt,
                    'lpbi': lpbi,
                    'latb': latb
                },
            }
    
            return self.env.ref('pam_accounting.action_pam_asset_recap_report').report_action(record, data=data)


class PamAssetRecapReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_asset_recap_template'
    _template = 'pam_accounting.report_asset_recap_template'

    @api.model
    def get_report_values(self, docids, data=None):
        months = data['form']['months']
        years = data['form']['years']
        datetime_cetak = data['form']['datetime_cetak']
        html = data['form']['html']
        html_land = data['form']['html_land']
        html_property = data['form']['html_property']
        html_software = data['form']['html_software']
        lat = data['form']['lat']
        lrnt = data['form']['lrnt']
        lpbi = data['form']['lpbi']
        latb = data['form']['latb']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'months': months,
            'years': years,
            'datetime_cetak': datetime_cetak,
            'html': html,
            'html_land': html_land,
            'html_property': html_property,
            'html_software': html_software,
            'lat': lat,
            'lrnt': lrnt,
            'lpbi': lpbi,
            'latb': latb
        }

