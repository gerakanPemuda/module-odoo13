import xlsxwriter
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import StringIO, BytesIO
from xlsxwriter.utility import xl_rowcol_to_cell


class PamCoDailyReport(models.TransientModel):
    _name = 'pam.co.daily.report'

    def _default_payment_date(self):
        payment_date = datetime.now().strftime('%Y-%m-%d')
        return  payment_date

    payment_date = fields.Date(required=True, default=_default_payment_date)
    file_bin = fields.Binary()
    count_lines = fields.Float(compute='compute_lines')

    file_name = fields.Char(string="File Name", size=64)

    line_ids = fields.One2many('pam.co.daily.report.line', 'co_daily_report_id')

    def compute_lines(self):
        self.count_lines = len(self.line_ids)

    def get_data(self):
        records = self.env['pam.journal.entry'].search([('journal_type', '=', 'ap'),
                                                        ('state', 'in', ('paid', 'submit', 'posted')), 
                                                        ('payment_date', '=', self.payment_date)
                                                        ], order='name asc')

        self.env['pam.co.daily.report.line'].search([('co_daily_report_id','=', self.id)]).unlink()

        data = []
        sequence = 0
        for record in records:
            if record.payment_type == 'cheque':
                payment_count = 0
                for payment in record.payment_ids:
                    if payment_count == 0:
                        report_value = {
                            'co_daily_report_id' : self.id,
                            'remark' : record.remark,
                            'coh_number' : record.coh_id.name,
                            'voucher_number' : record.name,
                            'cheque_number' : payment.cheque_number + '\n' + payment.coa_id_name,
                            'amount' : payment.amount,
                            'sequence' : sequence,
                        }
                        sequence += 1
                        row = (0, 0, report_value)
                        data.append(row)

                    else:
                        report_value = {
                            'co_daily_report_id' : self.id,
                            'remark' : '',
                            'coh_number' : record.coh_id.name,
                            'voucher_number' : '',
                            'cheque_number' : payment.cheque_number + '\n' + payment.coa_id_name,
                            'amount' : payment.amount,
                            'sequence' : sequence,
                        }
                        sequence += 1
                        row = (0, 0, report_value)
                        data.append(row)
                    
                    payment_count += 1

            else:
                coas = ['21111110', '21121110', '21131110']
                amount = 0

                for line in record.line_ids:
                    if line.coa_id.code in coas:
                        amount += line.debit + line.credit

                report_value = {
                    'co_daily_report_id' : self.id,
                    'remark' : record.remark,
                    'coh_number' : record.cheque_number + '\n' + record.coa_id_name,
                    'voucher_number' : record.name,
                    'cheque_number' : 'Tunai',
                    'amount' : amount,
                    'sequence' : sequence,
                }
                sequence += 1
                row = (0, 0, report_value)
                data.append(row)

        self.update({
            'line_ids' : data
        })

    def export_report_pdf(self):
        report_log = self.env['pam.report.log'].create({
            'name': self.env.user.name,
            'report_type': 'DAFTAR PENGELUARAN HARIAN - DPH',
            'report_format': 'Laporan PDF'
            })

        report_type = self.env['pam.report.type'].search([('code', '=', 'DPH')])

        rpt = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','tahu')])
        name1 = rpt.name
        position1 = rpt.position
        name_ttd1 = rpt.name_ttd

        rpt2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
        name2 = rpt2.name
        position2 = rpt2.position
        name_ttd2 = rpt2.name_ttd

        dailys = []
        for line in self.line_ids:
            dailys.append([line.remark, line.coh_number, line.voucher_number, line.cheque_number, line.amount])
            
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'payment_date': (datetime.strptime(self.payment_date, "%Y-%m-%d")).strftime("%d %B %Y"),
                'name1': name1,
                'position1': position1,
                'name_ttd1': name_ttd1,
                'name2': name2,
                'position2': position2,
                'name_ttd2': name_ttd2,
                'dailys': dailys,
            },
        }

        return self.env.ref('pam_accounting.action_pam_co_daily_report').report_action(self, data=data)

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'DAFTAR PENGELUARAN HARIAN (DPH)'
            filename = '%s.xlsx' % ('DAFTAR PENGELUARAN HARIAN - DPH', )
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'DAFTAR PENGELUARAN HARIAN - DPH',
                'report_format': 'Laporan Excel'
                })
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 14, 'bold': True})
            judul = workbook.add_format({'font_size': 16, 'bold': True})
            payment_date = workbook.add_format({'font_size': 12})
            jalan = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
            bold = workbook.add_format({'bold': True})
            bold_center = workbook.add_format({'bold': True, 'align': 'center'})
            merge = workbook.add_format({'bold': True, 'border': True})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1})
            top = workbook.add_format({'top': 1})
            right = workbook.add_format({'right': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1, 'right': 1,'left': 1})
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'right': 1,'left': 1, 'align': 'right'})
            jumlah = workbook.add_format({'right': 1,'left': 1, 'num_format': '#,##0.00'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True, 'right': 1, 'left': 1})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00', 'right': 1, 'left': 1})
    
            sheet.set_column(0, 0, 5)
            sheet.set_column(1, 1, 25)
            sheet.set_column(2, 2, 15)
            sheet.set_column(3, 5, 20)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','dph')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 5, 2, 5,code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 5, 2, 5,' ', bold_center)
    
            sheet.merge_range(0, 0, 0, 3, 'PERUSAHAAN DAERAH AIR MINUM', judul)
            sheet.merge_range(1, 0, 1, 3, 'TIRTA PAKUAN KOTA BOGOR', title)
            sheet.merge_range(2, 0, 2, 3, 'Jln. Siliwangi No. 121 Bogor Telp.8324111 Fax.8321575', jalan)
    
            sheet.merge_range(3, 2, 3, 4, 'DAFTAR PENGELUARAN HARIAN (DPH)', title)
    
            sheet.write(5, 5, datetime.strptime(record.payment_date.upper(), "%Y-%m-%d").strftime("%d %B %Y"), payment_date)
    
            sheet.write(6, 0, 'No. ', top_bottom)
            sheet.write(6, 1, 'URAIAN', top_bottom)
            sheet.write(6, 2, 'COH', top_bottom)
            sheet.write(6, 3, 'NOMOR VOUCHER', top_bottom)
            sheet.write(6, 4, 'NO CEK', top_bottom)
            sheet.write(6, 5, 'Rp JUMLAH', judul_jumlah)
    
            no = 1
            total_transaction = 0
            y = 7
            
            for line in record.line_ids:
                if line.remark != '':
                    sheet.write(y, 0, no, str_format)
                    sheet.write(y, 1, line.remark, str_format)
                    if line.coh_number:
                        sheet.write(y, 2, line.coh_number, str_format)
                    else:
                        sheet.write(y, 2, "", str_format)
                    sheet.write(y, 3, line.voucher_number, str_format)
                    sheet.write(y, 4, line.cheque_number, str_format)
                    sheet.write(y, 5, line.amount, jumlah)
                    no += 1
                else:
                    sheet.write(y, 0, "", str_format)
                    sheet.write(y, 1, line.remark, str_format)
                    if line.coh_number:
                        sheet.write(y, 2, line.coh_number, str_format)
                    else:
                        sheet.write(y, 2, "", str_format)
                    sheet.write(y, 3, line.voucher_number, str_format)
                    sheet.write(y, 4, line.cheque_number, str_format)
                    sheet.write(y, 5, line.amount, jumlah)
    
                y += 1
                total_transaction += line.amount
    
            sheet.merge_range(y, 0, y, 4, 'TOTAL TRANSAKSI :', footer)
            sheet.write(y, 5, total_transaction, footer)
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'DPH')])
            
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','tahu')])
            report_type_ttd2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
    
            y += 1
    
            sheet.write(y, 1, report_type_ttd.name)
            sheet.write(y, 4, report_type_ttd2.name)
            y +=1
    
            sheet.write(y, 1, report_type_ttd.position)
            sheet.write(y, 4, report_type_ttd2.position)
            y += 3
    
            sheet.write(y, 1, report_type_ttd.name_ttd)
            sheet.write(y, 4, report_type_ttd2.name_ttd)
    
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


class PamCoDailyReportLine(models.TransientModel):
    _name = 'pam.co.daily.report.line'

    co_daily_report_id = fields.Many2one('pam.co.daily.report', required=True, index=True)
    remark = fields.Char(string='Uraian')
    coh_number = fields.Char(string='COH')
    voucher_number = fields.Char(string='Nomor Voucher')
    cheque_number = fields.Text(string='No. Cek')
    amount = fields.Float(default=0, string='Jumlah')
    sequence = fields.Float()


class PamCoDailyReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_co_daily_report_template'
    _template ='pam_accounting.report_co_daily_report_template'

    @api.model
    def get_report_values(self, docids, data=None):
        payment_date = data['form']['payment_date']
        name1 = data['form']['name1']
        position1 = data['form']['position1']
        name_ttd1 = data['form']['name_ttd1']
        name2 = data['form']['name2']
        position2 = data['form']['position2']
        name_ttd2 = data['form']['name_ttd2']
        dailys = data['form']['dailys']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'payment_date': payment_date,
            'name1': name1,
            'position1': position1,
            'name_ttd1': name_ttd1,
            'name2': name2,
            'position2': position2,
            'name_ttd2': name_ttd2,
            'dailys': dailys,
        }
