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


class PamJournalVerificationReport(models.TransientModel):
    _name = 'pam.journal.verification.report'

    def _default_start_date(self):
        start_date = datetime.now().strftime('%Y') + '-' + datetime.now().strftime('%m') + '-01'
        return  start_date

    def _default_end_date(self):
        next_month = datetime.strptime(self._default_start_date(), '%Y-%m-%d') + relativedelta(months=1)
        return next_month - relativedelta(days=1)

    start_date = fields.Date(required=True, default=_default_start_date)
    end_date = fields.Date(required=True, default=_default_end_date)
    journal_type = fields.Selection([
        ('ju', 'Jurnal Umum (JU)'),
        ('ap', 'Jurnal Voucher (AP)'),
        ('co', 'Jurnal Bayar Kas (CO)'),
        ('ci', 'Jurnal Penerimaan Kas (CI)'),
        ('bl', 'Jurnal Rekening (BL)'),
        ('in', 'Jurnal Instalasi dan Kimia (IN)'),
        ('aj', 'Jurnal Penyesuaian (AJ)')
    ], default='ju', required=True)
    count_lines = fields.Float(compute='compute_lines')
    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)

    total_debit = fields.Float(default=0)
    total_credit = fields.Float(default=0)

    line_ids = fields.One2many('pam.journal.verification.line.report', 'journal_verification_report_id')

    def compute_lines(self):
        self.count_lines = len(self.line_ids)

    @api.depends('line_ids.debit')
    def compute_total_debit(self):
        for record in self:
            self.total_debit = sum(line.debit for line in record.line_ids)

    @api.depends('line_ids.credit')
    def compute_total_credit(self):
        for record in self:
            self.total_credit = sum(line.credit for line in record.line_ids)

    def _record(self):
        sql = """
            SELECT a.name, a.entry_date, a.remark, c.code, c.name, b.debit, b.credit, e.name as created_by
            FROM 
                pam_journal_entry as a
                INNER JOIN pam_journal_entry_line as b on a.id = b.journal_entry_id
                INNER JOIN pam_coa as c on c.id = b.coa_id
                inner join res_users as d on d.id = a.create_uid
                inner join res_partner as e on e.id = d.partner_id
            WHERE a.entry_date between %s and %s AND a.journal_type = %s AND a.state != 'draft'
            ORDER BY a.name, a.entry_date
            """

        self._cr.execute(sql, (self.start_date, self.end_date, self.journal_type))
        result = self._cr.fetchall()

        return result

    def get_data(self):
        records = self._record()

        self.env['pam.journal.verification.line.report'].search([('journal_verification_report_id','=', self.id)]).unlink()

        before_no = ''
        subtotal_debit = 0
        subtotal_credit = 0
        total_debit = 0
        total_credit = 0
        sequence = 1

        data = []

        for name, entry_date, remark, coa_number, coa_name, debit, credit, created_by in records:
            if before_no != name:
                if before_no != '':
                    vals = {
                        'journal_verification_report_id' : '',
                        'user_id': '',
                        'name' : '',
                        'entry_date' : '',
                        'remark': '',
                        'coa_number' : '',
                        'coa_name' : 'Sub Transaksi',
                        'debit' : subtotal_debit,
                        'credit' : subtotal_credit,
                        'sequence' : sequence
                        }
                    sequence += 1
                    # total_debit = total_debit + subtotal_debit
                    # total_credit = total_credit + subtotal_credit
                    subtotal_credit = 0
                    subtotal_debit = 0
                    
                    row = (0, 0, vals)
                    data.append(row)
                    
                vals = {
                    'journal_verification_report_id' : self.id,
                    'user_id': created_by,
                    'name' : name,
                    'remark': remark,
                    'entry_date' : datetime.strptime(entry_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    'coa_number' : coa_number,
                    'coa_name' : coa_name,
                    'debit' : debit,
                    'credit' : credit,
                    'sequence' : sequence
                    }
                sequence += 1
                
                row = (0, 0, vals)
                data.append(row)
                    
            else:
                vals = {
                    'journal_verification_report_id' : self.id,
                    'user_id' : '',
                    'name' : '',
                    'remark': '',
                    'entry_date' : '',
                    'coa_number' : coa_number,
                    'coa_name' : coa_name,
                    'debit' : debit,
                    'credit' : credit,
                    'sequence' : sequence
                    }
                sequence += 1
                
                row = (0, 0, vals)
                data.append(row)

            before_no = name
            subtotal_debit += debit
            subtotal_credit += credit
            total_debit += debit
            total_credit += credit

        vals = {
            'journal_verification_report_id' : '',
            'user_id' : '',
            'name' : '',
            'entry_date' : '',
            'remark': '',
            'coa_number' : '',
            'coa_name' : 'Sub Transaksi',
            'debit' : subtotal_debit,
            'credit' : subtotal_credit,
            'sequence' : sequence
            }
        sequence += 1
        
        row = (0, 0, vals)
        data.append(row)

        vals = {
            'journal_verification_report_id' : '',
            'user_id' : '',
            'name' : '',
            'entry_date' : '',
            'remark': '',
            'coa_number' : '',
            'coa_name' : 'Total Transaksi',
            'debit' : total_debit,
            'credit' : total_credit,
            'sequence' : sequence
            }
        sequence += 1
        
        row = (0, 0, vals)
        data.append(row)

        verification_report = self.env['pam.journal.verification.report'].search([('id', '=', self.id)])
        verification_report.update({
            'total_debit': total_debit,
            'total_credit': total_credit,
            'line_ids': data
        })

    def export_report_pdf(self):
        report_log = self.env['pam.report.log'].create({
            'name': self.env.user.name,
            'report_type': 'DAFTAR VERIFIKASI JURNAL',
            'report_format': 'Laporan PDF'
            })

        report_type = self.env['pam.report.type'].search([('code', '=', 'JV')])

        rpt = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','tahu')])
        name1 = rpt.name
        position1 = rpt.position
        name_ttd1 = rpt.name_ttd

        rpt2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
        name2 = rpt2.name
        position2 = rpt2.position
        name_ttd2 = rpt2.name_ttd

        verifs = []
        verification_lines = self.env['pam.journal.verification.line.report'].search([('journal_verification_report_id', '=', self.id)], order='sequence asc')
        for verification_line in verification_lines:
        # for line in self.line_ids:
            verifs.append([
                verification_line.name, 
                verification_line.entry_date, 
                verification_line.remark, 
                verification_line.coa_number, 
                verification_line.coa_name, 
                verification_line.debit, 
                verification_line.credit,
                verification_line.user_id 
                ])

        data= {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': (datetime.strptime(self.start_date, "%Y-%m-%d")).strftime("%d/%m/%Y"),
                'end_date': (datetime.strptime(self.end_date, "%Y-%m-%d")).strftime("%d/%m/%Y"),
                'journal_type' : self.journal_type,
                'verifs': verifs,
                'name1': name1,
                'position1': position1,
                'name_ttd1': name_ttd1,
                'name2': name2,
                'position2': position2,
                'name_ttd2': name_ttd2,
            },
        }

        return self.env.ref('pam_accounting.action_pam_journal_verification_report').report_action(self, data=data)

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'DAFTAR VERIFIKASI JURNAL'
            filename = '%s.xlsx' % ('DAFTAR VERIFIKASI JURNAL', )
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'DAFTAR VERIFIKASI JURNAL',
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
            top_right = workbook.add_format({'top': 1, 'right': 1})
            left = workbook.add_format({'left': 1})
            judul_jumlah = workbook.add_format({'top': 1, 'align': 'right'})
            currency_format = workbook.add_format({'num_format': '#,##0.00'})
            str_format = workbook.add_format()
            sub_total = workbook.add_format({'bold': True, 'align': 'right', 'num_format': '#,##0.00'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'bottom': 1, 'num_format': '#,##0.00'})
    
            sheet.set_column(0, 1, 15)
            sheet.set_column(2, 2, 40)
            sheet.set_column(3, 4, 20)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','rekap_buku_besar')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(1, 5, 2, 5, code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(1, 5, 2, 5,' ', bold_center)
    
            sheet.merge_range(0, 0, 0, 4, 'DAFTAR VERIFIKASI JURNAL', title)
            sheet.merge_range(1, 0, 1, 4, 'ENTRI JURNAL VOUCHER (' + record.journal_type.upper() + ')', title)
            sheet.merge_range(2, 0, 2, 4, 'Periode Tanggal : ' + datetime.strptime(record.start_date, "%Y-%m-%d").strftime("%d-%m-%Y") + ' s/d ' + datetime.strptime(record.end_date, "%Y-%m-%d").strftime("%d-%m-%Y"), bold)
            sheet.merge_range(3, 0, 3, 1, 'Tanggal Cetak : ' + (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'), bold)
            sheet.merge_range(4, 0, 4, 1, 'Telah Diperiksa Oleh : ' , bold)
            sheet.merge_range(4, 2, 4, 4, 'Tanggal : ' , bold)
    
    
            sheet.write(6, 0, 'PEMBUAT', top)
            sheet.write(6, 1, 'NO. TRANSAKSI', top)
            sheet.merge_range(6, 2, 6, 3, 'KETERANGAN', top)
            sheet.write(6, 4, 'DEBIT', judul_jumlah)
            sheet.write(6, 5, 'KREDIT', judul_jumlah)
    
            sheet.write(7, 0, '', bottom)
            sheet.write(7, 1, 'TANGGAL', bottom)
            sheet.merge_range(7, 2, 7, 3, 'KODE NAMA PERKIRAAN', bottom)
            sheet.write(7, 4, '', bottom)
            sheet.write(7, 5, '', bottom)
    
            y = 8
            verification_lines = self.env['pam.journal.verification.line.report'].search([('journal_verification_report_id', '=', record.id)], order='sequence asc')
            for verification_line in verification_lines:
                if verification_line.coa_name == 'Sub Transaksi':
                    sheet.merge_range(y, 1, y, 3, 'SUB TRANSAKSI :', sub_total)
                    sheet.write(y, 4, verification_line.debit, sub_total)
                    sheet.write(y, 5, verification_line.credit, sub_total)
    
                    y += 1
    
                elif verification_line.coa_name == 'Total Transaksi':
                    sheet.merge_range(y, 1, y, 3, 'TOTAL TRANSAKSI :', footer)
                    sheet.write(y, 4, verification_line.debit, footer)
                    sheet.write(y, 5, verification_line.credit, footer)
                
                    y += 1
    
                else:
                    if verification_line.name:
                        sheet.write(y, 0, verification_line.user_id, str_format)
                        sheet.write(y, 1, verification_line.name, str_format)
                        sheet.write(y, 2, verification_line.remark, str_format)
                        sheet.write(y, 3, '', str_format)
                        sheet.write(y, 4, '', currency_format)
                        sheet.write(y, 5, '', currency_format)
    
                        y += 1
    
                    sheet.write(y, 1, verification_line.entry_date, str_format)
                    sheet.write(y, 2, verification_line.coa_number, str_format)
                    sheet.write(y, 3, verification_line.coa_name, str_format)
                    sheet.write(y, 4, verification_line.debit, currency_format)
                    sheet.write(y, 5, verification_line.credit, currency_format)
    
                    y += 1
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'JR')])
            
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','tahu')])
            report_type_ttd2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
    
            y += 1
    
            sheet.write(y, 2, report_type_ttd.name)
            sheet.merge_range(y, 3, y, 4, 'Bogor,' + (datetime.now() + relativedelta(hours=7)).strftime('%d %B %Y'))
    
            y +=1
            
            sheet.write(y, 2, report_type_ttd.position)
            sheet.merge_range(y, 3, y, 4, report_type_ttd2.name)
    
            y += 3
    
            sheet.write(y, 2, report_type_ttd.name_ttd)
            sheet.merge_range(y, 3, y, 4, report_type_ttd2.name_ttd)
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename


class PamJournalVerificationLineReport(models.TransientModel):
    _name = 'pam.journal.verification.line.report'
    _order = 'name asc'

    journal_verification_report_id = fields.Many2one('pam.journal.verification.report', required=True, index=True)
    user_id = fields.Char(string='Pembuat')
    name = fields.Char(string='Transaksi')
    entry_date = fields.Char(string='Tanggal')
    remark = fields.Char(string='Keterangan')
    coa_number = fields.Char(string='Kode Perkiraan')
    coa_name = fields.Char(string='Nama Perkiraan')
    debit = fields.Float(default=0)
    credit = fields.Float(default=0)
    sequence = fields.Integer()


class PamJournalVerificationReportTemplate(models.AbstractModel):
    _name = 'report.pam_accounting.report_journal_verification_template'
    _template ='pam_accounting.report_journal_verification_template'

    @api.model
    def get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        journal_type = data['form']['journal_type']
        verifs = data['form']['verifs']
        name1 = data['form']['name1']
        position1 = data['form']['position1']
        name_ttd1 = data['form']['name_ttd1']
        name2 = data['form']['name2']
        position2 = data['form']['position2']
        name_ttd2 = data['form']['name_ttd2']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'journal_type': journal_type,
            'verifs': verifs,
            'name1': name1,
            'position1': position1,
            'name_ttd1': name_ttd1,
            'name2': name2,
            'position2': position2,
            'name_ttd2': name_ttd2,
        }

