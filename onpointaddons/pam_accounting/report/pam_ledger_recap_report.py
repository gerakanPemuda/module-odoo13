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

import logging
_logger = logging.getLogger(__name__)


class PamLedgerRecapReport(models.TransientModel):
    _name = 'pam.ledger.recap.report'

    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = current_year - 3
        results = []
        for year in range(min_year, current_year):
            str_year = str(year)
            results.append((str_year, str_year))
        return results

    from_month = fields.Selection([
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

    to_month = fields.Selection([
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
    years = fields.Selection(_get_years, string='Tahun Anggaran', default=_default_year, required=True)
    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)
    count_lines = fields.Float(compute='compute_lines')
    
    line_ids = fields.One2many('pam.ledger.recap.report.line', 'ledger_recap_report_id')

    def compute_lines(self):
        self.count_lines = len(self.line_ids)

    def _record(self, beginning_period, start_date, end_date):
        sql = """
                SELECT 
                    a.code as coa_number, 
                    a.name as coa_name,
                    coalesce((
						select yy.ending_balance 
						from pam_balance xx
						inner join pam_balance_line yy on xx.id = yy.balance_id
						where xx.name = %s and yy.coa_id = a.id and xx.state = 'active'
                    ),0) as beginning_balance,
                    coalesce((CASE 
                        WHEN b."position" = 'debit' then (SELECT sum(y.debit - y.credit) 
                                                        FROM pam_journal_entry x 
                                                        INNER JOIN pam_journal_entry_line y on x.id = y.journal_entry_id
                                                        WHERE y.coa_id = a.id and x.entry_date between %s and %s)
                        ELSE (SELECT sum(y.credit - y.debit) 
                            FROM pam_journal_entry x 
                            INNER JOIN pam_journal_entry_line y on x.id = y.journal_entry_id
                            WHERE y.coa_id = a.id  and x.entry_date between %s and %s)
                    END),0) as current_balance
                FROM pam_coa a
                INNER JOIN pam_coa_type b on b.id = a.coa_type_id
                WHERE transactional = true
            """

        self._cr.execute(sql, (beginning_period, start_date, end_date, start_date, end_date))
        result = self._cr.fetchall()

        return result

    def get_data(self):
        # period = self.years + '01'

        if self.from_month == '01':
            beginning_month = '12'
            beginning_year = int(self.years) - 1
        else:
            beginning_month = (int(self.from_month) - 1).zfill(2)
            beginning_year = self.years
        
        period = str(beginning_year) + beginning_month

        # start_date = self.years + '-01-01'
        # selected_month = self.years + '-' + self.months + '-01'
        # next_month = datetime.strptime(selected_month, '%Y-%m-%d') + relativedelta(months=1)
        # end_date = next_month - relativedelta(days=1)

        start_date = self.years + '-' + self.from_month + '-01'
        selected_month = self.years + '-' + self.to_month + '-01'
        next_month = datetime.strptime(selected_month, '%Y-%m-%d') + relativedelta(months=1)
        end_date = next_month - relativedelta(days=1)

        _logger.debug("Debug start_date : %s", start_date)
        _logger.debug("Debug end_date : %s", end_date)

        records = self._record(period, start_date, end_date)

        self.env['pam.ledger.recap.report.line'].search([('ledger_recap_report_id','=', self.id)]).unlink()

        data = []
        for coa_number, coa_name, beginning_balance, current_balance in records:
            ending_balance = beginning_balance + current_balance
            vals = {
                'ledger_recap_report_id' : self.id,
                'coa_number' : coa_number,
                'coa_name' : coa_name,
                'beginning_balance' : beginning_balance,
                'current_balance' : current_balance,
                'ending_balance' : ending_balance
            }

            row = (0, 0, vals)
            data.append(row)

        recap_report = self.env['pam.ledger.recap.report'].search([('id', '=', self.id)])
        recap_report.update({
            'line_ids': data
        })

    def export_report_pdf(self):
        report_log = self.env['pam.report.log'].create({
            'name': self.env.user.name,
            'report_type': 'DAFTAR REKAPITULASI BUKU BESAR',
            'report_format': 'Laporan PDF'
            })

        recaps = []
        for line in self.line_ids:
            recaps.append([line.coa_number, line.coa_name, line.beginning_balance, line.current_balance, line.ending_balance])
            
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'from_month': datetime.strptime(self.from_month, '%m').strftime("%B"),
                'to_month': datetime.strptime(self.to_month, '%m').strftime("%B"),
                'years': self.years,
                'recaps': recaps,
            },
        }

        return self.env.ref('pam_accounting.action_pam_ledger_recap_report').report_action(self, data=data)

    def export_report_xls(self):
        for v in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'DAFTAR REKAPITULASI BUKU BESAR'
            filename = '%s.xlsx' % ('DAFTAR REKAPITULASI BUKU BESAR', )
    
            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'DAFTAR REKAPITULASI BUKU BESAR',
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
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'right'})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True})
            no_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'border': True, 'num_format': '#,##0.00'})
    
            sheet.set_column(0, 0, 5)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 2, 40)
            sheet.set_column(3, 5, 25)
    
            code_iso = self.env['pam.code.iso'].search([('name','=','rekap_jurnal')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 5, 2, 5, code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 5, 2, 5, ' ', bold_center)
    
            sheet.merge_range(0, 0, 0, 2, 'DAFTAR REKAPITULASI BUKU BESAR', title)
            sheet.merge_range(1, 0, 1, 3, 'PERIODE : ' + (datetime.strptime(record.from_month, '%m').strftime("%B")) + ' - ' + (datetime.strptime(record.to_month, '%m').strftime("%B")) + ' ' + record.years, bold)
            sheet.merge_range(2, 0, 2, 2, 'Tanggal Cetak : ' + (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'), bold)
    
    
            sheet.write(4, 0, 'No. ', top_bottom)
            sheet.write(4, 1, 'KODE AKUN', top_bottom)
            sheet.write(4, 2, 'PERKIRAAN', top_bottom)
            sheet.write(4, 3, 'SALDO AWAL', judul_jumlah)
            sheet.write(4, 4, 'S/D BULAN', judul_jumlah)
            sheet.write(4, 5, 'SALDO AKHIR', judul_jumlah)
    
            no = 1
            y = 5
            
            for line in record.line_ids:
                sheet.write(y, 0, no, no_format)
                sheet.write(y, 1, line.coa_number, str_format)
                sheet.write(y, 2, line.coa_name, str_format)
                sheet.write(y, 3, line.beginning_balance, currency_format)
                sheet.write(y, 4, line.current_balance, currency_format)
                sheet.write(y, 5, line.ending_balance, currency_format)
    
                y += 1
                no += 1
    
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


class PamLedgerRecapReportLine(models.TransientModel):
    _name = 'pam.ledger.recap.report.line'
    _order = 'coa_number asc'

    ledger_recap_report_id = fields.Many2one('pam.ledger.recap.report', required=True, index=True)
    coa_number = fields.Char(string='Kode Perkiraan')
    coa_name = fields.Char(string='Nama Perkiraan')
    beginning_balance = fields.Float(default=0, string='Saldo Awal')
    current_balance = fields.Float(default=0, string='Saldo s/d bulan ini')
    ending_balance = fields.Float(default=0, string='Saldo Akhir')


class PamLedgerRecapReportTemplate(models.AbstractModel):
    _name = 'report.pam_accounting.report_ledger_recap_report_template'
    _template ='pam_accounting.report_ledger_recap_report_template'

    @api.model
    def get_report_values(self, docids, data=None):
        from_month = data['form']['from_month']
        to_month = data['form']['to_month']
        years = data['form']['years']
        recaps = data['form']['recaps']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'from_month': from_month,
            'to_month': to_month,
            'years': years,
            'recaps': recaps,
        }
