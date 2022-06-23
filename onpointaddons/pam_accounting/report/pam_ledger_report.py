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


class PamLedgerReport(models.TransientModel):
    _name = 'pam.ledger.report'

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
    coa_id = fields.Many2one('pam.coa', string='Kode Akun', required=True, domain="([('transactional', '=', True)])")
    coa_id_name = fields.Char()
    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)

    beginning_balance = fields.Float(default=0, string='Saldo Awal')
    last_month_debit = fields.Float(default=0, string='Debit')
    last_month_credit = fields.Float(default=0, string='Kredit')
    last_month_net = fields.Float(default=0, string='Net')
    current_month_debit = fields.Float(default=0, string='Debit')
    current_month_credit = fields.Float(default=0, string='Credit')
    current_month_net = fields.Float(default=0, string='Net')
    ending_month_debit = fields.Float(default=0, string='Debit')
    ending_month_credit = fields.Float(default=0, string='Credit')
    ending_month_net = fields.Float(default=0, string='Net')
    ending_balance = fields.Float(default=0, string='Saldo Akhir')
    count_lines = fields.Float(compute='compute_lines')

    line_ids = fields.One2many('pam.ledger.report.line', 'ledger_report_id')

    def compute_lines(self):
        self.count_lines = len(self.line_ids)

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name

    def _record(self, start_date, end_date):
        sql = """

                select a.entry_date, a.name, a.remark, b.debit, b.credit 
                from pam_journal_entry a
                inner join pam_journal_entry_line b on a.id = b.journal_entry_id
                where b.coa_id = %s and a.entry_date between %s and %s
                order by a.entry_date, a.name

            """

        self._cr.execute(sql, (self.coa_id.id, start_date, end_date))
        result = self._cr.fetchall()

        return result

    def get_data(self):
        # Saldo Awal
        last_year = int(self.years) - 1
        last_year_period = str(last_year) + '12'
        last_year_balance = self.env['pam.balance.line'].search([('balance_name', '=', last_year_period), ('balance_state', '=', 'active'), ('coa_id', '=', self.coa_id.id)])
        beginning_balance = last_year_balance.ending_balance 

        # Saldo s/d bulan lalu
        last_month_debit = 0
        last_month_credit = 0
        last_month_net = 0

        start_balance_date = self.years + '-01-01'
        selected_from_month = self.years + '-' + self.from_month + '-01'
        end_balance_date = datetime.strptime(selected_from_month, '%Y-%m-%d') - relativedelta(days=1)

        if self.from_month != '01':
            sql = """

                select SUM(b.debit) as debit, SUM(b.credit) as credit 
                from pam_journal_entry a
                inner join pam_journal_entry_line b on a.id = b.journal_entry_id
                where a.state in ('submit', 'posted') and b.coa_id = %s and a.entry_date between %s and %s

                """
            
            self._cr.execute(sql, (self.coa_id.id, start_balance_date, end_balance_date))
            last_month_balance = self._cr.dictfetchone()

            _logger.debug("Debug last_month_balance : %s", last_month_balance)


            last_month_debit = last_month_balance['debit'] 
            last_month_credit = last_month_balance['credit']
            if self.coa_id.coa_type_id.position == 'debit':
                last_month_net = last_month_debit - last_month_credit
            else:
                last_month_net =  last_month_credit - last_month_debit

        # Rincian Transaksi    
        current_month_debit = 0
        current_month_credit = 0
        current_month_net = 0

        start_date = self.years + '-' + self.from_month + '-01'
        selected_month = self.years + '-' + self.to_month + '-01'
        next_month = datetime.strptime(selected_month, '%Y-%m-%d') + relativedelta(months=1)
        end_date = next_month - relativedelta(days=1)

        records = self._record(start_date, end_date)

        self.env['pam.ledger.report.line'].search([('ledger_report_id','=', self.id)]).unlink()

        data = []
        for entry_date, name, remark, debit, credit in records:

            current_month_debit = current_month_debit + debit
            current_month_credit = current_month_credit + credit

            vals = {
                'ledger_recap_report_id' : self.id,
                'entry_date' : datetime.strptime(entry_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                'transaction_number' : name,
                'remark' : remark,
                'debit' : debit,
                'credit' : credit
            }

            row = (0, 0, vals)
            data.append(row)

        if self.coa_id.coa_type_id.position == 'debit':
            current_month_net = current_month_debit - current_month_credit
        else:
            current_month_net =  current_month_credit - current_month_debit

        ending_month_debit = last_month_debit + current_month_debit
        ending_month_credit = last_month_credit + current_month_credit

        if self.coa_id.coa_type_id.position == 'debit':
            ending_month_net = ending_month_debit - ending_month_credit
        else:
            ending_month_net =  ending_month_credit - ending_month_debit


        ending_balance = beginning_balance + ending_month_net    

        recap_report = self.env['pam.ledger.report'].search([('id', '=', self.id)])
        recap_report.update({
            'beginning_balance': beginning_balance,
            'last_month_debit' : last_month_debit,
            'last_month_credit' : last_month_credit,
            'last_month_net' : last_month_net,
            'current_month_debit' : current_month_debit,
            'current_month_credit' : current_month_credit,
            'current_month_net' : current_month_net,
            'ending_month_debit' : ending_month_debit,
            'ending_month_credit' : ending_month_credit,
            'ending_month_net' : ending_month_net,
            'ending_balance' : ending_balance,
            'line_ids': data
        })

    def export_report_pdf(self):
        report_log = self.env['pam.report.log'].create({
            'name': self.env.user.name,
            'report_type': 'LAPORAN BUKU BESAR',
            'report_format': 'Laporan PDF'
            })

        recaps = []
        for line in self.line_ids:
            recaps.append([line.entry_date, line.transaction_number, line.remark, line.debit, line.credit])
            
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'from_month': datetime.strptime(self.from_month, '%m').strftime("%B"),
                'to_month': datetime.strptime(self.to_month, '%m').strftime("%B"),
                'coa': self.coa_id.code,
                'coa_name': self.coa_id.name,
                'years': self.years,
                'beginning_balance': self.beginning_balance,
                'last_month_debit': self.last_month_debit,
                'last_month_credit': self.last_month_credit,
                'last_month_net': self.last_month_net,
                'current_month_debit': self.current_month_debit,
                'current_month_credit': self.current_month_credit,
                'current_month_net': self.current_month_net,
                'ending_month_debit': self.ending_month_debit,
                'ending_month_credit': self.ending_month_credit,
                'ending_month_net': self.ending_month_net,
                'ending_balance': self.ending_balance,
                'recaps': recaps,
            },
        }

        return self.env.ref('pam_accounting.action_pam_ledger_report').report_action(self, data=data)

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            # filename = 'LAPORAN BUKU BESAR'
            filename = '%s.xlsx' % ('LAPORAN BUKU BESAR', )

            report_log = self.env['pam.report.log'].create({
                'name': self.env.user.name,
                'report_type': 'LAPORAN BUKU BESAR',
                'report_format': 'Laporan Excel'
                })

            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 18, 'bold': True})
            bold_center = workbook.add_format({'bold': True, 'align': 'center'})
            bold = workbook.add_format({'bold': True})
            merge = workbook.add_format({'bold': True, 'border': True})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1, 'bold': True})
            top = workbook.add_format({'top': 1, 'bold': True})
            last_balance = workbook.add_format({'top': 1, 'bold': True, 'num_format': '#,##0.00'})
            right = workbook.add_format({'right': 1})
            top_bottom = workbook.add_format({'top': 1, 'bottom': 1})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00'})
            deb_cre = workbook.add_format({'align': 'right', 'top': 1, 'bottom': 1})
            total = workbook.add_format({'bold': True, 'align': 'right', 'top': 1, 'bottom': 1, 'num_format': '#,##0.00'})

            sheet.set_column(0, 1, 15)
            sheet.set_column(2, 2, 40)
            sheet.set_column(4, 5, 15)

            code_iso = self.env['pam.code.iso'].search([('name','=','laporan_buku_besar')])
            if code_iso:
                wrap_text = workbook.add_format()
                wrap_text.set_text_wrap()
                sheet.merge_range(0, 5, 2, 5, code_iso.code_iso, wrap_text)
            else:
                sheet.merge_range(0, 5, 2, 5, ' ', bold_center)

            sheet.merge_range(0, 0, 0, 4, 'LAPORAN BUKU BESAR', title)
            sheet.merge_range(1, 0, 1, 4, 'KODE PERKIRAAN : ' + record.coa_id.code + ' - ' + record.coa_id.name, bold)
            sheet.merge_range(2, 0, 2, 4, 'PERIODE BULAN : ' + datetime.strptime(record.from_month, '%m').strftime("%B") + ' - ' + datetime.strptime(record.to_month, '%m').strftime("%B") + ' ' + record.years, bold)

            sheet.merge_range(4, 0, 4, 5, 'Tanggal Cetak : ' + (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'), bold)
            sheet.merge_range(5, 0, 5, 2, 'Telah Diperiksa Oleh : . . . . . . ', bottom)
            sheet.merge_range(5, 3, 5, 5, 'Tanggal : . . . . . . ', bottom)

            sheet.write(6, 4, 'SALDO AWAL : ', bold)
            sheet.write(6, 5, record.beginning_balance , currency_format)

            sheet.write(7, 1, 'TRANSAKSI', top_bottom)
            sheet.write(7, 2, 'DEBET', deb_cre)
            sheet.write(7, 3, 'KREDIT', deb_cre)
            sheet.write(7, 4, 'NET', deb_cre)
            sheet.write(7, 5, '', top_bottom)

            sheet.write(8, 1, '1. S/D BULAN LALU :', str_format)
            sheet.write(8, 2, record.last_month_debit , currency_format)
            sheet.write(8, 3, record.last_month_credit , currency_format)
            sheet.write(8, 4, record.last_month_net , currency_format)

            sheet.write(9, 1, '2. BULAN INI :', str_format)
            sheet.write(9, 2, record.current_month_debit , currency_format)
            sheet.write(9, 3, record.current_month_credit , currency_format)
            sheet.write(9, 4, record.current_month_net , currency_format)

            sheet.write(10, 1, '3. S/D BULAN INI :', str_format)
            sheet.write(10, 2, record.ending_month_debit , currency_format)
            sheet.write(10, 3, record.ending_month_credit , currency_format)
            sheet.write(10, 5, record.ending_month_net , currency_format)

            sheet.write(11, 4, 'SALDO AKHIR :' , top)
            sheet.write(11, 5, record.ending_balance , last_balance)

            sheet.merge_range(12, 0, 12, 1, 'RINCIAN TRANSAKSI :  ', bold)

            sheet.write(13, 0, 'TANGGAL', top_bottom)
            sheet.write(13, 1, 'NO. TRANSAKSI', top_bottom)
            sheet.merge_range(13, 2, 13, 3, 'KETARANGAN', top_bottom)
            sheet.write(13, 4, 'DEBET', deb_cre)
            sheet.write(13, 5, 'KREDIT', deb_cre)

            total_debit = 0
            total_credit = 0
            y = 14

            for line in record.line_ids:
                sheet.write(y, 0, line.entry_date, str_format)
                sheet.write(y, 1, line.transaction_number, str_format)
                sheet.merge_range(y, 2, y, 3, line.remark, str_format)
                sheet.write(y, 4, line.debit, currency_format)
                sheet.write(y, 5, line.credit, currency_format)

                y += 1
                total_debit += line.debit
                total_credit += line.credit

            sheet.merge_range(y, 0, y, 3, 'TOTAL TRANSAKSI :', total)
            sheet.write(y, 4, total_debit, total)
            sheet.write(y, 5, total_credit, total)

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


class PamLedgerReportLine(models.TransientModel):
    _name = 'pam.ledger.report.line'

    ledger_report_id = fields.Many2one('pam.ledger.report', required=True, index=True)
    entry_date = fields.Char(string='Tanggal')
    transaction_number = fields.Char(string='No. Transaksi')
    remark = fields.Text(string='Keterangan')
    debit = fields.Float(default=0, string='Debit')
    credit = fields.Float(default=0, string='Kredit')


class PamLedgerReportTemplate(models.AbstractModel):
    _name = 'report.pam_accounting.report_ledger_report_template'
    _template ='pam_accounting.report_ledger_report_template'

    @api.model
    def get_report_values(self, docids, data=None):
        from_month = data['form']['from_month']
        to_month = data['form']['to_month']
        coa = data['form']['coa']
        coa_name = data['form']['coa_name']
        years = data['form']['years']
        beginning_balance = data['form']['beginning_balance']
        last_month_debit = data['form']['last_month_debit']
        last_month_credit = data['form']['last_month_credit']
        last_month_net = data['form']['last_month_net']
        current_month_debit = data['form']['current_month_debit']
        current_month_credit = data['form']['current_month_credit']
        current_month_net = data['form']['current_month_net']
        ending_month_debit = data['form']['ending_month_debit']
        ending_month_credit = data['form']['ending_month_credit']
        ending_month_net = data['form']['ending_month_net']
        ending_balance = data['form']['ending_balance']
        recaps = data['form']['recaps']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'from_month': from_month,
            'to_month': to_month,
            'coa': coa,
            'coa_name': coa_name,
            'years': years,
            'beginning_balance': beginning_balance,
            'last_month_debit': last_month_debit,
            'last_month_credit': last_month_credit,
            'last_month_net': last_month_net,
            'current_month_debit': current_month_debit,
            'current_month_credit': current_month_credit,
            'current_month_net': current_month_net,
            'ending_month_debit': ending_month_debit,
            'ending_month_credit': ending_month_credit,
            'ending_month_net': ending_month_net,
            'ending_balance': ending_balance,
            'recaps': recaps,
        }
