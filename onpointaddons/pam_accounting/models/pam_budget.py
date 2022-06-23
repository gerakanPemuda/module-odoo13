from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class PamBudget(models.Model):
    _name = 'pam.budget'
    _description = 'Anggaran'
    _inherit = ['mail.thread']
    _order = 'years, budget_type'

    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = current_year - 3
        results = []
        for year in range(min_year, current_year):
            results.append((str(year), str(year)))
        return results

    name = fields.Char()
    years = fields.Selection(_get_years, string='Tahun Anggaran', default=_default_year, readonly=True, store=True)
    budget_type = fields.Selection([
        ('ops', 'Biaya Operasi, Pemeliharaan dan Tenaga Kerja'),
        ('inv', 'Anggaran Kebutuhan Alat/alat dan Investasi (AKA)')
    ], readonly=True, store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('approve', 'Approve')
    ], default='draft', string='Status')
    line1_ids = fields.One2many('pam.budget.line1', 'budget_id')

    def to_submit(self):
        self.write({
            'state': 'submit'
            })

    def to_approve(self):
        self.write({
            'state': 'approve'
            })

class PamBudgetLine1(models.Model):
    _name = 'pam.budget.line1'
    _order = 'years, department_id'

    budget_id  = fields.Many2one('pam.budget', index=True, ondelete='cascade')
    name = fields.Char(store=True)
    years = fields.Char(string='Tahun Anggaran', index=True, store=True)
    department_id = fields.Many2one('hr.department', string='Department', index=True, store=True)
    month_1 = fields.Float(string='I', compute='compute_month_total')
    month_2 = fields.Float(string='II', compute='compute_month_total')
    month_3 = fields.Float(string='III', compute='compute_month_total')
    month_4 = fields.Float(string='IV', compute='compute_month_total')
    month_5 = fields.Float(string='V', compute='compute_month_total')
    month_6 = fields.Float(string='VI', compute='compute_month_total')
    month_7 = fields.Float(string='VII', compute='compute_month_total')
    month_8 = fields.Float(string='VIII', compute='compute_month_total')
    month_9 = fields.Float(string='IX', compute='compute_month_total')
    month_10 = fields.Float(string='X', compute='compute_month_total')
    month_11 = fields.Float(string='XI', compute='compute_month_total')
    month_12 = fields.Float(string='XII', compute='compute_month_total')
    month_1_value = fields.Float(string='I', compute='compute_month_total_value')
    month_2_value = fields.Float(string='II', compute='compute_month_total_value')
    month_3_value = fields.Float(string='III', compute='compute_month_total_value')
    month_4_value = fields.Float(string='IV', compute='compute_month_total_value')
    month_5_value = fields.Float(string='V', compute='compute_month_total_value')
    month_6_value = fields.Float(string='VI', compute='compute_month_total_value')
    month_7_value = fields.Float(string='VII', compute='compute_month_total_value')
    month_8_value = fields.Float(string='VIII', compute='compute_month_total_value')
    month_9_value = fields.Float(string='IX', compute='compute_month_total_value')
    month_10_value = fields.Float(string='X', compute='compute_month_total_value')
    month_11_value = fields.Float(string='XI', compute='compute_month_total_value')
    month_12_value = fields.Float(string='XII', compute='compute_month_total_value')
    line2_ids = fields.One2many('pam.budget.line2', 'budget_line1_id')


    @api.depends('line2_ids.month_1', 'line2_ids.month_2', 'line2_ids.month_3', 'line2_ids.month_4', 'line2_ids.month_5', 'line2_ids.month_6', 'line2_ids.month_7', 'line2_ids.month_8', 'line2_ids.month_9', 'line2_ids.month_10', 'line2_ids.month_11', 'line2_ids.month_12')
    def compute_month_total(self):
        self.month_1 = sum(line2.month_1 for line2 in self.line2_ids)
        self.month_2 = sum(line2.month_2 for line2 in self.line2_ids)
        self.month_3 = sum(line2.month_3 for line2 in self.line2_ids)
        self.month_4 = sum(line2.month_4 for line2 in self.line2_ids)
        self.month_5 = sum(line2.month_5 for line2 in self.line2_ids)
        self.month_6 = sum(line2.month_6 for line2 in self.line2_ids)
        self.month_7 = sum(line2.month_7 for line2 in self.line2_ids)
        self.month_8 = sum(line2.month_8 for line2 in self.line2_ids)
        self.month_9 = sum(line2.month_9 for line2 in self.line2_ids)
        self.month_10 = sum(line2.month_10 for line2 in self.line2_ids)
        self.month_11 = sum(line2.month_11 for line2 in self.line2_ids)
        self.month_12 = sum(line2.month_12 for line2 in self.line2_ids)


    @api.depends('line2_ids.month_1_value', 'line2_ids.month_2_value', 'line2_ids.month_3_value', 'line2_ids.month_4_value', 'line2_ids.month_5_value', 'line2_ids.month_6_value', 'line2_ids.month_7_value', 'line2_ids.month_8_value', 'line2_ids.month_9_value', 'line2_ids.month_10_value', 'line2_ids.month_11_value', 'line2_ids.month_12_value')
    def compute_month_total_value(self):
        self.month_1_value = sum(line2.month_1_value for line2 in self.line2_ids)
        self.month_2_value = sum(line2.month_2_value for line2 in self.line2_ids)
        self.month_3_value = sum(line2.month_3_value for line2 in self.line2_ids)
        self.month_4_value = sum(line2.month_4_value for line2 in self.line2_ids)
        self.month_5_value = sum(line2.month_5_value for line2 in self.line2_ids)
        self.month_6_value = sum(line2.month_6_value for line2 in self.line2_ids)
        self.month_7_value = sum(line2.month_7_value for line2 in self.line2_ids)
        self.month_8_value = sum(line2.month_8_value for line2 in self.line2_ids)
        self.month_9_value = sum(line2.month_9_value for line2 in self.line2_ids)
        self.month_10_value = sum(line2.month_10_value for line2 in self.line2_ids)
        self.month_11_value = sum(line2.month_11_value for line2 in self.line2_ids)
        self.month_12_value = sum(line2.month_12_value for line2 in self.line2_ids)

    def add_data(self):
        for record in self:
            view_id = self.env.ref('pam_accounting.view_pam_budget_line2_form').id
    
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'res_model': 'pam.budget.line2',
                'target': 'current',
                'context': {'default_budget_line1_id': record.id, 'default_years': record.years, 'default_department_id': record.department_id.id},
                }
    
            # return {
            #     'name': 'Buat Pembayaran',
            #     'type': 'ir.actions.act_window',
            #     'view_type': 'form',
            #     'view_mode': 'form',
            #     'view_id': view_id,
            #     'res_model': 'payment',
            #     'target': 'new',
            #     'context': {'default_invoice_id': record.id, 'default_date': record.date},
            #     }

    def line1_view(self):
        for record in self:
            view_id = self.env.ref('pam_accounting.view_pam_budget_line1_form').id
    
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': record.id,
                'view_id': view_id,
                'res_model': 'pam.budget.line1',
                }


class PamBudgetLine2(models.Model):
    _name = 'pam.budget.line2'
    _rec_name = 'coa_id'
    _order = 'years, department_id, coa_id'

    budget_line1_id  = fields.Many2one('pam.budget.line1', index=True, ondelete='cascade')
    name = fields.Char()
    years = fields.Char(string='Tahun Anggaran', index=True, store=True)
    department_id = fields.Many2one('hr.department', string='Department', index=True, store=True)
    coa_id = fields.Many2one('pam.coa', string='Kode Akun', index=True)
    coa_id_name = fields.Char(string='Nama Akun', index=True)
    month_1 = fields.Float(string='I', compute='compute_month_total')
    month_2 = fields.Float(string='II', compute='compute_month_total')
    month_3 = fields.Float(string='III', compute='compute_month_total')
    month_4 = fields.Float(string='IV', compute='compute_month_total')
    month_5 = fields.Float(string='V', compute='compute_month_total')
    month_6 = fields.Float(string='VI', compute='compute_month_total')
    month_7 = fields.Float(string='VII', compute='compute_month_total')
    month_8 = fields.Float(string='VIII', compute='compute_month_total')
    month_9 = fields.Float(string='IX', compute='compute_month_total')
    month_10 = fields.Float(string='X', compute='compute_month_total')
    month_11 = fields.Float(string='XI', compute='compute_month_total')
    month_12 = fields.Float(string='XII', compute='compute_month_total')
    month_1_value = fields.Float(string='I', compute='compute_month_total_value')
    month_2_value = fields.Float(string='II', compute='compute_month_total_value')
    month_3_value = fields.Float(string='III', compute='compute_month_total_value')
    month_4_value = fields.Float(string='IV', compute='compute_month_total_value')
    month_5_value = fields.Float(string='V', compute='compute_month_total_value')
    month_6_value = fields.Float(string='VI', compute='compute_month_total_value')
    month_7_value = fields.Float(string='VII', compute='compute_month_total_value')
    month_8_value = fields.Float(string='VIII', compute='compute_month_total_value')
    month_9_value = fields.Float(string='IX', compute='compute_month_total_value')
    month_10_value = fields.Float(string='X', compute='compute_month_total_value')
    month_11_value = fields.Float(string='XI', compute='compute_month_total_value')
    month_12_value = fields.Float(string='XII', compute='compute_month_total_value')
    line3_ids = fields.One2many('pam.budget.line3', 'budget_line2_id')

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id :
            self.name = self.coa_id.name
        else:
            self.name = False

    @api.depends('line3_ids.month_1', 'line3_ids.month_2', 'line3_ids.month_3', 'line3_ids.month_4', 'line3_ids.month_5', 'line3_ids.month_6', 'line3_ids.month_7', 'line3_ids.month_8', 'line3_ids.month_9', 'line3_ids.month_10', 'line3_ids.month_11', 'line3_ids.month_12')
    def compute_month_total(self):
        line3_ids = self.env['pam.budget.line3'].search([('budget_line2_id', '=', self.id), ('budget_state', '=', 'active')])
        self.month_1 = sum(line3.month_1 for line3 in line3_ids)
        self.month_2 = sum(line3.month_2 for line3 in line3_ids)
        self.month_3 = sum(line3.month_3 for line3 in line3_ids)
        self.month_4 = sum(line3.month_4 for line3 in line3_ids)
        self.month_5 = sum(line3.month_5 for line3 in line3_ids)
        self.month_6 = sum(line3.month_6 for line3 in line3_ids)
        self.month_7 = sum(line3.month_7 for line3 in line3_ids)
        self.month_8 = sum(line3.month_8 for line3 in line3_ids)
        self.month_9 = sum(line3.month_9 for line3 in line3_ids)
        self.month_10 = sum(line3.month_10 for line3 in line3_ids)
        self.month_11 = sum(line3.month_11 for line3 in line3_ids)
        self.month_12 = sum(line3.month_12 for line3 in line3_ids)

    @api.depends('line3_ids.month_1_value', 'line3_ids.month_2_value', 'line3_ids.month_3_value', 'line3_ids.month_4_value', 'line3_ids.month_5_value', 'line3_ids.month_6_value', 'line3_ids.month_7_value', 'line3_ids.month_8_value', 'line3_ids.month_9_value', 'line3_ids.month_10_value', 'line3_ids.month_11_value', 'line3_ids.month_12_value')
    def compute_month_total_value(self):
        line3_ids = self.env['pam.budget.line3'].search([('budget_line2_id', '=', self.id), ('budget_state', '=', 'active')])
        self.month_1_value = sum(line3.month_1_value for line3 in line3_ids)
        self.month_2_value = sum(line3.month_2_value for line3 in line3_ids)
        self.month_3_value = sum(line3.month_3_value for line3 in line3_ids)
        self.month_4_value = sum(line3.month_4_value for line3 in line3_ids)
        self.month_5_value = sum(line3.month_5_value for line3 in line3_ids)
        self.month_6_value = sum(line3.month_6_value for line3 in line3_ids)
        self.month_7_value = sum(line3.month_7_value for line3 in line3_ids)
        self.month_8_value = sum(line3.month_8_value for line3 in line3_ids)
        self.month_9_value = sum(line3.month_9_value for line3 in line3_ids)
        self.month_10_value = sum(line3.month_10_value for line3 in line3_ids)
        self.month_11_value = sum(line3.month_11_value for line3 in line3_ids)
        self.month_12_value = sum(line3.month_12_value for line3 in line3_ids)

    def line2_view(self):
        for record in self:
            view_id = self.env.ref('pam_accounting.view_pam_budget_line2_form').id
    
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': record.id,
                'view_id': view_id,
                'res_model': 'pam.budget.line2',
                }


class PamBudgetLine3(models.Model):
    _name = 'pam.budget.line3'
    _rec_name = 'remark'
    _order = 'job_id, remark'

    budget_line2_id  = fields.Many2one('pam.budget.line2', index=True, ondelete='cascade')
    budget_state = fields.Selection([
        ('active', 'Aktif'),
        ('inactive', 'Non-aktif')
    ], default='active')
    active = fields.Boolean(default=True)
    years = fields.Char('pam.budget.line2', related='budget_line2_id.years')
    department_id = fields.Many2one('pam.budget.line2', related='budget_line2_id.department_id')
    job_id = fields.Many2one('hr.job', index=True)
    remark = fields.Char(string='Keterangan')
    month_1 = fields.Float(string='I', default=0)
    month_2 = fields.Float(string='II', default=0)
    month_3 = fields.Float(string='III', default=0)
    month_4 = fields.Float(string='IV', default=0)
    month_5 = fields.Float(string='V', default=0)
    month_6 = fields.Float(string='VI', default=0)
    month_7 = fields.Float(string='VII', default=0)
    month_8 = fields.Float(string='VIII', default=0)
    month_9 = fields.Float(string='IX', default=0)
    month_10 = fields.Float(string='X', default=0)
    month_11 = fields.Float(string='XI', default=0)
    month_12 = fields.Float(string='XII', default=0)
    month_1_value = fields.Float(string='I', compute='compute_month_total_value', store=True)
    month_2_value = fields.Float(string='II', compute='compute_month_total_value', store=True)
    month_3_value = fields.Float(string='III', compute='compute_month_total_value', store=True)
    month_4_value = fields.Float(string='IV', compute='compute_month_total_value', store=True)
    month_5_value = fields.Float(string='V', compute='compute_month_total_value', store=True)
    month_6_value = fields.Float(string='VI', compute='compute_month_total_value', store=True)
    month_7_value = fields.Float(string='VII', compute='compute_month_total_value', store=True)
    month_8_value = fields.Float(string='VIII', compute='compute_month_total_value', store=True)
    month_9_value = fields.Float(string='IX', compute='compute_month_total_value', store=True)
    month_10_value = fields.Float(string='X', compute='compute_month_total_value', store=True)
    month_11_value = fields.Float(string='XI', compute='compute_month_total_value', store=True)
    month_12_value = fields.Float(string='XII', compute='compute_month_total_value', store=True)
    sub_total = fields.Float(string='Total', compute='compute_month_total_value')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('job_id', operator, name), ('remark', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        budget_line3 = self.search(domain + args, limit=limit)
        return budget_line3.name_get()

    @api.depends('job_id', 'remark')
    def name_get(self):
        result = []
        for budget_line3 in self:
            remark = ''
            if budget_line3.remark:
                remark = ' - ' + budget_line3.remark

            name = budget_line3.job_id.name + remark
            result.append((budget_line3.id, name))
        return result

    @api.depends('month_1', 'month_2', 'month_3', 'month_4', 'month_5', 'month_6', 'month_7', 'month_8', 'month_9', 'month_10', 'month_11', 'month_12')
    def compute_month_total_value(self):
        self.month_1_value = self.month_1 * 1000
        self.month_2_value = self.month_2 * 1000
        self.month_3_value = self.month_3 * 1000
        self.month_4_value = self.month_4 * 1000
        self.month_5_value = self.month_5 * 1000
        self.month_6_value = self.month_6 * 1000
        self.month_7_value = self.month_7 * 1000
        self.month_8_value = self.month_8 * 1000
        self.month_9_value = self.month_9 * 1000
        self.month_10_value = self.month_10 * 1000
        self.month_11_value = self.month_11 * 1000
        self.month_12_value = self.month_12 * 1000
        self.sub_total = self.month_1_value + self.month_2_value + self.month_3_value + self.month_4_value + self.month_5_value + self.month_6_value + self.month_7_value + self.month_8_value + self.month_9_value + self.month_10_value + self.month_11_value + self.month_12_value
