from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class PamBudgetChange(models.Model):
    _name = 'pam.budget.change'
    _rec_name = 'years'
    _inherit = ['mail.thread']

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
    department_id = fields.Many2one('hr.department', required=True, index=True)
    manager_name = fields.Char(compute='get_manager_name', strore=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('approved', 'Approved')
    ], default='draft')
    old_ids = fields.One2many('pam.budget.change.old', 'budget_change_id')
    new_ids = fields.One2many('pam.budget.change.new', 'budget_change_id')

    @api.depends('department_id')
    def get_manager_name(self):
        if self.department_id:
            self.manager_name = self.department_id.manager_id.name
        else:
            self.manager_name = ''

    def submit(self):
        subscribers = []
        subscribers.append(self.department_id.manager_id.user_id.id)

        for new_budget in self.new_ids:
            subscribers.append(new_budget.department_id.manager_id.user_id.id)

        self.message_subscribe_users(user_ids=subscribers)

        self.write({
            'state': 'submit'
        })

    def approve(self):
        budget_change_ids = []

        for old in self.old_ids:
            budget_change_ids.append(old.budget_line3_id.id)

        budget_revision = []
        for new in self.new_ids:

            budget_line3_val = {
                'job_id': new.job_id.id,
                'remark': new.remark,
                'month_1': new.month_1/1000,
                'month_2': new.month_2/1000,
                'month_3': new.month_3/1000,
                'month_4': new.month_4/1000,
                'month_5': new.month_5/1000,
                'month_6': new.month_6/1000,
                'month_7': new.month_7/1000,
                'month_8': new.month_8/1000,
                'month_9': new.month_9/1000,
                'month_10': new.month_10/1000,
                'month_11': new.month_11/1000,
                'month_12': new.month_12/1000
            }

            budget_line2_val = {
                'years': self.years,
                'name': new.coa_id.name,
                'department_id': new.department_id.id,
                'coa_id': new.coa_id.id,
                'line3_ids': [(0, 0, budget_line3_val)]
                }

            budget = self.env['pam.budget'].search([('years', '=', self.years)])
            budget_line1 = budget.line1_ids.search([('department_id', '=', new.department_id.id)])

            if budget_line1 == False:
                budget_line1_val = {
                    'years': self.years,
                    'name': new.department_id.name,
                    'department_id': new.department_id.id,
                    'line2_ids': [(0,0, budget_line2_val)]
                }

                budget_line1 = self.env['pam.budget.line1'].sudo().create(budget_line1_val)

            else:
                budget_line2 = self.env['pam.budget.line2'].search([('years', '=', self.years), ('department_id', '=', new.department_id.id), ('coa_id', '=', new.coa_id.id)])
                
                if budget_line2 == False:
                    budget_line1.sudo().create({
                        'line2_ids': [(0,0, budget_line2_val)]
                    })
                else:
                    budget_line2.sudo().update({
                        'line3_ids': [(0, 0, budget_line3_val)]
                    })


            if new.change_type == 'old':
                budget_change_ids.append(new.budget_line3_id.id)

        budget_line3 = self.env['pam.budget.line3'].search([('id', 'in', budget_change_ids)])
        budget_line3.update({
            'budget_state': 'inactive',
            'active': False
        })


        self.write({
            'state': 'approved'
        })


class PamBudgetChangeOld(models.Model):
    _name = 'pam.budget.change.old'

    budget_change_id  = fields.Many2one('pam.budget.change', required=True, index=True)
    # category_id = fields.Many2one('pam.budget.category', required=True, string="Uraian")
    budget_line2_id = fields.Many2one('pam.budget.line2', required=True, string='Kode Akun')
    budget_line3_id = fields.Many2one('pam.budget.line3', required=True, string='Anggaran Biaya')
    sub_total = fields.Float('pam.budget.line3', related='budget_line3_id.sub_total')

    @api.onchange('budget_line2_id')
    def _domain_budget_line2(self):
        context = self.env.context

        budget_department_ids = []
        if context.get('budget_year') and context.get('budget_department_id'):
            budget_year = context.get('budget_year')
            budget_department_id = context.get('budget_department_id')
            budget_departments = self.env['pam.budget.line2'].search([('department_id', '=', budget_department_id), ('years', '=', budget_year)])
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


class PamBudgetChangeNew(models.Model):
    _name = 'pam.budget.change.new'

    budget_change_id  = fields.Many2one('pam.budget.change', required=True, index=True)
    change_type = fields.Selection([
        ('new', 'Pos Anggaran Baru'),
        ('old', 'Pos Anggaran Lama')
    ], default='new')

    # New Budget
    department_id = fields.Many2one('hr.department', index=True)
    manager_name = fields.Char(compute='get_manager_name', strore=True)
    job_id = fields.Many2one('hr.job', index=True, string="Posisi")
    coa_id = fields.Many2one('pam.coa', string="Code COA", index=True)
    coa_id_name = fields.Char(string='Name COA')
    remark = fields.Char(string='Keterangan')

    # Old Budget
    budget_line2_id = fields.Many2one('pam.budget.line2', index=True, string='Kode Akun')
    budget_line3_id = fields.Many2one('pam.budget.line3', index=True, string='Anggaran Biaya')

    month_1       = fields.Float(string='I', default=0)
    month_2       = fields.Float(string='II', default=0)
    month_3       = fields.Float(string='III', default=0)
    month_4       = fields.Float(string='IV', default=0)
    month_5       = fields.Float(string='V', default=0)
    month_6       = fields.Float(string='VI', default=0)
    month_7       = fields.Float(string='VII', default=0)
    month_8       = fields.Float(string='VIII', default=0)
    month_9       = fields.Float(string='IX', default=0)
    month_10      = fields.Float(string='X', default=0)
    month_11      = fields.Float(string='XI', default=0)
    month_12      = fields.Float(string='XII', default=0)
    sub_total = fields.Float(string='Total', compute='compute_sub_total', store=True)

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name

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

        self.month_1 = budget_line_3.month_1_value
        self.month_2 = budget_line_3.month_2_value
        self.month_3 = budget_line_3.month_3_value
        self.month_4 = budget_line_3.month_4_value
        self.month_5 = budget_line_3.month_5_value
        self.month_6 = budget_line_3.month_6_value
        self.month_7 = budget_line_3.month_7_value
        self.month_8 = budget_line_3.month_8_value
        self.month_9 = budget_line_3.month_9_value
        self.month_10 = budget_line_3.month_10_value
        self.month_11 = budget_line_3.month_11_value
        self.month_12 = budget_line_3.month_12_value

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

    @api.depends('month_1', 'month_2', 'month_3', 'month_4', 'month_5', 'month_6', 'month_7', 'month_8', 'month_9', 'month_10', 'month_11', 'month_12')
    def compute_sub_total(self):
        self.sub_total = self.month_1 + self.month_2 + self.month_3 + self.month_4 + self.month_5 + self.month_6 + self.month_7 + self.month_8 + self.month_9 + self.month_10 + self.month_11 + self.month_12


