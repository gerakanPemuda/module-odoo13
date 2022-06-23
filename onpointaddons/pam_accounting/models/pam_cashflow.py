from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class PamCashflow(models.Model):
    _name = 'pam.cashflow'
    _description = "Kas Kecil"
    _inherit = ['mail.thread']

    def _default_date(self):
        return (datetime.now() + relativedelta(hours=7)).date()

    def _default_coa_id(self):
         return self.env['pam.coa'].search([('code', '=', '11111110')], limit=1).id

    name = fields.Char(string='Nomor')
    department_id = fields.Many2one('hr.department', string='Departemen', required=True, index=True)
    entry_date = fields.Date(string='Tanggal', required=True, default=_default_date)
    coa_id = fields.Many2one('pam.coa', string='Kas', required=True, index=True, domain="([('code', '=', '11111110')])", default=_default_coa_id)
    period = fields.Char(string='Periode')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('posted', 'Posted')
    ], default='draft')
    total_amount = fields.Float(compute='compute_total_amount')
    line_ids = fields.One2many('pam.cashflow.line', 'cashflow_id')

    @api.depends('line_ids.amount')
    def compute_total_amount(self):
        for record in self:
            self.total_amount = sum(line.amount for line in record.line_ids)

    def submit(self):
        if self.total_amount == 0 :
            raise ValidationError(_("Anda harus memasukkan nilai lebih besar dari 0"))
        else:
            if self.name == False: 
                sequence = self.env['ir.sequence'].next_by_code('cashflow') or ''
                self.write({'name' : sequence, 'state' : 'submit'})
                self.message_post(body="Submit Kas Kecil")                

    def posted(self):

        txtquery = """
            SELECT coa_id, sum(amount) as debit, 0 as credit 
            FROM pam_cashflow_line
            WHERE cashflow_id = %s
            GROUP BY coa_id
        """        

        self._cr.execute(txtquery, (self.id,))
        cashflow_lines = self._cr.fetchall()

        data = []
        for coa_id, debit, credit in cashflow_lines:
            
            vals = {
                'coa_id': coa_id,
                'debit': debit,
                'credit': credit 
            }

            row = (0, 0, vals)
            data.append(row)
        
        vals = {
            'coa_id': self.coa_id.id,
            'debit': 0,
            'credit': self.total_amount 
        }

        row = (0, 0, vals)
        data.append(row)

        journal_row = {
            'journal_type': 'co',
            'refers_to': 'pam.cashflow,' + str(self.id),
            'remark': self.name,
            'line_ids': data
        }

        # _logger.debug("Debug message : %s", journal_row)

        journal = self.env['pam.journal.entry'].create(journal_row)
        journal.submit()
        journal.posted()

        self.write({'state' : 'posted'})
        self.message_post(body="Posting Kas Kecil")                


class PamCashflowLine(models.Model):
    _name = 'pam.cashflow.line'

    cashflow_id  = fields.Many2one('pam.cashflow', required=True, index=True)
    cashflow_state = fields.Selection('pam.cashflow', related='cashflow_id.state', default='draft')
    coa_id      = fields.Many2one('pam.coa', string='Kode Perkiraan', index=True, domain="([('transactional', '=', True)])")
    transaction_date = fields.Date(string='Tanggal', required=True)
    notes       = fields.Char(string='Keterangan', required=True)
    amount       = fields.Float(default=0, required=True)