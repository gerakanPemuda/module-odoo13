import xlsxwriter
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import StringIO, BytesIO
from xlsxwriter.utility import xl_rowcol_to_cell


class PamJournalRecapReport(models.TransientModel):
    _name = 'pam.journal.recap.report'

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
    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)

    total_debit = fields.Float(compute='compute_total_debit')
    total_credit = fields.Float(compute='compute_total_credit')

    count_lines = fields.Float(compute='compute_lines')

    line_ids = fields.One2many('pam.journal.recap.report.line', 'journal_recap_report_id')

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
            SELECT c.code, c."name", SUM(b.debit) as debit, SUM(b.credit) as credit
            FROM 
                pam_journal_entry as a
                inner join pam_journal_entry_line as b on a.id = b.journal_entry_id
                inner join pam_coa as c on b.coa_id = c."id"
            WHERE 
                a.entry_date BETWEEN %s and %s AND a.journal_type = %s and a.state != 'draft'
            group by c.code, c."name"
            order by c.code
            """

        self._cr.execute(sql, (self.start_date, self.end_date, self.journal_type))
        result = self._cr.fetchall()

        return result

    def get_data(self):
        records = self._record()

        self.env['pam.journal.recap.report.line'].search([('journal_recap_report_id','=', self.id)]).unlink()

        for record in records:
            self.env['pam.journal.recap.report.line'].create({
                'journal_recap_report_id' : self.id,
                'coa_number' : record[0],
                'coa_name' : record[1],
                'debit' : record[2],
                'credit' : record[3],
            })

    def export_report_pdf(self):
        report_log = self.env['pam.report.log'].create({
            'name': self.env.user.name,
            'report_type': 'DAFTAR REKAPITULASI JURNAL',
            'report_format': 'Laporan PDF'
            })

        report_type = self.env['pam.report.type'].search([('code', '=', 'RJ')])

        rpt = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','tahu')])
        name1 = rpt.name
        position1 = rpt.position
        name_ttd1 = rpt.name_ttd

        rpt2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
        name2 = rpt2.name
        position2 = rpt2.position
        name_ttd2 = rpt2.name_ttd

        recaps = []
        for line in self.line_ids:
            recaps.append([line.coa_number, line.coa_name, line.debit, line.credit])
            
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': (datetime.strptime(self.start_date, "%Y-%m-%d")).strftime("%d/%m/%Y"),
                'end_date': (datetime.strptime(self.end_date, "%Y-%m-%d")).strftime("%d/%m/%Y"),
                'journal_type' : self.journal_type,
                'recaps': recaps,
                'name1': name1,
                'position1': position1,
                'name_ttd1': name_ttd1,
                'name2': name2,
                'position2': position2,
                'name_ttd2': name_ttd2,
            },
        }

        return self.env.ref('pam_accounting.action_pam_journal_recap_report').report_action(self, data=data)

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'DAFTAR REKAPITULASI JURNAL'
            filename = '%s.xlsx' % ('DAFTAR REKAPITULASI JURNAL', )
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'DAFTAR REKAPITULASI JURNAL',
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
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1 , 'num_format': '#,##0.00'})
    
            sheet.set_column(0, 0, 15)
            sheet.set_column(1, 1, 40)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 20)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','rekap_jurnal')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 3, 3, 3,code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 3, 3, 3,' ', bold_center)
    
            sheet.merge_range(0, 0, 0, 2, 'DAFTAR REKAPITULASI JURNAL', title)
            sheet.merge_range(1, 0, 1, 2, 'ENTRI JURNAL VOUCHER (' + record.journal_type.upper() + ')', title)
            sheet.merge_range(1, 0, 1, 2, 'Periode Tanggal : ' + datetime.strptime(record.start_date, "%Y-%m-%d").strftime("%d-%m-%Y") + ' s/d ' + datetime.strptime(record.end_date, "%Y-%m-%d").strftime("%d-%m-%Y"), bold)
            sheet.merge_range(2, 0, 2, 1, 'Tanggal Cetak : ' + (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'), bold)
            sheet.merge_range(3, 0, 3, 1, 'Telah Diperiksa Oleh : ' , bold)
            sheet.write(3, 2, 'Tanggal : ' , bold)
    
    
            sheet.write(5, 0, 'KODE', top_bottom)
            sheet.write(5, 1, 'NAMA PERKIRAAN', top_bottom)
            sheet.write(5, 2, 'Debit', judul_jumlah)
            sheet.write(5, 3, 'Credit', judul_jumlah)
    
            total_debit = 0
            total_creadit = 0
            y = 6
            
            for line in record.line_ids:
                sheet.write(y, 0, line.coa_number, str_format)
                sheet.write(y, 1, line.coa_name, str_format)
                sheet.write(y, 2, line.debit, currency_format)
                sheet.write(y, 3, line.credit, currency_format)
    
                total_debit += line.debit
                total_creadit += line.credit
                y += 1
    
            sheet.merge_range(y, 0, y, 1, 'TOTAL TRANSAKSI :', footer)
            sheet.write(y, 2, total_debit, footer)
            sheet.write(y, 3, total_creadit, footer)
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'JR')])
            
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','tahu')])
            report_type_ttd2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','buat')])
    
            y += 2
    
            sheet.write(y, 1, report_type_ttd.name)
            sheet.merge_range(y, 2, y, 3, 'Bogor,' + (datetime.now() + relativedelta(hours=7)).strftime('%d %B %Y'))
    
            y +=1
            
            sheet.write(y, 1, report_type_ttd.position)
            sheet.merge_range(y, 2, y, 3, report_type_ttd2.name)
    
            y += 3
    
            sheet.write(y, 1, report_type_ttd.name_ttd)
            sheet.merge_range(y, 2, y, 3, report_type_ttd2.name_ttd)
    
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


class PamJournalRecapReportLine(models.TransientModel):
    _name = 'pam.journal.recap.report.line'
    _order = 'coa_number asc'

    journal_recap_report_id = fields.Many2one('pam.journal.recap.report', required=True, index=True)
    coa_number = fields.Char(string='Kode')
    coa_name = fields.Char(string='Nama Perkiraan')
    debit = fields.Float(default=0)
    credit = fields.Float(default=0)


class PamJournalRecapReportTemplate(models.AbstractModel):
    _name = 'report.pam_accounting.report_journal_recap_report_template'
    _template ='pam_accounting.report_journal_recap_report_template'

    @api.model
    def get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        journal_type = data['form']['journal_type']
        recaps = data['form']['recaps']
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
            'recaps': recaps,
            'name1': name1,
            'position1': position1,
            'name_ttd1': name_ttd1,
            'name2': name2,
            'position2': position2,
            'name_ttd2': name_ttd2,
        }
