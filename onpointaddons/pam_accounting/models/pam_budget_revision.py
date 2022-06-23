from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class PamBudgetRevision(models.Model):
    _name = 'pam.budget.revision'
    _rec_name = 'years'
    _inherit = ['mail.thread']

    def _default_date(self):
        return (datetime.now() + relativedelta(hours=7)).date()

    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = current_year - 2
        results = []
        for year in range(min_year, current_year):
            str_year = str(year)
            results.append((str_year, str_year))
        return results

    years = fields.Selection(_get_years, string='Tahun Anggaran', required=True, default=_default_year)
    revision_date = fields.Date(string='Tanggal', required=True, default=_default_date)    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('approved', 'Approve')
    ], default='draft', string='Status')

    line_ids = fields.One2many('pam.budget.revision.line', 'budget_revision_id')

    # def submit(self):
    #     subscribers = []
    #     subscribers.append(self.department_id.manager_id.user_id.id)

    #     for new_budget in self.new_ids:
    #         subscribers.append(new_budget.department_id.manager_id.user_id.id)

    #     self.message_subscribe_users(user_ids=subscribers)


class PamBudgetRevisionLine(models.Model):
    _name = 'pam.budget.revision.line'

    budget_revision_id  = fields.Many2one('pam.budget.revision', required=True, index=True)
    budget_type = fields.Selection([
        ('new', 'Pos Anggaran Baru'),
        ('old', 'Pos Anggaran Lama')
    ], default='new', required=True)

    revision_type = fields.Selection([
        ('update', 'Revisi'),
        ('delete', 'Hapus'),
        ('add', 'Penambahan')
    ], default='update', required=True)

    # New Budget
    department_id = fields.Many2one('hr.department', index=True)
    manager_name = fields.Char(compute='get_manager_name', strore=True)
    job_id = fields.Many2one('hr.job', index=True, string="Posisi")
    coa_id = fields.Many2one('pam.coa', string="Kode COA", index=True)
    coa_id_name = fields.Char(string="Nama COA", index=True)
    remark = fields.Char(string='Keterangan')

    # Old Budget
    budget_line2_id = fields.Many2one('pam.budget.line2', index=True, string='Kode Akun')
    budget_line3_id = fields.Many2one('pam.budget.line3', index=True, string='Anggaran Biaya')

    month_1_old       = fields.Float(string='I', default=0)
    month_2_old       = fields.Float(string='II', default=0)
    month_3_old       = fields.Float(string='III', default=0)
    month_4_old       = fields.Float(string='IV', default=0)
    month_5_old       = fields.Float(string='V', default=0)
    month_6_old       = fields.Float(string='VI', default=0)
    month_7_old       = fields.Float(string='VII', default=0)
    month_8_old       = fields.Float(string='VIII', default=0)
    month_9_old       = fields.Float(string='IX', default=0)
    month_10_old      = fields.Float(string='X', default=0)
    month_11_old      = fields.Float(string='XI', default=0)
    month_12_old      = fields.Float(string='XII', default=0)
    sub_total_old     = fields.Float(string='Semula', compute='compute_sub_total_old')

    month_1_new       = fields.Float(string='I', default=0)
    month_2_new       = fields.Float(string='II', default=0)
    month_3_new       = fields.Float(string='III', default=0)
    month_4_new       = fields.Float(string='IV', default=0)
    month_5_new       = fields.Float(string='V', default=0)
    month_6_new       = fields.Float(string='VI', default=0)
    month_7_new       = fields.Float(string='VII', default=0)
    month_8_new       = fields.Float(string='VIII', default=0)
    month_9_new       = fields.Float(string='IX', default=0)
    month_10_new      = fields.Float(string='X', default=0)
    month_11_new      = fields.Float(string='XI', default=0)
    month_12_new      = fields.Float(string='XII', default=0)
    sub_total_new     = fields.Float(string='Revisi', compute='compute_sub_total_new')

    sub_total_diff  = fields.Float(string="Selisih", compute='compute_sub_total_diff')

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name

    @api.onchange('budget_line2_id')
    def _domain_budget_line2(self):
        context = self.env.context

        budget_department_ids = []
        if context.get('budget_year'):
            budget_year = context.get('budget_year')
            budget_departments = self.env['pam.budget.line2'].search([('years', '=', budget_year)])
            for budget_department in budget_departments:
                budget_department_ids.append(budget_department.id)
            
            domain = [('id', 'in', budget_department_ids)]
        else:
            domain = [('id', '=', False)]

        return {'domain': {'budget_line2_id': domain}}

    @api.onchange('budget_line2_id')
    def _domain_budget_line3(self):
        if self.budget_line2_id:
            domain = [('budget_line2_id', '=', self.budget_line2_id.id)]
        else:
            domain = [('budget_line2_id', '=', False)]

        return {'domain': {'budget_line3_id': domain}}

    @api.onchange('budget_line3_id')
    def _get_budget_line3(self):
        budget_line_3 = self.env['pam.budget.line3'].search([('id', '=', self.budget_line3_id.id)])

        self.department_id = budget_line_3.budget_line2_id.department_id.id
        self.job_id = budget_line_3.job_id.id
        self.coa_id = budget_line_3.budget_line2_id.coa_id.id
        self.remark = budget_line_3.remark 

        self.month_1_old = budget_line_3.month_1_value
        self.month_2_old = budget_line_3.month_2_value
        self.month_3_old = budget_line_3.month_3_value
        self.month_4_old = budget_line_3.month_4_value
        self.month_5_old = budget_line_3.month_5_value
        self.month_6_old = budget_line_3.month_6_value
        self.month_7_old = budget_line_3.month_7_value
        self.month_8_old = budget_line_3.month_8_value
        self.month_9_old = budget_line_3.month_9_value
        self.month_10_old = budget_line_3.month_10_value
        self.month_11_old = budget_line_3.month_11_value
        self.month_12_old = budget_line_3.month_12_value

    def get_manager_name(self):
        if self.department_id:
            self.manager_name = self.department_id.manager_id.name
        else:
            self.manager_name = ''

    @api.onchange('department_id')
    def _onchange_department(self):
        if self.department_id:
            domain = [('department_id', '=', self.department_id.id)]
        else:
            domain = [('department_id', '=', False)]

        return {'domain': {'job_id': domain}}

    @api.depends('month_1_old', 'month_2_old', 'month_3_old', 'month_4_old', 'month_5_old', 'month_6_old', 'month_7_old', 'month_8_old', 'month_9_old', 'month_10_old', 'month_11_old', 'month_12_old')
    def compute_sub_total_old(self):
        self.sub_total_old = self.month_1_old + self.month_2_old + self.month_3_old + self.month_4_old + self.month_5_old + self.month_6_old + self.month_7_old + self.month_8_old + self.month_9_old + self.month_10_old + self.month_11_old + self.month_12_old

    @api.depends('month_1_new', 'month_2_new', 'month_3_new', 'month_4_new', 'month_5_new', 'month_6_new', 'month_7_new', 'month_8_new', 'month_9_new', 'month_10_new', 'month_11_new', 'month_12_new')
    def compute_sub_total_new(self):
        self.sub_total_new = self.month_1_new + self.month_2_new + self.month_3_new + self.month_4_new + self.month_5_new + self.month_6_new + self.month_7_new + self.month_8_new + self.month_9_new + self.month_10_new + self.month_11_new + self.month_12_new

    @api.depends('sub_total_old', 'sub_total_new')
    def compute_sub_total_diff(self):
        self.sub_total_diff = self.sub_total_new - self.sub_total_old