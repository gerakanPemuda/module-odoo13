from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class PamBudgetEntry(models.Model):
    _name = 'pam.budget.entry'
    _rec_name = 'years'
    _description = 'Input Anggaran'
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

    years = fields.Selection(_get_years, string='Tahun Anggaran', default=_default_year, required=True)
    department_id = fields.Many2one('hr.department', required=True, index=True)
    manager_name = fields.Char('hr.department', related="department_id.manager_id.name")
    job_id = fields.Many2one('hr.job', required=True, index=True, string="Posisi")

    budget_type = fields.Selection([
        ('ops', 'Biaya Operasi, Pemeliharaan dan Tenaga Kerja'),
        ('inv', 'Anggaran Kebutuhan Alat/alat dan Investasi (AKA)')
    ], required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('approved', 'Approved')
    ], default='draft', track_visibility=True)
    line_ids = fields.One2many('pam.budget.entry.line', 'budget_entry_id')

    is_approver = fields.Boolean(compute='_compute_approver')

    @api.model
    def create(self, values):
        result = super(PamBudgetEntry, self).create(values)

        result.message_subscribe_users(user_ids=[result.department_id.manager_id.user_id.id])

        return result

    # def _track_subtype(self, init_values):
    #     if 'state' in init_values:
    #         return 'mail.mt_comment'
    #     return False

    @api.depends('year')
    def _compute_year(self):
        self.year_selected = self.year

    @api.onchange('department_id')
    def _onchange_department(self):
        if self.department_id:
            domain = [('department_id', '=', self.department_id.id)]
        else:
            domain = [('department_id', '=', False)]

        return {'domain': {'job_id': domain}}

    def submit(self):

        self.write({
            'state': 'submit'
        })

        subject = 'Pengajuan Anggaran ' + dict(self._fields['budget_type'].selection).get(self.budget_type)

        body = '<p>Dear All,' + '</p>'
        body += '<br>'
        body += '<p>Anggaran ' + dict(self._fields['budget_type'].selection).get(self.budget_type) + ' Tahun Anggaran ' + self.years + ', telah diajukan.</p>'
        body += '<p>Saat ini menunggu pemeriksaan dan persetujuan dari Bpk/Ibu ' + self.manager_name +'</p>'

        self.message_post(body=body, subject=subject, subtype="mt_comment")

    def _compute_approver(self):
        if self._uid == self.department_id.manager_id.user_id.id:
            self.is_approver = True
        else:
            self.is_approver = False

    def approve(self):

        self.write({
            'state': 'approved'
        })


class PamBudgetEntryLine(models.Model):
    _name = 'pam.budget.entry.line'

    budget_entry_id  = fields.Many2one('pam.budget.entry', required=True, index=True, ondelete='cascade')
    coa_id = fields.Many2one('pam.coa', string="Kode COA", required=True, index=True)
    coa_id_name = fields.Char(string='Nama COA')
    remark = fields.Char(string='Keterangan')
    month_1       = fields.Float(string='I', default=0, compute='_compute_real_value', store=True)
    month_1_entry = fields.Float(string='I', default=0)
    month_2       = fields.Float(string='II', default=0, compute='_compute_real_value', store=True)
    month_2_entry = fields.Float(string='II', default=0)
    month_3       = fields.Float(string='III', default=0, compute='_compute_real_value', store=True)
    month_3_entry = fields.Float(string='III', default=0)
    month_4       = fields.Float(string='IV',default=0, compute='_compute_real_value', store=True)
    month_4_entry = fields.Float(string='IV', default=0)
    month_5       = fields.Float(string='V',default=0, compute='_compute_real_value', store=True)
    month_5_entry = fields.Float(string='V', default=0)
    month_6       = fields.Float(string='VI',default=0, compute='_compute_real_value', store=True)
    month_6_entry = fields.Float(string='VI', default=0)
    month_7       = fields.Float(string='VII',default=0, compute='_compute_real_value', store=True)
    month_7_entry = fields.Float(string='VII', default=0)
    month_8       = fields.Float(string='VIII',default=0, compute='_compute_real_value', store=True)
    month_8_entry = fields.Float(string='VIII', default=0)
    month_9       = fields.Float(string='IX',default=0, compute='_compute_real_value', store=True)
    month_9_entry = fields.Float(string='IX', default=0)
    month_10      = fields.Float(string='X',default=0, compute='_compute_real_value', store=True)
    month_10_entry= fields.Float(string='X', default=0)
    month_11      = fields.Float(string='XI',default=0, compute='_compute_real_value', store=True)
    month_11_entry= fields.Float(string='XI', default=0)
    month_12      = fields.Float(string='XII',default=0, compute='_compute_real_value', store=True)
    month_12_entry= fields.Float(string='XII', default=0)

    @api.onchange('coa_id')
    def onchange_coa_id(self):
        if self.coa_id:
            self.coa_id_name = self.coa_id.name

    def _count_real_value(self, entry_value):
        return entry_value * 1000

    @api.depends('month_1_entry', 'month_2_entry', 'month_3_entry', 'month_4_entry', 'month_5_entry', 'month_6_entry', 'month_7_entry', 'month_8_entry', 'month_9_entry', 'month_10_entry', 'month_11_entry', 'month_12_entry')
    def _compute_real_value(self):
        self.month_1 = self._count_real_value(self.month_1_entry)
        self.month_2 = self._count_real_value(self.month_2_entry)
        self.month_3 = self._count_real_value(self.month_3_entry)
        self.month_4 = self._count_real_value(self.month_4_entry)
        self.month_5 = self._count_real_value(self.month_5_entry)
        self.month_6 = self._count_real_value(self.month_6_entry)
        self.month_7 = self._count_real_value(self.month_7_entry)
        self.month_8 = self._count_real_value(self.month_8_entry)
        self.month_9 = self._count_real_value(self.month_9_entry)
        self.month_10= self._count_real_value(self.month_10_entry)
        self.month_11= self._count_real_value(self.month_11_entry)
        self.month_12= self._count_real_value(self.month_12_entry)