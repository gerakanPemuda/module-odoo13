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


class PamApdOpenReport(models.TransientModel):
    _name = 'pam.ap.open.report'

    def _default_start_date(self):
        start_date = datetime.now().strftime('%Y') + '-' + datetime.now().strftime('%m') + '-01'
        return  start_date

    def _default_end_date(self):
        next_month = datetime.strptime(self._default_start_date(), '%Y-%m-%d') + relativedelta(months=1)
        return next_month - relativedelta(days=1)

    start_date = fields.Date(required=True, default=_default_start_date)
    end_date = fields.Date(required=True, default=_default_end_date)
    file_bin = fields.Binary()
    count_lines = fields.Float(compute='compute_lines')

    file_name = fields.Char(string="File Name", size=64)
   
    line_ids = fields.One2many('pam.ap.open.report.line', 'ap_open_report_id')

    def compute_lines(self):
        self.count_lines = len(self.line_ids)

    def _record(self):
        sql = """
            select 
                a.name,
                a.entry_date,
                SUM(b.debit) as ap_amount
            from 
                pam_journal_entry a
                inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where 
                a.journal_type = 'ap'
                and a.entry_date between %s and %s
                and a.state = 'payment'
            group by
                a.name, a.entry_date
            order by 
                a.entry_date
            """

        self._cr.execute(sql, (self.start_date, self.end_date))
        result = self._cr.fetchall()

        return result

    def get_data(self):

        records = self._record()

        self.env['pam.ap.open.report.line'].search([('ap_open_report_id','=', self.id)]).unlink()

        data = []
        for ap_number, entry_date, ap_amount in records:
            vals = {
                'ap_open_report_id' : self.id,
                'ap_number' : ap_number,
                'entry_date' : datetime.strptime(entry_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                'ap_amount' : ap_amount
            }

            row = (0, 0, vals)
            data.append(row)

        recap_report = self.env['pam.ap.open.report'].search([('id', '=', self.id)])
        recap_report.update({
            'line_ids': data
        })

    def export_report_pdf(self):
        report_log = self.env['pam.report.log'].create({
            'name': self.env.user.name,
            'report_type': 'DHHD TERBUKA',
            'report_format': 'Laporan PDF'
            })

        recaps = []
        for line in self.line_ids:
            recaps.append([line.ap_number, line.entry_date, line.ap_amount])
            
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': (datetime.strptime(self.start_date, "%Y-%m-%d")).strftime("%d/%m/%Y"),
                'end_date': (datetime.strptime(self.end_date, "%Y-%m-%d")).strftime("%d/%m/%Y"),
                'recaps': recaps,
            },
        }

        return self.env.ref('pam_accounting.action_pam_ap_open_report').report_action(self, data=data)

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            filename = '%s.xlsx' % ('DHHD TERBUKA', )
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'DHHD TERBUKA',
                'report_format': 'Laporan Excel'
                })
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 18, 'bold': True})
            bold = workbook.add_format({'bold': True, 'align': 'center'})
            merge = workbook.add_format({'bold': True, 'border': True})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'border': 1})
            jumlah = workbook.add_format({'border': 1, 'align': 'right'})
            top = workbook.add_format({'top': 1})
            right = workbook.add_format({'right': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'border': 1})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
    
            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 2, 15)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','dhhd_terbuka')])
            if code_iso:
                wrap_text = workbook.add_format({'bold': True, 'align': 'center'})
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 3, 1, 3,code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 3, 1, 3,' ', bold)
    
            sheet.merge_range(0, 1, 0, 2, 'DHHD TERBUKA', title)
            sheet.merge_range(1, 0, 1, 2, 'SAMPAI DENGAN BULAN : ' + datetime.strptime(record.start_date, "%Y-%m-%d").strftime("%d-%m-%Y") + ' s/d ' + datetime.strptime(record.end_date, "%Y-%m-%d").strftime("%d-%m-%Y"), bold)
    
            sheet.write(3, 0, 'No. Transaksi', bottom)
            sheet.write(3, 1, 'Tanggal', bottom)
            sheet.merge_range(3, 2, 3, 3, 'Jumlah AP', jumlah)
    
            y = 4
            
            for line in record.line_ids:
                sheet.write(y, 0, line.ap_number, bottom)
                sheet.write(y, 1, line.entry_date, bottom)
                sheet.merge_range(y, 2, y, 3, line.ap_amount, currency_format)
                y += 1
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename
    
            # return{
            #     'view_mode': 'form',
            #     'res_id': record.id,
            #     'res_model': 'pam.journal.verification.report',
            #     'view_type': 'form',
            #     'type': 'ir.actions.act_window',
            #     'context': self.env.context,
            #     'target': 'new',
            #     }


class PamApdOpenReportLine(models.TransientModel):
    _name = 'pam.ap.open.report.line'

    ap_open_report_id = fields.Many2one('pam.ap.open.report', required=True, index=True)
    ap_number = fields.Char(string='No. Transaksi')
    entry_date = fields.Char(string='Tanggal')
    ap_amount = fields.Float(default=0, string='Jumlah AP')


class PamCoRecapReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_ap_open_report_template'
    _template ='pam_accounting.report_ap_open_report_template'

    @api.model
    def get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        recaps = data['form']['recaps']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'recaps': recaps,
        }
