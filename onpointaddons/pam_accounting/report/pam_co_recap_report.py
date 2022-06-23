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


class PamCoRecapReport(models.TransientModel):
    _name = 'pam.co.recap.report'

    def _default_start_date(self):
        start_date = datetime.now().strftime('%Y') + '-' + datetime.now().strftime('%m') + '-01'
        return  start_date

    def _default_end_date(self):
        next_month = datetime.strptime(self._default_start_date(), '%Y-%m-%d') + relativedelta(months=1)
        return next_month - relativedelta(days=1)

    start_date = fields.Date(required=True, default=_default_start_date)
    end_date = fields.Date(required=True, default=_default_end_date)
    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    count_lines = fields.Float(compute='compute_lines')
   
    line_ids = fields.One2many('pam.co.recap.report.line', 'co_recap_report_id')

    def compute_lines(self):
        self.count_lines = len(self.line_ids)

    def _record(self):
        sql = """
            select
                a.name,
                a.entry_date,
                coalesce((select x.name from pam_journal_entry x where x.id = a.link_journal_id), '-') as ap_name,
                coalesce(c.cheque_number, '-') as cheque_number,
                d.name as coa_name,
                sum(b.credit) as amount
            from
                pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            inner join pam_journal_payment_line c on a.link_journal_id = c.journal_entry_id
            inner join pam_coa d on d.id = c.coa_id
            where a.journal_type = 'co'
                and state != 'draft'
                and a.entry_date between %s and %s
            group by
                a.name,
                a.entry_date,
                c.cheque_number,
                a.link_journal_id,
                d.name
            order by a.name
            """

        self._cr.execute(sql, (self.start_date, self.end_date))
        result = self._cr.fetchall()

        return result

    def get_data(self):

        records = self._record()

        self.env['pam.co.recap.report.line'].search([('co_recap_report_id','=', self.id)]).unlink()

        data = []
        for co_number, entry_date, ap_number, cheque_number, coa_name, amount in records:
            vals = {
                'co_recap_report_id' : self.id,
                'co_number' : co_number,
                'co_date' : datetime.strptime(entry_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                'ap_number' : ap_number,
                'cheque_number' : cheque_number,
                'bank_name' : coa_name,
                'amount': amount
            }

            row = (0, 0, vals)
            data.append(row)

        recap_report = self.env['pam.co.recap.report'].search([('id', '=', self.id)])
        recap_report.update({
            'line_ids': data
        })

    def export_report_pdf(self):
        for record in self:
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'DAFTAR JURNAL BAYAR KAS',
                'report_format': 'Laporan PDF'
                })
    
            recaps = []
            for line in record.line_ids:
                recaps.append([line.co_number, line.co_date, line.ap_number, line.cheque_number, line.bank_name, line.amount])
                
            data = {
                'ids': record.ids,
                'model': record._name,
                'form': {
                    'start_date': (datetime.strptime(record.start_date, "%Y-%m-%d")).strftime("%d/%m/%Y"),
                    'end_date': (datetime.strptime(record.end_date, "%Y-%m-%d")).strftime("%d/%m/%Y"),
                    'datetime_cetak': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                    'recaps': recaps,
                },
            }
    
            return self.env.ref('pam_accounting.action_pam_co_recap_report').report_action(record, data=data)

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'DAFTAR JURNAL BAYAR KAS'
            filename = '%s.xlsx' % ('DAFTAR JURNAL BAYAR KAS', )
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'DAFTAR JURNAL BAYAR KAS',
                'report_format': 'Laporan Excel'
                })
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 18, 'bold': True})
            bold = workbook.add_format({'bold': True})
            bold_center = workbook.add_format({'bold': True, 'align': 'center'})
            merge = workbook.add_format({'bold': True, 'border': True})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1})
            top = workbook.add_format({'top': 1})
            right = workbook.add_format({'right': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1})
            left = workbook.add_format({'left': 1})
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'right'})
            str_format = workbook.add_format({'text_wrap': True})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})
    
            sheet.set_column(5, 0, 5)
            sheet.set_column(5, 1, 15)
            sheet.set_column(5, 2, 10)
            sheet.set_column(5, 3, 20)
            sheet.set_column(5, 4, 20)
            sheet.set_column(5, 5, 20)
            sheet.set_column(5, 6, 20)
            
            code_iso = self.env['pam.code.iso'].search([('name','=','jurnal_pembayaran_kas')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 5, 3, 6,code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 5, 3, 6,' ', bold_center)
    
            sheet.merge_range(0, 0, 0, 3, 'DAFTAR JURNAL BAYAR KAS', title)
            sheet.merge_range(1, 0, 1, 3, 'PERIODE TANGGAL : ' + datetime.strptime(record.start_date, "%Y-%m-%d").strftime("%d-%m-%Y") + ' s/d ' + datetime.strptime(record.end_date, "%Y-%m-%d").strftime("%d-%m-%Y"), bold)
            sheet.merge_range(2, 0, 2, 3, 'Tanggal Cetak : ' + (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'), bold)
            sheet.merge_range(3, 0, 3, 2, 'Telah Diperiksa Oleh : ' , bold)
            sheet.merge_range(3, 3, 3, 4, 'Tanggal : ' , bold)
    
            sheet.write(5, 0, 'No. ', top_bottom)
            sheet.write(5, 1, 'NOMOR CO', top_bottom)
            sheet.write(5, 2, 'TANGGAL', top_bottom)
            sheet.write(5, 3, 'NOMOR AP', top_bottom)
            sheet.write(5, 4, 'NOMOR CHECK', top_bottom)
            sheet.write(5, 5, 'NAMA BANK', top_bottom)
            sheet.write(5, 6, 'JUMLAH', judul_jumlah)
    
            no = 1
            total_transaction = 0
            y = 6
            
            for line in record.line_ids:
                sheet.write(y, 0, no, no_format)
                sheet.write(y, 1, line.co_number, str_format)
                sheet.write(y, 2, line.co_date, str_format)
                sheet.write(y, 3, line.ap_number, str_format)
                sheet.write(y, 4, line.cheque_number, str_format)
                sheet.write(y, 5, line.bank_name, str_format)
                sheet.write(y, 6, line.amount, currency_format)
    
                y += 1
                total_transaction += line.amount
                no += 1
    
            sheet.merge_range(y, 0, y, 5, 'TOTAL TRANSAKSI :', footer)
            sheet.write(y, 6, total_transaction, footer)
    
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


class PamCoRecapReportLine(models.TransientModel):
    _name = 'pam.co.recap.report.line'
    _order = 'co_number asc'

    co_recap_report_id = fields.Many2one('pam.co.recap.report', required=True, index=True)
    co_number = fields.Char(string='Nomor CO')
    co_date = fields.Char(string='Tanggal')
    ap_number = fields.Char(string='Nomor AP')
    cheque_number = fields.Char(string='Nomor Check')
    bank_name = fields.Char(string='Nama Bank')
    amount = fields.Float(default=0, string='Jumlah')


class PamCoRecapReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_co_recap_report_template'
    _template ='pam_accounting.report_co_recap_report_template'

    @api.model
    def get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        datetime_cetak = data['form']['datetime_cetak']
        recaps = data['form']['recaps']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'datetime_cetak': datetime_cetak,
            'recaps': recaps,
        }

