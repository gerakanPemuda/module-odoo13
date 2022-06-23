import os
import xlsxwriter
import base64
import xlwt
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import StringIO, BytesIO
from xlsxwriter.utility import xl_rowcol_to_cell

import logging
_logger = logging.getLogger(__name__)


class PamJournalEntry(models.Model):
    _name = 'pam.journal.entry'
    _description = "Journal"
    _sql_constraints = [
            ('name_uniq', 'UNIQUE (name)',  'Kode yang dimasukkan sudah ada dalam database !')
        ]    
    _inherit = ['mail.thread']
    _order = 'entry_date desc, code_year desc, code_month desc, code_number desc'


    def _get_code_month(self, entry_date):
        if entry_date:
            return datetime.strptime(entry_date, "%Y-%m-%d").strftime("%m")
        else:
            return '01'

    def _get_code_year(self, entry_date):
        if entry_date:
            return datetime.strptime(entry_date, "%Y-%m-%d").strftime("%Y")
        else:
            return '2019'

    def xstr(self, s):
        if s is None:
            return ''
        return str(s)

    def _get_suffix(self, code_journal_type, entry_date):
        code_month = self._get_code_month(entry_date)
        code_year = self._get_code_year(entry_date)

        suffix = '/' + self.xstr(code_journal_type) + '/' + self.xstr(code_month) + '/' + self.xstr(code_year)
        return suffix

    def _get_new_code_number(self, entry_date):
        context = self.env.context
        suffix = self._get_suffix(context.get('default_code_journal_type'), entry_date)

        last_code = self.env['pam.journal.entry'].search([('name', 'like', '%' + suffix)], limit=1, order='name desc')
        new_code_number = int(last_code.code_number) + 1

        return str(new_code_number).zfill(3)

    def _get_new_co_code_number(self, entry_date):

        _logger.debug("Debug message entry_date : %s", entry_date)

        suffix = self._get_suffix('CO', entry_date)

        _logger.debug("Debug message suffix : %s", suffix)


        last_code = self.env['pam.journal.entry'].search([('name', 'like', '%' + suffix)], limit=1, order='name desc')
        new_code_number = int(last_code.code_number) + 1

        _logger.debug("Debug message new_code : %s", new_code_number)

        return str(new_code_number).zfill(3)

    def _default_date(self):
        return (datetime.now() + relativedelta(hours=7)).date()
    
    def _default_code_month(self):
        return self._get_code_month(datetime.now().strftime("%Y-%m-%d"))

    def _default_code_year(self):
        return self._get_code_year(datetime.now().strftime("%Y-%m-%d"))

    def _default_code_number(self):
        return self._get_new_code_number(datetime.now().strftime("%Y-%m-%d"))

    name = fields.Char(string='Nomor')
    code_number = fields.Char(string='Nomor', required=True, default=_default_code_number)
    code_journal_type = fields.Char()
    code_month = fields.Char(compute='compute_code_month_year', default=_default_code_month)
    code_year = fields.Char(compute='compute_code_month_year', default=_default_code_year)

    link_journal_id  = fields.Many2one('pam.journal.entry', index=True)

    journal_type = fields.Selection([
        ('ju', 'Jurnal Umum'),
        ('ap', 'Jurnal Voucher'),
        ('co', 'Jurnal Bayar Kas'),
        ('ci', 'Jurnal Penerimaan Kas'),
        ('bl', 'Jurnal Rekening'),
        ('in', 'Jurnal Instalasi dan Kimia'),
        ('aj', 'Jurnal Penyesuaian')
    ], default='ju')
    entry_date = fields.Date(string='Tanggal', required=True, index=True)
    remark = fields.Text(string='Uraian', required=True)
    refers_to = fields.Reference([
        ('pam.cashflow', 'Kas Kecil'),
        ], readonly=True)
    bank_id = fields.Many2one('pam.bank', index=True)
    vendor_id = fields.Many2one('pam.vendor', string='Penerima', index=True)
    payment_type = fields.Selection([
        ('cheque', 'Cek'),
        ('cash', 'Tunai')
    ], default='cheque', required=True, index=True)

    # Cash on Hand (COH) / Tunai 
    coh_id = fields.Many2one('pam.journal.payment', string="Cash On Hand")
    coa_id = fields.Many2one('pam.coa', string='Kas/Bank', related='coh_id.coa_id')
    coa_id_name = fields.Char()
    cheque_number = fields.Char(string='Cek No.', related='coh_id.cheque_number')
    coh_date = fields.Date(string='Tanggal COH', related='coh_id.payment_date')

    # Cheque
    payment_date = fields.Date(string='Tanggal Pembayaran')
    payment_ids = fields.One2many('pam.journal.payment.line', 'journal_entry_id')

    total_payment = fields.Float(compute='compute_total_payment')
    total_payment_diff = fields.Float(compute='compute_total_payment')

    total_debit = fields.Float(compute='compute_total_debit')
    total_credit = fields.Float(compute='compute_total_credit')
    total_credit_name = fields.Char(compute='compute_total_credit')
    total_diff = fields.Float(compute='compute_total_diff')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('payment', 'Payment'),
        ('paid', 'Paid'),
        ('submit', 'Submit'),
        ('posted', 'Posted')
    ], default='draft', index=True)
    # voucher_printout_html = fields.Html()
    approval_name1 = fields.Char()
    approval_name2 = fields.Char()
    approval_name3 = fields.Char()
    approval_name4 = fields.Char()
    is_cancellation = fields.Boolean(string='Pembatalan', default=False)
    is_cash_flow = fields.Boolean(string='Arus Kas', default=False)
    cash_flow_type = fields.Selection([
        ('income', 'Penerimaan'),
        ('cost', 'Pengeluaran')
    ])

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)

    line_ids = fields.One2many('pam.journal.entry.line', 'journal_entry_id')

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name

    dic = {       
        'to_19' : ('Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'),
        'tens'  : ('Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'),
        'denom' : ('', 'Thousand', 'Million', 'Billion', 'Trillion', 'Quadrillion', 'Quintillion'),        
        'to_19_id' : ('Nol', 'Satu', 'Dua', 'Tiga', 'Empat', 'Lima', 'Enam', 'Tujuh', 'Delapan', 'Sembilan', 'Sepuluh', 'Sebelas', 'Dua Belas', 'Tiga Belas', 'Empat Belas', 'Lima Belas', 'Enam Belas', 'Tujuh Belas', 'Delapan Belas', 'Sembilan Belas'),
        'tens_id'  : ('Dua Puluh', 'Tiga Puluh', 'Empat Puluh', 'Lima Puluh', 'Enam Puluh', 'Tujuh Puluh', 'Delapan Puluh', 'Sembilan Puluh'),
        'denom_id' : ('', 'Ribu', 'Juta', 'Miliar', 'Triliun', 'Biliun')
        }

    def terbilang(self, number, currency, bhs):
        number = '%.2f' % number
        units_name = ' ' + self.cur_name(currency) + ' '
        lis = str(number).split('.')
        start_word = self.english_number(int(lis[0]), bhs)
        end_word = self.english_number(int(lis[1]), bhs)
        cents_number = int(lis[1])
        cents_name = (cents_number > 1) and 'Sen' or 'sen'
        final_result_sen = start_word + units_name + end_word +' '+cents_name
        final_result = start_word + units_name
        if end_word == 'Nol' or end_word == 'Zero':
            final_result = final_result
        else:
            final_result = final_result_sen
         
        return final_result[:1].upper()+final_result[1:]
     
    def _convert_nn(self, val, bhs):
        tens = self.dic['tens_id']
        to_19 = self.dic['to_19_id']
        if bhs == 'en':
            tens = self.dic['tens']
            to_19 = self.dic['to_19']
        if val < 20:
            return to_19[val]
        for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
            if dval + 10 > val:
                if val % 10:
                    return dcap + ' ' + to_19[val % 10]
                return dcap
     
    def _convert_nnn(self, val, bhs):
        word = ''; rat = ' Ratus'; to_19 = self.dic['to_19_id']
        if bhs == 'en':
            rat = ' Hundred'
            to_19 = self.dic['to_19']
        (mod, rem) = (val % 100, val // 100)
        if rem == 1:
            word = 'Seratus'
            if mod > 0:
                word = word + ' '   
        elif rem > 1:
            word = to_19[rem] + rat
            if mod > 0:
                word = word + ' '
        if mod > 0:
            word = word + self._convert_nn(mod, bhs)
        return word
     
    def english_number(self, val, bhs):
        denom = self.dic['denom_id']
        if bhs == 'en':
            denom = self.dic['denom']
        if val < 100:
            return self._convert_nn(val, bhs)
        if val < 1000:
            return self._convert_nnn(val, bhs)
        for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
            if dval > val:
                mod = 1000 ** didx
                l = val // mod
                r = val - (l * mod)
                ret = self._convert_nnn(l, bhs) + ' ' + denom[didx]
                if r > 0:
                    ret = ret + ' ' + self.english_number(r, bhs)
                if bhs == 'id':
                    if val < 2000:
                        ret = ret.replace("Satu Ribu", "Seribu")
                return ret
     
    def cur_name(self, cur="idr"):
        cur = cur.lower()
        if cur=="usd":
            return "Dollars"
        elif cur=="aud":
            return "Dollars"
        elif cur=="idr":
            return "Rupiah"
        elif cur=="jpy":
            return "Yen"
        elif cur=="sgd":
            return "Dollars"
        elif cur=="usd":
            return "Dollars"
        elif cur=="eur":
            return "Euro"
        else:
            return cur

    def approval_hierarchy(self):
        approval_hierarchy = self.env['pam.approval.hierarchy'].search([('approval_type', '=', 'ap')])
        approval_hierarchy_lines = self.env['pam.approval.hierarchy.line'].search([('approval_hierarchy_id', '=', approval_hierarchy.id)],order='sequence desc')
        
        approval_names = []
        for approval_hierarchy_line in approval_hierarchy_lines:
            employee = self.env['hr.employee'].search([('department_id','=', approval_hierarchy_line.department_id.id),('job_id','=',approval_hierarchy_line.job_id.id)])
            approval_names.append(employee.name)

        return approval_names

    @api.depends('line_ids.debit')
    def compute_total_debit(self):
        for record in self:
            self.total_debit = sum(line.debit for line in record.line_ids)

    @api.depends('line_ids.credit')
    def compute_total_credit(self):
        for record in self:
            self.total_credit = sum(line.credit for line in record.line_ids)
            self.total_credit_name = self.terbilang(round(self.total_credit), 'idr', 'id')            

    @api.depends('total_debit', 'total_credit')
    def compute_total_diff(self):
        self.total_diff = self.total_debit - self.total_credit

    @api.depends('payment_ids.amount')
    def compute_total_payment(self):
        for record in self:
            self.total_payment = sum(line.amount for line in record.payment_ids)
        
        
        coas = ['21111110', '21121110', '21131110']
        total_debt = 0
        for line in self.line_ids:
            if line.coa_id.code in coas:
                total_debt = total_debt + line.credit

        self.total_payment_diff = total_debt - self.total_payment

    @api.depends('entry_date')
    def compute_code_month_year(self):
        self.code_month = self._get_code_month(self.entry_date)
        self.code_year = self._get_code_year(self.entry_date)
        self.code_number = self._get_new_code_number(self.entry_date)

        # message = _('Anda tidak bisa menambahkan data untuk bulan ini karena periode ini sudah di-Posting')
        # mess= {
        #             'title': _('Warning'),
        #             'message' : message
        #         }
        # return {'warning': mess}

    @api.model
    def create(self, vals):
        code_journal_type = vals['journal_type'].upper()
        code_month = self._get_code_month(vals['entry_date'])
        code_year = self._get_code_year(vals['entry_date'])

        suffix = self._get_suffix(vals['journal_type'].upper(), vals['entry_date'])

        # _logger.debug("Debug message suffix : %s", suffix)

        sequence = vals['code_number'] + suffix

        # _logger.debug("Debug message sequence : %s", sequence)

        vals.update({
            'name': sequence
        })
        res = super(PamJournalEntry, self).create(vals)
        return res

    def write(self, vals):
        for record in self:
            if 'code_number' in vals.keys() or 'entry_date' in vals.keys():
                
                code_number = record.code_number
                suffix = record.journal_type.upper() + '/' + datetime.strptime(record.entry_date, "%Y-%m-%d").strftime("%m") + '/' + datetime.strptime(record.entry_date, "%Y-%m-%d").strftime("%Y")
    
                if 'entry_date' in vals.keys():
    
                    code_journal_type = (record.journal_type).upper()
                    # code_journal_type = vals['journal_type'].upper()
                    code_month = record._get_code_month(vals['entry_date'])
                    code_year = record._get_code_year(vals['entry_date'])
                    
                    suffix = record._get_suffix((record.journal_type).upper(), vals['entry_date'])
                    # suffix = record._get_suffix(vals['journal_type'].upper(), vals['entry_date'])
    
                if 'code_number' in vals.keys():
                    code_number = vals['code_number']
    
                sequence = code_number + '/' + suffix
                vals.update({
                    'name': sequence
                })
    
            res = super(PamJournalEntry, record).write(vals)
            return res

    def payment(self):
        balances = self.env['pam.balance'].search([])
        for balance in balances:
            # if self.code_month == balance.period_month and self.code_year == balance.period_year:
            #     raise ValidationError(_('Bulan Dan Tahun Ini Sudah Terposting'))
            # else:
            if self.total_debit == 0 and self.total_credit == 0 :
                raise ValidationError(_("Anda harus memasukkan nilai Debit atau Kredit"))
            elif self.total_diff != 0:
                raise ValidationError(_("Nilai Debit dan Kredit harus seimbang"))
            else:
                sequence = self.code_number + '/' + self.code_journal_type + '/' + self.code_month + '/' + self.code_year
                self.write({'name' : sequence, 'state' : 'payment'})
                self.message_post(body="Journal Waiting for Payment")

    def is_asset(self):
        sql = """
            select COUNT(id) from pam_journal_entry_line x
            where x.journal_entry_id = %s and x.coa_id in (
            select c.coa_id from pam_report_configuration a
            inner join pam_report_configuration_line b on a.id = b.report_id
            inner join pam_report_configuration_detail c on b.id = c.report_line_id
            where a.report_type_id in (select id from pam_report_type where code in ('LAT', 'LRNT', 'LBPI', 'LATB')))
            """

        self._cr.execute(sql, (self.id,))
        result = self._cr.fetchone()
        if result[0] > 0:
            cek = True
        else:
            cek = False

        return cek

    def is_coa_asset(self, coa_id):
        sql = """
            select COUNT(c.coa_id) from pam_report_configuration a
            inner join pam_report_configuration_line b on a.id = b.report_id
            inner join pam_report_configuration_detail c on b.id = c.report_line_id
            where a.report_type_id in (select id from pam_report_type where code in ('LAT', 'LRNT', 'LBPI', 'LATB')) and c.coa_id = %s

            """

        self._cr.execute(sql, (coa_id,))
        result = self._cr.fetchone()
        if result[0] > 0:
            cek = True
        else:
            cek = False

        return cek

    def submit(self):
        balances = self.env['pam.balance'].search([])
        for balance in balances:
            # if self.code_month == balance.period_month and self.code_year == balance.period_year:
            #     raise ValidationError(_('Bulan Dan Tahun Ini Sudah Terposting'))
            # else:
            if self.total_debit == 0 and self.total_credit == 0 :
                raise ValidationError(_("Anda harus memasukkan nilai Debit atau Kredit"))
            elif self.total_diff != 0:
                raise ValidationError(_("Nilai Debit dan Kredit harus seimbang"))
            else:
                if self.journal_type in ('ju','ap','in'):
                    
                    cek_asset = self.is_asset()

                    if cek_asset:
                        for line in self.line_ids:
                            if self.is_coa_asset(line.coa_id.id):
                                create_asset = self.env['pam.asset'].create({
                                    'name' : self.remark,
                                    'journal_id': self.id,
                                    'coa_id' : line.coa_id.id,
                                    'get_month' : ((datetime.strptime(self.entry_date, "%Y-%m-%d")).strftime("%m")),
                                    'years' : (datetime.strptime(self.entry_date, "%Y-%m-%d")).strftime("%Y"),
                                    'price' : line.debit + line.credit
                                    })

                        # asset_lines = []

                        # for line in self.line_ids:
                        #     asset_lines.append({
                        #         'coa_id': line.coa_id.id,
                        #         'price': line.debit + line.credit
                        #         })

                        # view_id = self.env.ref('pam_accounting.view_pam_asset_wizard').id

                        # return {
                        #     'name': 'Buat Asset',
                        #     'type': 'ir.actions.act_window',
                        #     'view_type': 'form',
                        #     'view_mode': 'form',
                        #     'view_id': view_id,
                        #     'res_model': 'pam.asset.wizard',
                        #     'target': 'new',
                        #     'context': {'default_name': '', 'default_journal_entry_id': self.id, 'default_line_ids': asset_lines},
                        #     }

                if self.state == 'draft':
                    sequence = self.code_number + '/' + self.code_journal_type + '/' + self.code_month + '/' + self.code_year
                    self.write({'name' : sequence, 'state' : 'submit'})
                    self.message_post(body="Journal Submitted")
                else:
                    if self.state == 'paid':
                        self.payment_submit()

                    self.write({'state' : 'submit'})
                    self.message_post(body="Journal Submitted")
                
                if self.journal_type == 'ap':
                    self.action_refresh_printer_data()

    def action_refresh_printer_data(self):
        pass

    def co_submit(self):
        self.write({'state' : 'submit'})
        self.message_post(body="Journal Submitted")

    def paid(self):

        if self.payment_type == 'cheque' and self.total_payment_diff != 0:
            raise ValidationError(_("Jumlah Pembayaran yang Anda masukkan tidak sesuai"))
        else:
            self.write({'state' : 'paid'})
            self.message_post(body="Voucher Paid")                

        # if self.coa_id.id == False or self.payment_date == False :
        #     raise ValidationError(_("Anda harus memasukkan Kode Perkiraan Kas/Bank dan Tanggal Pembayaran"))
        # else:
        #     self.write({'state' : 'paid'})
        #     self.message_post(body="Voucher Paid")                

    def posted(self):
        self.write({'state' : 'posted'})
        self.message_post(body="Journal Posted")                

    def payment_submit(self):


        # if self.payment_type == 'cheque':
        #     payment_date = self.payment_date
        # else:
        #     payment_date = self.coh_date

        payment_date = self.payment_date

        code_number = self._get_new_co_code_number(payment_date)

        _logger.debug("Debug message code_number : %s", code_number)

        journal_co = self.env['pam.journal.entry'].create({
            'journal_type': 'co',
            'code_number': code_number,
            'code_journal_type': 'CO',
            'entry_date': payment_date,
            'link_journal_id': self.id,
            'remark': self.name + ' - ' + datetime.strptime(self.entry_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
            'state': 'draft',
            'create_uid': self.env.uid
        })

        coa_co = self.env['pam.coa'].search([('code', '=', '21131110')], limit=1)

        coas = ['21111110', '21121110', '21131110']
        total_debt = 0
        for line in self.line_ids:
            if line.coa_id.code in coas:
                total_debt = total_debt + line.credit


        self.env['pam.journal.entry.line'].sudo().create({
            'journal_entry_id': journal_co.id,
            'coa_id': coa_co.id,
            'debit': total_debt,
            'credit': 0
            })

        if self.payment_type == 'cheque':

            for payment in self.payment_ids:
                self.env['pam.journal.entry.line'].sudo().create({
                    'journal_entry_id': journal_co.id,
                    'coa_id': payment.coa_id.id,
                    'debit': 0,
                    'credit': payment.amount
                })
        else:

            self.env['pam.journal.entry.line'].sudo().create({
                'journal_entry_id': journal_co.id,
                'coa_id': self.coh_id.coa_id.id,
                'debit': 0,
                'credit': total_debt
            })


        journal_co.co_submit()
        self.message_post(body="Journal Submitted")                


    def payment_reject(self):
        self.write({'state' : 'payment'})

    @api.model
    def get_data(self):

        data = {
            'id' : 1
        }

        return data

    def generate_excel_report(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
    
            filename = '%s.xlsx' % (record.name,)
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'bold': True, 'font': 'Arial', 'font_size': 20, 'align': 'center'})
            write = workbook.add_format({'font': 'Arial', 'font_size': 11, 'align': 'right'})
            header = workbook.add_format({'bold': True, 'font': 'Arial', 'font_size': 11, 'align': 'center', 'border': 1})
            border = workbook.add_format({'border': 1, 'font': 'Arial', 'font_size': 11, 'align': 'left'})
            border_center = workbook.add_format({'border': 1, 'font': 'Arial', 'font_size': 11, 'align': 'center'})
            center = workbook.add_format({'font': 'Arial', 'font_size': 11, 'align': 'center'})
            currency_format = workbook.add_format({'font': 'Arial', 'font_size': 11, 'num_format': '#,##0.00', 'border': 1})
            currency_bold = workbook.add_format({'bold': True, 'font': 'Arial', 'font_size': 11, 'num_format': '#,##0.00', 'border': 1})
    
            sheet.set_column(0, 11, 40)
            sheet.set_column(1, 11, 20)
            sheet.set_column(2, 11, 20)
            sheet.set_column(3, 11, 20)
    
            company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            logo = BytesIO(base64.b64decode(company.logo))
    
            sheet.insert_image(3, 0, 'logo.jpg', {'image_data' : logo, 'x_scale': 0.7, 'y_scale': 0.7, 'x_offset': 15})
    
            sheet.merge_range(3, 0, 3, 3, dict(record._fields['journal_type'].selection).get(record.journal_type).upper(), title)
            sheet.write(6, 3, 'Nomor : ' + (record.name).upper(), write)
            sheet.write(7, 3, 'Tanggal : ' + datetime.strptime(record.entry_date, "%Y-%m-%d").strftime("%d %B %Y").upper(), write)
            # sheet.merge_range(0, 4, 3, 4, 'SAMPAI DENGAN BULAN : ' + datetime.strptime(record.start_date, "%Y-%m-%d").strftime("%d-%m-%Y") + ' s/d ' + datetime.strptime(record.end_date, "%Y-%m-%d").strftime("%d-%m-%Y"), bold)
    
            sheet.merge_range(9, 0, 10, 0, 'NAMA PERKIRAAN', header)
            sheet.merge_range(9, 1, 10, 1, 'KODE PERKIRAAN', header)
            sheet.merge_range(9, 2, 9, 3, 'JUMLAH', header)
            sheet.write(10, 2, 'DEBET', header)
            sheet.write(10, 3, 'KREDIT', header)
    
            y = 11
            
            debit = 0
            credit = 0
            for line in record.line_ids:
                sheet.write(y, 0, line.coa_id_name, border)
                sheet.write(y, 1, line.coa_id.code, border_center)
                sheet.write(y, 2, line.debit, currency_format)
                sheet.write(y, 3, line.credit, currency_format)
    
                y += 1
                debit += line.debit
                credit += line.credit
    
            sheet.write(y, 0, '', border)
            sheet.write(y, 1, '', border_center)
            sheet.write(y, 2, '', currency_bold)
            sheet.write(y, 3, '', currency_bold)
            y += 1
            sheet.write(y, 0, '', border)
            sheet.write(y, 1, '', border_center)
            sheet.write(y, 2, '', currency_bold)
            sheet.write(y, 3, '', currency_bold)
            y += 1
            sheet.write(y, 0, '', border)
            sheet.write(y, 1, '', border_center)
            sheet.write(y, 2, debit, currency_bold)
            sheet.write(y, 3, credit, currency_bold)
            y += 1
            sheet.write(y, 0, '', border)
            sheet.write(y, 1, '', border_center)
            sheet.write(y, 2, '', currency_bold)
            sheet.write(y, 3, '', currency_bold)
            y += 1
    
            wrap_text = workbook.add_format({'border': True, 'font': 'Arial', 'font_size': 11})
            wrap_text.set_text_wrap()
            wrap_text.set_align('top')
            sheet.merge_range(y, 0, y + 1, 3, 'Penjelasan : ' + record.remark, wrap_text)
    
            report_type = self.env['pam.report.type'].search([('code', '=', 'JR')])
            
            report_type_ttd = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','BOOKED')])
            report_type_ttd2 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','CREATED')])
            report_type_ttd3 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','VERIFIED')])
            report_type_ttd4 = self.env['pam.report.type.ttd'].search([('report_id', '=', report_type.id), ('code','=','APPROVED')])
    
            y += 3
            sheet.write(y, 0, report_type_ttd.name, center)
            sheet.write(y, 1, report_type_ttd2.name, center)
            sheet.write(y, 2, report_type_ttd3.name, center)
            sheet.write(y, 3, report_type_ttd4.name, center)
            y += 3
            sheet.write(y, 0, record.create_uid.name, center)
            sheet.write(y, 1, self.env.user.name, center)
            sheet.write(y, 2, report_type_ttd3.name_ttd, center)
            sheet.write(y, 3, report_type_ttd4.name_ttd, center)
            # sheet.merge_range(y, 0, y, 3, "Dibukukan oleh,          Dibuat oleh,            Diperiksa oleh,         Disetujui oleh,", center)
            # y += 3
            # sheet.merge_range(y, 0, y, 3, "_______________          ____________            _______________         _______________", center)
    
            workbook.close()
            fp.seek(0)
            record.file_bin = base64.encodestring(fp.read())
            record.file_name = filename
    

class PamJournalEntryLine(models.Model):
    _name = 'pam.journal.entry.line'

    journal_entry_id  = fields.Many2one('pam.journal.entry', required=True, index=True, ondelete='cascade')
    coa_id      = fields.Many2one('pam.coa', string='Kode Perkiraan', required=True, index=True, domain="([('transactional', '=', True)])")
    coa_id_name = fields.Char(string='Nama Perkiraan')
    debit       = fields.Float(default=0, required=True)
    credit      = fields.Float(default=0, required=True)

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name


class PamJournalPayment(models.Model):
    _name = 'pam.journal.payment'
    _description = "COH"

    name = fields.Char(string="No. COH")
    coa_id      = fields.Many2one('pam.coa', string='Kode Perkiraan', required=True, index=True, domain="([('transactional', '=', True)])")
    coa_id_name = fields.Char()
    cheque_number = fields.Char(string='Cek No.')
    payment_date = fields.Date(string="Tanggal")
    total_payment = fields.Float(string="Jumlah", compute='_compute_total_payment')
    # line_ids = fields.Many2one('pam.journal.entry', 'coh_id')

    file_bin = fields.Binary()
    file_name = fields.Char(string="File Name", size=64)

    line_ids = fields.One2many('pam.journal.entry', 'coh_id')

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name

    @api.depends('line_ids.total_debit')
    def _compute_total_payment(self):
        for record in self:
            self.total_payment = sum(line.total_debit for line in record.line_ids)

    def export_report_pdf(self):
        journals = []
        for line in self.line_ids:
            journals.append([line.name, line.remark, line.vendor_id.name])
            
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': self.name,
                'coa_id': self.coa_id.bank_name,
                'cheque_number': self.cheque_number,
                'payment_date': (datetime.strptime(self.payment_date, "%Y-%m-%d")).strftime("%d-%B-%Y"),
                'total_payment': self.total_payment,
                'journals': journals
            },
        }

        return self.env.ref('pam_accounting.action_pam_journal_payment_report').report_action(self, data=data)

    def export_report_xls(self):
        for record in self:
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            filename = 'REKAPITULASI PEMBAYARAN'
            # filename = '%s - %s.xlsx' % ('Laporan Estimasi', datetime.strptime(record.date, "%Y-%m-%d").strftime("%d/%m/%Y"))
            
            sheet = workbook.add_worksheet()
            title = workbook.add_format({'font_size': 18, 'bold': True})
            bold = workbook.add_format({'bold': True})
            tujuan = workbook.add_format({'align': 'left', 'bold': True})
            align_right = workbook.add_format({'align': 'right'})
            merge = workbook.add_format({'bold': True, 'border': True})
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            date_format = workbook.add_format({'bold': True, 'num_format': 'dd-mm-yyyy'})
            num_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': True})
            bottom = workbook.add_format({'bottom': 1})
            top = workbook.add_format({'top': 1})
            right = workbook.add_format({'right': 1})
            border = workbook.add_format({'border': True})
            judul_jumlah = workbook.add_format({'top': 1, 'bottom': 1, 'align': 'right'})
            judul = workbook.add_format({'bottom': 1, 'align': 'center', 'bold': True})
            left = workbook.add_format({'left': 1})
            str_format = workbook.add_format({'text_wrap': True})
            currency_format = workbook.add_format({'text_wrap': True, 'num_format': '#,##0.00', 'border': True})
            footer = workbook.add_format({'bold': True, 'align': 'right', 'border': True})
    
            sheet.set_column(12, 0, 5)
            sheet.set_column(12, 1, 15)
            sheet.set_column(12, 2, 15)
            sheet.set_column(12, 3, 25)
            sheet.set_column(12, 4, 40)
            sheet.set_column(12, 5, 15)
    
            sheet.write(0, 5, 'No: ' + record.name, str_format)
            sheet.write(1, 5, 'Tgl: ' + record.payment_date, str_format)
    
            sheet.merge_range(2, 4, 2, 5, 'Kepada Yth :', tujuan)
            sheet.merge_range(3, 4, 3, 5, 'Kepala Bagian Keuangan', tujuan)
            sheet.merge_range(4, 4, 4, 5, 'PDAM Tirta Pakuan Kota Bogor', tujuan)
            sheet.merge_range(5, 4, 5, 5, 'Di Tempat', tujuan)
    
            sheet.merge_range(6, 0, 6, 5, 'Dengan Hormat,', bold)
            sheet.merge_range(7, 0, 7, 3, 'Mohon dapat mengalihkan kas di Bank : ' + record.coa_id.bank_name, bold)
            sheet.merge_range(7, 4, 7, 5, 'No. Cek : ' + record.cheque_number, bold)
            sheet.merge_range(8, 0, 8, 5, 'pada kas perusahaan untuk pembayaran tagihan - tagihan sebagai berikut : ', bold)
    
            sheet.merge_range(10, 1, 10, 4, 'REKAPITULASI PEMBAYARAN VOUCHER MELALUI KAS TUNAI', judul)
    
            sheet.write(12, 0, 'No', border)
            sheet.write(12, 1, 'NO VOUCHER', border)
            sheet.write(12, 2, 'TGL VOUCHER', border)
            sheet.write(12, 3, 'KEPADA', border)
            sheet.write(12, 4, 'URAIAN', border)
            sheet.write(12, 5, '', border)
    
            no = 1
            total_jumlah = 0
            y = 13
            
            for line in record.line_ids:
                sheet.write(y, 0, no, border)
                sheet.write(y, 1, line.name, border)
                sheet.write(y, 2, (datetime.strptime(record.payment_date, "%Y-%m-%d").strftime("%d-%B-%Y")), border)
                sheet.write(y, 3, line.vendor_id.name, border)
                sheet.write(y, 4, line.remark, border)
                sheet.write(y, 5, record.total_payment, currency_format)
    
                no += 1
                total_jumlah += record.total_payment
                y += 1
    
            sheet.merge_range(y, 0, y, 4, 'JUMLAH', footer)
            sheet.write(y, 5, total_jumlah, currency_format)
    
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


class PamJournalEntryPayment(models.Model):
    _name = 'pam.journal.payment.line'

    journal_entry_id  = fields.Many2one('pam.journal', required=True, index=True, ondelete='cascade')
    coa_id      = fields.Many2one('pam.coa', string='Kode Perkiraan', required=True, index=True, domain="([('transactional', '=', True)])")
    coa_id_name = fields.Char(string='Nama Perkiraan')
    cheque_number = fields.Char(string='Cek No.')
    amount      = fields.Float(string="Jumlah", default=0, required=True)

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name


class PamJournalPaymentReport(models.AbstractModel):
    _name = 'report.pam_accounting.report_journal_payment_report_template'
    _template ='pam_accounting.report_journal_payment_template'

    @api.model
    def get_report_values(self, docids, data=None):
        name = data['form']['name']
        coa_id = data['form']['coa_id']
        cheque_number = data['form']['cheque_number']
        payment_date = data['form']['payment_date']
        total_payment = data['form']['total_payment']
        journals = data['form']['journals']

        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'name': name,
            'coa_id': coa_id,
            'cheque_number': cheque_number,
            'payment_date': payment_date,
            'total_payment': total_payment,
            'journals': journals
        }